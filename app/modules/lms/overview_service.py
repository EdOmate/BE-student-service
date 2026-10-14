"""Aggregated LMS overview for students and parents."""

from sqlalchemy.orm import Session

from app.modules.lms.assignment_service import AssignmentService
from app.modules.lms.classwork_service import StudentClassWorkService
from app.modules.lms.lesson_plan_service import StudentLessonPlanService
from app.modules.lms.material_service import StudentMaterialService


class StudentLMSOverviewService:
    """Build the LMS landing-page payload from the existing scoped lists."""

    PREVIEW_SIZE = 2

    @staticmethod
    def get_overview(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict:
        classworks = StudentClassWorkService.list_classworks(
            db, student_id, organization_id, 1,
            StudentLMSOverviewService.PREVIEW_SIZE,
        )
        assignments = AssignmentService.list_student_assignments(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            status_filter="all",
            page=1,
            page_size=StudentLMSOverviewService.PREVIEW_SIZE,
            latest_first=True,
        ).model_dump(mode="json")
        materials = StudentMaterialService.list_student_materials(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            page=1,
            page_size=StudentLMSOverviewService.PREVIEW_SIZE,
        ).model_dump(mode="json")
        lesson_plans = StudentLessonPlanService.list_plans(
            db, student_id, organization_id, 1,
            StudentLMSOverviewService.PREVIEW_SIZE,
        )

        return {
            "classworks": classworks,
            "assignments": assignments,
            "study_materials": materials,
            "lesson_plans": lesson_plans,
        }
