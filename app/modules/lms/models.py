from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
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
    organization_id = Column(BigInteger, nullable=False, index=True)
    academic_year = Column(String(10), nullable=False)
    section_ids = Column(JSON, default=list, nullable=False)
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey("org_class_subject_mapping.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    teacher_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    grading_mode = Column(SmallInteger, default=1, nullable=False)
    max_marks = Column(Numeric(8, 2))
    deadline_type = Column(SmallInteger, default=1, nullable=False)
    due_at = Column(DateTime)
    attachments = Column(JSON, default=list)
    status = Column(SmallInteger, default=1, nullable=False, index=True)
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class LMSAssignmentSubmission(Base):
    __tablename__ = 'org_lms_assignment_submissions'
    __table_args__ = (UniqueConstraint('assignment_id', 'student_id'),)
    SUBMISSION_STATUS_ASSIGNED = 1
    SUBMISSION_STATUS_SUBMITTED = 2
    SUBMISSION_STATUS_SUBMITTED_LATE = 3
    SUBMISSION_STATUS_EXEMPT_MEDICAL = 4
    SUBMISSION_STATUS_RETURNED = 5
    id = Column(BigInteger, primary_key=True)
    assignment_id = Column(BigInteger, ForeignKey('org_lms_assignments.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = Column(BigInteger, index=True, nullable=False)
    submission_status = Column(SmallInteger, default=1, index=True, nullable=False)
    submitted_at = Column(DateTime)
    remarks = Column(Text)
    files = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

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
        nullable=False,
    )
    marks = Column(Numeric(8, 2))
    feedback = Column(Text)
    evaluated_by_id = Column(BigInteger, nullable=False)
    evaluated_at = Column(DateTime, server_default=func.now(), nullable=False)


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
        index=True,
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
        index=True,
    )
    parent_comment_id = Column(
        BigInteger,
        ForeignKey("org_lms_assignment_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
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
        index=True,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    activity_type = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class LessonPlan(Base):
    __tablename__ = "org_lesson_plans"
    __table_args__ = (
        UniqueConstraint(
            "subject_mapping_id",
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
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey("org_class_subject_mapping.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curriculum_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_syllabus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    term = Column(String(50), nullable=True, index=True)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    status = Column(SmallInteger, default=STATUS_DRAFT, nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    assigned_teacher_id = Column(Integer, nullable=True, index=True)
    approved_by_id = Column(Integer, nullable=True, index=True)
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
    curriculum_chapter_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    curriculum_unit_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    curriculum_topic_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    completed_by_id = Column(Integer, nullable=True, index=True)
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
    acted_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

class StudyMaterial(Base):
    __tablename__ = 'org_lms_study_materials'
    id = Column(BigInteger, primary_key=True)
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey("org_class_subject_mapping.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    material_type = Column(SmallInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    attachments = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    publish_at = Column(DateTime, index=True)
    expires_at = Column(DateTime)
    status = Column(SmallInteger, default=1, nullable=False, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class LMSClassWork(Base):
    __tablename__ = "org_lms_classworks"
    __table_args__ = (
        Index(
            "ix_lms_classwork_org_year_active",
            "organization_id",
            "academic_year",
            "is_active",
        ),
        Index(
            "ix_lms_classwork_section_date_status",
            "section_id",
            "classwork_date",
            "status",
        ),
        Index(
            "ix_lms_classwork_mapping_date",
            "subject_mapping_id",
            "classwork_date",
        ),
        Index("ix_lms_classwork_teacher_date", "teacher_id", "classwork_date"),
    )

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELLED = "cancelled"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), index=True, nullable=False)
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey("org_class_subject_mapping.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    curriculum_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_syllabus.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    teacher_id = Column(Integer, nullable=False, index=True)
    classwork_date = Column(Date, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attachments = Column(JSON, default=list, nullable=False)
    status = Column(String(20), default=STATUS_DRAFT, index=True, nullable=False)
    published_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LMSClassWorkItem(Base):
    __tablename__ = "org_lms_classwork_items"
    __table_args__ = (
        UniqueConstraint(
            "classwork_id",
            "sequence_no",
            name="uniq_classwork_item_sequence",
        ),
        CheckConstraint(
            "coverage_percent >= 0 AND coverage_percent <= 100",
            name="chk_classwork_item_coverage",
        ),
        CheckConstraint(
            "(coverage_level = 'unit' AND curriculum_unit_id IS NOT NULL "
            "AND curriculum_chapter_id IS NULL AND curriculum_topic_id IS NULL "
            "AND custom_title IS NULL) OR "
            "(coverage_level = 'chapter' AND curriculum_unit_id IS NULL "
            "AND curriculum_chapter_id IS NOT NULL AND curriculum_topic_id IS NULL "
            "AND custom_title IS NULL) OR "
            "(coverage_level = 'topic' AND curriculum_unit_id IS NULL "
            "AND curriculum_chapter_id IS NULL AND curriculum_topic_id IS NOT NULL "
            "AND custom_title IS NULL) OR "
            "(coverage_level = 'custom' AND curriculum_unit_id IS NULL "
            "AND curriculum_chapter_id IS NULL AND curriculum_topic_id IS NULL "
            "AND custom_title IS NOT NULL)",
            name="chk_classwork_item_target",
        ),
        Index("ix_lms_classwork_item_level", "classwork_id", "coverage_level"),
    )

    LEVEL_UNIT = "unit"
    LEVEL_CHAPTER = "chapter"
    LEVEL_TOPIC = "topic"
    LEVEL_CUSTOM = "custom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    classwork_id = Column(
        BigInteger,
        ForeignKey("org_lms_classworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coverage_level = Column(String(20), index=True, nullable=False)
    curriculum_unit_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_units.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    curriculum_chapter_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_chapters.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    curriculum_topic_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_topics.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
    )
    custom_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    sequence_no = Column(Integer, default=1, nullable=False)
    coverage_percent = Column(Numeric(5, 2), default=100, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class StudentDiaryEntry(Base):
    __tablename__ = "org_student_diary_entries"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "reference_type",
            "reference_id",
            name="uniq_student_diary_reference",
        ),
        Index(
            "ix_diary_org_year_student_active",
            "organization_id",
            "academic_year",
            "student_id",
            "is_active",
        ),
        Index("ix_diary_reference", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey("org_school_students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    reference_type = Column(String(32), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    publish_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_published = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    published_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class StudentDiaryAcknowledgement(Base):
    __tablename__ = "org_student_diary_acknowledgements"
    __table_args__ = (
        Index(
            "ix_diary_ack_entry_active_date",
            "diary_entry_id",
            "is_active",
            "acknowledged_at",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diary_entry_id = Column(
        BigInteger,
        ForeignKey("org_student_diary_entries.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    viewed_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledgement_note = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


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
    "LMSClassWork",
    "LMSClassWorkItem",
    "StudentDiaryEntry",
    "StudentDiaryAcknowledgement",
]
