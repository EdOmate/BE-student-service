from typing import Any, Literal

from pydantic import BaseModel, Field


class DeviceTokenUpsertRequest(BaseModel):
    fcm_token: str = Field(..., min_length=1, max_length=512)
    platform: Literal["android", "ios", "web"]
    device_id: str | None = Field(default=None, max_length=150)
    device_name: str | None = Field(default=None, max_length=255)
    push_enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationReadStatusRequest(BaseModel):
    notification_id: int = Field(..., ge=1)
    is_read: bool
