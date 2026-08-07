"""Database access for student study-material operations."""

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.academics.models import OrgSubject
from app.modules.lms.models import StudyMaterial


class StudyMaterialRepository:
    @staticmethod
    def _available_materials_query(
        db: Session,
        section_id: int,
        now: datetime,
    ):
        return db.query(StudyMaterial).filter(
            StudyMaterial.section_id == section_id,
            StudyMaterial.status == 2,
            or_(
                StudyMaterial.publish_at.is_(None),
                StudyMaterial.publish_at <= now,
            ),
            or_(
                StudyMaterial.expires_at.is_(None),
                StudyMaterial.expires_at > now,
            ),
        )

    @staticmethod
    def list_student_materials(
        db: Session,
        section_id: int,
        organization_id: int,
        now: datetime,
        page: int,
        page_size: int,
        subject_id: int | None = None,
        material_type: int | None = None,
        search: str | None = None,
    ) -> dict:
        query = StudyMaterialRepository._available_materials_query(
            db,
            section_id,
            now,
        )
        if subject_id is not None:
            query = query.filter(StudyMaterial.subject_id == subject_id)
        if material_type is not None:
            query = query.filter(StudyMaterial.material_type == material_type)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    StudyMaterial.title.ilike(pattern),
                    StudyMaterial.description.ilike(pattern),
                )
            )

        total_items = query.count()
        materials = (
            query.order_by(
                StudyMaterial.publish_at.desc(),
                StudyMaterial.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        subject_ids = {material.subject_id for material in materials}
        subjects = (
            {
                subject.id: subject.name
                for subject in db.query(OrgSubject)
                .filter(
                    OrgSubject.id.in_(subject_ids),
                    OrgSubject.organization_id == organization_id,
                )
                .all()
            }
            if subject_ids
            else {}
        )
        return {
            "materials": materials,
            "subjects": subjects,
            "total_items": total_items,
        }

    @staticmethod
    def get_student_material_detail(
        db: Session,
        material_id: int,
        section_id: int,
        organization_id: int,
        now: datetime,
    ) -> dict | None:
        material = (
            StudyMaterialRepository._available_materials_query(
                db,
                section_id,
                now,
            )
            .filter(StudyMaterial.id == material_id)
            .first()
        )
        if not material:
            return None

        subject = (
            db.query(OrgSubject)
            .filter(
                OrgSubject.id == material.subject_id,
                OrgSubject.organization_id == organization_id,
            )
            .first()
        )
        return {
            "material": material,
            "subject_name": subject.name if subject else None,
        }
