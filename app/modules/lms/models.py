from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from core.database import Base

class LMSAssignment(Base):
    __tablename__ = 'org_lms_assignments'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(BigInteger)
    academic_year = Column(String(20))
    section_ids = Column(JSON, default=list)
    subject_id = Column(BigInteger)
    teacher_id = Column(BigInteger)
    title = Column(String(255))
    description = Column(Text)
    grading_mode = Column(Integer)
    max_marks = Column(Numeric(8, 2))
    deadline_type = Column(Integer)
    due_at = Column(DateTime)
    attachments = Column(JSON, default=list)
    status = Column(Integer)
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class LMSAssignmentSubmission(Base):
    __tablename__ = 'org_lms_assignment_submissions'
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id'),)
    id = Column(BigInteger, primary_key=True)
    assignment_id = Column(BigInteger, ForeignKey('org_lms_assignments.id', ondelete='CASCADE'))
    student_id = Column(BigInteger, index=True)
    submitted_at = Column(DateTime)
    remarks = Column(Text)
    files = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())

class LMSAssignmentEvaluation(Base):
    __tablename__ = 'org_lms_assignment_evaluations'
    id = Column(BigInteger, primary_key=True)
    submission_id = Column(
        BigInteger,
        ForeignKey(
            "org_lms_assignment_submissions.id",
            ondelete="CASCADE",
        ),
        unique=True,
    )
    marks = Column(Numeric(8, 2))
    feedback = Column(Text)
    evaluated_by_id = Column(BigInteger)
    evaluated_at = Column(DateTime)


class LMSSubmissionThread(Base):
    __tablename__ = "org_lms_submission_threads"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    submission_id = Column(
        BigInteger,
        ForeignKey("org_lms_assignment_submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LMSSubmissionMessage(Base):
    __tablename__ = "org_lms_submission_messages"

    SENDER_TEACHER = 1
    SENDER_STUDENT = 2
    SENDER_PARENT = 3

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thread_id = Column(
        BigInteger,
        ForeignKey("org_lms_submission_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(BigInteger, nullable=False)
    sender_type = Column(SmallInteger, nullable=False)
    message = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LMSAssignmentComment(Base):
    __tablename__ = "org_lms_assignment_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id = Column(
        BigInteger,
        ForeignKey("org_lms_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_comment_id = Column(
        BigInteger,
        ForeignKey("org_lms_assignment_comments.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LMSAssignmentActivityLog(Base):
    __tablename__ = "org_lms_assignment_activity_logs"

    ACTIVITY_VIEWED = 1
    ACTIVITY_DOWNLOADED_FILE = 2
    ACTIVITY_OPENED_SUBMISSION = 3
    ACTIVITY_SUBMITTED = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id = Column(
        BigInteger,
        ForeignKey("org_lms_assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    activity_type = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LessonPlan(Base):
    __tablename__ = "org_lesson_plans"
    __table_args__ = (
        UniqueConstraint(
            "class_subject_mapping_id",
            "title",
            name="uq_lesson_plan_title_mapping",
        ),
    )

    STATUS_DRAFT = 1
    STATUS_SUBMITTED = 2
    STATUS_APPROVED = 3
    STATUS_COMPLETED = 4
    STATUS_REJECTED = 5

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_subject_mapping_id = Column(BigInteger, nullable=False, index=True)
    curriculum_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    term = Column(String(50), nullable=True, index=True)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    status = Column(SmallInteger, default=STATUS_DRAFT, nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by_id = Column(BigInteger, nullable=True)
    updated_by_id = Column(BigInteger, nullable=True)
    assigned_teacher_id = Column(BigInteger, nullable=True)
    approved_by_id = Column(BigInteger, nullable=True)
    remarks = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LessonPlanItem(Base):
    __tablename__ = "org_lesson_plan_items"
    __table_args__ = (
        UniqueConstraint(
            "lesson_plan_id",
            "sequence_no",
            name="uq_lesson_plan_item_sequence",
        ),
        CheckConstraint(
            "coverage_percent >= 0 AND coverage_percent <= 100",
            name="chk_lesson_item_coverage",
        ),
    )

    STATUS_PLANNED = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETED = 3
    STATUS_SKIPPED = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lesson_plan_id = Column(
        BigInteger,
        ForeignKey("org_lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curriculum_chapter_id = Column(BigInteger, nullable=True)
    curriculum_unit_id = Column(BigInteger, nullable=True)
    curriculum_topic_id = Column(BigInteger, nullable=True)
    sequence_no = Column(Integer, default=1, nullable=False)
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    learning_outcome = Column(Text, nullable=True)
    planned_date = Column(Date, nullable=True, index=True)
    actual_date = Column(Date, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    status = Column(
        SmallInteger,
        default=STATUS_PLANNED,
        nullable=False,
        index=True,
    )
    coverage_percent = Column(Numeric(5, 2), default=0, nullable=False)
    teacher_notes = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    completed_by_id = Column(BigInteger, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LessonPlanActivityLog(Base):
    __tablename__ = "org_lesson_plan_activity_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lesson_plan_id = Column(
        BigInteger,
        ForeignKey("org_lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(SmallInteger, nullable=False, index=True)
    from_status = Column(SmallInteger, nullable=True)
    to_status = Column(SmallInteger, nullable=True)
    remarks = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, default=dict, nullable=False)
    acted_by_id = Column(BigInteger, nullable=True)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

class StudyMaterial(Base):
    __tablename__ = 'org_lms_study_materials'
    id = Column(BigInteger, primary_key=True)
    section_id = Column(Integer, index=True)
    subject_id = Column(Integer)
    material_type = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    attachments = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    publish_at = Column(DateTime)
    expires_at = Column(DateTime)
    status = Column(Integer)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


__all__ = [
    "LMSAssignment",
    "LMSAssignmentSubmission",
    "LMSAssignmentEvaluation",
    "LMSSubmissionThread",
    "LMSSubmissionMessage",
    "LMSAssignmentComment",
    "LMSAssignmentActivityLog",
    "LessonPlan",
    "LessonPlanItem",
    "LessonPlanActivityLog",
    "StudyMaterial",
]
