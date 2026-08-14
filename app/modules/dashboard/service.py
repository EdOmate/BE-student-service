from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.exams.service import ExamService
from app.modules.lms.assignment_service import AssignmentService
from app.modules.students.service import StudentService
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
    def get_student_quick_actions_list():
        return {
            "pay_fee": "Pay Fee",
            "track_bus": "Track Bus",
            "apply_leave": "Apply Leave",
            "message_teacher": "Message Teacher",
            "attendance": "Attendance",
            "homework": "Homework",
            "assignments": "Assignments",
            "exam_schedule": "Exam Schedule",
            "results": "Results",
            "report_card": "Report Card",
            "class_timetable": "Class Timetable",
            "school_calendar": "School Calendar",
            "library": "Library",
            "study_material": "Study Material",
            "fee_receipts": "Fee Receipts",
            "transport": "Transport",
            "canteen": "Canteen",
            "hostel": "Hostel",
            "gallery": "Gallery"
        }

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
