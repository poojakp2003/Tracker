"""Configuration management for Desktop Tracking Agent."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import sys

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"


@dataclass
class AgentConfig:
    backend_url: str = "http://127.0.0.1:8000"
    email: str = ""
    password: str = ""
    access_token: str = ""
    poll_interval_seconds: float = 1.0
    min_duration_seconds: int = 1
    batch_size: int = 5
    flush_interval_seconds: int = 30
    ignored_apps: list[str] = field(
        default_factory=lambda: [
            "LockApp.exe",
            "SearchHost.exe",
            "ShellExperienceHost.exe",
            "ScreenClippingHost.exe",
        ]
    )


def load_config() -> AgentConfig:
    """Load configuration from config.json or return defaults."""
    if not CONFIG_FILE.exists():
        cfg = AgentConfig()
        save_config(cfg)
        return cfg

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AgentConfig(
            backend_url=data.get("backend_url", "http://127.0.0.1:8000"),
            email=data.get("email", ""),
            password=data.get("password", ""),
            access_token=data.get("access_token", ""),
            poll_interval_seconds=float(data.get("poll_interval_seconds", 1.0)),
            min_duration_seconds=int(data.get("min_duration_seconds", 1)),
            batch_size=int(data.get("batch_size", 5)),
            flush_interval_seconds=int(data.get("flush_interval_seconds", 30)),
            ignored_apps=data.get(
                "ignored_apps",
                [
                    "LockApp.exe",
                    "SearchHost.exe",
                    "ShellExperienceHost.exe",
                    "ScreenClippingHost.exe",
                ],
            ),
        )
    except Exception as exc:
        print(f"[Config] Error loading config.json ({exc}), using defaults.", file=sys.stderr)
        return AgentConfig()


def save_config(config: AgentConfig) -> None:
    """Persist current configuration to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2)
    except Exception as exc:
        print(f"[Config] Failed to save config.json: {exc}", file=sys.stderr)
