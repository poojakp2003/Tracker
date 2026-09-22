/**
 * Productivity & Activity Tracker - Chrome Extension Service Worker (Manifest V3)
 * Handles tab change detection, YouTube identification, event buffering, and batch dispatch to FastAPI.
 */

const DEFAULT_API_URL = "http://127.0.0.1:8000";
const BATCH_SIZE_THRESHOLD = 5;
const FLUSH_ALARM_NAME = "flush_tracker_queue";

// In-memory cache to prevent duplicate tab events (tabId -> { url, timestamp })
const lastTabState = new Map();

let flushing = false; // prevents overlapping syncs
let refreshPromise = null; // prevents parallel refresh calls

/* ------------------------------------------------------------------ */
/* Setup                                                               */
/* ------------------------------------------------------------------ */

chrome.runtime.onInstalled.addListener(async () => {
  console.log("[Tracker] Extension installed / reloaded.");

  const current = await chrome.storage.local.get([
    "apiUrl",
    "trackingEnabled",
    "eventQueue",
    "recentVisits",
    "lastSyncTime",
  ]);

  await chrome.storage.local.set({
    apiUrl: current.apiUrl || DEFAULT_API_URL,
    trackingEnabled: current.trackingEnabled !== undefined ? current.trackingEnabled : true,
    eventQueue: current.eventQueue || [],
    recentVisits: current.recentVisits || [],
    lastSyncTime: current.lastSyncTime || null,
    syncStatus: "Ready",
  });

  ensureFlushAlarm();
});

function ensureFlushAlarm() {
  chrome.alarms.get(FLUSH_ALARM_NAME, (alarm) => {
    if (!alarm) chrome.alarms.create(FLUSH_ALARM_NAME, { periodInMinutes: 0.5 });
  });
}
ensureFlushAlarm();
chrome.runtime.onStartup.addListener(ensureFlushAlarm);

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === FLUSH_ALARM_NAME) {
    flushQueue();
  }
});

/* ------------------------------------------------------------------ */
/* Auth helpers                                                        */
/* ------------------------------------------------------------------ */

async function refreshAccessToken() {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const { apiUrl, refreshToken } = await chrome.storage.local.get(["apiUrl", "refreshToken"]);
    if (!refreshToken) throw new Error("NO_REFRESH_TOKEN");

    const res = await fetch(`${apiUrl || DEFAULT_API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if ([400, 401, 403].includes(res.status)) throw new Error("REFRESH_FAILED");
    if (!res.ok) throw new Error("REFRESH_SERVER_ERROR");

    const data = await res.json();
    await chrome.storage.local.set({
      token: data.access_token,
      refreshToken: data.refresh_token || refreshToken,
      authState: "ok",
    });
    chrome.action.setBadgeText({ text: "" });
    return data.access_token;
  })().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

async function markSessionExpired() {
  await chrome.storage.local.set({
    authState: "expired",
    syncStatus: "Session expired - please log in again",
  });
  chrome.action.setBadgeText({ text: "!" });
  chrome.action.setBadgeBackgroundColor({ color: "#e11d48" });
}

// fetch wrapper: on 401, refresh once and retry once
async function authFetch(path, options = {}) {
  const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);
  const base = apiUrl || DEFAULT_API_URL;
  const send = (t) =>
    fetch(`${base}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        "Content-Type": "application/json",
        Authorization: `Bearer ${t}`,
      },
    });

  let res = await send(token);
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    res = await send(newToken);
  }
  return res;
}

/* ------------------------------------------------------------------ */
/* URL helpers                                                         */
/* ------------------------------------------------------------------ */

function isValidWebUrl(url) {
  if (!url || typeof url !== "string") return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function parseYouTubeDetails(url) {
  if (!url || typeof url !== "string") {
    return { isYouTube: false, videoId: null, isShort: false };
  }
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();

    if (!host.includes("youtube.com") && host !== "youtu.be") {
      return { isYouTube: false, videoId: null, isShort: false };
    }

    // 1. YouTube Shorts: /shorts/<id>
    if (parsed.pathname.startsWith("/shorts/")) {
      const parts = parsed.pathname.split("/").filter(Boolean);
      if (parts.length >= 2) {
        const videoId = parts[1].split("?")[0].split("&")[0];
        if (videoId) {
          return { isYouTube: true, videoId, isShort: true };
        }
      }
    }

    // 2. Standard Watch page: /watch?v=<id>
    if (parsed.pathname === "/watch" || parsed.pathname.startsWith("/watch")) {
      const videoId = parsed.searchParams.get("v");
      if (videoId) {
        return { isYouTube: true, videoId, isShort: false };
      }
    }

    // 3. youtu.be/<id>
    if (host === "youtu.be") {
      const videoId = parsed.pathname.replace("/", "").trim();
      if (videoId) {
        return { isYouTube: true, videoId, isShort: false };
      }
    }

    return { isYouTube: true, videoId: null, isShort: false };
  } catch {
    // Ignore URL parse errors
  }
  return { isYouTube: false, videoId: null, isShort: false };
}

/**
 * While a page is still loading, Chrome reports the URL (without "https://" and "www.")
 * as the tab title. Treat that as "no real title yet".
 */
function isPlaceholderTitle(title, url) {
  if (!title || !title.trim()) return true;
  const strip = (s) =>
    s
      .trim()
      .replace(/^https?:\/\//i, "")
      .replace(/^www\./i, "")
      .replace(/\/$/, "");
  return strip(title) === strip(url);
}

/* ------------------------------------------------------------------ */
/* Event capture                                                       */
/* ------------------------------------------------------------------ */

async function enqueueBrowserVisit(tab, triggerType = "update") {
  const { trackingEnabled } = await chrome.storage.local.get(["trackingEnabled"]);

  if (trackingEnabled === false) {
    return;
  }

  const url = tab.url;
  if (!isValidWebUrl(url)) {
    return;
  }

  // Resolve a real title. While a page loads, Chrome shows the URL as the title.
  let tabTitle = tab.title;
  if (isPlaceholderTitle(tabTitle, url)) {
    if (triggerType === "updated") {
      // Early URL-change event: wait for the "complete" event, which carries the real title
      return;
    }
    if (triggerType === "complete") {
      // Some pages set their title a moment after "complete", so wait and read it again
      await new Promise((resolve) => setTimeout(resolve, 1500));
      try {
        const fresh = await chrome.tabs.get(tab.id);
        if (fresh && fresh.url === url && fresh.title) {
          tabTitle = fresh.title;
        }
      } catch {
        return; // tab was closed
      }
    }
  }

  const now = Date.now();
  const lastState = lastTabState.get(tab.id);
  const ytInfo = parseYouTubeDetails(url);

  // Deduplicate: YouTube rewrites the title after load, so use a longer window there
  const dedupeWindowMs = ytInfo.isYouTube ? 60000 : 3500;
  if (lastState && lastState.url === url && now - lastState.timestamp < dedupeWindowMs) {
    return;
  }

  // Update in-memory tab state
  lastTabState.set(tab.id, { url, timestamp: now });

  const cleanTitle = tabTitle || new URL(url).hostname;
  const timestampIso = new Date(now).toISOString();

  const eventItem = {
    id: `${now}_${Math.random().toString(36).substring(2, 7)}`,
    browser: "Chrome",
    url: url,
    title: cleanTitle,
    timestamp: timestampIso,
    isYouTube: ytInfo.isYouTube,
    videoId: ytInfo.videoId,
    isIncognito: tab.incognito || false,
    triggerType,
  };

  const stored = await chrome.storage.local.get(["eventQueue", "recentVisits"]);
  const queue = stored.eventQueue || [];
  const recent = stored.recentVisits || [];

  queue.push(eventItem);

  // Keep last 10 visits for popup preview
  const updatedRecent = [
    {
      url: eventItem.url,
      title: eventItem.title,
      timestamp: eventItem.timestamp,
      isYouTube: eventItem.isYouTube,
      isIncognito: eventItem.isIncognito,
    },
    ...recent.slice(0, 9),
  ];

  await chrome.storage.local.set({
    eventQueue: queue,
    recentVisits: updatedRecent,
  });

  console.log(`[Tracker] Logged visit: ${cleanTitle} (${url}) [Queue: ${queue.length}]`);

  if (queue.length >= BATCH_SIZE_THRESHOLD) {
    flushQueue();
  }
}

/* ------------------------------------------------------------------ */
/* Tab listeners                                                       */
/* ------------------------------------------------------------------ */

// Listen for tab updates: page load finished, or the URL changed (single-page apps)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    enqueueBrowserVisit(tab, "complete");
  } else if (changeInfo.url) {
    enqueueBrowserVisit(tab, "updated");
  }
});

// Listen for tab activation (user switched to an existing tab)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab && tab.url) {
      enqueueBrowserVisit(tab, "activated");
    }
  } catch (err) {
    // Tab might have been closed immediately
  }
});

/* ------------------------------------------------------------------ */
/* Sync                                                                */
/* ------------------------------------------------------------------ */

async function flushQueue() {
  if (flushing) return { success: false, error: "Sync already running" };
  flushing = true;

  try {
    const { eventQueue = [], token, authState } = await chrome.storage.local.get([
      "eventQueue",
      "token",
      "authState",
    ]);

    if (eventQueue.length === 0) return { success: true, count: 0 };

    if (!token || authState === "expired") {
      console.warn("[Tracker] Cannot flush queue: not authenticated. Please log in via popup.");
      await chrome.storage.local.set({ syncStatus: "Authentication Required" });
      return { success: false, error: "Authentication Required" };
    }

    const batch = eventQueue.slice(0, 30);
    const sentIds = new Set(batch.map((e) => e.id));

    await chrome.storage.local.set({ syncStatus: "Syncing..." });

    const res = await authFetch("/track/browser-activity", {
      method: "POST",
      body: JSON.stringify(
        batch.map(({ browser, url, title, timestamp }) => ({ browser, url, title, timestamp }))
      ),
    });

    if (res.status === 201) {
      // Re-read the queue: new events may have arrived while the request was in flight
      const { eventQueue: latest = [] } = await chrome.storage.local.get("eventQueue");
      await chrome.storage.local.set({
        eventQueue: latest.filter((e) => !sentIds.has(e.id)),
        lastSyncTime: new Date().toISOString(),
        syncStatus: "Synced",
        authState: "ok",
      });
      console.log(`[Tracker] Successfully dispatched ${batch.length} records.`);
      return { success: true, count: batch.length };
    }

    const errData = await res.json().catch(() => ({}));
    const msg = errData.detail || `Server Error (${res.status})`;
    console.warn(`[Tracker] Server rejected sync (${res.status}): ${msg}`);
    await chrome.storage.local.set({ syncStatus: msg });
    return { success: false, error: msg };
  } catch (err) {
    if (["REFRESH_FAILED", "NO_REFRESH_TOKEN"].includes(err.message)) {
      await markSessionExpired();
      return { success: false, error: "Session expired" };
    }
    console.error("[Tracker] Failed to connect to server:", err);
    await chrome.storage.local.set({ syncStatus: "Network Error: Server Unreachable" });
    return { success: false, error: err.message };
  } finally {
    flushing = false;
  }
}

/* ------------------------------------------------------------------ */
/* YouTube sessions from content script                                */
/* ------------------------------------------------------------------ */

async function handleYouTubeSession(data) {
  const { trackingEnabled, token } = await chrome.storage.local.get(["trackingEnabled", "token"]);

  if (trackingEnabled === false) {
    return { success: false, reason: "Tracking paused" };
  }

  const isShort = data.isShort || false;
  const videoTitle = data.video_title || (isShort ? "YouTube Short" : "YouTube Video");

  // 1. Update recentVisits in popup preview
  const stored = await chrome.storage.local.get(["recentVisits"]);
  const recent = stored.recentVisits || [];
  const updatedRecent = [
    {
      url: data.url,
      title: videoTitle,
      timestamp: data.timestamp || new Date().toISOString(),
      isYouTube: true,
      isShort: isShort,
      watchedSeconds: data.watched_time_seconds,
    },
    ...recent.slice(0, 9),
  ];
  await chrome.storage.local.set({ recentVisits: updatedRecent });

  if (!token) {
    console.warn("[Tracker] Cannot send YouTube activity: Not authenticated. Please log in via popup.");
    return { success: false, reason: "Not authenticated" };
  }

  try {
    // 2. POST /track/youtube-activity
    const ytRes = await authFetch("/track/youtube-activity", {
      method: "POST",
      body: JSON.stringify({
        video_id: data.video_id,
        video_title: videoTitle,
        url: data.url,
        watched_time_seconds: data.watched_time_seconds || 15,
        timestamp: data.timestamp || new Date().toISOString(),
      }),
    });

    if (ytRes.status === 201) {
      console.log(
        `[Tracker] Logged YouTube ${isShort ? "Short" : "video"}: ${videoTitle} (${data.watched_time_seconds}s)`
      );
    } else {
      const err = await ytRes.json().catch(() => ({}));
      console.warn(`[Tracker] YouTube tracking rejected (${ytRes.status}):`, err);
    }

    // 3. Also POST to /track/browser-activity so it shows in the Browser Activity table
    //    (first chunk only, so one video does not create many rows)
    if (!data.isContinuation) {
      await authFetch("/track/browser-activity", {
        method: "POST",
        body: JSON.stringify([
          {
            browser: "Chrome",
            url: data.url,
            title: videoTitle,
            timestamp: data.timestamp || new Date().toISOString(),
          },
        ]),
      });
    }
  } catch (err) {
    if (["REFRESH_FAILED", "NO_REFRESH_TOKEN"].includes(err.message)) {
      await markSessionExpired();
      return { success: false, reason: "Session expired" };
    }
    console.error("[Tracker] Failed to dispatch YouTube activity:", err);
  }

  return { success: true };
}

/* ------------------------------------------------------------------ */
/* Messages from popup / content scripts                               */
/* ------------------------------------------------------------------ */

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "TRACK_YOUTUBE_SESSION") {
    handleYouTubeSession(request.data).then((res) => sendResponse(res));
    return true;
  }

  if (request.action === "SYNC_NOW") {
    flushQueue().then((res) => sendResponse(res));
    return true;
  }

  if (request.action === "CLEAR_QUEUE") {
    chrome.storage.local.set({ eventQueue: [] }).then(() => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === "CHECK_INCOGNITO") {
    chrome.extension.isAllowedIncognitoAccess((isAllowed) => {
      sendResponse({ isAllowed });
    });
    return true;
  }
});