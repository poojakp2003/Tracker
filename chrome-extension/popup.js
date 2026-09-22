
/**
 * Productivity Tracker - Popup Controller
 * Manages status indicators, user authentication, incognito detection, and activity feeds.
 */

document.addEventListener("DOMContentLoaded", async () => {
  // DOM Elements
  const trackingToggle = document.getElementById("tracking-toggle");
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  const queueBadge = document.getElementById("queue-badge");
  const syncNowBtn = document.getElementById("sync-now-btn");
  const lastSyncTimeEl = document.getElementById("last-sync-time");

  // Incognito Elements
  const incognitoBadge = document.getElementById("incognito-badge");
  const incognitoHelp = document.getElementById("incognito-help-text");
  const incognitoGuide = document.getElementById("incognito-guide");

  // Auth Elements
  const loggedInView = document.getElementById("logged-in-view");
  const loggedOutView = document.getElementById("logged-out-view");
  const userEmailEl = document.getElementById("user-email");
  const logoutBtn = document.getElementById("logout-btn");
  const loginForm = document.getElementById("login-form");
  const loginEmail = document.getElementById("login-email");
  const loginPassword = document.getElementById("login-password");
  const apiUrlInput = document.getElementById("api-url");
  const loginSubmitBtn = document.getElementById("login-submit-btn");
  const authErrorMsg = document.getElementById("auth-error-msg");

  // Recent Visits Elements
  const visitsList = document.getElementById("visits-list");
  const clearQueueBtn = document.getElementById("clear-queue-btn");

  // ---- Dynamically created elements (no popup.html changes needed) ----

  // Red banner shown when the session has expired
  const sessionBanner = document.createElement("div");
  sessionBanner.id = "session-banner";
  sessionBanner.textContent = "Session expired. Please log in again to resume syncing.";
  sessionBanner.style.cssText =
    "display:none;margin:8px 12px;padding:8px 10px;border-radius:8px;" +
    "background:rgba(225,29,72,0.15);border:1px solid rgba(225,29,72,0.5);" +
    "color:#fda4af;font-size:12px;line-height:1.4;";
  document.body.prepend(sessionBanner);

  // Small line under "Last synced" that shows the latest sync error
  const syncErrorEl = document.createElement("div");
  syncErrorEl.id = "sync-error";
  syncErrorEl.style.cssText = "display:none;margin-top:4px;font-size:11px;color:#fda4af;";
  if (lastSyncTimeEl && lastSyncTimeEl.parentNode) {
    lastSyncTimeEl.parentNode.appendChild(syncErrorEl);
  }

  function clearBadge() {
    try {
      chrome.action.setBadgeText({ text: "" });
    } catch {
      // ignore
    }
  }

  /**
   * Check Incognito support permission per Chrome extension rules.
   */
  function checkIncognitoSupport() {
    if (chrome.extension && typeof chrome.extension.isAllowedIncognitoAccess === "function") {
      chrome.extension.isAllowedIncognitoAccess((isAllowed) => {
        if (isAllowed) {
          incognitoBadge.textContent = "Active";
          incognitoBadge.className = "incognito-status-badge allowed";
          incognitoHelp.textContent = "Incognito browsing is permitted & tracked.";
          incognitoGuide.style.display = "none";
        } else {
          incognitoBadge.textContent = "Disabled";
          incognitoBadge.className = "incognito-status-badge blocked";
          incognitoHelp.textContent = "Chrome requires user permission to track private windows.";
          incognitoGuide.style.display = "block";
        }
      });
    } else {
      incognitoBadge.textContent = "Standard";
      incognitoBadge.className = "incognito-status-badge allowed";
      incognitoGuide.style.display = "none";
    }
  }

  /**
   * Format relative or short timestamp.
   */
  function formatTimestamp(isoStr) {
    if (!isoStr) return "Just now";
    try {
      const d = new Date(isoStr);
      const diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
      if (diffSec < 60) return `${Math.max(diffSec, 1)}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "Recently";
    }
  }

  /**
   * Render the recent visits list.
   */
  function renderVisits(visits) {
    if (!visits || visits.length === 0) {
      visitsList.innerHTML = '<div class="empty-state">No tabs recorded yet. Start browsing!</div>';
      return;
    }

    visitsList.innerHTML = "";
    visits.forEach((v) => {
      const item = document.createElement("div");
      item.className = `visit-item ${v.isYouTube ? "youtube" : ""}`;

      const top = document.createElement("div");
      top.className = "visit-item-top";

      const title = document.createElement("span");
      title.className = "visit-title";
      title.textContent = v.title || v.url;
      title.title = v.title || v.url;
      top.appendChild(title);

      const badges = document.createElement("div");
      badges.style.display = "flex";
      badges.style.gap = "4px";

      if (v.isYouTube) {
        const ytBadge = document.createElement("span");
        ytBadge.className = "visit-badge yt";
        ytBadge.textContent = v.isShort ? "Shorts" : "YouTube";
        badges.appendChild(ytBadge);

        if (v.watchedSeconds) {
          const timeBadge = document.createElement("span");
          timeBadge.className = "visit-badge";
          timeBadge.style.background = "rgba(16, 185, 129, 0.2)";
          timeBadge.style.color = "#6ee7b7";
          timeBadge.textContent = `${v.watchedSeconds}s`;
          badges.appendChild(timeBadge);
        }
      }

      if (v.isIncognito) {
        const incBadge = document.createElement("span");
        incBadge.className = "visit-badge incognito";
        incBadge.textContent = "Incognito";
        badges.appendChild(incBadge);
      }

      top.appendChild(badges);

      const bottom = document.createElement("div");
      bottom.className = "visit-item-bottom";

      const urlEl = document.createElement("span");
      urlEl.className = "visit-url";
      try {
        const parsed = new URL(v.url);
        urlEl.textContent = parsed.hostname + (parsed.pathname !== "/" ? parsed.pathname : "");
      } catch {
        urlEl.textContent = v.url;
      }
      bottom.appendChild(urlEl);

      const timeEl = document.createElement("span");
      timeEl.textContent = formatTimestamp(v.timestamp);
      bottom.appendChild(timeEl);

      item.appendChild(top);
      item.appendChild(bottom);
      visitsList.appendChild(item);
    });
  }

  /**
   * Refresh all UI state from chrome.storage.local.
   */
  async function refreshUI() {
    const data = await chrome.storage.local.get([
      "apiUrl",
      "token",
      "refreshToken",
      "authState",
      "userEmail",
      "trackingEnabled",
      "eventQueue",
      "recentVisits",
      "lastSyncTime",
      "syncStatus",
    ]);

    const sessionExpired = data.authState === "expired";
    const loggedIn = Boolean(data.token) && !sessionExpired;

    // Master Tracking Switch
    const isTracking = data.trackingEnabled !== false;
    trackingToggle.checked = isTracking;

    // Queue count
    const queue = data.eventQueue || [];
    queueBadge.textContent = `${queue.length} buffered`;

    // Last Sync time
    if (data.lastSyncTime) {
      lastSyncTimeEl.textContent = `Synced ${formatTimestamp(data.lastSyncTime)}`;
    } else {
      lastSyncTimeEl.textContent = "Never synced";
    }

    // Last sync error line
    const okStatuses = ["Ready", "Synced", "Syncing..."];
    if (data.syncStatus && !okStatuses.includes(data.syncStatus) && !sessionExpired) {
      syncErrorEl.textContent = data.syncStatus;
      syncErrorEl.style.display = "block";
    } else {
      syncErrorEl.style.display = "none";
    }

    // Session expired banner
    sessionBanner.style.display = sessionExpired ? "block" : "none";

    // Status Dot & Text
    if (sessionExpired) {
      statusDot.className = "status-dot error";
      statusText.textContent = "Session Expired";
    } else if (!isTracking) {
      statusDot.className = "status-dot warning";
      statusText.textContent = "Tracking Paused";
    } else if (!data.token) {
      statusDot.className = "status-dot error";
      statusText.textContent = "Login Required";
    } else if (data.syncStatus === "Syncing...") {
      statusDot.className = "status-dot active";
      statusText.textContent = "Syncing...";
    } else if (data.syncStatus && data.syncStatus.startsWith("Network Error")) {
      statusDot.className = "status-dot error";
      statusText.textContent = "Offline / Error";
    } else {
      statusDot.className = "status-dot active";
      statusText.textContent = "Active & Logging";
    }

    // Auth state view
    if (loggedIn) {
      loggedInView.style.display = "block";
      loggedOutView.style.display = "none";
      userEmailEl.textContent = data.userEmail || "Authenticated User";
    } else {
      loggedInView.style.display = "none";
      loggedOutView.style.display = "block";
      if (data.apiUrl) {
        apiUrlInput.value = data.apiUrl;
      }
      // Prefill email when the session expired so re-login is quick
      if (sessionExpired && data.userEmail && !loginEmail.value) {
        loginEmail.value = data.userEmail;
      }
    }

    // Recent visits feed
    renderVisits(data.recentVisits || []);

    // Check Incognito permission status
    checkIncognitoSupport();
  }

  // Initial load
  await refreshUI();

  // Listen for storage changes from background service worker
  chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === "local") {
      refreshUI();
    }
  });

  // Toggle master tracking
  trackingToggle.addEventListener("change", async (e) => {
    const isEnabled = e.target.checked;
    await chrome.storage.local.set({ trackingEnabled: isEnabled });
    await refreshUI();
  });

  // Manual Sync Button
  syncNowBtn.addEventListener("click", async () => {
    syncNowBtn.disabled = true;
    syncNowBtn.textContent = "Syncing...";
    try {
      await chrome.runtime.sendMessage({ action: "SYNC_NOW" });
    } catch (err) {
      console.warn("Sync message error:", err);
    } finally {
      syncNowBtn.disabled = false;
      syncNowBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="1 4 1 10 7 10"></polyline>
          <polyline points="23 20 23 14 17 14"></polyline>
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
        </svg>
        Sync Now
      `;
      await refreshUI();
    }
  });

  // Clear Queue Button
  clearQueueBtn.addEventListener("click", async () => {
    await chrome.runtime.sendMessage({ action: "CLEAR_QUEUE" });
    await refreshUI();
  });

  // Login Form Submission
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    authErrorMsg.style.display = "none";
    authErrorMsg.textContent = "";

    const email = loginEmail.value.trim();
    const password = loginPassword.value;
    const apiUrl = apiUrlInput.value.trim() || "http://127.0.0.1:8000";

    if (!email || !password) {
      authErrorMsg.textContent = "Email and password are required.";
      authErrorMsg.style.display = "block";
      return;
    }

    loginSubmitBtn.disabled = true;
    loginSubmitBtn.textContent = "Connecting...";

    try {
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Login failed (${response.status})`);
      }

      const data = await response.json();
      await chrome.storage.local.set({
        token: data.access_token,
        refreshToken: data.refresh_token || null,
        authState: "ok",
        userEmail: email,
        apiUrl: apiUrl,
        syncStatus: "Ready",
      });
      clearBadge();

      // Reset form
      loginPassword.value = "";

      // Trigger sync
      chrome.runtime.sendMessage({ action: "SYNC_NOW" }).catch(() => { });

      await refreshUI();
    } catch (err) {
      authErrorMsg.textContent = err.message || "Failed to reach backend server.";
      authErrorMsg.style.display = "block";
    } finally {
      loginSubmitBtn.disabled = false;
      loginSubmitBtn.textContent = "Connect & Login";
    }
  });

  // Logout Button
  logoutBtn.addEventListener("click", async () => {
    await chrome.storage.local.remove(["token", "refreshToken", "authState", "userEmail"]);
    await chrome.storage.local.set({ syncStatus: "Ready" });
    clearBadge();
    await refreshUI();
  });
});