"""Database access for student LMS operations."""

import json
from datetime import datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.academics.models import OrgSubject
from app.modules.lms.models import (
    LMSAssignment,
    LMSAssignmentEvaluation,
    LMSAssignmentSubmission,
)


class LMSRepository:
    @staticmethod
    def get_pending_assignment_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
    ) -> tuple[int, LMSAssignment | None]:
        query = (
            db.query(LMSAssignment)
            .outerjoin(
                LMSAssignmentSubmission,
                and_(
                    LMSAssignmentSubmission.assignment_id == LMSAssignment.id,
                    LMSAssignmentSubmission.student_id == student_id,
                ),
            )
            .filter(
                LMSAssignment.organization_id == organization_id,
                LMSAssignment.status == 2,
                LMSAssignmentSubmission.id.is_(None),
                LMSAssignment.section_ids.is_not(None),
                func.json_contains(
                    LMSAssignment.section_ids,
                    json.dumps(section_id),
                )
                == 1,
            )
        )
        if academic_year:
            query = query.filter(LMSAssignment.academic_year == academic_year)
        return query.count(), query.order_by(
            LMSAssignment.due_at.is_(None),
            LMSAssignment.due_at.asc(),
            LMSAssignment.id.asc(),
        ).first()

    @staticmethod
    def create_assignment_submission(
        db: Session,
        assignment_id: int,
        student_id: int,
        submitted_at: datetime,
        remarks: str | None,
        files: list[str],
    ) -> LMSAssignmentSubmission | None:
        submission = LMSAssignmentSubmission(
            assignment_id=assignment_id,
            student_id=student_id,
            submitted_at=submitted_at,
            remarks=remarks,
            files=files,
        )
        db.add(submission)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return None
        db.refresh(submission)
        return submission

    @staticmethod
    def get_student_assignment_detail(
        db: Session,
        assignment_id: int,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
    ):
        assignment_query = db.query(LMSAssignment).filter(
            LMSAssignment.id == assignment_id,
            LMSAssignment.organization_id == organization_id,
            LMSAssignment.status == 2,
            LMSAssignment.section_ids.is_not(None),
            func.json_contains(
                LMSAssignment.section_ids,
                json.dumps(section_id),
            )
            == 1,
        )
        if academic_year:
            assignment_query = assignment_query.filter(
                LMSAssignment.academic_year == academic_year
            )
        assignment = assignment_query.first()
        if not assignment:
            return None

        submission_rows = (
            db.query(LMSAssignmentSubmission, LMSAssignmentEvaluation)
            .outerjoin(
                LMSAssignmentEvaluation,
                LMSAssignmentEvaluation.submission_id
                == LMSAssignmentSubmission.id,
            )
            .filter(
                LMSAssignmentSubmission.assignment_id == assignment.id,
                LMSAssignmentSubmission.student_id == student_id,
            )
            .order_by(LMSAssignmentSubmission.id.desc())
            .all()
        )
        subject = (
            db.query(OrgSubject)
            .filter(
                OrgSubject.id == assignment.subject_id,
                OrgSubject.organization_id == organization_id,
            )
            .first()
        )
        return {
            "assignment": assignment,
            "subject_name": subject.name if subject else None,
            "submission_rows": submission_rows,
        }

    @staticmethod
    def get_student_assignments(
        db: Session,
        student_id: int,
        organization_id: int,
        section_id: int,
        academic_year: str | None,
        status_filter: str,
        page: int,
        page_size: int,
        now: datetime,
        subject_id: int | None = None,
        search: str | None = None,
    ) -> dict:
        submission_join = and_(
            LMSAssignmentSubmission.assignment_id == LMSAssignment.id,
            LMSAssignmentSubmission.student_id == student_id,
        )
        query = (
            db.query(LMSAssignment, LMSAssignmentSubmission)
            .outerjoin(LMSAssignmentSubmission, submission_join)
            .filter(
                LMSAssignment.organization_id == organization_id,
                LMSAssignment.status == 2,
                LMSAssignment.section_ids.is_not(None),
                # MySQL JSON arrays contain numeric section IDs.
                func.json_contains(
                    LMSAssignment.section_ids,
                    json.dumps(section_id),
                )
                == 1,
            )
        )
        if academic_year:
            query = query.filter(LMSAssignment.academic_year == academic_year)
        if subject_id is not None:
            query = query.filter(LMSAssignment.subject_id == subject_id)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    LMSAssignment.title.ilike(pattern),
                    LMSAssignment.description.ilike(pattern),
                )
            )

        not_submitted = LMSAssignmentSubmission.id.is_(None)
        submitted = LMSAssignmentSubmission.id.is_not(None)
        overdue = and_(
            not_submitted,
            LMSAssignment.due_at.is_not(None),
            LMSAssignment.due_at < now,
        )
        pending = and_(
            not_submitted,
            or_(
                LMSAssignment.due_at.is_(None),
                LMSAssignment.due_at >= now,
            ),
        )

        counts = {
            "all": query.count(),
            "pending": query.filter(pending).count(),
            "submitted": query.filter(submitted).count(),
            "overdue": query.filter(overdue).count(),
        }
        status_expressions = {
            "pending": pending,
            "submitted": submitted,
            "overdue": overdue,
        }
        if status_filter != "all":
            query = query.filter(status_expressions[status_filter])

        total_items = query.count()
        rows = (
            query.order_by(
                LMSAssignment.due_at.is_(None),
                LMSAssignment.due_at.asc(),
                LMSAssignment.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        subject_ids = {assignment.subject_id for assignment, _ in rows}
        subjects = (
            {
                subject.id: subject.name
                for subject in db.query(OrgSubject)
                .filter(OrgSubject.id.in_(subject_ids))
                .all()
            }
            if subject_ids
            else {}
        )
        return {
            "rows": rows,
            "subjects": subjects,
            "counts": counts,
            "total_items": total_items,
        }
