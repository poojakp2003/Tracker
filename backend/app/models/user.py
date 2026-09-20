from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.app_usage import AppUsage
    from app.models.browser_activity import BrowserActivity
    from app.models.permission import Permission
    from app.models.youtube_activity import YouTubeActivity


class User(Base):
    """SQLAlchemy model representing an application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    permission: Mapped["Permission"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    app_usages: Mapped[list["AppUsage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    browser_activities: Mapped[list["BrowserActivity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    youtube_activities: Mapped[list["YouTubeActivity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


