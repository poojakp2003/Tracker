from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.permissions import router as permissions_router
from app.routers.tracking import router as tracking_router

__all__ = ["auth_router", "permissions_router", "tracking_router", "dashboard_router"]

