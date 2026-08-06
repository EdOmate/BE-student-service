"""Student API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.students.service import StudentService
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


student_router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
)


@student_router.get("/today-status")
async def get_student_today_status(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    status = StudentService.get_today_status(
        db=db,
        role=auth.role,
        student_id=auth.student_id,
        parent_id=auth.parent_id,
    )
    if not status:
        return ErrorResponse(
            message="Student not found",
            status_code=404,
        )

    return SuccessResponse(
        message="Student today status fetched successfully",
        data=status.model_dump(mode="json"),
    )
