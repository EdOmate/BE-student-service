"""Student diary listing and acknowledgement logic."""

from datetime import date, datetime
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.modules.lms.models import (
    StudentDiaryAcknowledgement,
    StudentDiaryEntry,
)
from app.modules.students.repository import StudentRepository


IST = ZoneInfo("Asia/Kolkata")


class StudentDiaryService:
    REFERENCE_TYPES = {
        "classwork",
        "homework",
        "student_remark",
        "event_announcement",
        "activity_spotlight",
        "lesson_plan",
        "assignment",
        "assessment",
        "study_material",
        "event",
    }

    @staticmethod
    def _now():
        return datetime.now(IST).replace(tzinfo=None)

    @staticmethod
    def _academic_year(db: Session, student_id: int):
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section or not mapping.section.org_class:
            return None
        return mapping.section.org_class.academic_year

    @staticmethod
    def _base_query(db, student_id, organization_id):
        academic_year = StudentDiaryService._academic_year(db, student_id)
        if not academic_year:
            return None
        now = StudentDiaryService._now()
        return (
            db.query(StudentDiaryEntry, StudentDiaryAcknowledgement)
            .outerjoin(
                StudentDiaryAcknowledgement,
                and_(
                    StudentDiaryAcknowledgement.diary_entry_id
                    == StudentDiaryEntry.id,
                    StudentDiaryAcknowledgement.is_active.is_(True),
                ),
            )
            .filter(
                StudentDiaryEntry.organization_id == organization_id,
                StudentDiaryEntry.student_id == student_id,
                StudentDiaryEntry.academic_year == academic_year,
                StudentDiaryEntry.is_active.is_(True),
                StudentDiaryEntry.is_published.is_(True),
                or_(
                    StudentDiaryEntry.publish_at.is_(None),
                    StudentDiaryEntry.publish_at <= now,
                ),
                or_(
                    StudentDiaryEntry.expires_at.is_(None),
                    StudentDiaryEntry.expires_at > now,
                ),
            )
        )

    @staticmethod
    def list_entries(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
        reference_type: str | None = None,
        entry_date: date | None = None,
        acknowledged: bool | None = None,
    ) -> dict:
        selected_date = entry_date or StudentDiaryService._now().date()
        query = StudentDiaryService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return StudentDiaryService._empty(
                page, page_size, selected_date
            )
        if reference_type:
            reference_type = reference_type.strip().lower()
            if reference_type not in StudentDiaryService.REFERENCE_TYPES:
                raise ValueError("Invalid reference_type")
            query = query.filter(
                StudentDiaryEntry.reference_type == reference_type
            )
        query = query.filter(
            func.date(StudentDiaryEntry.created_at) == selected_date
        )
        if acknowledged is True:
            query = query.filter(
                StudentDiaryAcknowledgement.acknowledged_at.is_not(None)
            )
        elif acknowledged is False:
            query = query.filter(
                or_(
                    StudentDiaryAcknowledgement.id.is_(None),
                    StudentDiaryAcknowledgement.acknowledged_at.is_(None),
                )
            )
        total_items = query.count()
        rows = (
            query.order_by(
                StudentDiaryEntry.created_at.desc(),
                StudentDiaryEntry.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "date": selected_date,
            "results": [StudentDiaryService._serialize(*row) for row in rows],
            "pagination": StudentDiaryService._pagination(
                page, page_size, total_items
            ),
        }

    @staticmethod
    def get_entry(db, diary_entry_id, student_id, organization_id):
        query = StudentDiaryService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return None
        row = query.filter(StudentDiaryEntry.id == diary_entry_id).first()
        return StudentDiaryService._serialize(*row) if row else None

    @staticmethod
    def mark_viewed(db, diary_entry_id, student_id, organization_id):
        row = StudentDiaryService._get_mutable_entry(
            db, diary_entry_id, student_id, organization_id
        )
        if not row:
            return None
        entry, acknowledgement = row
        if not acknowledgement:
            acknowledgement = StudentDiaryAcknowledgement(
                diary_entry_id=entry.id,
                is_active=True,
            )
            db.add(acknowledgement)
        if acknowledgement.viewed_at is None:
            acknowledgement.viewed_at = StudentDiaryService._now()
        db.commit()
        db.refresh(acknowledgement)
        return StudentDiaryService._serialize(entry, acknowledgement)

    @staticmethod
    def acknowledge(
        db,
        diary_entry_id,
        student_id,
        organization_id,
        acknowledgement_note,
    ):
        row = StudentDiaryService._get_mutable_entry(
            db, diary_entry_id, student_id, organization_id
        )
        if not row:
            return None
        entry, acknowledgement = row
        now = StudentDiaryService._now()
        if not acknowledgement:
            acknowledgement = StudentDiaryAcknowledgement(
                diary_entry_id=entry.id,
                is_active=True,
            )
            db.add(acknowledgement)
        acknowledgement.viewed_at = acknowledgement.viewed_at or now
        acknowledgement.acknowledged_at = now
        acknowledgement.acknowledgement_note = acknowledgement_note
        db.commit()
        db.refresh(acknowledgement)
        return StudentDiaryService._serialize(entry, acknowledgement)

    @staticmethod
    def _get_mutable_entry(db, diary_entry_id, student_id, organization_id):
        query = StudentDiaryService._base_query(
            db, student_id, organization_id
        )
        return query.filter(StudentDiaryEntry.id == diary_entry_id).first() if query is not None else None

    @staticmethod
    def _serialize(entry, acknowledgement):
        return {
            "id": entry.id,
            "reference_type": entry.reference_type,
            "reference_id": entry.reference_id,
            "title": entry.title,
            "description": entry.description,
            "due_date": entry.due_date,
            "publish_at": entry.publish_at,
            "expires_at": entry.expires_at,
            "created_at": entry.created_at,
            "acknowledgement": {
                "assigned_at": acknowledgement.assigned_at,
                "viewed_at": acknowledgement.viewed_at,
                "acknowledged_at": acknowledgement.acknowledged_at,
                "acknowledgement_note": acknowledgement.acknowledgement_note,
            } if acknowledgement else None,
        }

    @staticmethod
    def _pagination(page, page_size, total_items):
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1 and total_pages > 0,
        }

    @staticmethod
    def _empty(page, page_size, selected_date):
        return {
            "date": selected_date,
            "results": [],
            "pagination": StudentDiaryService._pagination(page, page_size, 0),
        }
