
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.modules.academics.timetable_service import TimetableService
from app.modules.academics.attendance_service import StudentAttendanceService
from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from core.database import get_db
from core.response import SuccessResponse
from app.modules.students.service import StudentService

academics_router = APIRouter(
    prefix="/api/v1"
)

IST = ZoneInfo("Asia/Kolkata")


@academics_router.get("/academics/attendance/today")
async def get_today_attendance(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    status = StudentService.get_today_status(
        db=db,
        role=auth.role,
        student_id=auth.student_id,
        parent_id=auth.parent_id,
    )
    return SuccessResponse(
        message="Today's attendance fetched successfully",
        data=status.attendance.model_dump(mode="json") if status else None,
    )


@academics_router.get("/academics/attendance/calendar")
async def get_monthly_attendance(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    today = datetime.now(IST).date()
    data = StudentAttendanceService.get_month(
        db,
        auth.student_id,
        year or today.year,
        month or today.month,
    )
    return SuccessResponse(
        message="Monthly attendance fetched successfully",
        data=data,
    )


@academics_router.get("/academics/attendance/statistics")
async def get_attendance_statistics(
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    today = datetime.now(IST).date()
    data = StudentAttendanceService.get_statistics(
        db,
        auth.student_id,
        year or today.year,
        month or today.month,
    )
    return SuccessResponse(
        message="Attendance statistics fetched successfully",
        data=data,
    )

@academics_router.get("/timetable/timetable-today")
async def get_today_timetable(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    timetable = TimetableService.get_today_timetable(
        db=db,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
    )
    return SuccessResponse(
        message="Today's timetable fetched successfully",
        data=timetable,
    )


@academics_router.get("/timetable/timetable-weekly")
async def get_weekly_timetable(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    timetable = TimetableService.get_weekly_timetable(
        db=db,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
    )
    return SuccessResponse(
        message="Weekly timetable fetched successfully",
        data=timetable,
    )
