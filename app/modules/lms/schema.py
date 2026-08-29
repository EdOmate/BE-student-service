"""Schemas for student LMS APIs."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class AssignmentListItem(BaseModel):
    id: int
    title: str
    description: str
    subject_mapping_id: int
    subject_id: int
    subject_name: str | None = None
    teacher_id: int
    grading_mode: int
    max_marks: float | None = None
    deadline_type: int
    due_at: datetime | None = None
    attachments: list | None = None
    published_at: datetime | None = None
    assignment_status: str
    submission_id: int | None = None
    submitted_at: datetime | None = None


class AssignmentStatusCounts(BaseModel):
    all: int
    pending: int
    submitted: int
    overdue: int


class CustomPagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class StudentAssignmentListResponse(BaseModel):
    results: list[AssignmentListItem]
    counts: AssignmentStatusCounts
    pagination: CustomPagination


class AssignmentEvaluationDetail(BaseModel):
    id: int
    marks: float | None = None
    feedback: str | None = None
    evaluated_by_id: int | None = None
    evaluated_at: datetime | None = None


class AssignmentSubmissionDetail(BaseModel):
    id: int
    student_id: int
    submitted_at: datetime | None = None
    remarks: str | None = None
    files: list | None = None
    created_at: datetime | None = None
    evaluation: AssignmentEvaluationDetail | None = None


class CreateAssignmentSubmissionRequest(BaseModel):
    remarks: str | None = Field(default=None, max_length=5000)
    files: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("files")
    @classmethod
    def validate_file_keys(cls, files: list[str]) -> list[str]:
        normalized_files = []
        for file_key in files:
            normalized_key = file_key.strip().lstrip("/")
            if (
                not normalized_key.startswith("uploads/")
                or ".." in normalized_key.split("/")
                or normalized_key.endswith("/")
            ):
                raise ValueError(
                    "Each file must be a valid S3 key under uploads/"
                )
            normalized_files.append(normalized_key)
        return normalized_files

    @model_validator(mode="after")
    def require_submission_content(self):
        if not self.files and not (self.remarks and self.remarks.strip()):
            raise ValueError("At least one file or remarks is required")
        if self.remarks is not None:
            self.remarks = self.remarks.strip() or None
        return self


class StudentAssignmentDetailResponse(BaseModel):
    id: int
    title: str
    description: str
    subject_mapping_id: int
    subject_id: int
    subject_name: str | None = None
    teacher_id: int
    grading_mode: int
    max_marks: float | None = None
    deadline_type: int
    due_at: datetime | None = None
    attachments: list | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    assignment_status: str
    submissions: list[AssignmentSubmissionDetail]


class StudentMaterialItem(BaseModel):
    id: int
    section_id: int
    section_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    subject_mapping_id: int
    subject_id: int
    subject_name: str | None = None
    material_type: int
    material_type_label: str
    title: str
    description: str | None = None
    attachments: list
    tags: list
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StudentMaterialListResponse(BaseModel):
    results: list[StudentMaterialItem]
    pagination: CustomPagination


class DiaryAcknowledgementRequest(BaseModel):
    acknowledgement_note: str | None = Field(default=None, max_length=2000)

    @field_validator("acknowledgement_note")
    @classmethod
    def normalize_note(cls, value):
        return value.strip() or None if value is not None else None


class AssignmentMessageRequest(BaseModel):
    message: str | None = Field(default=None, max_length=5000)
    attachment_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_content(self):
        self.message = self.message.strip() if self.message else None
        if self.attachment_url:
            self.attachment_url = self.attachment_url.strip().lstrip("/")
            if (
                not self.attachment_url.startswith("uploads/")
                or ".." in self.attachment_url.split("/")
                or self.attachment_url.endswith("/")
            ):
                raise ValueError("attachment_url must be a valid uploads/ key")
        if not self.message and not self.attachment_url:
            raise ValueError("message or attachment_url is required")
        return self


class AssignmentCommentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    parent_comment_id: int | None = Field(default=None, ge=1)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("message is required")
        return value
