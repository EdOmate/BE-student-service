
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.modules.academics.timetable_service import TimetableService
from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from core.database import get_db
from core.response import SuccessResponse

academics_router = APIRouter(
    prefix="/api/v1"
)

@academics_router.get("/timetable/timetable-today")
async def get_today_timetable(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    timetable = TimetableService.get_today_timetable(
        db=db,
        student_id=auth.student_id,
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
    )
    return SuccessResponse(
        message="Weekly timetable fetched successfully",
        data=timetable,
    )
