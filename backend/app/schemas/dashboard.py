from datetime import datetime
from pydantic import BaseModel


def format_duration(seconds: int) -> str:
    """Formats an integer duration in seconds into human-readable text."""
    if seconds <= 0:
        return "0 mins"
    if seconds < 60:
        return f"{seconds} sec" if seconds == 1 else f"{seconds} secs"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts: list[str] = []
    if hours > 0:
        parts.append(f"{hours} hr" if hours == 1 else f"{hours} hrs")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} min" if minutes == 1 else f"{minutes} mins")
    return " ".join(parts)

class DashboardSummaryResponse(BaseModel):
    """Schema for top-level usage summary metrics across periods."""

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
    """Schema representing aggregated usage for a specific application."""

    app_name: str
    duration_seconds: int
    duration_formatted: str
    session_count: int
    percentage: float


class DashboardAppsResponse(BaseModel):
    """Schema for returning aggregated app usage analytics."""

    range: str
    total_duration_seconds: int
    total_duration_formatted: str
    items: list[AppUsageItem]


class BrowserDomainItem(BaseModel):
    """Schema representing aggregated visits for a specific domain."""

    domain: str
    visit_count: int
    last_visited: datetime
    percentage: float


class DashboardBrowserResponse(BaseModel):
    """Schema for returning domain-aggregated browser analytics."""

    range: str
    total_visits: int
    items: list[BrowserDomainItem]


class YouTubeItem(BaseModel):
    """Schema representing aggregated watching stats for a YouTube video."""

    video_id: str
    video_title: str
    url: str
    watched_seconds: int
    watched_formatted: str
    watch_count: int
    last_watched: datetime


class DashboardYouTubeResponse(BaseModel):
    """Schema for returning aggregated YouTube analytics."""

    range: str
    total_watched_seconds: int
    total_watched_formatted: str
    items: list[YouTubeItem]


class TimelinePoint(BaseModel):
    """Schema representing a single day's activity on the timeline."""

    date: str
    day: str
    hours: float
    duration_seconds: int
    duration_formatted: str
    session_count: int


class DashboardTimelineResponse(BaseModel):
    """Schema for returning multi-day timeline activity trends."""

    range: str
    total_hours: float
    total_duration_formatted: str
    items: list[TimelinePoint]


class BrowserHistoryItem(BaseModel):
    """Schema representing an individual browser history event."""

    id: int
    url: str
    domain: str
    title: str | None = None
    browser: str
    timestamp: datetime
    time_formatted: str


class DashboardBrowserHistoryResponse(BaseModel):
    """Schema for returning a paginated or filtered list of browser visits."""

    range: str
    total_count: int
    items: list[BrowserHistoryItem]


