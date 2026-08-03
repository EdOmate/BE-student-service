from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schema import (
    AttendanceCard,
    FeeCard,
    HomeworkCard,
    ResultCard,
    StudentSnapshotResponse,
)


IST = ZoneInfo("Asia/Kolkata")


class DashboardService:
    ATTENDANCE_STATUS = {
        1: "Present",
        2: "Absent",
        3: "Half Day",
        4: "Leave",
    }

    @staticmethod
    def get_student_quick_actions_list():
        return {
            "pay_fee": "Pay Fee",
            "track_bus": "Track Bus",
            "book_ptm": "Book PTM",
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
            "notifications": "Notifications",
            "announcements": "Announcements",
            "events": "School Events",
            "library": "Library",
            "study_material": "Study Material",
            "fee_receipts": "Fee Receipts",
            "transport": "Transport",
            "canteen": "Canteen",
            "hostel": "Hostel",
            "gallery": "Gallery",
            "customize": "Customize",
        }

    @staticmethod
    def get_student_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> StudentSnapshotResponse:
        now = datetime.now(IST)
        section_id = DashboardRepository.get_active_section_id(db, student_id)
        attendance = DashboardRepository.get_today_attendance(
            db,
            student_id,
            now.date(),
        )
        homework_count, earliest = DashboardRepository.get_pending_homework(
            db,
            student_id,
            section_id,
        )
        latest_result = DashboardRepository.get_latest_result(
            db,
            student_id,
            organization_id,
        )
        fee_status = DashboardRepository.get_fee_status(db, student_id)

        return StudentSnapshotResponse(
            student_id=student_id,
            generated_at=now,
            attendance=DashboardService._attendance_card(attendance),
            homework=HomeworkCard(
                pending_count=homework_count,
                earliest_title=earliest.title if earliest else None,
                due_at=earliest.due_at if earliest else None,
                due_label=(
                    DashboardService._due_label(earliest.due_at, now)
                    if earliest and earliest.due_at
                    else None
                ),
            ),
            latest_result=(
                ResultCard(available=True, **latest_result)
                if latest_result
                else ResultCard(available=False)
            ),
            fee_status=(
                FeeCard(
                    available=True,
                    all_paid=fee_status["due_amount"] <= 0,
                    action=(
                        "fee_details"
                        if fee_status["due_amount"] <= 0
                        else "pay_now"
                    ),
                    **fee_status,
                )
                if fee_status is not None
                else FeeCard(available=False)
            ),
        )

    @staticmethod
    def _attendance_card(attendance) -> AttendanceCard:
        if not attendance:
            return AttendanceCard(status="Not Marked")

        total_hours = None
        if attendance.check_in_time and attendance.check_out_time:
            start = datetime.combine(attendance.date, attendance.check_in_time)
            end = datetime.combine(attendance.date, attendance.check_out_time)
            if end < start:
                end += timedelta(days=1)
            minutes = int((end - start).total_seconds() // 60)
            total_hours = f"{minutes // 60}h {minutes % 60}m"

        return AttendanceCard(
            status=DashboardService.ATTENDANCE_STATUS.get(
                attendance.status,
                "Unknown",
            ),
            check_in=(
                attendance.check_in_time.strftime("%-I:%M %p")
                if attendance.check_in_time
                else None
            ),
            check_out=(
                attendance.check_out_time.strftime("%-I:%M %p")
                if attendance.check_out_time
                else None
            ),
            total_hours=total_hours,
        )

    @staticmethod
    def _due_label(due_at: datetime, now: datetime) -> str:
        due_date = due_at.date()
        difference = (due_date - now.date()).days
        if difference == 0:
            return "Due Today"
        if difference == 1:
            return "Due Tomorrow"
        if difference < 0:
            return "Overdue"
        return f"Due {due_at.strftime('%d %b')}"
