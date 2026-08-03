from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.modules.dashboard.service import DashboardService
from app.modules.auth.model import OrgSchoolStudent, StudentParent
from core.database import get_db
from core.jwt_config import get_token_payload, get_token_subject
from core.response import ErrorResponse, SuccessResponse

dashboard_router = APIRouter(
    prefix="/api/v1/dashboard"
)

@dashboard_router.get("/quick-actions")
async def get_student_quick_actions(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    results = DashboardService.get_student_quick_actions_list()
    return SuccessResponse(
        data=results,
        status_code=200
    )


@dashboard_router.get("/student-snapshot")
async def get_student_snapshot(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        return ErrorResponse(
            message="Authorization token is required",
            status_code=401,
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = get_token_payload(token)
    subject_id = get_token_subject(token)
    if (
        not payload
        or payload.get("token_type") != "access"
        or payload.get("role") not in ("parent", "student")
        or not subject_id
    ):
        return ErrorResponse(
            message="Invalid or expired token",
            status_code=401,
        )

    if payload["role"] == "parent":
        parent = (
            db.query(StudentParent)
            .filter(StudentParent.id == subject_id)
            .first()
        )
        student_id = parent.student_id if parent else None
    else:
        student_id = subject_id

    student = (
        db.query(OrgSchoolStudent)
        .filter(OrgSchoolStudent.id == student_id)
        .first()
        if student_id
        else None
    )
    if not student:
        return ErrorResponse(
            message="Student not found",
            status_code=404,
        )

    snapshot = DashboardService.get_student_snapshot(
        db,
        student.id,
        student.organization_id,
    )
    return SuccessResponse(
        message="Student snapshot fetched successfully",
        data=snapshot.model_dump(mode="json"),
    )

