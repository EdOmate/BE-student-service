from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.library.service import StudentLibraryService
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


library_router = APIRouter(prefix="/api/v1/library", tags=["Library"])


@library_router.get("/loans/current")
async def get_current_issued_books(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentLibraryService.get_current_issued_books(
        db, auth.student_id, auth.student.organization_id
    )
    return SuccessResponse(message="Issued books fetched successfully", data=data)


@library_router.get("/loans/history")
async def get_past_issued_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentLibraryService.get_past_issued_books(
        db, auth.student_id, auth.student.organization_id, page, page_size
    )
    return SuccessResponse(message="Past issued books fetched successfully", data=data)


@library_router.get("/membership")
async def get_library_membership(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentLibraryService.get_membership_details(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    if not data:
        return ErrorResponse(message="Library membership not found", status_code=404)
    return SuccessResponse(
        message="Library membership fetched successfully",
        data=data,
    )
