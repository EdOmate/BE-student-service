"""Business logic for student-domain operations."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.students.repository import StudentRepository
from app.modules.students.schema import (
    ParentTodayStatus,
    StudentClassSection,
    StudentSummaryResponse,
    StudentTodayInfo,
    StudentTodayStatusResponse,
    TodayAttendanceStatus,
)


IST = ZoneInfo("Asia/Kolkata")


class StudentService:
    ATTENDANCE_STATUS = {
        1: "Present",
        2: "Absent",
        3: "Half Day",
        4: "On Leave",
    }

    @staticmethod
    def get_student_summary(
        db: Session,
        student_id: int,
    ) -> StudentSummaryResponse | None:
        student = StudentRepository.get_student_by_id(db, student_id)
        if not student:
            return None

        return StudentSummaryResponse(
            id=student.id,
            organization_id=student.organization_id,
            admission_number=student.admission_number,
            first_name=student.first_name,
            middle_name=student.middle_name,
            last_name=student.last_name,
            full_name=student.full_name,
            date_of_birth=student.date_of_birth,
            email=student.email,
            mobile=student.mobile,
            profile_picture=student.profile_picture,
            enrollment_status=student.enrollment_status,
        )

    @staticmethod
    def get_today_status(
        db: Session,
        role: str,
        student_id: int,
        parent_id: int | None = None,
    ) -> StudentTodayStatusResponse | None:
        student = StudentRepository.get_student_by_id(db, student_id)
        if not student:
            return None

        today = datetime.now(IST).date()
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        section = mapping.section if mapping else None
        org_class = section.org_class if section else None
        master_class = org_class.master_class if org_class else None
        attendance = StudentRepository.get_attendance_for_date(
            db,
            student_id,
            today,
        )

        day_of_week = today.strftime("%A").lower()
        is_weekly_off = False
        if section:
            timetable = StudentRepository.get_active_timetable(db, section.id)
            off_days = {
                value.strip().lower()
                for value in (timetable.off_days or "").split(",")
                if value.strip()
            } if timetable else set()
            is_weekly_off = day_of_week in off_days

        approved_leave = None
        if not attendance and not is_weekly_off:
            approved_leave = StudentRepository.get_approved_leave_for_date(
                db,
                student_id,
                today,
            )

        if attendance:
            status_code = attendance.status
            status_text = StudentService.ATTENDANCE_STATUS.get(
                attendance.status,
                "Unknown",
            )
            is_working_day = True
        elif is_weekly_off:
            status_code = None
            status_text = "Weekly Off"
            is_working_day = False
        elif approved_leave:
            status_code = 4
            status_text = "On Leave"
            is_working_day = True
        else:
            status_code = None
            status_text = "Not Marked"
            is_working_day = True

        parent_response = None
        if role == "parent" and parent_id:
            parent = StudentRepository.get_parent_by_id(db, parent_id)
            if parent:
                name, relation = StudentService._parent_name(parent)
                parent_response = ParentTodayStatus(
                    id=parent.id,
                    name=name,
                    relation=relation,
                    username=parent.username,
                )

        return StudentTodayStatusResponse(
            role=role,
            parent=parent_response,
            student=StudentTodayInfo(
                id=student.id,
                admission_number=student.admission_number,
                full_name=student.full_name,
                profile_picture=student.profile_picture,
                class_section=StudentClassSection(
                    class_id=org_class.id if org_class else None,
                    class_name=master_class.name if master_class else None,
                    section_id=section.id if section else None,
                    section_name=section.name if section else None,
                    roll_number=mapping.roll_number if mapping else None,
                    academic_year=(
                        org_class.academic_year if org_class else None
                    ),
                ),
            ),
            attendance=TodayAttendanceStatus(
                date=today,
                day_of_week=day_of_week,
                status_code=status_code,
                status=status_text,
                is_working_day=is_working_day,
                check_in=(
                    attendance.check_in_time.strftime("%-I:%M %p")
                    if attendance and attendance.check_in_time
                    else None
                ),
                check_out=(
                    attendance.check_out_time.strftime("%-I:%M %p")
                    if attendance and attendance.check_out_time
                    else None
                ),
                marked_at=attendance.created_at if attendance else None,
            ),
        )

    @staticmethod
    def _parent_name(parent) -> tuple[str | None, str | None]:
        if parent.father_name:
            return parent.father_name, "Father"
        if parent.mother_name:
            return parent.mother_name, "Mother"
        if parent.guardian_name:
            return parent.guardian_name, parent.guardian_relation or "Guardian"
        return parent.username, None
