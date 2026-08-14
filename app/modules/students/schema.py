"""Request and response schemas for the student module."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


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


class CreateLeaveRequest(BaseModel):
    start_date: date
    end_date: date
    leave_type: int = Field(ge=1, le=5)
    reason: str = Field(min_length=1, max_length=5000)
    attachments: list[str | dict] = Field(default_factory=list, max_length=10)
    duration: int = Field(default=1, ge=1, le=2)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, reason: str) -> str:
        reason = reason.strip()
        if not reason:
            raise ValueError("reason is required")
        return reason

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("end_date cannot be earlier than start_date")
        if self.duration == 2 and self.start_date != self.end_date:
            raise ValueError(
                "Half-day leave can only be requested for a single day"
            )
        return self


class StudentLeaveItem(BaseModel):
    leave_id: int
    student_id: int
    student_name: str
    admission_number: str
    start_date: date
    end_date: date
    leave_type: int
    leave_type_display: str
    reason: str
    attachments: list
    status: int
    status_display: str
    duration: int
    duration_display: str
    requested_by_id: int | None = None
    requested_at: datetime | None = None
    reviewed_by_id: int | None = None
    reviewed_at: datetime | None = None
    review_remarks: str | None = None


class LeavePagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class StudentLeaveListResponse(BaseModel):
    results: list[StudentLeaveItem]
    pagination: LeavePagination


class StudentHouseResponse(BaseModel):
    assignment_id: int
    house_id: int
    name: str
    code: str
    color_code: str | None = None
    description: str | None = None
    academic_year: str
    assigned_on: date
    contribution_points: int
    house_points: int
    rank: int
    total_houses: int


class StudentGroupItem(BaseModel):
    assignment_id: int
    group_id: int
    name: str
    code: str
    group_type: int
    group_type_display: str
    description: str | None = None
    academic_year: str
    role: int
    role_display: str
    joined_on: date
    member_count: int
