# Productivity & Activity Tracker — Chrome Extension (Phase 7)

A lightweight, secure Google Chrome extension built with **Manifest V3** to automatically track web navigation activity, identify YouTube learning sessions, and batch-dispatch telemetry to your local FastAPI backend and PostgreSQL database.

---

## Features

- **Manifest V3 Compliance**: Built with a modular background service worker (`background.js`), storage APIs, and Chrome alarms.
- **Tab Change Detection (Step 23)**:
  - Listens to `chrome.tabs.onUpdated` and `chrome.tabs.onActivated`.
  - Captures page URL, title, and ISO UTC timestamp.
  - Automatically identifies and tags YouTube pages (including video IDs from `/watch?v=...`).
  - Filters out internal browser pages (`chrome://`, `about:blank`, `chrome-extension://`).
  - Intelligent deduplication: prevents duplicate events on rapid reloads or in-page hash changes.
- **Batch Data Transmission (Step 24)**:
  - Collects browsing events locally in `chrome.storage.local`.
  - Transmits in batches of up to 30 events to `POST /track/browser-activity`.
  - Triggers automatically when 5 events accumulate or every 30 seconds via alarm.
  - Offline-resilient: events remain buffered locally if the backend server is temporarily unreachable.
- **Incognito Mode Support**:
  - Configured with `"incognito": "spanning"` per browser security rules.
  - Real-time indicator in popup displaying whether Incognito permission has been granted.
  - Strictly adheres to Chrome security sandbox without bypassing browser safeguards.

---

## Installation Guide

### Step 1: Open Chrome Extensions Manager
1. Open Google Chrome.
2. In the address bar, navigate to:
   ```
   chrome://extensions
   ```
3. Enable **Developer mode** using the toggle switch in the top right corner.

### Step 2: Load Unpacked Extension
1. Click the **Load unpacked** button in the top left.
2. Select the `chrome-extension` folder located at:
   ```
   C:\TRACKER\tracker-phase1-backend\chrome-extension
   ```
3. The extension **Productivity & Activity Tracker** will now appear in your extensions list.

---

## Enabling Incognito Support

By default, Chrome security isolates extensions from private browsing windows until the user explicitly grants permission:

1. On `chrome://extensions`, locate **Productivity & Activity Tracker**.
2. Click **Details**.
3. Scroll down to find **Allow in incognito**.
4. Toggle the switch to **ON**.

> [!NOTE]
> Once enabled, the extension will monitor tabs in Incognito windows and send them to the backend alongside regular sessions, using a unified background service worker.

---

## Usage & Configuration

1. Click the extension icon in the Chrome toolbar.
2. **Login to Backend**:
   - Enter your email and password (e.g. `user@example.com` and your password).
   - Enter the API URL (defaults to `http://127.0.0.1:8000`).
   - Click **Connect & Login**.
3. **Master Tracking Toggle**:
   - Toggle tracking on or off anytime using the switch in the popup header.
4. **Manual Sync**:
   - Click **Sync Now** to instantly push buffered events to the backend.
5. **Dashboard**:
   - Click **Open Web Dashboard &rarr;** at the bottom of the popup to view your live stats at `http://localhost:5173`.
