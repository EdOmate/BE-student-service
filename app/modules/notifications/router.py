from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.notifications.schema import (
    DeviceTokenUpsertRequest,
    NotificationReadStatusRequest,
)
from app.modules.notifications.service import StudentNotificationService
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


notifications_router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)


@notifications_router.get("/inbox")
async def get_notification_inbox(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_read: bool | None = Query(default=None),
    query: str | None = Query(default=None, max_length=200),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentNotificationService.list_notifications(
        db,
        auth,
        page,
        page_size,
        is_read,
        query,
    )
    return SuccessResponse(
        message="Notifications fetched successfully",
        data=data,
    )


@notifications_router.put("/inbox")
async def update_notification_read_status(
    data: NotificationReadStatusRequest,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    recipient = StudentNotificationService.update_read_status(
        db,
        auth,
        data.notification_id,
        data.is_read,
    )
    if not recipient:
        return ErrorResponse(message="Notification not found", status_code=404)
    return SuccessResponse(
        message=(
            "Notification marked as read"
            if data.is_read
            else "Notification marked as unread"
        ),
        data=StudentNotificationService._serialize_notification(recipient),
    )


@notifications_router.put("/device-token")
async def upsert_device_token(
    data: DeviceTokenUpsertRequest,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    token, created = StudentNotificationService.upsert_device_token(db, auth, data)
    return SuccessResponse(
        message=(
            "Notification device token added successfully"
            if created
            else "Notification device token updated successfully"
        ),
        data=StudentNotificationService.serialize_device_token(token),
        status_code=201 if created else 200,
    )
