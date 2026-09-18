from datetime import datetime
from pydantic import BaseModel


def format_duration(seconds: int) -> str:
    """Formats an integer duration in seconds into human-readable text."""
    if seconds <= 0:
        return "0 mins"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts: list[str] = []
    if hours > 0:
        parts.append(f"{hours} hr" if hours == 1 else f"{hours} hrs")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} min" if minutes == 1 else f"{minutes} mins")
    return " ".join(parts)


class DashboardSummaryResponse(BaseModel):
    today_seconds: int
    today_formatted: str
    week_seconds: int
    week_formatted: str
    month_seconds: int
    month_formatted: str
    total_app_sessions: int
    total_browser_visits: int
    total_videos_watched: int


class AppUsageItem(BaseModel):
    app_name: str
    duration_seconds: int
    duration_formatted: str
    session_count: int
    percentage: float


class DashboardAppsResponse(BaseModel):
    range: str
    total_duration_seconds: int
    total_duration_formatted: str
    items: list[AppUsageItem]


class BrowserDomainItem(BaseModel):
    domain: str
    visit_count: int
    last_visited: datetime
    percentage: float


class DashboardBrowserResponse(BaseModel):
    range: str
    total_visits: int
    items: list[BrowserDomainItem]


class YouTubeItem(BaseModel):
    video_id: str
    video_title: str
    url: str
    watched_seconds: int
    watched_formatted: str
    watch_count: int
    last_watched: datetime


class DashboardYouTubeResponse(BaseModel):
    range: str
    total_watched_seconds: int
    total_watched_formatted: str
    items: list[YouTubeItem]
