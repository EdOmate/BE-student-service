"""Business logic for student-domain operations."""

from datetime import datetime, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.students.repository import StudentRepository
from app.modules.students.schema import (
    CreateLeaveRequest,
    LeavePagination,
    ParentTodayStatus,
    StudentClassSection,
    StudentSummaryResponse,
    StudentTodayInfo,
    StudentTodayStatusResponse,
    StudentLeaveItem,
    StudentLeaveListResponse,
    TodayAttendanceStatus,
)
from core.storage import S3StorageService


IST = ZoneInfo("Asia/Kolkata")


class StudentService:
    ATTENDANCE_STATUS = {
        1: "Present",
        2: "Absent",
        3: "Half Day",
        4: "On Leave",
    }
    LEAVE_TYPES = {
        1: "Sick Leave",
        2: "Casual Leave",
        3: "Medical Leave",
        4: "Family Reason",
        5: "Other",
    }
    LEAVE_STATUSES = {
        1: "Pending",
        2: "Approved",
        3: "Rejected",
        4: "Cancelled",
    }
    LEAVE_DURATIONS = {1: "Full Day", 2: "Half Day"}

    @staticmethod
    def get_snapshot_attendance(db: Session, student_id: int) -> dict:
        now = datetime.now(IST)
        today = now.date()
        attendance = StudentRepository.get_attendance_for_date(
            db,
            student_id,
            today,
        )
        if attendance:
            total_hours = None
            if attendance.check_in_time and attendance.check_out_time:
                check_in = datetime.combine(today, attendance.check_in_time)
                check_out = datetime.combine(today, attendance.check_out_time)
                if check_out < check_in:
                    check_out += timedelta(days=1)
                minutes = int((check_out - check_in).total_seconds() // 60)
                total_hours = f"{minutes // 60}h {minutes % 60}m"
            return {
                "status": StudentService.ATTENDANCE_STATUS.get(
                    attendance.status,
                    "Unknown",
                ),
                "check_in": (
                    attendance.check_in_time.strftime("%-I:%M %p")
                    if attendance.check_in_time
                    else None
                ),
                "check_out": (
                    attendance.check_out_time.strftime("%-I:%M %p")
                    if attendance.check_out_time
                    else None
                ),
                "total_hours": total_hours,
            }

        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        section = mapping.section if mapping else None
        if section:
            timetable = StudentRepository.get_active_timetable(db, section.id)
            off_days = {
                value.strip().lower()
                for value in (timetable.off_days or "").split(",")
                if value.strip()
            } if timetable else set()
            if today.strftime("%A").lower() in off_days:
                return {"status": "Weekly Off"}

        approved_leave = StudentRepository.get_approved_leave_for_date(
            db,
            student_id,
            today,
        )
        return {"status": "On Leave" if approved_leave else "Not Marked"}

    @staticmethod
    def list_leave_requests(
        db: Session,
        student_id: int,
        organization_id: int,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> StudentLeaveListResponse:
        status = StudentService._normalize_leave_status(status_filter)
        student = StudentRepository.get_student_by_id(db, student_id)
        if not student or student.organization_id != organization_id:
            return StudentService._empty_leave_response(page, page_size)

        data = StudentRepository.list_leave_requests(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        results = [
            StudentService._serialize_leave(leave, student)
            for leave in data["leaves"]
        ]
        total_items = data["total_items"]
        total_pages = ceil(total_items / page_size) if total_items else 0
        return StudentLeaveListResponse(
            results=results,
            pagination=LeavePagination(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1 and total_pages > 0,
            ),
        )

    @staticmethod
    def create_leave_request(
        db: Session,
        student_id: int,
        organization_id: int,
        parent_id: int,
        payload: CreateLeaveRequest,
    ) -> tuple[str, StudentLeaveItem | None]:
        student = StudentRepository.get_student_by_id(db, student_id)
        if (
            not student
            or student.organization_id != organization_id
            or student.enrollment_status != 1
        ):
            return "student_not_found", None

        today = datetime.now(IST).date()
        if payload.start_date < today:
            return "past_date", None
        if StudentRepository.has_overlapping_leave_request(
            db=db,
            student_id=student_id,
            organization_id=organization_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        ):
            return "overlap", None

        attachments = StudentService._normalize_leave_attachments(
            payload.attachments
        )
        leave = StudentRepository.create_leave_request(
            db=db,
            organization_id=organization_id,
            student_id=student_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            leave_type=payload.leave_type,
            reason=payload.reason,
            attachments=attachments,
            duration=payload.duration,
            requested_by_id=parent_id,
        )
        return "created", StudentService._serialize_leave(leave, student)

    @staticmethod
    def _normalize_leave_status(status_filter: str | None) -> int | None:
        if status_filter is None or status_filter.strip().lower() == "all":
            return None
        status_map = {
            "1": 1,
            "pending": 1,
            "2": 2,
            "approved": 2,
            "3": 3,
            "rejected": 3,
            "4": 4,
            "cancelled": 4,
        }
        status = status_map.get(status_filter.strip().lower())
        if status is None:
            raise ValueError(
                "status must be all, pending, approved, rejected, or cancelled"
            )
        return status

    @staticmethod
    def _normalize_leave_attachments(attachments: list) -> list:
        normalized = []
        for attachment in attachments:
            if isinstance(attachment, str):
                item = {"url": attachment.strip(), "media_type": None}
            else:
                item = dict(attachment)
                key = item.get("url") or item.get("file_url") or item.get("path")
                item["url"] = str(key or "").strip()
            key = item["url"].lstrip("/")
            if not key.startswith("uploads/") or ".." in key.split("/"):
                raise ValueError(
                    "Each attachment must use a valid S3 key under uploads/"
                )
            item["url"] = key
            normalized.append(item)
        return normalized

    @staticmethod
    def _serialize_leave(leave, student) -> StudentLeaveItem:
        attachments = []
        for attachment in leave.attachments or []:
            item = dict(attachment) if isinstance(attachment, dict) else {
                "url": str(attachment),
                "media_type": None,
            }
            if item.get("url"):
                item["url"] = S3StorageService.file_url(item["url"])
            attachments.append(item)
        return StudentLeaveItem(
            leave_id=leave.id,
            student_id=student.id,
            student_name=student.full_name,
            admission_number=student.admission_number,
            start_date=leave.start_date,
            end_date=leave.end_date,
            leave_type=leave.leave_type,
            leave_type_display=StudentService.LEAVE_TYPES[leave.leave_type],
            reason=leave.reason,
            attachments=attachments,
            status=leave.status,
            status_display=StudentService.LEAVE_STATUSES[leave.status],
            duration=leave.duration,
            duration_display=StudentService.LEAVE_DURATIONS[leave.duration],
            requested_by_id=leave.requested_by_id,
            requested_at=leave.requested_at,
            reviewed_by_id=leave.reviewed_by_id,
            reviewed_at=leave.reviewed_at,
            review_remarks=leave.review_remarks,
        )

    @staticmethod
    def _empty_leave_response(page: int, page_size: int):
        return StudentLeaveListResponse(
            results=[],
            pagination=LeavePagination(
                page=page,
                page_size=page_size,
                total_items=0,
                total_pages=0,
                has_next=False,
                has_previous=False,
            ),
        )

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
