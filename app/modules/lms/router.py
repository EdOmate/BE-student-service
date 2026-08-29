"""Student LMS API routes."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.lms.assignment_service import AssignmentService
from app.modules.lms.classwork_service import StudentClassWorkService
from app.modules.lms.communication_service import AssignmentCommunicationService
from app.modules.lms.diary_service import StudentDiaryService
from app.modules.lms.lesson_plan_service import StudentLessonPlanService
from app.modules.lms.material_service import StudentMaterialService
from app.modules.lms.schema import (
    AssignmentCommentRequest,
    AssignmentMessageRequest,
    CreateAssignmentSubmissionRequest,
    DiaryAcknowledgementRequest,
)
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse


lms_router = APIRouter(
    prefix="/api/v1/lms",
    tags=["LMS"],
)


@lms_router.get("/classworks/{classwork_id}")
async def get_student_classwork_detail(
    classwork_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    classwork = StudentClassWorkService.get_classwork_detail(
        db, classwork_id, auth.student_id, auth.student.organization_id
    )
    if not classwork:
        return ErrorResponse(message="Classwork not found", status_code=404)
    return SuccessResponse(
        message="Classwork fetched successfully",
        data=jsonable_encoder(classwork),
    )


@lms_router.get("/classworks")
async def get_student_classworks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    classwork_date: date | None = Query(default=None, alias="date"),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    subject_id: int | None = Query(default=None, ge=1),
    coverage_level: Literal["unit", "chapter", "topic", "custom"] | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        data = StudentClassWorkService.list_classworks(
            db, auth.student_id, auth.student.organization_id,
            page, page_size, classwork_date, from_date, to_date,
            subject_id, coverage_level, search,
        )
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    return SuccessResponse(
        message="Classwork list fetched successfully",
        data=jsonable_encoder(data),
    )


@lms_router.post("/diary/{diary_entry_id}/view")
async def mark_student_diary_viewed(
    diary_entry_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    entry = StudentDiaryService.mark_viewed(
        db, diary_entry_id, auth.student_id, auth.student.organization_id
    )
    if not entry:
        return ErrorResponse(message="Diary entry not found", status_code=404)
    return SuccessResponse(
        message="Diary entry marked as viewed",
        data=jsonable_encoder(entry),
    )


@lms_router.post("/diary/{diary_entry_id}/acknowledge")
async def acknowledge_student_diary(
    payload: DiaryAcknowledgementRequest,
    diary_entry_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    entry = StudentDiaryService.acknowledge(
        db, diary_entry_id, auth.student_id, auth.student.organization_id,
        payload.acknowledgement_note,
    )
    if not entry:
        return ErrorResponse(message="Diary entry not found", status_code=404)
    return SuccessResponse(
        message="Diary entry acknowledged successfully",
        data=jsonable_encoder(entry),
    )


@lms_router.get("/diary/{diary_entry_id}")
async def get_student_diary_detail(
    diary_entry_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    entry = StudentDiaryService.get_entry(
        db, diary_entry_id, auth.student_id, auth.student.organization_id
    )
    if not entry:
        return ErrorResponse(message="Diary entry not found", status_code=404)
    return SuccessResponse(
        message="Diary entry fetched successfully",
        data=jsonable_encoder(entry),
    )


@lms_router.get("/diary")
async def get_student_diary(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    reference_type: str | None = Query(default=None, max_length=32),
    entry_date: date | None = Query(default=None, alias="date"),
    acknowledged: bool | None = Query(default=None),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        data = StudentDiaryService.list_entries(
            db, auth.student_id, auth.student.organization_id,
            page, page_size, reference_type, entry_date, acknowledged,
        )
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    return SuccessResponse(
        message="Student diary fetched successfully",
        data=jsonable_encoder(data),
    )


@lms_router.get("/lesson-plans/{lesson_plan_id}")
async def get_student_lesson_plan_detail(
    lesson_plan_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    plan = StudentLessonPlanService.get_plan_detail(
        db, lesson_plan_id, auth.student_id, auth.student.organization_id
    )
    if not plan:
        return ErrorResponse(message="Lesson plan not found", status_code=404)
    return SuccessResponse(
        message="Lesson plan fetched successfully",
        data=jsonable_encoder(plan),
    )


@lms_router.get("/lesson-plans")
async def get_student_lesson_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    subject_id: int | None = Query(default=None, ge=1),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    try:
        data = StudentLessonPlanService.list_plans(
            db, auth.student_id, auth.student.organization_id,
            page, page_size, subject_id, from_date, to_date, search,
        )
    except ValueError as exc:
        return ErrorResponse(message=str(exc), status_code=400)
    return SuccessResponse(
        message="Lesson plans fetched successfully",
        data=jsonable_encoder(data),
    )


@lms_router.get("/materials/{material_id}")
async def get_student_material_detail(
    material_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    material = StudentMaterialService.get_student_material_detail(
        db=db,
        material_id=material_id,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
    )
    if not material:
        return ErrorResponse(
            message="Study material not found",
            status_code=404,
        )
    return SuccessResponse(
        message="Study material fetched successfully",
        data=material.model_dump(mode="json"),
    )


@lms_router.get("/materials")
async def get_student_materials(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    subject_id: int | None = Query(default=None, ge=1),
    material_type: int | None = Query(default=None, ge=1, le=7),
    search: str | None = Query(default=None, max_length=255),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    materials = StudentMaterialService.list_student_materials(
        db=db,
        student_id=auth.student_id,
        organization_id=auth.student.organization_id,
        page=page,
        page_size=page_size,
        subject_id=subject_id,
        material_type=material_type,
        search=search,
    )
    return SuccessResponse(
        message="Study material list fetched successfully",
        data=materials.model_dump(mode="json"),
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


@lms_router.get("/assignments/{assignment_id}/thread")
async def get_assignment_submission_thread(
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    result, data = AssignmentCommunicationService.get_thread(
        db, assignment_id, auth.student_id, auth.student.organization_id
    )
    if result == "not_found":
        return ErrorResponse(message="Assignment not found", status_code=404)
    if result == "submission_required":
        return ErrorResponse(
            message="Assignment must be submitted before starting a thread",
            status_code=409,
        )
    return SuccessResponse(
        message="Assignment thread fetched successfully",
        data=jsonable_encoder(data),
    )


@lms_router.post(
    "/assignments/{assignment_id}/thread/messages",
    status_code=201,
)
async def create_assignment_submission_message(
    payload: AssignmentMessageRequest,
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    result, data = AssignmentCommunicationService.create_message(
        db, assignment_id, auth.student_id, auth.student.organization_id,
        auth.role, auth.parent_id, payload.message, payload.attachment_url,
    )
    if result == "not_found":
        return ErrorResponse(message="Assignment not found", status_code=404)
    if result == "submission_required":
        return ErrorResponse(
            message="Assignment must be submitted before sending a message",
            status_code=409,
        )
    return SuccessResponse(
        message="Assignment message sent successfully",
        data=jsonable_encoder(data),
        status_code=201,
    )


@lms_router.get("/assignments/{assignment_id}/comments")
async def get_assignment_comments(
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    comments = AssignmentCommunicationService.list_comments(
        db, assignment_id, auth.student_id, auth.student.organization_id
    )
    if comments is None:
        return ErrorResponse(message="Assignment not found", status_code=404)
    return SuccessResponse(
        message="Assignment comments fetched successfully",
        data=jsonable_encoder({"comments": comments}),
    )


@lms_router.post("/assignments/{assignment_id}/comments", status_code=201)
async def create_assignment_comment(
    payload: AssignmentCommentRequest,
    assignment_id: int = Path(ge=1),
    auth: AuthenticatedStudent = Depends(get_authenticated_student),
    db: Session = Depends(get_db),
):
    result, comment = AssignmentCommunicationService.create_comment(
        db, assignment_id, auth.student_id, auth.student.organization_id,
        auth.role, auth.parent_id, payload.message, payload.parent_comment_id,
    )
    if result == "not_found":
        return ErrorResponse(message="Assignment not found", status_code=404)
    if result == "invalid_parent":
        return ErrorResponse(
            message="Parent comment does not belong to this assignment",
            status_code=400,
        )
    return SuccessResponse(
        message="Assignment comment created successfully",
        data=jsonable_encoder(comment),
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
