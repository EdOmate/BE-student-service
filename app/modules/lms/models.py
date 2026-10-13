"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql

from core.database import Base
from core.model_defaults import utc_now


class LMSAssignment(Base):
    __tablename__ = 'org_lms_assignments'
    __table_args__ = (
        Index('org_lms_ass_organiz_3c6fcd_idx', 'organization_id'),
        Index('org_lms_ass_teacher_16b8b3_idx', 'teacher_id'),
        Index('org_lms_ass_subject_2046e6_idx', 'subject_mapping_id'),
        Index('org_lms_ass_status_f50963_idx', 'status'),
    )

    class GradingMode:
        UNGRADED = 1
        GRADED = 2
        choices = [(1, 'Ungraded'), (2, 'Graded')]

    class DeadlineType:
        NO_DEADLINE = 1
        DUE_DATE = 2
        choices = [(1, 'No Deadline'), (2, 'Due Date')]

    class Status:
        DRAFT = 1
        PUBLISHED = 2
        GRADED = 3
        ARCHIVED = 4
        choices = [(1, 'Draft'), (2, 'Published'), (3, 'Graded'), (4, 'Archived')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(BigInteger, nullable=False, index=True)
    academic_year = Column(String(10), nullable=False)
    section_ids = Column(JSON(none_as_null=True), nullable=False, default=list)
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=False,
        index=True,
    )
    teacher_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=False)
    grading_mode = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    max_marks = Column(Numeric(8, 2), nullable=True)
    deadline_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    due_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    attachments = Column(JSON(none_as_null=True), nullable=True, default=list)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class LMSAssignmentSubmission(Base):
    __tablename__ = 'org_lms_assignment_submissions'
    __table_args__ = (
        UniqueConstraint('assignment_id', 'student_id'),
        Index('org_lms_ass_student_c4098c_idx', 'student_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    assignment_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignments.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    submitted_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    files = Column(JSON(none_as_null=True), nullable=True, default=list)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LMSAssignmentEvaluation(Base):
    __tablename__ = 'org_lms_assignment_evaluations'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    submission_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignment_submissions.id'),
        nullable=False,
        unique=True,
    )
    marks = Column(Numeric(8, 2), nullable=True)
    feedback = Column(mysql.LONGTEXT, nullable=True)
    evaluated_by_id = Column(BigInteger, nullable=False)
    evaluated_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LMSSubmissionThread(Base):
    __tablename__ = 'org_lms_submission_threads'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    submission_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignment_submissions.id'),
        nullable=False,
        unique=True,
    )
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LMSSubmissionMessage(Base):
    __tablename__ = 'org_lms_submission_messages'

    class SenderType:
        TEACHER = 1
        STUDENT = 2
        PARENT = 3
        choices = [(1, 'Teacher'), (2, 'Student'), (3, 'Parent')]

    SENDER_TEACHER = 1
    SENDER_STUDENT = 2
    SENDER_PARENT = 3

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    thread_id = Column(
        BigInteger,
        ForeignKey('org_lms_submission_threads.id'),
        nullable=False,
        index=True,
    )
    sender_id = Column(BigInteger, nullable=False)
    sender_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    message = Column(mysql.LONGTEXT, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LMSAssignmentComment(Base):
    __tablename__ = 'org_lms_assignment_comments'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    assignment_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignments.id'),
        nullable=False,
        index=True,
    )
    parent_comment_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignment_comments.id'),
        nullable=True,
        index=True,
    )
    user_id = Column(BigInteger, nullable=False)
    message = Column(mysql.LONGTEXT, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LMSAssignmentActivityLog(Base):
    __tablename__ = 'org_lms_assignment_activity_logs'

    class ActivityType:
        VIEWED = 1
        DOWNLOADED_FILE = 2
        OPENED_SUBMISSION = 3
        SUBMITTED = 4
        choices = [
            (1, 'Viewed'),
            (2, 'Downloaded File'),
            (3, 'Opened Submission'),
            (4, 'Submitted'),
        ]

    ACTIVITY_VIEWED = 1
    ACTIVITY_DOWNLOADED_FILE = 2
    ACTIVITY_OPENED_SUBMISSION = 3
    ACTIVITY_SUBMITTED = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    assignment_id = Column(
        BigInteger,
        ForeignKey('org_lms_assignments.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    activity_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class LessonPlan(Base):
    __tablename__ = 'org_lesson_plans'
    __table_args__ = (
        UniqueConstraint('subject_mapping_id', 'title', name='uq_lesson_plan_title_mapping'),
        Index('org_lesson__subject_9d702f_idx', 'subject_mapping_id'),
        Index('org_lesson__status_42523d_idx', 'status'),
        Index('org_lesson__term_253d73_idx', 'term'),
    )

    class LessonPlanStatus:
        DRAFT = 1
        SUBMITTED = 2
        APPROVED = 3
        COMPLETED = 4
        REJECTED = 5
        choices = [
            (1, 'Draft'),
            (2, 'Submitted'),
            (3, 'Approved'),
            (4, 'Completed'),
            (5, 'Rejected'),
        ]

    STATUS_DRAFT = 1
    STATUS_SUBMITTED = 2
    STATUS_APPROVED = 3
    STATUS_COMPLETED = 4
    STATUS_REJECTED = 5

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=False,
        index=True,
    )
    curriculum_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_syllabus.id'),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    term = Column(String(50), nullable=True, index=True)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    submitted_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    approved_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    completed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    assigned_teacher_id = Column(Integer, nullable=True, index=True)
    approved_by_id = Column(Integer, nullable=True, index=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class LessonPlanItem(Base):
    __tablename__ = 'org_lesson_plan_items'
    __table_args__ = (
        UniqueConstraint('lesson_plan_id', 'sequence_no', name='uq_lesson_plan_item_sequence'),
        CheckConstraint('(`coverage_percent` >= 0 AND `coverage_percent` <= 100)', name='chk_lesson_item_coverage'),
        Index('org_lesson__lesson__bbe9ca_idx', 'lesson_plan_id'),
        Index('org_lesson__status_2c8d9d_idx', 'status'),
        Index('org_lesson__planned_7188ec_idx', 'planned_date'),
    )

    class LessonPlanItemStatus:
        PLANNED = 1
        IN_PROGRESS = 2
        COMPLETED = 3
        SKIPPED = 4
        choices = [(1, 'Planned'), (2, 'In Progress'), (3, 'Completed'), (4, 'Skipped')]

    STATUS_PLANNED = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETED = 3
    STATUS_SKIPPED = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    lesson_plan_id = Column(
        BigInteger,
        ForeignKey('org_lesson_plans.id'),
        nullable=False,
        index=True,
    )
    curriculum_chapter_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_chapters.id'),
        nullable=True,
        index=True,
    )
    curriculum_unit_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_units.id'),
        nullable=True,
        index=True,
    )
    curriculum_topic_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_topics.id'),
        nullable=True,
        index=True,
    )
    sequence_no = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    learning_outcome = Column(mysql.LONGTEXT, nullable=True)
    planned_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)
    estimated_duration_minutes = Column(mysql.INTEGER(unsigned=True), nullable=True)
    actual_duration_minutes = Column(mysql.INTEGER(unsigned=True), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    coverage_percent = Column(Numeric(5, 2), nullable=False, default=0)
    teacher_notes = Column(mysql.LONGTEXT, nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    completed_by_id = Column(Integer, nullable=True, index=True)
    completed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class LessonPlanActivityLog(Base):
    __tablename__ = 'org_lesson_plan_activity_logs'
    __table_args__ = (
        Index('org_lesson__lesson__6489ab_idx', 'lesson_plan_id'),
        Index('org_lesson__action_601210_idx', 'action'),
        Index('org_lesson__created_b07b51_idx', 'created_at'),
    )

    class LessonPlanAction:
        CREATED = 1
        UPDATED = 2
        SUBMITTED = 3
        APPROVED = 4
        REJECTED = 5
        COMPLETED = 6
        choices = [
            (1, 'Created'),
            (2, 'Updated'),
            (3, 'Submitted'),
            (4, 'Approved'),
            (5, 'Rejected'),
            (6, 'Completed'),
        ]

    class LessonPlanStatus:
        DRAFT = 1
        SUBMITTED = 2
        APPROVED = 3
        COMPLETED = 4
        REJECTED = 5
        choices = [
            (1, 'Draft'),
            (2, 'Submitted'),
            (3, 'Approved'),
            (4, 'Completed'),
            (5, 'Rejected'),
        ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    lesson_plan_id = Column(
        BigInteger,
        ForeignKey('org_lesson_plans.id'),
        nullable=False,
        index=True,
    )
    action = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    from_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    to_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    acted_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class StudyMaterial(Base):
    __tablename__ = 'org_lms_study_materials'
    __table_args__ = (
        Index('org_lms_stu_section_8f3fd2_idx', 'section_id'),
        Index('org_lms_stu_subject_a6c96b_idx', 'subject_mapping_id'),
        Index('org_lms_stu_materia_4d06cd_idx', 'material_type'),
        Index('org_lms_stu_publish_37858b_idx', 'publish_at'),
        Index('org_lms_stu_status_f734f1_idx', 'status'),
    )

    MATERIAL_TYPE_CHOICES = [
        (1, 'Notes'),
        (2, 'Presentation'),
        (3, 'Worksheet'),
        (4, 'Video'),
        (5, 'Audio'),
        (6, 'External Link'),
        (7, 'Reference Material'),
    ]
    STATUS_CHOICES = ((1, 'Draft'), (2, 'Published'), (3, 'Archived'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=False,
        index=True,
    )
    material_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    attachments = Column(JSON(none_as_null=True), nullable=False, default=list)
    tags = Column(JSON(none_as_null=True), nullable=False, default=list)
    publish_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    expires_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class LMSClassWork(Base):
    __tablename__ = 'org_lms_classworks'
    __table_args__ = (
        Index('org_lms_cla_organiz_e75409_idx', 'organization_id', 'academic_year', 'is_active'),
        Index('org_lms_cla_organiz_f1db9a_idx', 'organization_id', 'academic_year', 'classwork_type'),
        Index('org_lms_cla_section_db6553_idx', 'section_id', 'classwork_date', 'status'),
        Index('org_lms_cla_subject_1126e6_idx', 'subject_mapping_id', 'classwork_date'),
        Index('org_lms_cla_teacher_339447_idx', 'teacher_id', 'classwork_date'),
    )

    class ClassWorkType:
        CURRICULUM = 'curriculum'
        GENERAL = 'general'
        choices = [('curriculum', 'Curriculum'), ('general', 'General')]

    class Status:
        DRAFT = 'draft'
        PUBLISHED = 'published'
        CANCELLED = 'cancelled'
        choices = [('draft', 'Draft'), ('published', 'Published'), ('cancelled', 'Cancelled')]

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CANCELLED = 'cancelled'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    classwork_type = Column(String(20), nullable=False, index=True, default='curriculum')
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=True,
        index=True,
    )
    curriculum_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_syllabus.id'),
        nullable=True,
        index=True,
    )
    teacher_id = Column(Integer, nullable=False, index=True)
    classwork_date = Column(Date, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    attachments = Column(JSON(none_as_null=True), nullable=False, default=list)
    status = Column(String(20), nullable=False, index=True, default='published')
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    cancelled_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class LMSClassWorkItem(Base):
    __tablename__ = 'org_lms_classwork_items'
    __table_args__ = (
        UniqueConstraint('classwork_id', 'sequence_no', name='uniq_classwork_item_sequence'),
        CheckConstraint('(`coverage_percent` >= 0 AND `coverage_percent` <= 100)', name='chk_classwork_item_coverage'),
        CheckConstraint("((`coverage_level` = 'unit' AND `curriculum_chapter_id` IS NULL AND `curriculum_topic_id` IS NULL AND `curriculum_unit_id` IS NOT NULL AND `custom_title` IS NULL) OR (`coverage_level` = 'chapter' AND `curriculum_chapter_id` IS NOT NULL AND `curriculum_topic_id` IS NULL AND `curriculum_unit_id` IS NULL AND `custom_title` IS NULL) OR (`coverage_level` = 'topic' AND `curriculum_chapter_id` IS NULL AND `curriculum_topic_id` IS NOT NULL AND `curriculum_unit_id` IS NULL AND `custom_title` IS NULL) OR (`coverage_level` = 'custom' AND `curriculum_chapter_id` IS NULL AND `curriculum_topic_id` IS NULL AND `curriculum_unit_id` IS NULL AND `custom_title` IS NOT NULL))", name='chk_classwork_item_target'),
        Index('org_lms_cla_classwo_5aaf7a_idx', 'classwork_id', 'coverage_level'),
        Index('org_lms_cla_curricu_bd71cf_idx', 'curriculum_unit_id'),
        Index('org_lms_cla_curricu_a43f11_idx', 'curriculum_chapter_id'),
        Index('org_lms_cla_curricu_a602f5_idx', 'curriculum_topic_id'),
    )

    class CoverageLevel:
        UNIT = 'unit'
        CHAPTER = 'chapter'
        TOPIC = 'topic'
        CUSTOM = 'custom'
        choices = [
            ('unit', 'Unit'),
            ('chapter', 'Chapter'),
            ('topic', 'Topic'),
            ('custom', 'Custom'),
        ]

    LEVEL_UNIT = 'unit'
    LEVEL_CHAPTER = 'chapter'
    LEVEL_TOPIC = 'topic'
    LEVEL_CUSTOM = 'custom'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    classwork_id = Column(
        BigInteger,
        ForeignKey('org_lms_classworks.id'),
        nullable=False,
        index=True,
    )
    coverage_level = Column(String(20), nullable=False, index=True)
    curriculum_unit_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_units.id'),
        nullable=True,
        index=True,
    )
    curriculum_chapter_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_chapters.id'),
        nullable=True,
        index=True,
    )
    curriculum_topic_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_topics.id'),
        nullable=True,
        index=True,
    )
    custom_title = Column(String(255), nullable=True)
    description = Column(mysql.LONGTEXT, nullable=True)
    sequence_no = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    coverage_percent = Column(Numeric(5, 2), nullable=False, default=100)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class StudentDiaryEntry(Base):
    __tablename__ = 'org_student_diary_entries'
    __table_args__ = (
        UniqueConstraint('student_id', 'reference_type', 'reference_id', name='uniq_student_diary_reference'),
        Index('org_student_organiz_c843de_idx', 'organization_id', 'academic_year', 'student_id', 'is_active'),
        Index('org_student_referen_cc2a23_idx', 'reference_type', 'reference_id'),
    )

    class ReferenceType:
        CLASSWORK = 'classwork'
        HOMEWORK = 'homework'
        STUDENT_REMARK = 'student_remark'
        EVENT_ANNOUNCEMENT = 'event_announcement'
        ACTIVITY_SPOTLIGHT = 'activity_spotlight'
        LESSON_PLAN = 'lesson_plan'
        ASSIGNMENT = 'assignment'
        ASSESSMENT = 'assessment'
        STUDY_MATERIAL = 'study_material'
        EVENT = 'event'
        choices = [
            ('classwork', 'Classwork'),
            ('homework', 'Homework'),
            ('student_remark', 'Student Remark'),
            ('event_announcement', 'Event Announcement'),
            ('activity_spotlight', 'Activity Spotlight'),
            ('lesson_plan', 'Lesson Plan'),
            ('assignment', 'Assignment'),
            ('assessment', 'Assessment'),
            ('study_material', 'Study Material'),
            ('event', 'Event'),
        ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    reference_type = Column(String(32), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=False)
    due_date = Column(Date, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    publish_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    expires_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    is_published = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    published_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class StudentDiaryAcknowledgement(Base):
    __tablename__ = 'org_student_diary_acknowledgements'
    __table_args__ = (
        Index('org_student_diary_e_0e678a_idx', 'diary_entry_id', 'is_active', 'acknowledged_at'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    diary_entry_id = Column(
        BigInteger,
        ForeignKey('org_student_diary_entries.id'),
        nullable=False,
        unique=True,
    )
    assigned_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    viewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    acknowledged_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    acknowledgement_note = Column(mysql.LONGTEXT, nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

__all__ = [
    'LMSAssignment',
    'LMSAssignmentSubmission',
    'LMSAssignmentEvaluation',
    'LMSSubmissionThread',
    'LMSSubmissionMessage',
    'LMSAssignmentComment',
    'LMSAssignmentActivityLog',
    'LessonPlan',
    'LessonPlanItem',
    'LessonPlanActivityLog',
    'StudyMaterial',
    'LMSClassWork',
    'LMSClassWorkItem',
    'StudentDiaryEntry',
    'StudentDiaryAcknowledgement',
]
