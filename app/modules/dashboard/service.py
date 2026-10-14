from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.exams.service import ExamService
from app.modules.hostel.models import OrgHostelStudentAllocation
from app.modules.library.models import OrgLibraryMember
from app.modules.lms.assignment_service import AssignmentService
from app.modules.students.service import StudentService
from app.modules.transport.models import TransportStudentAssignment
from app.modules.dashboard.schema import (
    AttendanceCard,
    HomeworkCard,
    ResultCard,
    StudentSnapshotResponse,
    UpcomingExamCard,
)


IST = ZoneInfo("Asia/Kolkata")


class DashboardService:
    @staticmethod
    def get_student_quick_actions_list(
        db: Session,
        student_id: int,
        organization_id: int,
    ):
        actions = {
            "diary": "Daily Diary",
            "pay_fee": "Pay Fee",
            "track_bus": "Track Bus",
            "apply_leave": "Apply Leave",
            "message_teacher": "Message Teacher",
            "attendance": "Attendance",
            "homework": "Homework",
            "assignments": "Assignments",
            "exams": "Exams",
            "report_cards": "Report Cards",
            "class_timetable": "Class Timetable",
            "school_calendar": "Event & Calender",
            "library": "Library",
            "study_material": "Study Material",
            "fee_receipts": "Fee Receipts",
            "transport": "Transport",
            "canteen": "Canteen",
            "hostel": "Hostel",
            "gallery": "Gallery"
        }

        today = datetime.now(IST).date()
        has_transport = (
            db.query(TransportStudentAssignment.id)
            .filter(
                TransportStudentAssignment.student_id == student_id,
                TransportStudentAssignment.organization_id == organization_id,
                TransportStudentAssignment.status.is_(True),
                or_(
                    TransportStudentAssignment.effective_from.is_(None),
                    TransportStudentAssignment.effective_from <= today,
                ),
                or_(
                    TransportStudentAssignment.effective_to.is_(None),
                    TransportStudentAssignment.effective_to >= today,
                ),
            )
            .first()
            is not None
        )
        has_library_membership = (
            db.query(OrgLibraryMember.id)
            .filter(
                OrgLibraryMember.student_id == student_id,
                OrgLibraryMember.organization_id == organization_id,
                OrgLibraryMember.member_type == OrgLibraryMember.MEMBER_TYPE_STUDENT,
                OrgLibraryMember.status == OrgLibraryMember.STATUS_ACTIVE,
                or_(
                    OrgLibraryMember.valid_from.is_(None),
                    OrgLibraryMember.valid_from <= today,
                ),
                or_(
                    OrgLibraryMember.valid_until.is_(None),
                    OrgLibraryMember.valid_until >= today,
                ),
            )
            .first()
            is not None
        )
        has_hostel_allocation = (
            db.query(OrgHostelStudentAllocation.id)
            .filter(
                OrgHostelStudentAllocation.student_id == student_id,
                OrgHostelStudentAllocation.organization_id == organization_id,
                OrgHostelStudentAllocation.status
                == OrgHostelStudentAllocation.STATUS_ACTIVE,
                OrgHostelStudentAllocation.is_current.is_(True),
                OrgHostelStudentAllocation.allocation_date <= today,
            )
            .first()
            is not None
        )

        if not has_transport:
            actions.pop("track_bus")
            actions.pop("transport")
        if not has_library_membership:
            actions.pop("library")
        if not has_hostel_allocation:
            actions.pop("hostel")

        return actions

    @staticmethod
    def get_student_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> StudentSnapshotResponse:
        now = datetime.now(IST)
        attendance = StudentService.get_snapshot_attendance(db, student_id)
        homework = AssignmentService.get_pending_assignment_snapshot(
            db,
            student_id,
            organization_id,
        )
        latest_result = ExamService.get_latest_result_snapshot(
            db,
            student_id,
            organization_id,
        )
        upcoming_exam = ExamService.get_upcoming_exam_snapshot(
            db,
            student_id,
            organization_id,
        )

        return StudentSnapshotResponse(
            student_id=student_id,
            generated_at=now,
            attendance=AttendanceCard(**attendance),
            homework=HomeworkCard(**homework),
            latest_result=ResultCard(**latest_result) if latest_result else None,
            upcoming_exam=(
                UpcomingExamCard(
                    **{
                        **upcoming_exam,
                        "start_time": (
                            upcoming_exam["start_time"].strftime("%-I:%M %p")
                            if upcoming_exam["start_time"]
                            else None
                        ),
                        "end_time": (
                            upcoming_exam["end_time"].strftime("%-I:%M %p")
                            if upcoming_exam["end_time"]
                            else None
                        ),
                    }
                )
                if upcoming_exam
                else None
            ),
        )
