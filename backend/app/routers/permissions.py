from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.permission import Permission
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.tracking import get_or_create_user_permission
from app.schemas.tracking import PermissionResponse, PermissionUpdate

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user tracking permissions",
)
def get_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Permission:
    """Retrieve tracking permissions for the authenticated user from the database.
    If no record exists, default permissions are created and returned.
    """
    return get_or_create_user_permission(db, current_user.id)


@router.put(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user tracking permissions",
)
def update_permissions(
    payload: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Permission:
    """Update tracking permissions (app_tracking, browser_tracking, youtube_tracking)
    in PostgreSQL database for the authenticated user.
    """
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
