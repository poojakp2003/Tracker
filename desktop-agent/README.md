# Tracker Desktop Agent (Phase 6)

A lightweight background daemon that automatically monitors active desktop applications, records usage intervals, and dispatches batches of telemetry to the Tracker FastAPI backend.

---

## Features

- **Accurate Interval Tracking (Step 19)**:
  - Tracks application active intervals (e.g. Chrome 10:00–10:30, VS Code 10:30–11:15).
  - Automatically seals the previous interval when the user switches windows and begins a new interval.
  - Sub-second switches (e.g., rapid Alt-Tab cycling) are filtered out to prevent database spam.
- **Batch Data Transmission (Step 20)**:
  - Queues records locally and flushes to `POST /track/app-usage` when either:
    - Queue reaches `batch_size` (default: 5 records), or
    - `flush_interval_seconds` elapses (default: 30 seconds).
  - Persists un-sent records to local disk buffer (`.buffer.json`) to guarantee zero data loss during network interruptions or computer shutdown.
- **Automatic System Startup (Step 21)**:
  - Supports non-elevated installation into the Windows Startup folder via `--install-startup`.
  - Can be easily removed via `--uninstall-startup`.
- **Cross-Platform**:
  - Windows: Native Win32 API via standard library `ctypes` and `psutil`.
  - macOS: `osascript` / `AppKit`.
  - Linux: `xdotool`.

---

## Installation & Setup

1. Navigate to the agent directory:
   ```bash
   cd desktop-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure credentials in `config.json`:
   ```json
   {
     "backend_url": "http://127.0.0.1:8000",
     "email": "your_email@example.com",
     "password": "your_password",
     "access_token": "",
     "poll_interval_seconds": 1.0,
     "min_duration_seconds": 1,
     "batch_size": 5,
     "flush_interval_seconds": 30
   }
   ```
   *(You can either provide your account email/password for automatic JWT acquisition, or paste a pre-generated token into `access_token`.)*

---

## Usage Commands

### 1. Test Window Detection (Step 18)
To verify that the agent detects your current foreground window:
```bash
python agent.py --test
```

### 2. Run the Agent (Steps 19 & 20)
Start the agent in the foreground:
```bash
python agent.py
```
Stop anytime with `Ctrl + C`. The agent will seal the open session and flush any remaining records to the database before exiting.

### 3. Check Status
Inspect active configuration and startup registration:
```bash
python agent.py --status
```

### 4. Enable Automatic Startup on Login (Step 21)
```bash
python agent.py --install-startup
```

### 5. Disable Automatic Startup
```bash
python agent.py --uninstall-startup
```
