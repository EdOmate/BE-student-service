"""Request and response schemas for the student module."""

from datetime import date, datetime

from pydantic import BaseModel


class StudentSummaryResponse(BaseModel):
    id: int
    organization_id: int
    admission_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    full_name: str
    date_of_birth: date | None = None
    email: str | None = None
    mobile: str | None = None
    profile_picture: str | None = None
    enrollment_status: int


class ParentTodayStatus(BaseModel):
    id: int
    name: str | None = None
    relation: str | None = None
    username: str | None = None


class StudentClassSection(BaseModel):
    class_id: int | None = None
    class_name: str | None = None
    section_id: int | None = None
    section_name: str | None = None
    roll_number: int | None = None
    academic_year: str | None = None


class StudentTodayInfo(BaseModel):
    id: int
    admission_number: str
    full_name: str
    profile_picture: str | None = None
    class_section: StudentClassSection


class TodayAttendanceStatus(BaseModel):
    date: date
    day_of_week: str
    status_code: int | None = None
    status: str
    is_working_day: bool
    check_in: str | None = None
    check_out: str | None = None
    marked_at: datetime | None = None


class StudentTodayStatusResponse(BaseModel):
    role: str
    parent: ParentTodayStatus | None = None
    student: StudentTodayInfo
    attendance: TodayAttendanceStatus
