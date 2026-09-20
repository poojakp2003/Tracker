"""Desktop Tracking Agent Daemon.

Monitors active applications, records usage intervals, and periodically
dispatches batches to the Tracker backend.

Usage:
  python agent.py                  # Run agent in foreground / daemon loop
  python agent.py --test           # Test active window detection once
  python agent.py --status         # Check configuration & startup status
  python agent.py --install-startup   # Enable auto-start on login
  python agent.py --uninstall-startup # Disable auto-start on login
"""

import argparse
from datetime import datetime, timezone
import signal
import sys
import time

from batch_sender import BatchSender
from config import load_config
from startup import install_startup, is_startup_installed, uninstall_startup
from window_tracker import get_active_window


class DesktopAgent:
    """Core tracking daemon."""

    def __init__(self) -> None:
        self.config = load_config()
        self.sender = BatchSender(self.config)
        self.running = False

        # Interval tracking state
        self.current_app_name: str | None = None
        self.current_window_title: str | None = None
        self.current_start_time: datetime | None = None

    def _close_current_interval(self) -> None:
        """Close current active application interval and enqueue if duration threshold met."""
        if not self.current_app_name or not self.current_start_time:
            return

        now = datetime.now(timezone.utc)
        duration_seconds = int((now - self.current_start_time).total_seconds())

        if duration_seconds >= self.config.min_duration_seconds:
            record = {
                "app_name": self.current_app_name,
                "window_title": self.current_window_title,
                "start_time": self.current_start_time.isoformat(),
                "end_time": now.isoformat(),
                "duration_seconds": duration_seconds,
            }
            self.sender.enqueue(record)

        self.current_app_name = None
        self.current_window_title = None
        self.current_start_time = None

    def _start_new_interval(self, app_name: str, window_title: str) -> None:
        """Begin a new interval for the focused application."""
        self.current_app_name = app_name
        self.current_window_title = window_title
        self.current_start_time = datetime.now(timezone.utc)

    def tick(self) -> None:
        """Single polling cycle."""
        window_info = get_active_window()

        if window_info is not None:
            # Check ignored apps list
            is_ignored = (
                window_info.app_name in self.config.ignored_apps
                or (window_info.window_title and window_info.window_title in self.config.ignored_apps)
            )

            if is_ignored:
                # If currently tracking an app, close it
                if self.current_app_name:
                    self._close_current_interval()
            else:
                has_changed = (
                    window_info.app_name != self.current_app_name
                    or window_info.window_title != self.current_window_title
                )

                if has_changed:
                    self._close_current_interval()
                    self._start_new_interval(window_info.app_name, window_info.window_title)

        # Flush batch if threshold reached
        if self.sender.should_flush():
            self.sender.flush()

    def run(self) -> None:
        """Main daemon loop."""
        self.running = True
        print("=" * 60)
        print("  TRACKER DESKTOP AGENT STARTED")
        print(f"  Backend:        {self.config.backend_url}")
        print(f"  Poll Interval:  {self.config.poll_interval_seconds}s")
        print(f"  Batch Size:     {self.config.batch_size} records / {self.config.flush_interval_seconds}s")
        print("  Press Ctrl+C to stop.")
        print("=" * 60)

        # Setup graceful termination signals
        def handle_exit(signum, frame):
            print("\n[Agent] Stop signal received. Shutting down gracefully...")
            self.stop()

        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        try:
            while self.running:
                self.tick()
                time.sleep(self.config.poll_interval_seconds)
        finally:
            self._shutdown()

    def stop(self) -> None:
        """Signal the agent to stop."""
        self.running = False

    def _shutdown(self) -> None:
        """Flush final interval and buffered records before exiting."""
        print("[Agent] Finalizing active interval...")
        self._close_current_interval()
        if self.sender.queue:
            print(f"[Agent] Flushing remaining {len(self.sender.queue)} records to backend...")
            self.sender.flush()
        print("[Agent] Desktop Agent stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tracker Desktop Application Agent")
    parser.add_argument("--test", action="store_true", help="Detect current active window once and exit")
    parser.add_argument("--status", action="store_true", help="Display agent config and startup status")
    parser.add_argument("--install-startup", action="store_true", help="Register agent for automatic system startup")
    parser.add_argument("--uninstall-startup", action="store_true", help="Remove agent from automatic system startup")

    args = parser.parse_args()

    if args.test:
        print("[Test] Detecting current foreground window...")
        info = get_active_window()
        if info:
            print(f"  App Name:     {info.app_name}")
            print(f"  Window Title: {info.window_title}")
            print(f"  Process ID:   {info.process_id}")
        else:
            print("  No foreground window detected (desktop or locked).")
        return

    if args.status:
        cfg = load_config()
        print("=== Desktop Agent Status ===")
        print(f"  Backend URL:      {cfg.backend_url}")
        print(f"  Auth Token:       {'Configured ✓' if cfg.access_token else 'Not set (will use email/pwd)'}")
        print(f"  Account Email:    {cfg.email or '(None)'}")
        print(f"  Poll Frequency:   {cfg.poll_interval_seconds}s")
        print(f"  Batch Trigger:    {cfg.batch_size} records or {cfg.flush_interval_seconds}s")
        print(f"  System Startup:   {'Enabled ✓' if is_startup_installed() else 'Disabled'}")
        return

    if args.install_startup:
        success = install_startup()
        if success:
            print("[Startup] Agent installed for automatic startup on system log in ✓")
        else:
            print("[Startup] Failed to configure automatic startup.", file=sys.stderr)
        return

    if args.uninstall_startup:
        success = uninstall_startup()
        if success:
            print("[Startup] Agent removed from automatic system startup ✓")
        else:
            print("[Startup] Startup configuration was not found or could not be removed.")
        return

    # Default: run daemon
    agent = DesktopAgent()
    agent.run()


if __name__ == "__main__":
    main()
