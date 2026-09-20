import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from agent import DesktopAgent
from batch_sender import BatchSender
from config import AgentConfig
from window_tracker import WindowInfo, _clean_app_name


class TestDesktopAgent(unittest.TestCase):
    def test_clean_app_name(self):
        """Verify application name normalization."""
        self.assertEqual(_clean_app_name("chrome.exe"), "Google Chrome")
        self.assertEqual(_clean_app_name("code.exe"), "VS Code")
        self.assertEqual(_clean_app_name("msedge.exe"), "Microsoft Edge")
        self.assertEqual(_clean_app_name("spotify.exe"), "Spotify")
        self.assertEqual(_clean_app_name("custom_app.exe"), "Custom_app")


    def test_interval_tracking_on_app_switch(self):
        """Verify that switching active application closes previous interval and enqueues record."""
        cfg = AgentConfig(min_duration_seconds=1, batch_size=10)
        agent = DesktopAgent()
        agent.config = cfg
        agent.sender = MagicMock(spec=BatchSender)

        # 1. Start on Chrome
        t0 = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
        agent.current_app_name = "Google Chrome"
        agent.current_window_title = "GitHub"
        agent.current_start_time = t0

        # 2. Switch to VS Code 30 seconds later
        t1 = t0 + timedelta(seconds=30)
        with patch("agent.datetime") as mock_dt:
            mock_dt.now.return_value = t1
            agent._close_current_interval()

        # Verify enqueued record
        self.assertEqual(agent.sender.enqueue.call_count, 1)
        enqueued = agent.sender.enqueue.call_args[0][0]
        self.assertEqual(enqueued["app_name"], "Google Chrome")
        self.assertEqual(enqueued["window_title"], "GitHub")
        self.assertEqual(enqueued["duration_seconds"], 30)
        self.assertEqual(enqueued["start_time"], t0.isoformat())
        self.assertEqual(enqueued["end_time"], t1.isoformat())

    def test_sub_second_glitch_filtered_out(self):
        """Verify that transient switches under min_duration_seconds are not enqueued."""
        cfg = AgentConfig(min_duration_seconds=2)
        agent = DesktopAgent()
        agent.config = cfg
        agent.sender = MagicMock(spec=BatchSender)

        t0 = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
        agent.current_app_name = "AltTab"
        agent.current_start_time = t0

        # Closed 0.5s later
        t1 = t0 + timedelta(milliseconds=500)
        with patch("agent.datetime") as mock_dt:
            mock_dt.now.return_value = t1
            agent._close_current_interval()

        # Enqueue should not have been called
        self.assertEqual(agent.sender.enqueue.call_count, 0)

    def test_batch_sender_flush_trigger(self):
        """Verify should_flush triggers when queue reaches batch_size."""
        cfg = AgentConfig(batch_size=3, flush_interval_seconds=60)
        sender = BatchSender(cfg)
        sender.queue = []

        self.assertFalse(sender.should_flush())
        sender.queue.append({"app_name": "App1", "duration_seconds": 10})
        sender.queue.append({"app_name": "App2", "duration_seconds": 20})
        self.assertFalse(sender.should_flush())

        # 3rd item reaches batch_size
        sender.queue.append({"app_name": "App3", "duration_seconds": 30})
        self.assertTrue(sender.should_flush())

    def test_shutdown_flushes_active_interval(self):
        """Verify that shutting down agent seals current session and flushes batch."""
        agent = DesktopAgent()
        agent.sender = MagicMock(spec=BatchSender)
        agent.sender.queue = [{"app_name": "Queued"}]

        agent.current_app_name = "Notepad"
        agent.current_window_title = "Notes.txt"
        agent.current_start_time = datetime.now(timezone.utc) - timedelta(seconds=15)

        agent._shutdown()

        # Should have enqueued the closing Notepad session and called flush()
        self.assertEqual(agent.sender.enqueue.call_count, 1)
        self.assertEqual(agent.sender.flush.call_count, 1)


if __name__ == "__main__":
    unittest.main()

