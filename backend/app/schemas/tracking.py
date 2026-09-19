from datetime import datetime, timezone
# from typing import Self
from typing_extensions import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppUsageCreate(BaseModel):
    app_name: str = Field(min_length=1, max_length=255)
    window_title: str | None = Field(default=None, max_length=512)
    start_time: datetime
    end_time: datetime
    duration_seconds: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def compute_duration(self) -> Self:
        if self.duration_seconds is None:
            diff = int((self.end_time - self.start_time).total_seconds())
            self.duration_seconds = max(diff, 0)
        return self


class AppUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    app_name: str
    window_title: str | None
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    created_at: datetime


class BrowserActivityCreate(BaseModel):
    browser: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1)
    title: str | None = Field(default=None, max_length=1024)
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def default_timestamp(self) -> Self:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        return self


class BrowserActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    browser: str
    url: str
    title: str | None
    timestamp: datetime
    created_at: datetime


class YouTubeActivityCreate(BaseModel):
    video_id: str = Field(min_length=1, max_length=64)
    video_title: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1)
    watched_time_seconds: int = Field(default=0, ge=0)
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def default_timestamp(self) -> Self:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        return self


class YouTubeActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    video_id: str
    video_title: str
    url: str
    watched_time_seconds: int
    timestamp: datetime
    created_at: datetime


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    app_tracking: bool
    browser_tracking: bool
    youtube_tracking: bool
    updated_at: datetime


class PermissionUpdate(BaseModel):
    app_tracking: bool | None = None
    browser_tracking: bool | None = None
    youtube_tracking: bool | None = None
