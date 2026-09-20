from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.app_usage import AppUsage
from app.models.browser_activity import BrowserActivity
from app.models.permission import Permission
from app.models.user import User
from app.models.youtube_activity import YouTubeActivity
from app.routers.auth import get_current_user
from app.schemas.tracking import (
    AppUsageCreate,
    AppUsageResponse,
    BrowserActivityCreate,
    BrowserActivityResponse,
    PermissionResponse,
    PermissionUpdate,
    YouTubeActivityCreate,
    YouTubeActivityResponse,
)

router = APIRouter(prefix="/track", tags=["tracking"])


def get_or_create_user_permission(db: Session, user_id: int) -> Permission:
    """Ensure a user has a permissions record, creating default if missing."""
    perm = db.scalar(select(Permission).where(Permission.user_id == user_id))
    if perm is None:
        perm = Permission(
            user_id=user_id,
            app_tracking=True,
            browser_tracking=True,
            youtube_tracking=False,
        )
        db.add(perm)
        db.commit()
        db.refresh(perm)
    return perm


@router.post(
    "/app-usage",
    response_model=AppUsageResponse | list[AppUsageResponse],
    status_code=status.HTTP_201_CREATED,
)
def track_app_usage(
    payload: AppUsageCreate | list[AppUsageCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppUsage | list[AppUsage]:
    """Record application usage session(s) if app tracking permission is enabled."""
    permission = get_or_create_user_permission(db, current_user.id)
    if not permission.app_tracking:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="App tracking is disabled in user settings",
        )

    if isinstance(payload, list):
        if not payload:
            return []
        records = [
            AppUsage(
                user_id=current_user.id,
                app_name=item.app_name,
                window_title=item.window_title,
                start_time=item.start_time,
                end_time=item.end_time,
                duration_seconds=item.duration_seconds,
            )
            for item in payload
        ]
        db.add_all(records)
        db.commit()
        for r in records:
            db.refresh(r)
        return records

    record = AppUsage(
        user_id=current_user.id,
        app_name=payload.app_name,
        window_title=payload.window_title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_seconds=payload.duration_seconds,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/app-usage/batch",
    response_model=list[AppUsageResponse],
    status_code=status.HTTP_201_CREATED,
)
def track_app_usage_batch(
    payload: list[AppUsageCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AppUsage]:
    """Record a batch of application usage sessions."""
    result = track_app_usage(payload, current_user, db)
    return result if isinstance(result, list) else [result]



@router.post(
    "/browser-activity",
    response_model=BrowserActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def track_browser_activity(
    payload: BrowserActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrowserActivity:
    """Record browser activity if browser tracking permission is enabled."""
    permission = get_or_create_user_permission(db, current_user.id)
    if not permission.browser_tracking:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Browser tracking is disabled in user settings",
        )

    record = BrowserActivity(
        user_id=current_user.id,
        browser=payload.browser,
        url=payload.url,
        title=payload.title,
        timestamp=payload.timestamp,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/youtube-activity",
    response_model=YouTubeActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def track_youtube_activity(
    payload: YouTubeActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> YouTubeActivity:
    """Record YouTube viewing activity if YouTube tracking permission is enabled."""
    permission = get_or_create_user_permission(db, current_user.id)
    if not permission.youtube_tracking:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="YouTube tracking is disabled in user settings",
        )

    record = YouTubeActivity(
        user_id=current_user.id,
        video_id=payload.video_id,
        video_title=payload.video_title,
        url=payload.url,
        watched_time_seconds=payload.watched_time_seconds,
        timestamp=payload.timestamp,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
)
def get_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Permission:
    """Retrieve tracking permission flags for the current user."""
    return get_or_create_user_permission(db, current_user.id)


@router.put(
    "/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
)
def update_permissions(
    payload: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Permission:
    """Update tracking permission flags for the current user."""
    perm = get_or_create_user_permission(db, current_user.id)

    if payload.app_tracking is not None:
        perm.app_tracking = payload.app_tracking
    if payload.browser_tracking is not None:
        perm.browser_tracking = payload.browser_tracking
    if payload.youtube_tracking is not None:
        perm.youtube_tracking = payload.youtube_tracking

    db.commit()
    db.refresh(perm)
    return perm

