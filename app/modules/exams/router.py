from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.exams.service import ExamService
from core.database import get_db
from core.response import SuccessResponse


exams_router = APIRouter(prefix="/api/v1/exams", tags=["Exams"])


@exams_router.get("")
async def get_exams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = ExamService.list_exam_series(
        db,
        auth.student_id,
        auth.student.organization_id,
        page,
        page_size,
    )
    return SuccessResponse(message="Exams fetched successfully", data=data)


@exams_router.get("/upcoming")
async def get_upcoming_exams(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = ExamService.list_upcoming_exam_series(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    return SuccessResponse(
        message="Upcoming exams fetched successfully",
        data=data,
    )


@exams_router.get("/report-cards")
async def get_report_cards(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = ExamService.list_report_cards(
        db,
        auth.student_id,
        auth.student.organization_id,
        page,
        page_size,
    )
    return SuccessResponse(message="Report cards fetched successfully", data=data)


@exams_router.get("/{exam_id}")
async def get_exam_detail(
    exam_id: int,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = ExamService.get_exam_detail(
        db,
        exam_id,
        auth.student_id,
        auth.student.organization_id,
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    return SuccessResponse(message="Exam details fetched successfully", data=data)


@exams_router.get("/{exam_id}/results")
async def get_exam_results(
    exam_id: int,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = ExamService.get_exam_results(
        db,
        exam_id,
        auth.student_id,
        auth.student.organization_id,
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found",
        )
    return SuccessResponse(message="Exam results fetched successfully", data=data)
