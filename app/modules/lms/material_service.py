"""Business logic for student study-material APIs."""

from datetime import datetime
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.lms.material_repository import StudyMaterialRepository
from app.modules.lms.schema import (
    CustomPagination,
    StudentMaterialItem,
    StudentMaterialListResponse,
)
from app.modules.students.repository import StudentRepository
from core.storage import S3StorageService


IST = ZoneInfo("Asia/Kolkata")


class StudentMaterialService:
    MATERIAL_TYPE_LABELS = {
        1: "Notes",
        2: "Presentation",
        3: "Worksheet",
        4: "Video",
        5: "Audio",
        6: "External Link",
        7: "Reference Material",
    }

    @staticmethod
    def list_student_materials(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int = 1,
        page_size: int = 20,
        subject_id: int | None = None,
        material_type: int | None = None,
        search: str | None = None,
    ) -> StudentMaterialListResponse:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section:
            return StudentMaterialService._empty_response(page, page_size)

        data = StudyMaterialRepository.list_student_materials(
            db=db,
            section_id=mapping.section_id,
            organization_id=organization_id,
            now=datetime.now(IST).replace(tzinfo=None),
            page=page,
            page_size=page_size,
            subject_id=subject_id,
            material_type=material_type,
            search=search,
        )
        results = [
            StudentMaterialService._serialize_material(
                material=material,
                subject=data["subjects"].get(material.subject_mapping_id, {}),
                mapping=mapping,
            )
            for material in data["materials"]
        ]
        total_items = data["total_items"]
        total_pages = ceil(total_items / page_size) if total_items else 0
        return StudentMaterialListResponse(
            results=results,
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
    def get_student_material_detail(
        db: Session,
        material_id: int,
        student_id: int,
        organization_id: int,
    ) -> StudentMaterialItem | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not mapping or not mapping.section:
            return None

        data = StudyMaterialRepository.get_student_material_detail(
            db=db,
            material_id=material_id,
            section_id=mapping.section_id,
            organization_id=organization_id,
            now=datetime.now(IST).replace(tzinfo=None),
        )
        if not data:
            return None
        return StudentMaterialService._serialize_material(
            material=data["material"],
            subject={
                "subject_id": data["subject_id"],
                "subject_name": data["subject_name"],
            },
            mapping=mapping,
        )

    @staticmethod
    def _serialize_material(material, subject: dict, mapping):
        org_class = mapping.section.org_class
        master_class = org_class.master_class if org_class else None
        return StudentMaterialItem(
            id=material.id,
            section_id=material.section_id,
            section_name=mapping.section.name,
            class_id=org_class.id if org_class else None,
            class_name=master_class.name if master_class else None,
            subject_mapping_id=material.subject_mapping_id,
            subject_id=subject.get("subject_id"),
            subject_name=subject.get("subject_name"),
            material_type=material.material_type,
            material_type_label=StudentMaterialService.MATERIAL_TYPE_LABELS.get(
                material.material_type,
                "Unknown",
            ),
            title=material.title,
            description=material.description,
            attachments=StudentMaterialService._serialize_attachments(
                material.attachments
            ),
            tags=material.tags or [],
            publish_at=material.publish_at,
            expires_at=material.expires_at,
            created_at=material.created_at,
            updated_at=material.updated_at,
        )

    @staticmethod
    def _serialize_attachments(attachments) -> list:
        if not attachments:
            return []
        values = attachments if isinstance(attachments, list) else [attachments]
        serialized = []
        for attachment in values:
            if isinstance(attachment, dict):
                item = dict(attachment)
                for field in ("url", "file_url", "path"):
                    if item.get(field):
                        item[field] = S3StorageService.file_url(item[field])
                serialized.append(item)
            else:
                serialized.append(
                    {
                        "url": S3StorageService.file_url(str(attachment)),
                        "media_type": None,
                    }
                )
        return serialized

    @staticmethod
    def _empty_response(page: int, page_size: int):
        return StudentMaterialListResponse(
            results=[],
            pagination=CustomPagination(
                page=page,
                page_size=page_size,
                total_items=0,
                total_pages=0,
                has_next=False,
                has_previous=False,
            ),
        )
