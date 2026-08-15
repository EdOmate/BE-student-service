"""Student event and holiday API routes."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.events.service import EventService
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


events_router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@events_router.get("/calendar")
async def get_month_calendar(
    month: str | None = Query(default=None, description="Month in YYYY-MM format"),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        selected_month = month or date.today().strftime("%Y-%m")
        data = EventService.get_month_calendar(db, auth, selected_month)
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    return SuccessResponse(message="Calendar fetched successfully", data=data)


@events_router.get("/upcoming-holidays")
async def get_upcoming_holidays(
    limit: int = Query(default=10, ge=1, le=50),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    holidays = EventService.get_upcoming_holidays(db, auth, limit)
    return SuccessResponse(
        message="Upcoming holidays fetched successfully",
        data={"holidays": holidays},
    )


@events_router.get("/upcoming-events")
async def get_upcoming_events(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = EventService.get_upcoming_events(db, auth)
    return SuccessResponse(
        message="Upcoming events for the next 15 days fetched successfully",
        data=data,
    )
