from datetime import date, datetime

from pydantic import BaseModel


class AttendanceCard(BaseModel):
    status: str
    check_in: str | None = None
    check_out: str | None = None
    total_hours: str | None = None
    action: str = "attendance_details"


class HomeworkCard(BaseModel):
    pending_count: int
    earliest_title: str | None = None
    due_at: datetime | None = None
    due_label: str | None = None
    action: str = "homework_list"


class ResultCard(BaseModel):
    available: bool
    exam_id: int | None = None
    exam_title: str | None = None
    percentage: float | None = None
    rank: int | None = None
    participants: int | None = None
    grade: str | None = None
    published_at: datetime | None = None
    action: str = "report_card"


class FeeCard(BaseModel):
    available: bool
    all_paid: bool | None = None
    due_amount: float | None = None
    due_date: date | None = None
    installment_count: int | None = None
    action: str = "fee_details"


class StudentSnapshotResponse(BaseModel):
    student_id: int
    generated_at: datetime
    attendance: AttendanceCard
    homework: HomeworkCard
    latest_result: ResultCard
    fee_status: FeeCard
