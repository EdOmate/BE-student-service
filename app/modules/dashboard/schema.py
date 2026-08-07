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
    exam_id: int | None = None
    exam_title: str | None = None
    percentage: float | None = None
    rank: int | None = None
    participants: int | None = None
    grade: str | None = None
    published_at: datetime | None = None
    action: str = "report_card"


class UpcomingExamCard(BaseModel):
    exam_id: int
    exam_title: str
    exam_paper_id: int
    subject_name: str
    exam_date: date
    start_time: str | None = None
    end_time: str | None = None
    room_number: str | None = None
    action: str = "exam_schedule"


class StudentSnapshotResponse(BaseModel):
    student_id: int
    generated_at: datetime
    attendance: AttendanceCard
    homework: HomeworkCard
    latest_result: ResultCard | None = None
    upcoming_exam: UpcomingExamCard | None = None
