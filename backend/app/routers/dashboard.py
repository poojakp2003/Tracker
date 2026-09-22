from collections import defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.app_usage import AppUsage
from app.models.browser_activity import BrowserActivity
from app.models.user import User
from app.models.youtube_activity import YouTubeActivity
from app.routers.auth import get_current_user
from app.schemas.dashboard import (
    AppUsageItem,
    BrowserDomainItem,
    BrowserHistoryItem,
    DashboardAppsResponse,
    DashboardBrowserHistoryResponse,
    DashboardBrowserResponse,
    DashboardSummaryResponse,
    DashboardTimelineResponse,
    DashboardYouTubeResponse,
    TimelinePoint,
    YouTubeItem,
    format_duration,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_range_cutoff(range_key: str) -> datetime | None:
    """Computes cutoff datetime based on range parameter."""
    now = datetime.now(timezone.utc)
    key = range_key.lower().strip()

    match key:
        case "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        case "24h":
            return now - timedelta(hours=24)
        case "7d":
            return now - timedelta(days=7)
        case "30d":
            return now - timedelta(days=30)
        case "all":
            return None
        case _:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid range '{range_key}'. Allowed values: today, 24h, 7d, 30d, all",
            )


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    cleaned = url.strip()
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    try:
        parsed = urlparse(cleaned)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or cleaned
    except Exception:
        return cleaned



@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Retrieve high-level dashboard metrics (today, 7d, 30d totals and counts)."""
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # App usage durations
    today_app_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= start_of_today,
        )
    ) or 0

    week_app_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= seven_days_ago,
        )
    ) or 0

    month_app_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= thirty_days_ago,
        )
    ) or 0

    # YouTube watch durations
    today_yt_seconds = db.scalar(
        select(func.coalesce(func.sum(YouTubeActivity.watched_time_seconds), 0)).where(
            YouTubeActivity.user_id == current_user.id,
            YouTubeActivity.timestamp >= start_of_today,
        )
    ) or 0

    week_yt_seconds = db.scalar(
        select(func.coalesce(func.sum(YouTubeActivity.watched_time_seconds), 0)).where(
            YouTubeActivity.user_id == current_user.id,
            YouTubeActivity.timestamp >= seven_days_ago,
        )
    ) or 0

    month_yt_seconds = db.scalar(
        select(func.coalesce(func.sum(YouTubeActivity.watched_time_seconds), 0)).where(
            YouTubeActivity.user_id == current_user.id,
            YouTubeActivity.timestamp >= thirty_days_ago,
        )
    ) or 0

    today_seconds = today_app_seconds + today_yt_seconds
    week_seconds = week_app_seconds + week_yt_seconds
    month_seconds = month_app_seconds + month_yt_seconds

    # Activity counts
    total_app_sessions = db.scalar(
        select(func.count(AppUsage.id)).where(AppUsage.user_id == current_user.id)
    ) or 0

    total_browser_visits = db.scalar(
        select(func.count(BrowserActivity.id)).where(
            BrowserActivity.user_id == current_user.id
        )
    ) or 0

    total_videos_watched = db.scalar(
        select(func.count(YouTubeActivity.id)).where(
            YouTubeActivity.user_id == current_user.id
        )
    ) or 0

    return DashboardSummaryResponse(
        today_seconds=today_seconds,
        today_formatted=format_duration(today_seconds),
        week_seconds=week_seconds,
        week_formatted=format_duration(week_seconds),
        month_seconds=month_seconds,
        month_formatted=format_duration(month_seconds),
        total_app_sessions=total_app_sessions,
        total_browser_visits=total_browser_visits,
        total_videos_watched=total_videos_watched,
    )


@router.get(
    "/apps",
    response_model=DashboardAppsResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_apps(
    range: str = Query(default="7d", description="Time period (today, 24h, 7d, 30d, all)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardAppsResponse:
    """Retrieve application usage statistics grouped by app and ordered by duration."""
    cutoff = get_range_cutoff(range)

    query = (
        select(
            AppUsage.app_name,
            func.sum(AppUsage.duration_seconds).label("total_duration"),
            func.count(AppUsage.id).label("session_count"),
        )
        .where(AppUsage.user_id == current_user.id)
        .group_by(AppUsage.app_name)
        .order_by(desc("total_duration"))
    )

    if cutoff is not None:
        query = query.where(AppUsage.start_time >= cutoff)

    results = db.execute(query).all()

    total_duration = sum(row.total_duration for row in results) if results else 0

    items: list[AppUsageItem] = []
    for row in results:
        dur = int(row.total_duration)
        percentage = round((dur / total_duration) * 100, 1) if total_duration > 0 else 0.0
        items.append(
            AppUsageItem(
                app_name=row.app_name,
                duration_seconds=dur,
                duration_formatted=format_duration(dur),
                session_count=int(row.session_count),
                percentage=percentage,
            )
        )

    return DashboardAppsResponse(
        range=range,
        total_duration_seconds=total_duration,
        total_duration_formatted=format_duration(total_duration),
        items=items,
    )


@router.get(
    "/browser",
    response_model=DashboardBrowserResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_browser(
    range: str = Query(default="7d", description="Time period (today, 24h, 7d, 30d, all)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardBrowserResponse:
    """Retrieve domain-aggregated browser activity and visit percentages."""
    cutoff = get_range_cutoff(range)

    query = select(BrowserActivity.url, BrowserActivity.timestamp).where(
        BrowserActivity.user_id == current_user.id
    )

    if cutoff is not None:
        query = query.where(BrowserActivity.timestamp >= cutoff)

    rows = db.execute(query).all()

    domain_counts: dict[str, int] = defaultdict(int)
    domain_latest: dict[str, datetime] = {}

    for row in rows:
        dom = extract_domain(row.url)
        domain_counts[dom] += 1
        ts = row.timestamp
        if dom not in domain_latest or ts > domain_latest[dom]:
            domain_latest[dom] = ts

    total_visits = len(rows)
    sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)

    items: list[BrowserDomainItem] = []
    for domain, count in sorted_domains:
        percentage = round((count / total_visits) * 100, 1) if total_visits > 0 else 0.0
        items.append(
            BrowserDomainItem(
                domain=domain,
                visit_count=count,
                last_visited=domain_latest[domain],
                percentage=percentage,
            )
        )

    return DashboardBrowserResponse(
        range=range,
        total_visits=total_visits,
        items=items,
    )


@router.get(
    "/youtube",
    response_model=DashboardYouTubeResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_youtube(
    range: str = Query(default="7d", description="Time period (today, 24h, 7d, 30d, all)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardYouTubeResponse:
    """Retrieve YouTube viewing activity grouped by video and sorted by watch duration."""
    cutoff = get_range_cutoff(range)

    query = (
        select(
            YouTubeActivity.video_id,
            YouTubeActivity.video_title,
            YouTubeActivity.url,
            func.sum(YouTubeActivity.watched_time_seconds).label("total_watched"),
            func.count(YouTubeActivity.id).label("watch_count"),
            func.max(YouTubeActivity.timestamp).label("last_watched"),
        )
        .where(YouTubeActivity.user_id == current_user.id)
        .group_by(
            YouTubeActivity.video_id,
            YouTubeActivity.video_title,
            YouTubeActivity.url,
        )
        .order_by(desc("total_watched"))
    )

    if cutoff is not None:
        query = query.where(YouTubeActivity.timestamp >= cutoff)

    results = db.execute(query).all()

    total_watched = sum(row.total_watched for row in results) if results else 0

    items: list[YouTubeItem] = []
    for row in results:
        watched_sec = int(row.total_watched)
        items.append(
            YouTubeItem(
                video_id=row.video_id,
                video_title=row.video_title,
                url=row.url,
                watched_seconds=watched_sec,
                watched_formatted=format_duration(watched_sec),
                watch_count=int(row.watch_count),
                last_watched=row.last_watched,
            )
        )

    return DashboardYouTubeResponse(
        range=range,
        total_watched_seconds=total_watched,
        total_watched_formatted=format_duration(total_watched),
        items=items,
    )


@router.get(
    "/timeline",
    response_model=DashboardTimelineResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_timeline(
    time_range: str = Query(default="7d", alias="range", description="Time period (today, 24h, 7d, 30d, all)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardTimelineResponse:
    """Retrieve daily timeline points for charting combined app + YouTube usage duration."""
    cutoff = get_range_cutoff(time_range)
    now = datetime.now(timezone.utc)

    # Determine date span to display
    key = time_range.lower().strip()
    match key:
        case "today" | "24h":
            day_count = 1
        case "30d":
            day_count = 30
        case "all":
            day_count = 14
        case _:  # default 7d
            day_count = 7

    target_dates = [now.date() - timedelta(days=i) for i in range(day_count - 1, -1, -1)]

    # Fetch app usage records for user in range
    query = select(AppUsage.start_time, AppUsage.duration_seconds).where(
        AppUsage.user_id == current_user.id
    )
    if cutoff is not None:
        query = query.where(AppUsage.start_time >= cutoff)

    records = db.execute(query).all()

    daily_seconds: dict[str, int] = defaultdict(int)
    daily_sessions: dict[str, int] = defaultdict(int)

    for rec in records:
        d_str = rec.start_time.date().strftime("%Y-%m-%d")
        daily_seconds[d_str] += rec.duration_seconds
        daily_sessions[d_str] += 1

    # Fetch YouTube watch records for user in range and merge into the same daily buckets
    yt_query = select(YouTubeActivity.timestamp, YouTubeActivity.watched_time_seconds).where(
        YouTubeActivity.user_id == current_user.id
    )
    if cutoff is not None:
        yt_query = yt_query.where(YouTubeActivity.timestamp >= cutoff)

    yt_records = db.execute(yt_query).all()

    for rec in yt_records:
        d_str = rec.timestamp.date().strftime("%Y-%m-%d")
        daily_seconds[d_str] += rec.watched_time_seconds
        daily_sessions[d_str] += 1

    items: list[TimelinePoint] = []
    total_sec = 0

    for d in target_dates:
        d_str = d.strftime("%Y-%m-%d")
        dur = daily_seconds.get(d_str, 0)
        total_sec += dur
        hours = round(dur / 3600.0, 1)
        items.append(
            TimelinePoint(
                date=d_str,
                day=d.strftime("%A"),  # Monday, Tuesday, etc.
                hours=hours,
                duration_seconds=dur,
                duration_formatted=format_duration(dur),
                session_count=daily_sessions.get(d_str, 0),
            )
        )

    return DashboardTimelineResponse(
        range=time_range,
        total_hours=round(total_sec / 3600.0, 1),
        total_duration_formatted=format_duration(total_sec),
        items=items,
    )


@router.get(
    "/browser-history",
    response_model=DashboardBrowserHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_browser_history(
    range: str = Query(default="7d", description="Time period (today, 24h, 7d, 30d, all)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max history records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardBrowserHistoryResponse:
    """Retrieve chronological list of individual browser history records."""
    cutoff = get_range_cutoff(range)

    query = (
        select(BrowserActivity)
        .where(BrowserActivity.user_id == current_user.id)
        .order_by(desc(BrowserActivity.timestamp))
    )

    if cutoff is not None:
        query = query.where(BrowserActivity.timestamp >= cutoff)

    query = query.limit(limit)
    rows = db.scalars(query).all()

    items: list[BrowserHistoryItem] = []
    for row in rows:
        items.append(
            BrowserHistoryItem(
                id=row.id,
                url=row.url,
                domain=extract_domain(row.url),
                title=row.title,
                browser=row.browser,
                timestamp=row.timestamp,
                time_formatted=row.timestamp.strftime("%H:%M"),
            )
        )

    return DashboardBrowserHistoryResponse(
        range=range,
        total_count=len(items),
        items=items,
    )