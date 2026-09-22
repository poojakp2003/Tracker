/**
 * Productivity Tracker - YouTube & Shorts Content Script
 * Directly monitors YouTube playback, in-page SPA navigation, Shorts scrolling,
 * and exact watch duration for learning analytics.
 */

(function () {
  let currentVideoId = null;
  let currentUrl = null;
  let currentTitle = null;
  let previousTitle = null;
  let accumulatedWatchSeconds = 0;
  let lastTickTime = Date.now();
  let isWatchingShort = false;
  let chunkCount = 0; // chunks already sent for the current video

  /**
   * Extract video ID and type from any YouTube URL.
   */
  function parseYouTubeUrl(urlStr) {
    if (!urlStr) return { isYouTube: false, videoId: null, isShort: false };
    try {
      const url = new URL(urlStr);
      const host = url.hostname.toLowerCase();

      if (!host.includes("youtube.com") && host !== "youtu.be") {
        return { isYouTube: false, videoId: null, isShort: false };
      }

      // 1. YouTube Shorts: /shorts/<id>
      if (url.pathname.startsWith("/shorts/")) {
        const parts = url.pathname.split("/").filter(Boolean);
        if (parts.length >= 2) {
          const rawId = parts[1].split("?")[0].split("&")[0];
          if (rawId) {
            return { isYouTube: true, videoId: rawId, isShort: true };
          }
        }
      }

      // 2. Standard Watch: /watch?v=<id>
      if (url.pathname === "/watch" || url.pathname.startsWith("/watch")) {
        const rawId = url.searchParams.get("v");
        if (rawId) {
          return { isYouTube: true, videoId: rawId, isShort: false };
        }
      }

      // 3. Shortened youtu.be/<id>
      if (host === "youtu.be") {
        const rawId = url.pathname.replace("/", "").trim();
        if (rawId) {
          return { isYouTube: true, videoId: rawId, isShort: false };
        }
      }

      return { isYouTube: true, videoId: null, isShort: false };
    } catch {
      return { isYouTube: false, videoId: null, isShort: false };
    }
  }

  /**
   * Strip notification counts and the " - YouTube" suffix. Returns "" for a bare "YouTube".
   */
  function cleanTitle(raw) {
    if (!raw) return "";
    const cleaned = raw
      .replace(/^\(\d+\)\s*/, "")
      .replace(/\s*-\s*YouTube\s*$/i, "")
      .trim();
    return /^youtube$/i.test(cleaned) ? "" : cleaned;
  }

  /**
   * Read the current video title from the DOM or document.title. Returns "" if none is usable.
   */
  function readTitle(isShort) {
    let title = "";

    if (isShort) {
      const activeShort = document.querySelector(
        "ytd-reel-video-renderer[is-active] #overlay #title, ytd-reel-video-renderer[is-active] h2.title, h2.yt-shorts-title"
      );
      if (activeShort && activeShort.textContent.trim()) {
        title = activeShort.textContent.trim();
      }
    } else {
      const standardTitle = document.querySelector(
        "ytd-watch-metadata #title h1 yt-formatted-string, #title h1.ytd-video-primary-info-renderer"
      );
      if (standardTitle && standardTitle.textContent.trim()) {
        title = standardTitle.textContent.trim();
      }
    }

    return cleanTitle(title) || cleanTitle(document.title);
  }

  function defaultTitle(isShort) {
    return isShort ? "YouTube Short" : "YouTube Video";
  }

  /**
   * Capture the title for the video that just started. Retries for ~5 seconds because
   * YouTube updates the page title late, and skips a title that still matches the previous video.
   */
  function captureTitle(videoId, attempt = 0) {
    if (videoId !== currentVideoId) return; // user already moved on

    const title = readTitle(isWatchingShort);
    const looksStale = title && previousTitle && title === previousTitle;

    if (title && !looksStale) {
      currentTitle = title;
      return;
    }
    if (attempt < 10) {
      setTimeout(() => captureTitle(videoId, attempt + 1), 500);
      return;
    }
    if (title) currentTitle = title; // accept after ~5s even if it matches
  }

  /**
   * Finalize and dispatch the current watch session to the background service worker.
   */
  function dispatchSession() {
    if (!currentVideoId || accumulatedWatchSeconds < 0.3) {
      return;
    }
    // Extension was reloaded: this old content script can no longer reach the background
    if (!chrome.runtime || !chrome.runtime.id) {
      return;
    }

    // Use the title captured when the video started. Only re-read the page if we are
    // still on the same video, otherwise the page already shows the NEXT video's title.
    const stillOnSameVideo = parseYouTubeUrl(window.location.href).videoId === currentVideoId;
    const titleToReport =
      currentTitle ||
      (stillOnSameVideo ? readTitle(isWatchingShort) : "") ||
      defaultTitle(isWatchingShort);

    const payload = {
      video_id: currentVideoId,
      video_title: titleToReport,
      url: currentUrl || window.location.href,
      watched_time_seconds: Math.round(accumulatedWatchSeconds),
      isShort: isWatchingShort,
      isContinuation: chunkCount > 0,
      timestamp: new Date().toISOString(),
    };

    console.log("[YouTube Tracker] Dispatching session:", payload);

    try {
      chrome.runtime.sendMessage({
        action: "TRACK_YOUTUBE_SESSION",
        data: payload,
      });
    } catch (err) {
      console.warn("[YouTube Tracker] Failed to send message to background:", err);
    }

    chunkCount += 1;
    accumulatedWatchSeconds = 0;
  }

  /**
   * Called whenever navigation occurs (SPA route transition or Shorts scroll).
   */
  function handleNavigation() {
    const newUrl = window.location.href;
    const parsed = parseYouTubeUrl(newUrl);

    if (parsed.videoId === currentVideoId) {
      // Same video, don't restart session
      return;
    }

    // Finalize the previous video before switching (uses its own stored title)
    if (currentVideoId) {
      dispatchSession();
    }

    previousTitle = currentTitle;

    if (parsed.videoId) {
      currentVideoId = parsed.videoId;
      currentUrl = newUrl;
      isWatchingShort = parsed.isShort;
      lastTickTime = Date.now();
      accumulatedWatchSeconds = 0;
      chunkCount = 0;
      currentTitle = null;

      // Give the page a moment to render, then read the title (with retries)
      setTimeout(() => captureTitle(parsed.videoId), 300);

      console.log(`[YouTube Tracker] Started tracking ${isWatchingShort ? "Short" : "Video"}: ${parsed.videoId}`);
    } else {
      currentVideoId = null;
      currentUrl = null;
      currentTitle = null;
      accumulatedWatchSeconds = 0;
      chunkCount = 0;
    }
  }

  /**
   * Periodic ticker to accumulate watch time when video is actively playing.
   */
  setInterval(() => {
    if (!currentVideoId) return;

    const now = Date.now();
    const elapsedSeconds = (now - lastTickTime) / 1000;
    lastTickTime = now;

    // Skip when the page is hidden
    if (document.hidden) return;
           let videoEl = null;
    const allVideos = document.querySelectorAll("video.html5-main-video, video");
    for (const v of allVideos) {
      if (!v.paused && !v.ended && v.currentTime > 0 && v.readyState > 2) {
        videoEl = v;
        break;
      }
    }

       if (videoEl && !videoEl.paused && !videoEl.ended) {
      accumulatedWatchSeconds += Math.min(elapsedSeconds, 2.0);

      // Periodically flush long watch sessions every 30 seconds
      if (accumulatedWatchSeconds >= 30) {
        dispatchSession();
      }
    }
  }, 250);

  // 1. YouTube native SPA navigation events
  document.addEventListener("yt-navigate-finish", () => {
    setTimeout(handleNavigation, 200);
  });
  document.addEventListener("yt-page-data-updated", () => {
    setTimeout(handleNavigation, 200);
  });

  // 2. Standard browser navigation events
  window.addEventListener("popstate", handleNavigation);

  // 3. Fallback URL polling (catches rapid scroll in Shorts)
  let lastCheckedHref = window.location.href;
  setInterval(() => {
    if (window.location.href !== lastCheckedHref) {
      lastCheckedHref = window.location.href;
      handleNavigation();
    }
  }, 500);

  // 4. Finalize session on tab close or navigation away
  window.addEventListener("beforeunload", dispatchSession);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && accumulatedWatchSeconds >= 2) {
      dispatchSession();
    }
  });

  // Initial check on load
  setTimeout(handleNavigation, 500);
})();