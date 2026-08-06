"""Student LMS API routes."""

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.lms.assignment_service import AssignmentService
from app.modules.lms.schema import CreateAssignmentSubmissionRequest
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


lms_router = APIRouter(
    prefix="/api/v1/lms",
    tags=["LMS"],
)


@lms_router.post("/assignments/{assignment_id}/submissions", status_code=201)
async def create_student_assignment_submission(
    payload: CreateAssignmentSubmissionRequest,
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    result, submission = AssignmentService.create_student_assignment_submission(
        db=db,
        assignment_id=assignment_id,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
        payload=payload,
    )
    if result == "not_found":
        return ErrorResponse(
            message="Assignment not found",
            status_code=404,
        )
    if result == "already_submitted":
        return ErrorResponse(
            message="Assignment already submitted",
            status_code=409,
        )

    return SuccessResponse(
        message="Assignment submitted successfully",
        data=submission.model_dump(mode="json"),
        status_code=201,
    )


@lms_router.get("/assignments/{assignment_id}")
async def get_student_assignment_detail(
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    assignment = AssignmentService.get_student_assignment_detail(
        db=db,
        assignment_id=assignment_id,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
    )
    if not assignment:
        return ErrorResponse(
            message="Assignment not found",
            status_code=404,
        )

    return SuccessResponse(
        message="Student assignment detail fetched successfully",
        data=assignment.model_dump(mode="json"),
    )


@lms_router.get("/assignments")
async def get_student_assignments(
    status_filter: Literal["all", "pending", "submitted", "overdue"] = Query(
        default="all",
        alias="status",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    subject_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, max_length=255),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    assignments = AssignmentService.list_student_assignments(
        db=db,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
        subject_id=subject_id,
        search=search,
    )
    return SuccessResponse(
        message="Student assignments fetched successfully",
        data=assignments.model_dump(mode="json"),
    )
