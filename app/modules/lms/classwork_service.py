"""Student-facing classwork queries."""

from datetime import date
from math import ceil

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.academics.models import (
    CurriculumChapter,
    CurriculumTopic,
    CurriculumUnit,
    OrgClassSubjectMapping,
    OrgSubject,
)
from app.modules.lms.models import LMSClassWork, LMSClassWorkItem
from app.modules.students.repository import StudentRepository
from core.storage import S3StorageService


class StudentClassWorkService:
    @staticmethod
    def _context(db: Session, student_id: int):
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section or not mapping.section.org_class:
            return None
        return mapping, mapping.section.org_class

    @staticmethod
    def _base_query(
        db: Session,
        student_id: int,
        organization_id: int,
    ):
        context = StudentClassWorkService._context(db, student_id)
        if not context:
            return None
        mapping, org_class = context
        query = (
            db.query(LMSClassWork, OrgClassSubjectMapping, OrgSubject)
            .join(
                OrgClassSubjectMapping,
                OrgClassSubjectMapping.id == LMSClassWork.subject_mapping_id,
            )
            .join(OrgSubject, OrgSubject.id == OrgClassSubjectMapping.subject_id)
            .filter(
                LMSClassWork.organization_id == organization_id,
                LMSClassWork.academic_year == org_class.academic_year,
                LMSClassWork.section_id == mapping.section_id,
                LMSClassWork.status == LMSClassWork.STATUS_PUBLISHED,
                LMSClassWork.is_active.is_(True),
                OrgSubject.organization_id == organization_id,
            )
        )
        return query

    @staticmethod
    def list_classworks(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
        classwork_date: date | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        subject_id: int | None = None,
        coverage_level: str | None = None,
        search: str | None = None,
    ) -> dict:
        query = StudentClassWorkService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return StudentClassWorkService._empty(page, page_size)
        if from_date and to_date and from_date > to_date:
            raise ValueError("from_date cannot be later than to_date")
        if classwork_date:
            query = query.filter(LMSClassWork.classwork_date == classwork_date)
        if from_date:
            query = query.filter(LMSClassWork.classwork_date >= from_date)
        if to_date:
            query = query.filter(LMSClassWork.classwork_date <= to_date)
        if subject_id:
            query = query.filter(OrgClassSubjectMapping.subject_id == subject_id)
        if coverage_level:
            if coverage_level not in {
                LMSClassWorkItem.LEVEL_UNIT,
                LMSClassWorkItem.LEVEL_CHAPTER,
                LMSClassWorkItem.LEVEL_TOPIC,
                LMSClassWorkItem.LEVEL_CUSTOM,
            }:
                raise ValueError("Invalid coverage_level")
            query = query.filter(
                db.query(LMSClassWorkItem.id)
                .filter(
                    LMSClassWorkItem.classwork_id == LMSClassWork.id,
                    LMSClassWorkItem.coverage_level == coverage_level,
                )
                .exists()
            )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    LMSClassWork.title.ilike(pattern),
                    LMSClassWork.description.ilike(pattern),
                )
            )
        total_items = query.count()
        rows = (
            query.order_by(
                LMSClassWork.classwork_date.desc(),
                LMSClassWork.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        results = [
            StudentClassWorkService._serialize(
                db, classwork, subject_mapping, subject, include_items=False
            )
            for classwork, subject_mapping, subject in rows
        ]
        return {
            "results": results,
            "pagination": StudentClassWorkService._pagination(
                page, page_size, total_items
            ),
        }

    @staticmethod
    def get_classwork_detail(
        db: Session,
        classwork_id: int,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        query = StudentClassWorkService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return None
        row = query.filter(LMSClassWork.id == classwork_id).first()
        if not row:
            return None
        return StudentClassWorkService._serialize(db, *row, include_items=True)

    @staticmethod
    def _serialize(db, classwork, subject_mapping, subject, include_items):
        data = {
            "id": classwork.id,
            "classwork_date": classwork.classwork_date.isoformat(),
            "title": classwork.title,
            "description": classwork.description,
            "section_id": classwork.section_id,
            "subject_mapping_id": classwork.subject_mapping_id,
            "subject_id": subject_mapping.subject_id,
            "subject_name": subject.name,
            "curriculum_id": classwork.curriculum_id,
            "teacher_id": classwork.teacher_id,
            "attachments": StudentClassWorkService._attachments(
                classwork.attachments
            ),
            "published_at": classwork.published_at,
            "created_at": classwork.created_at,
        }
        if include_items:
            items = (
                db.query(LMSClassWorkItem)
                .filter(LMSClassWorkItem.classwork_id == classwork.id)
                .order_by(LMSClassWorkItem.sequence_no, LMSClassWorkItem.id)
                .all()
            )
            unit_ids = {item.curriculum_unit_id for item in items if item.curriculum_unit_id}
            chapter_ids = {item.curriculum_chapter_id for item in items if item.curriculum_chapter_id}
            topic_ids = {item.curriculum_topic_id for item in items if item.curriculum_topic_id}
            titles = {}
            for model, ids in (
                (CurriculumUnit, unit_ids),
                (CurriculumChapter, chapter_ids),
                (CurriculumTopic, topic_ids),
            ):
                if ids:
                    titles.update({row.id: row.title for row in db.query(model).filter(model.id.in_(ids)).all()})
            data["items"] = [
                {
                    "id": item.id,
                    "coverage_level": item.coverage_level,
                    "curriculum_unit_id": item.curriculum_unit_id,
                    "curriculum_chapter_id": item.curriculum_chapter_id,
                    "curriculum_topic_id": item.curriculum_topic_id,
                    "coverage_title": item.custom_title
                    or titles.get(item.curriculum_topic_id)
                    or titles.get(item.curriculum_chapter_id)
                    or titles.get(item.curriculum_unit_id),
                    "custom_title": item.custom_title,
                    "description": item.description,
                    "sequence_no": item.sequence_no,
                    "coverage_percent": float(item.coverage_percent),
                }
                for item in items
            ]
        return data

    @staticmethod
    def _attachments(values):
        return [
            S3StorageService.file_url(str(value)) if not isinstance(value, dict) else value
            for value in (values or [])
        ]

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
    def _empty(page, page_size):
        return {
            "results": [],
            "pagination": StudentClassWorkService._pagination(page, page_size, 0),
        }
