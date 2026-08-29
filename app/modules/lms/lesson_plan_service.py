"""Read-only lesson-plan APIs for students and parents."""

from datetime import date
from math import ceil

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.academics.models import (
    CurriculumSyllabus,
    OrgClassSubjectMapping,
    OrgSubject,
)
from app.modules.lms.models import LessonPlan, LessonPlanItem
from app.modules.students.repository import StudentRepository


class StudentLessonPlanService:
    VISIBLE_STATUSES = (
        LessonPlan.STATUS_APPROVED,
        LessonPlan.STATUS_COMPLETED,
    )

    @staticmethod
    def _base_query(db, student_id, organization_id):
        student_mapping = StudentRepository.get_active_section_mapping(
            db, student_id
        )
        if (
            not student_mapping
            or not student_mapping.section
            or not student_mapping.section.org_class
        ):
            return None
        org_class = student_mapping.section.org_class
        return (
            db.query(
                LessonPlan,
                OrgClassSubjectMapping,
                OrgSubject,
                CurriculumSyllabus,
            )
            .join(
                OrgClassSubjectMapping,
                OrgClassSubjectMapping.id == LessonPlan.subject_mapping_id,
            )
            .join(OrgSubject, OrgSubject.id == OrgClassSubjectMapping.subject_id)
            .outerjoin(
                CurriculumSyllabus,
                CurriculumSyllabus.id == LessonPlan.curriculum_id,
            )
            .filter(
                OrgClassSubjectMapping.class_id == org_class.id,
                OrgClassSubjectMapping.status.is_(True),
                OrgSubject.organization_id == organization_id,
                LessonPlan.status.in_(StudentLessonPlanService.VISIBLE_STATUSES),
                LessonPlan.is_active.is_(True),
            )
        )

    @staticmethod
    def list_plans(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
        subject_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
    ) -> dict:
        query = StudentLessonPlanService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return StudentLessonPlanService._empty(page, page_size)
        if from_date and to_date and from_date > to_date:
            raise ValueError("from_date cannot be later than to_date")
        if subject_id:
            query = query.filter(OrgClassSubjectMapping.subject_id == subject_id)
        if from_date:
            query = query.filter(
                or_(
                    LessonPlan.planned_end_date.is_(None),
                    LessonPlan.planned_end_date >= from_date,
                )
            )
        if to_date:
            query = query.filter(
                or_(
                    LessonPlan.planned_start_date.is_(None),
                    LessonPlan.planned_start_date <= to_date,
                )
            )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    LessonPlan.title.ilike(pattern),
                    LessonPlan.description.ilike(pattern),
                )
            )
        total_items = query.count()
        rows = (
            query.order_by(LessonPlan.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "results": [
                StudentLessonPlanService._serialize(*row, items=None)
                for row in rows
            ],
            "pagination": StudentLessonPlanService._pagination(
                page, page_size, total_items
            ),
        }

    @staticmethod
    def get_plan_detail(
        db,
        lesson_plan_id,
        student_id,
        organization_id,
    ):
        query = StudentLessonPlanService._base_query(
            db, student_id, organization_id
        )
        if query is None:
            return None
        row = query.filter(LessonPlan.id == lesson_plan_id).first()
        if not row:
            return None
        items = (
            db.query(LessonPlanItem)
            .filter(LessonPlanItem.lesson_plan_id == lesson_plan_id)
            .order_by(LessonPlanItem.sequence_no, LessonPlanItem.id)
            .all()
        )
        return StudentLessonPlanService._serialize(*row, items=items)

    @staticmethod
    def _serialize(plan, subject_mapping, subject, curriculum, items):
        data = {
            "id": plan.id,
            "subject_mapping_id": plan.subject_mapping_id,
            "subject_id": subject_mapping.subject_id,
            "subject_name": subject.name,
            "curriculum_id": plan.curriculum_id,
            "curriculum_title": curriculum.title if curriculum else None,
            "title": plan.title,
            "description": plan.description,
            "term": plan.term,
            "planned_start_date": plan.planned_start_date,
            "planned_end_date": plan.planned_end_date,
            "status": plan.status,
            "completed_at": plan.completed_at,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
        }
        if items is not None:
            data["items"] = [
                {
                    "id": item.id,
                    "curriculum_unit_id": item.curriculum_unit_id,
                    "curriculum_chapter_id": item.curriculum_chapter_id,
                    "curriculum_topic_id": item.curriculum_topic_id,
                    "sequence_no": item.sequence_no,
                    "topic": item.topic,
                    "subtopic": item.subtopic,
                    "learning_outcome": item.learning_outcome,
                    "planned_date": item.planned_date,
                    "actual_date": item.actual_date,
                    "status": item.status,
                    "coverage_percent": float(item.coverage_percent),
                    "teacher_notes": item.teacher_notes,
                    "remarks": item.remarks,
                }
                for item in items
            ]
        return data

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
            "pagination": StudentLessonPlanService._pagination(
                page, page_size, 0
            ),
        }
