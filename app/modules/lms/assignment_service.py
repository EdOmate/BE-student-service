"""Business logic for student assignment APIs."""

from datetime import datetime
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.lms.repository import LMSRepository
from app.modules.lms.communication_service import AssignmentCommunicationService
from app.modules.lms.models import LMSAssignmentActivityLog
from app.modules.lms.schema import (
    AssignmentEvaluationDetail,
    AssignmentListItem,
    AssignmentSubmissionDetail,
    AssignmentStatusCounts,
    CreateAssignmentSubmissionRequest,
    CustomPagination,
    StudentAssignmentDetailResponse,
    StudentAssignmentListResponse,
)
from app.modules.students.repository import StudentRepository


IST = ZoneInfo("Asia/Kolkata")


class AssignmentService:
    @staticmethod
    def get_pending_assignment_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section:
            return {"pending_count": 0}

        org_class = mapping.section.org_class
        pending_count, earliest = LMSRepository.get_pending_assignment_snapshot(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )
        now = datetime.now(IST).replace(tzinfo=None)
        return {
            "pending_count": pending_count,
            "earliest_title": earliest.title if earliest else None,
            "due_at": earliest.due_at if earliest else None,
            "due_label": (
                AssignmentService._due_label(earliest.due_at, now)
                if earliest and earliest.due_at
                else None
            ),
        }

    @staticmethod
    def _due_label(due_at: datetime, now: datetime) -> str:
        difference = (due_at.date() - now.date()).days
        if difference == 0:
            return "Due Today"
        if difference == 1:
            return "Due Tomorrow"
        if difference < 0:
            return "Overdue"
        return f"Due {due_at.strftime('%d %b')}"

    @staticmethod
    def create_student_assignment_submission(
        db: Session,
        assignment_id: int,
        student_id: int,
        organization_id: int,
        payload: CreateAssignmentSubmissionRequest,
    ) -> tuple[str, AssignmentSubmissionDetail | None]:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping:
            return "not_found", None

        org_class = mapping.section.org_class if mapping.section else None
        assignment_data = LMSRepository.get_student_assignment_detail(
            db=db,
            assignment_id=assignment_id,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )
        if not assignment_data:
            return "not_found", None
        if assignment_data["submission_rows"]:
            return "already_submitted", None

        submitted_at = datetime.now(IST).replace(tzinfo=None)
        submission = LMSRepository.create_assignment_submission(
            db=db,
            assignment_id=assignment_id,
            student_id=student_id,
            submitted_at=submitted_at,
            remarks=payload.remarks,
            files=payload.files,
        )
        if not submission:
            return "already_submitted", None
        AssignmentCommunicationService.log_activity(
            db,
            assignment_id,
            student_id,
            LMSAssignmentActivityLog.ACTIVITY_SUBMITTED,
        )
        return "created", AssignmentSubmissionDetail(
            id=submission.id,
            student_id=submission.student_id,
            submitted_at=submission.submitted_at,
            remarks=submission.remarks,
            files=submission.files,
            created_at=submission.created_at,
            evaluation=None,
        )

    @staticmethod
    def get_student_assignment_detail(
        db: Session,
        assignment_id: int,
        student_id: int,
        organization_id: int,
    ) -> StudentAssignmentDetailResponse | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping:
            return None

        org_class = mapping.section.org_class if mapping.section else None
        data = LMSRepository.get_student_assignment_detail(
            db=db,
            assignment_id=assignment_id,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )
        if not data:
            return None

        AssignmentCommunicationService.log_activity(
            db,
            assignment_id,
            student_id,
            LMSAssignmentActivityLog.ACTIVITY_VIEWED,
        )

        assignment = data["assignment"]
        now = datetime.now(IST).replace(tzinfo=None)
        submissions = []
        for submission, evaluation in data["submission_rows"]:
            evaluation_detail = None
            if evaluation:
                evaluation_detail = AssignmentEvaluationDetail(
                    id=evaluation.id,
                    marks=(
                        float(evaluation.marks)
                        if evaluation.marks is not None
                        else None
                    ),
                    feedback=evaluation.feedback,
                    evaluated_by_id=evaluation.evaluated_by_id,
                    evaluated_at=evaluation.evaluated_at,
                )
            submissions.append(
                AssignmentSubmissionDetail(
                    id=submission.id,
                    student_id=submission.student_id,
                    submitted_at=submission.submitted_at,
                    remarks=submission.remarks,
                    files=submission.files,
                    created_at=submission.created_at,
                    evaluation=evaluation_detail,
                )
            )

        current_submission = (
            data["submission_rows"][0][0]
            if data["submission_rows"]
            else None
        )
        return StudentAssignmentDetailResponse(
            id=assignment.id,
            title=assignment.title,
            description=assignment.description,
            subject_mapping_id=assignment.subject_mapping_id,
            subject_id=data["subject_id"],
            subject_name=data["subject_name"],
            teacher_id=assignment.teacher_id,
            grading_mode=assignment.grading_mode,
            max_marks=(
                float(assignment.max_marks)
                if assignment.max_marks is not None
                else None
            ),
            deadline_type=assignment.deadline_type,
            due_at=assignment.due_at,
            attachments=assignment.attachments,
            published_at=assignment.published_at,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            assignment_status=AssignmentService._assignment_status(
                assignment,
                current_submission,
                now,
            ),
            submissions=submissions,
        )

    @staticmethod
    def list_student_assignments(
        db: Session,
        student_id: int,
        organization_id: int,
        status_filter: str = "all",
        page: int = 1,
        page_size: int = 20,
        subject_id: int | None = None,
        search: str | None = None,
    ) -> StudentAssignmentListResponse:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping:
            return AssignmentService._empty_response(page, page_size)

        org_class = mapping.section.org_class if mapping.section else None
        now = datetime.now(IST).replace(tzinfo=None)
        data = LMSRepository.get_student_assignments(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
            now=now,
            subject_id=subject_id,
            search=search,
        )

        results = []
        for assignment, submission in data["rows"]:
            assignment_status = AssignmentService._assignment_status(
                assignment,
                submission,
                now,
            )
            subject = data["subjects"].get(assignment.subject_mapping_id, {})
            results.append(
                AssignmentListItem(
                    id=assignment.id,
                    title=assignment.title,
                    description=assignment.description,
                    subject_mapping_id=assignment.subject_mapping_id,
                    subject_id=subject.get("subject_id"),
                    subject_name=subject.get("subject_name"),
                    teacher_id=assignment.teacher_id,
                    grading_mode=assignment.grading_mode,
                    max_marks=(
                        float(assignment.max_marks)
                        if assignment.max_marks is not None
                        else None
                    ),
                    deadline_type=assignment.deadline_type,
                    due_at=assignment.due_at,
                    attachments=assignment.attachments,
                    published_at=assignment.published_at,
                    assignment_status=assignment_status,
                    submission_id=submission.id if submission else None,
                    submitted_at=submission.submitted_at if submission else None,
                )
            )

        total_items = data["total_items"]
        total_pages = ceil(total_items / page_size) if total_items else 0
        return StudentAssignmentListResponse(
            results=results,
            counts=AssignmentStatusCounts(**data["counts"]),
            pagination=CustomPagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1 and total_pages > 0,
            ),
        )

    @staticmethod
    def _assignment_status(assignment, submission, now: datetime) -> str:
        if submission:
            return "submitted"
        if assignment.due_at and assignment.due_at < now:
            return "overdue"
        return "pending"

    @staticmethod
    def _empty_response(page: int, page_size: int):
        return StudentAssignmentListResponse(
            results=[],
            counts=AssignmentStatusCounts(
                all=0,
                pending=0,
                submitted=0,
                overdue=0,
            ),
            pagination=CustomPagination(
                page=page,
                page_size=page_size,
                total_items=0,
                total_pages=0,
                has_next=False,
                has_previous=False,
            ),
        )
