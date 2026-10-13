"""Business logic for student exam APIs and summaries."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.academics.models import OrgSchoolClass, OrgSchoolSection
from app.modules.exams.repository import ExamRepository
from app.modules.students.repository import StudentRepository


IST = ZoneInfo("Asia/Kolkata")


class ExamService:
    @staticmethod
    def get_latest_result_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not ExamService._valid_mapping(mapping, organization_id):
            return None
        org_class = mapping.section.org_class
        return ExamRepository.get_latest_result(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
        )

    @staticmethod
    def get_upcoming_exam_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        if not ExamService._valid_mapping(mapping, organization_id):
            return None
        org_class = mapping.section.org_class
        row = ExamRepository.get_upcoming_exam(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            section_id=mapping.section_id,
            academic_year=org_class.academic_year if org_class else None,
            today=datetime.now(IST).date(),
        )
        if not row:
            return None
        schedule, paper, exam = row
        return {
            "exam_id": exam.id,
            "exam_title": exam.title,
            "exam_paper_id": paper.id,
            "subject_name": paper.subject_name,
            "exam_date": schedule.exam_date,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "room_number": schedule.room_number,
        }

    @staticmethod
    def _valid_mapping(mapping, organization_id: int) -> bool:
        if not mapping or not mapping.section:
            return False
        section: OrgSchoolSection = mapping.section
        org_class: OrgSchoolClass | None = section.org_class
        return bool(
            section.is_active
            and org_class
            and org_class.is_active
            and org_class.organization_id == organization_id
        )
