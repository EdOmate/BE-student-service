"""Student fee API routes."""

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.fees.service import StudentFeeService
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


fees_router = APIRouter(prefix="/api/v1/fees", tags=["Fees"])


@fees_router.get("/credits")
async def get_credit_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.list_credit_transactions(
        db,
        auth.student_id,
        auth.student.organization_id,
        page,
        page_size,
    )
    return SuccessResponse(
        message="Credit transactions fetched successfully",
        data=data,
    )


@fees_router.get("/credits/snapshot")
async def get_credit_snapshot(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.get_credit_snapshot(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    return SuccessResponse(
        message="Credit snapshot fetched successfully",
        data=data,
    )


@fees_router.get("/invoices")
async def get_invoices(
    status_filter: Literal[
        "all", "paid", "unpaid", "partially_paid", "overdue"
    ] = Query(default="all", alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.list_invoices(
        db,
        auth.student_id,
        auth.student.organization_id,
        status_filter,
        page,
        page_size,
    )
    return SuccessResponse(
        message="Invoices fetched successfully",
        data=data,
    )


@fees_router.get("/invoices/snapshot")
async def get_invoice_snapshot(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.get_invoice_snapshot(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    return SuccessResponse(
        message="Invoice snapshot fetched successfully",
        data=data,
    )


@fees_router.get("/invoices/{invoice_id}")
async def get_invoice_detail(
    invoice_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.get_invoice_detail(
        db,
        invoice_id,
        auth.student_id,
        auth.student.organization_id,
    )
    if not data:
        return ErrorResponse(message="Invoice not found", status_code=404)
    return SuccessResponse(
        message="Invoice detail fetched successfully",
        data=data,
    )


@fees_router.get("/overview")
async def get_fee_overview(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentFeeService.get_overview(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    return SuccessResponse(
        message="Fee overview fetched successfully",
        data=data,
    )
