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


def _listing_period(year: int | None, month: int | None) -> tuple[int, int]:
    today = date.today()
    return year or today.year, month or today.month


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


@events_router.get("/holidays")
async def get_holiday_listing(
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    selected_year, selected_month = _listing_period(year, month)
    data = EventService.get_month_event_listing(
        db, auth, "holiday", selected_year, selected_month, page, page_size
    )
    return SuccessResponse(message="Holidays fetched successfully", data=data)


@events_router.get("/notices")
async def get_notice_listing(
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    selected_year, selected_month = _listing_period(year, month)
    data = EventService.get_month_event_listing(
        db, auth, "formal_circular", selected_year, selected_month, page, page_size
    )
    return SuccessResponse(message="Notices fetched successfully", data=data)


@events_router.get("/ptms")
async def get_ptm_listing(
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    selected_year, selected_month = _listing_period(year, month)
    data = EventService.get_month_event_listing(
        db, auth, "ptm", selected_year, selected_month, page, page_size
    )
    return SuccessResponse(message="PTMs fetched successfully", data=data)


@events_router.get("/broadcasts")
async def get_broadcast_listing(
    year: int | None = Query(default=None, ge=1),
    month: int | None = Query(default=None, ge=1, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    selected_year, selected_month = _listing_period(year, month)
    data = EventService.get_month_event_listing(
        db, auth, "broadcast", selected_year, selected_month, page, page_size
    )
    return SuccessResponse(message="Broadcasts fetched successfully", data=data)
