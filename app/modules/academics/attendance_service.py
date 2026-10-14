"""Student-facing attendance queries."""

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.modules.students.models import (
    OrgClassStudentAttendance,
    OrgStudentLeaveRequest,
)
from app.modules.students.repository import StudentRepository


class StudentAttendanceService:
    REQUIRED_MINIMUM = 75
    STATUS_NAMES = {
        OrgClassStudentAttendance.STATUS_PRESENT: "present",
        OrgClassStudentAttendance.STATUS_ABSENT: "absent",
        OrgClassStudentAttendance.STATUS_HALF_DAY: "half_day",
        OrgClassStudentAttendance.STATUS_LEAVE: "on_leave",
        OrgClassStudentAttendance.STATUS_WEEKLY_OFF: "week_off",
    }

    @staticmethod
    def get_month(
        db: Session,
        student_id: int,
        year: int,
        month: int,
    ) -> dict:
        first_date = date(year, month, 1)
        last_date = date(year, month, monthrange(year, month)[1])
        statuses = StudentAttendanceService._get_statuses(
            db, student_id, first_date, last_date
        )

        days = [
            {
                "date": attendance_date.isoformat(),
                "day": attendance_date.day,
                "status": status,
            }
            for attendance_date, status in sorted(statuses.items())
        ]
        return {
            "year": year,
            "month": month,
            "days_in_month": last_date.day,
            "first_day_of_week": (
                first_date.weekday() + 1 if first_date.weekday() < 6 else 0
            ),
            "days": days,
            "summary": StudentAttendanceService._summary(statuses),
        }

    @staticmethod
    def get_statistics(
        db: Session,
        student_id: int,
        year: int,
        month: int,
    ) -> dict:
        selected_start = date(year, month, 1)
        selected_end = date(year, month, monthrange(year, month)[1])
        previous_end = selected_start - timedelta(days=1)
        previous_start = date(previous_end.year, previous_end.month, 1)
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        selected = StudentAttendanceService._summary(
            StudentAttendanceService._get_statuses(
                db, student_id, selected_start, selected_end
            )
        )
        previous = StudentAttendanceService._summary(
            StudentAttendanceService._get_statuses(
                db, student_id, previous_start, previous_end
            )
        )
        yearly = StudentAttendanceService._summary(
            StudentAttendanceService._get_statuses(
                db, student_id, year_start, year_end
            )
        )
        return {
            "selected_month": {
                "year": year,
                "month": month,
                **selected,
            },
            "previous_month": {
                "year": previous_end.year,
                "month": previous_end.month,
                **previous,
            },
            "year": {"year": year, **yearly},
            "required_minimum": StudentAttendanceService.REQUIRED_MINIMUM,
        }

    @staticmethod
    def _get_statuses(
        db: Session,
        student_id: int,
        first_date: date,
        last_date: date,
    ) -> dict[date, str]:
        rows = (
            db.query(OrgClassStudentAttendance)
            .filter(
                OrgClassStudentAttendance.student_id == student_id,
                OrgClassStudentAttendance.date >= first_date,
                OrgClassStudentAttendance.date <= last_date,
            )
            .order_by(OrgClassStudentAttendance.date)
            .all()
        )

        statuses = {
            row.date: StudentAttendanceService.STATUS_NAMES.get(row.status)
            for row in rows
            if StudentAttendanceService.STATUS_NAMES.get(row.status)
        }
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        timetable = (
            StudentRepository.get_active_timetable(db, mapping.section_id)
            if mapping
            else None
        )
        off_days = {
            value.strip().lower()
            for value in (timetable.off_days or "").split(",")
            if value.strip()
        } if timetable else set()
        current = first_date
        while current <= last_date:
            if current.strftime("%A").lower() in off_days:
                statuses.setdefault(current, "week_off")
            current += timedelta(days=1)

        approved_leaves = (
            db.query(OrgStudentLeaveRequest)
            .filter(
                OrgStudentLeaveRequest.student_id == student_id,
                OrgStudentLeaveRequest.status == 2,
                OrgStudentLeaveRequest.start_date <= last_date,
                OrgStudentLeaveRequest.end_date >= first_date,
            )
            .all()
        )
        for leave in approved_leaves:
            current = max(leave.start_date, first_date)
            leave_end = min(leave.end_date, last_date)
            while current <= leave_end:
                statuses.setdefault(current, "on_leave")
                current += timedelta(days=1)

        return statuses

    @staticmethod
    def _summary(statuses: dict[date, str]) -> dict:
        counts = {
            status: sum(1 for value in statuses.values() if value == status)
            for status in StudentAttendanceService.STATUS_NAMES.values()
        }
        working_days = sum(
            counts[key] for key in ("present", "absent", "half_day", "on_leave")
        )
        attended_days = counts["present"] + (counts["half_day"] * 0.5)
        percentage = round(attended_days * 100 / working_days, 2) if working_days else 0

        return {
            **counts,
            "working_days": working_days,
            "attended_days": attended_days,
            "attendance_percentage": percentage,
        }
