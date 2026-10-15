from datetime import date

from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import AuthenticatedStudent, get_authenticated_student
from app.modules.hostel.service import StudentHostelService
from app.modules.hostel.schema import CreateHostelComplaintRequest
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


hostel_router = APIRouter(prefix="/api/v1/hostel", tags=["Hostel"])


@hostel_router.post("/complaints", status_code=201)
async def create_hostel_complaint(
    payload: CreateHostelComplaintRequest,
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        data = StudentHostelService.create_complaint(db, auth.student_id, auth.student.organization_id, payload)
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    if data is None:
        return ErrorResponse(message="Active hostel allocation not found", status_code=404)
    return SuccessResponse(message="Complaint raised successfully", data=jsonable_encoder(data), status_code=201)


@hostel_router.get("/complaints/snapshot")
async def get_hostel_complaint_snapshot(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_complaint_snapshot(db, auth.student_id, auth.student.organization_id)
    return SuccessResponse(message="Recent complaints fetched successfully", data=jsonable_encoder(data))


@hostel_router.get("/complaints")
async def get_hostel_complaints(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: int | None = Query(default=None, ge=1, le=6),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.list_complaints(db, auth.student_id, auth.student.organization_id, page, page_size, status)
    return SuccessResponse(message="Complaints fetched successfully", data=jsonable_encoder(data))


@hostel_router.get("/complaints/{complaint_id}")
async def get_hostel_complaint_detail(
    complaint_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_complaint_detail(db, auth.student_id, auth.student.organization_id, complaint_id)
    if data is None:
        return ErrorResponse(message="Complaint not found", status_code=404)
    return SuccessResponse(message="Complaint fetched successfully", data=jsonable_encoder(data))


@hostel_router.get("/overview")
async def get_hostel_overview(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_overview(
        db, auth.student_id, auth.student.organization_id
    )
    if not data:
        return ErrorResponse(message="Active hostel allocation not found", status_code=404)
    return SuccessResponse(message="Hostel overview fetched successfully", data=data)


@hostel_router.get("/wardens")
async def get_hostel_wardens(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_wardens(
        db, auth.student_id, auth.student.organization_id
    )
    if data is None:
        return ErrorResponse(message="Active hostel allocation not found", status_code=404)
    return SuccessResponse(
        message="Hostel wardens fetched successfully",
        data={"wardens": data},
    )


@hostel_router.get("/mess/today")
async def get_today_mess(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_mess_for_date(
        db, auth.student_id, auth.student.organization_id, StudentHostelService.today()
    )
    if data is None:
        return ErrorResponse(message="Active hostel allocation not found", status_code=404)
    return SuccessResponse(message="Today's mess menu fetched successfully", data=data)


@hostel_router.get("/mess/weekly")
async def get_weekly_mess(
    week_start: date | None = Query(default=None),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    data = StudentHostelService.get_weekly_mess(
        db, auth.student_id, auth.student.organization_id, week_start or StudentHostelService.today()
    )
    if data is None:
        return ErrorResponse(message="Active hostel allocation not found", status_code=404)
    return SuccessResponse(message="Weekly mess menu fetched successfully", data=data)
