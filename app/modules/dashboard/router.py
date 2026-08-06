from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.dashboard.service import DashboardService
from core.database import get_db
from core.response import SuccessResponse

dashboard_router = APIRouter(
    prefix="/api/v1/dashboard"
)

@dashboard_router.get("/quick-actions")
async def get_student_quick_actions(
    _auth: AuthenticatedStudent = Depends(get_authenticated_student),
):
    results = DashboardService.get_student_quick_actions_list()
    return SuccessResponse(
        data=results,
        status_code=200
    )


@dashboard_router.get("/student-snapshot")
async def get_student_snapshot(
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    snapshot = DashboardService.get_student_snapshot(
        db,
        auth.student_id,
        auth.student.organization_id,
    )
    return SuccessResponse(
        message="Student snapshot fetched successfully",
        data=snapshot.model_dump(mode="json"),
    )
