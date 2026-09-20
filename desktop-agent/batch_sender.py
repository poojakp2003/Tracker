"""Batch collection, offline resilience buffer, and transmission to FastAPI backend."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

try:
    import requests
except ImportError:
    requests = None  # Will fall back to urllib.request if requests is not installed

from config import AgentConfig, save_config

BUFFER_FILE = Path(__file__).resolve().parent / ".buffer.json"


@dataclass
class AppUsageRecord:
    app_name: str
    window_title: str | None
    start_time: str
    end_time: str
    duration_seconds: int

    def to_dict(self) -> dict:
        return asdict(self)


class BatchSender:
    """Manages the in-memory queue, disk-backed buffer, and HTTP transport."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.queue: list[dict] = []
        self.last_flush_time: float = time.time()
        self._load_buffer()

    def _load_buffer(self) -> None:
        """Load any unsent records from disk buffer."""
        if BUFFER_FILE.exists():
            try:
                with open(BUFFER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.queue.extend(data)
                    print(f"[BatchSender] Loaded {len(data)} buffered records from disk.")
            except Exception as exc:
                print(f"[BatchSender] Warning: failed to load buffer ({exc}).", file=sys.stderr)

    def _save_buffer(self) -> None:
        """Persist current queue to disk buffer."""
        try:
            with open(BUFFER_FILE, "w", encoding="utf-8") as f:
                json.dump(self.queue, f, indent=2)
        except Exception as exc:
            print(f"[BatchSender] Warning: failed to write buffer ({exc}).", file=sys.stderr)

    def enqueue(self, record: dict) -> None:
        """Add an interval record to the local batch queue."""
        self.queue.append(record)
        self._save_buffer()
        print(
            f"[Queue] +1: {record['app_name']} ({record['duration_seconds']}s) "
            f"[Buffer size: {len(self.queue)}]"
        )

    def should_flush(self) -> bool:
        """Determine if batch threshold or time elapsed condition is met."""
        if not self.queue:
            return False
        count_trigger = len(self.queue) >= self.config.batch_size
        time_trigger = (time.time() - self.last_flush_time) >= self.config.flush_interval_seconds
        return count_trigger or time_trigger

    def _ensure_token(self) -> str | None:
        """Ensure a valid JWT access token is available, logging in if needed."""
        if self.config.access_token:
            return self.config.access_token

        if not self.config.email or not self.config.password:
            print(
                "[BatchSender] Error: No access_token or email/password configured in config.json!",
                file=sys.stderr,
            )
            return None

        # Authenticate via /auth/login
        login_url = f"{self.config.backend_url.rstrip('/')}/auth/login"
        payload = {"email": self.config.email, "password": self.config.password}

        try:
            if requests:
                resp = requests.post(login_url, json=payload, timeout=10)
                if resp.status_code == 200:
                    token = resp.json().get("access_token")
                    self.config.access_token = token
                    save_config(self.config)
                    print("[BatchSender] Authentication successful. Token cached.")
                    return token
                else:
                    print(f"[BatchSender] Login failed: HTTP {resp.status_code} - {resp.text}", file=sys.stderr)
            else:
                import urllib.request

                req = urllib.request.Request(
                    login_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        token = data.get("access_token")
                        self.config.access_token = token
                        save_config(self.config)
                        print("[BatchSender] Authentication successful. Token cached.")
                        return token
        except Exception as exc:
            print(f"[BatchSender] Login connection failed: {exc}", file=sys.stderr)
        return None

    def flush(self) -> int:
        """Send all buffered records to the backend in a single batch."""
        if not self.queue:
            return 0

        token = self._ensure_token()
        if not token:
            print("[BatchSender] Skipping flush: unable to acquire valid authorization token.")
            return 0

        batch_to_send = list(self.queue)
        endpoint = f"{self.config.backend_url.rstrip('/')}/track/app-usage"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(f"[BatchSender] Dispatching batch of {len(batch_to_send)} records to {endpoint}...")

        try:
            if requests:
                resp = requests.post(endpoint, headers=headers, json=batch_to_send, timeout=10)
                status_code = resp.status_code
                response_text = resp.text
            else:
                import urllib.error
                import urllib.request

                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(batch_to_send).encode("utf-8"),
                    headers=headers,
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        status_code = resp.status
                        response_text = resp.read().decode("utf-8")
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    response_text = e.read().decode("utf-8")

            if status_code in (200, 201):
                sent_count = len(batch_to_send)
                # Remove sent items from queue
                self.queue = self.queue[sent_count:]
                self._save_buffer()
                self.last_flush_time = time.time()
                print(f"[BatchSender] Successfully posted batch of {sent_count} records (HTTP {status_code}) ✓")
                return sent_count

            elif status_code == 401:
                print("[BatchSender] Authorization failed (HTTP 401). Invalidating cached token.")
                self.config.access_token = ""
                save_config(self.config)
                return 0

            elif status_code == 403:
                print(
                    "[BatchSender] Backend returned HTTP 403: App tracking is disabled in user settings.",
                    file=sys.stderr,
                )
                # Drop batch to prevent infinite loop if permissions are off
                self.queue = self.queue[len(batch_to_send):]
                self._save_buffer()
                self.last_flush_time = time.time()
                return 0

            else:
                print(f"[BatchSender] Backend returned error: HTTP {status_code} - {response_text}", file=sys.stderr)
                return 0

        except Exception as exc:
            print(f"[BatchSender] Network transmission error: {exc}. Batch retained for retry.", file=sys.stderr)
            return 0
