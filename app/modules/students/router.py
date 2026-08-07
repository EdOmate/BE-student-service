"""Student API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_parent,
    get_authenticated_student,
)
from app.modules.students.service import StudentService
from app.modules.students.schema import CreateLeaveRequest
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


student_router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
)


@student_router.get("/leave-requests")
async def get_student_leave_requests(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        leaves = StudentService.list_leave_requests(
            db=db,
            student_id=auth.student_id,
            organization_id=auth.student.organization_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    return SuccessResponse(
        message="Student leave requests fetched successfully",
        data=leaves.model_dump(mode="json"),
    )


@student_router.post("/leave-requests", status_code=201)
async def create_student_leave_request(
    payload: CreateLeaveRequest,
    auth: AuthenticatedStudent = Depends(get_authenticated_parent),
    db: Session = Depends(get_db),
):
    try:
        result, leave = StudentService.create_leave_request(
            db=db,
            student_id=auth.student_id,
            organization_id=auth.student.organization_id,
            parent_id=auth.parent_id,
            payload=payload,
        )
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    if result == "student_not_found":
        return ErrorResponse(message="Active student not found", status_code=404)
    if result == "past_date":
        return ErrorResponse(
            message="Leave cannot be requested for past dates",
            status_code=400,
        )
    if result == "overlap":
        return ErrorResponse(
            message=(
                "An overlapping pending or approved leave request already exists"
            ),
            status_code=409,
        )
    return SuccessResponse(
        message="Student leave request submitted successfully",
        data=leave.model_dump(mode="json"),
        status_code=201,
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
