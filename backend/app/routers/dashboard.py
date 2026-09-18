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
    DashboardAppsResponse,
    DashboardBrowserResponse,
    DashboardSummaryResponse,
    DashboardYouTubeResponse,
    YouTubeItem,
    format_duration,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_range_cutoff(range_key: str) -> datetime | None:
    """Computes cutoff datetime based on range parameter."""
    now = datetime.now(timezone.utc)
    key = range_key.lower().strip()

    if key == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif key == "24h":
        return now - timedelta(hours=24)
    elif key == "7d":
        return now - timedelta(days=7)
    elif key == "30d":
        return now - timedelta(days=30)
    elif key == "all":
        return None
    else:
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
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # App usage durations
    today_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= start_of_today,
        )
    ) or 0

    week_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= seven_days_ago,
        )
    ) or 0

    month_seconds = db.scalar(
        select(func.coalesce(func.sum(AppUsage.duration_seconds), 0)).where(
            AppUsage.user_id == current_user.id,
            AppUsage.start_time >= thirty_days_ago,
        )
    ) or 0

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
