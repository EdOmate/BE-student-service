"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Boolean,
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


class ExamSeries(Base):
    __tablename__ = 'org_exam_series'
    __table_args__ = (
        Index('org_exam_se_organiz_26fbac_idx', 'organization_id', 'academic_year'),
        Index('org_exam_se_organiz_3f97c8_idx', 'organization_id', 'status'),
        Index('org_exam_se_exam_ty_2cd8d9_idx', 'exam_type', 'status'),
    )

    TYPE_UNIT_TEST = 1
    TYPE_PERIODIC_TEST = 2
    TYPE_HALF_YEARLY = 3
    TYPE_ANNUAL = 4
    TYPE_PREBOARD = 5
    TYPE_OTHER = 6
    EXAM_TYPE_CHOICES = [
        (1, 'Unit Test'),
        (2, 'Periodic Test'),
        (3, 'Half Yearly'),
        (4, 'Annual'),
        (5, 'Pre Board'),
        (6, 'Other'),
    ]
    STATUS_CHOICES = [
        (2, 'Scheduled'),
        (3, 'Ongoing'),
        (4, 'Completed'),
        (5, 'Published'),
        (6, 'Cancelled'),
    ]
    STATUS_SCHEDULED = 2
    STATUS_ONGOING = 3
    STATUS_COMPLETED = 4
    STATUS_PUBLISHED = 5
    STATUS_CANCELLED = 6

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    exam_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=6)
    description = Column(mysql.LONGTEXT, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamSection(Base):
    __tablename__ = 'org_exam_sections'
    __table_args__ = (
        UniqueConstraint('exam_id', 'section_id'),
        Index('org_exam_se_exam_id_39e849_idx', 'exam_id'),
        Index('org_exam_se_section_db144e_idx', 'section_id'),
        Index('org_exam_se_status_9489d7_idx', 'status'),
    )

    SECTION_STATUS_CHOICES = [
        (1, 'Draft'),
        (2, 'Scheduled'),
        (3, 'Published'),
        (4, 'Completed'),
        (5, 'Cancelled'),
    ]
    STATUS_DRAFT = 1
    STATUS_SCHEDULED = 2
    STATUS_PUBLISHED = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_id = Column(BigInteger, ForeignKey('org_exam_series.id'), nullable=False, index=True)
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True)
    instructions = Column(mysql.LONGTEXT, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamPaper(Base):
    __tablename__ = 'org_exam_papers'
    __table_args__ = (
        Index('org_exam_pa_section_38347c_idx', 'section_id'),
        Index('org_exam_pa_status_d5e5ba_idx', 'status'),
        Index('org_exam_pa_subject_4a44a5_idx', 'subject_name'),
    )

    PAPER_STATUS_CHOICES = [(1, 'Draft'), (2, 'Scheduled'), (4, 'Completed'), (5, 'Cancelled')]
    STATUS_DRAFT = 1
    STATUS_SCHEDULED = 2
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    section_id = Column(
        BigInteger,
        ForeignKey('org_exam_sections.id'),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=True,
        index=True,
    )
    subject_name = Column(String(255), nullable=False)
    paper_code = Column(String(100), nullable=True)
    description = Column(mysql.LONGTEXT, nullable=True)
    max_marks = Column(Numeric(8, 2), nullable=False, default=0)
    passing_marks = Column(Numeric(8, 2), nullable=False, default=0)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamSchedule(Base):
    __tablename__ = 'org_exam_schedules'
    __table_args__ = (
        UniqueConstraint('exam_paper_id', 'section_id', 'exam_date'),
        Index('org_exam_sc_exam_pa_5d2452_idx', 'exam_paper_id'),
        Index('org_exam_sc_section_06a7a8_idx', 'section_id', 'exam_date'),
        Index('org_exam_sc_status_ea7bd3_idx', 'status'),
    )

    SCHEDULE_STATUS_CHOICES = [
        (2, 'Scheduled'),
        (3, 'Published'),
        (4, 'Completed'),
        (5, 'Cancelled'),
    ]
    STATUS_SCHEDULED = 2
    STATUS_PUBLISHED = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey('org_exam_papers.id'),
        nullable=False,
        index=True,
    )
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    exam_date = Column(Date, nullable=False, index=True)
    start_time = Column(mysql.TIME(fsp=6), nullable=True)
    end_time = Column(mysql.TIME(fsp=6), nullable=True)
    room_number = Column(String(100), nullable=True)
    invigilator_id = Column(Integer, nullable=True, index=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamStudentRegistration(Base):
    __tablename__ = 'org_exam_student_registrations'
    __table_args__ = (
        UniqueConstraint('exam_section_id', 'student_id'),
        Index('org_exam_st_exam_se_528bec_idx', 'exam_section_id', 'registration_status'),
        Index('org_exam_st_student_e69b4b_idx', 'student_id'),
    )

    REGISTRATION_STATUS_CHOICES = [
        (1, 'Registered'),
        (2, 'Admit Card Issued'),
        (3, 'Absent'),
        (4, 'Cancelled'),
    ]
    STATUS_REGISTERED = 1
    STATUS_ADMIT_CARD_ISSUED = 2
    STATUS_ABSENT = 3
    STATUS_CANCELLED = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_section_id = Column(
        BigInteger,
        ForeignKey('org_exam_sections.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    registration_status = Column(
        mysql.SMALLINT(unsigned=True),
        nullable=False,
        index=True,
        default=1,
    )
    admit_card_url = Column(mysql.LONGTEXT, nullable=True)
    roll_number = Column(Integer, nullable=True)
    seat_number = Column(String(50), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamAttendance(Base):
    __tablename__ = 'org_exam_attendance'
    __table_args__ = (
        UniqueConstraint('exam_paper_id', 'student_id'),
        Index('org_exam_at_exam_pa_f46f00_idx', 'exam_paper_id', 'status'),
        Index('org_exam_at_student_0b80d9_idx', 'student_id'),
    )

    ATTENDANCE_STATUS_CHOICES = [(1, 'Present'), (2, 'Absent'), (3, 'Late'), (4, 'Withdrawn')]
    STATUS_PRESENT = 1
    STATUS_ABSENT = 2
    STATUS_LATE = 3
    STATUS_WITHDRAWN = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey('org_exam_papers.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    checked_in_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    marked_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamGradingScale(Base):
    __tablename__ = 'org_exam_grading_scales'
    __table_args__ = (
        UniqueConstraint('organization_id', 'version', name='uniq_exam_grading_scale_org_version'),
        Index('org_exam_gr_organiz_b3e837_idx', 'organization_id', 'status'),
    )

    STATUS_DRAFT = 1
    STATUS_ACTIVE = 2
    STATUS_ARCHIVED = 3
    STATUS_CHOICES = [(1, 'Draft'), (2, 'Active'), (3, 'Archived')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False, default='Default Grading Scale')
    version = Column(mysql.INTEGER(unsigned=True), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    activated_at = Column(mysql.DATETIME(fsp=6), nullable=True)


class ExamGradeRule(Base):
    __tablename__ = 'org_exam_grade_rules'
    __table_args__ = (
        UniqueConstraint('grading_scale_id', 'grade_name'),
        Index('org_exam_gr_organiz_b9302e_idx', 'organization_id', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    grading_scale_id = Column(
        BigInteger,
        ForeignKey('org_exam_grading_scales.id'),
        nullable=True,
        index=True,
    )
    grade_name = Column(String(20), nullable=False)
    min_percentage = Column(Numeric(6, 2), nullable=False)
    max_percentage = Column(Numeric(6, 2), nullable=False)
    grade_point = Column(Numeric(6, 2), nullable=True)
    remark = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamResult(Base):
    __tablename__ = 'org_exam_results'
    __table_args__ = (
        UniqueConstraint('exam_paper_id', 'student_id'),
        Index('org_exam_re_exam_pa_2d356a_idx', 'exam_paper_id', 'result_status'),
        Index('org_exam_re_student_0be3f2_idx', 'student_id'),
    )

    RESULT_STATUS_CHOICES = [(1, 'Draft'), (2, 'Published'), (3, 'Withheld')]
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_WITHHELD = 3

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey('org_exam_papers.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    obtained_marks = Column(Numeric(8, 2), nullable=False, default=0)
    grade_rule_id = Column(
        BigInteger,
        ForeignKey('org_exam_grade_rules.id'),
        nullable=True,
        index=True,
    )
    grade = Column(String(20), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    result_status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    published_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class ExamResultPublishLog(Base):
    __tablename__ = 'org_exam_result_publish_logs'
    __table_args__ = (
        Index('org_exam_re_exam_id_573d50_idx', 'exam_id', 'published_at'),
        Index('org_exam_re_section_88a5ab_idx', 'section_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_id = Column(BigInteger, ForeignKey('org_exam_series.id'), nullable=False, index=True)
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    published_by_id = Column(Integer, nullable=True, index=True)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    remarks = Column(mysql.LONGTEXT, nullable=True)


class ExamReportCard(Base):
    __tablename__ = 'org_exam_report_cards'
    __table_args__ = (
        UniqueConstraint('exam_id', 'student_id', 'version', name='uniq_exam_report_card_version'),
        Index('org_exam_re_exam_id_dca9e8_idx', 'exam_id', 'status'),
        Index('org_exam_re_student_765150_idx', 'student_id', 'is_active'),
    )

    class Status:
        PENDING = 'pending'
        GENERATED = 'generated'
        FAILED = 'failed'
        PUBLISHED = 'published'
        choices = [
            ('pending', 'Pending'),
            ('generated', 'Generated'),
            ('failed', 'Failed'),
            ('published', 'Published'),
        ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    exam_id = Column(BigInteger, ForeignKey('org_exam_series.id'), nullable=False, index=True)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    grading_scale_id = Column(
        BigInteger,
        ForeignKey('org_exam_grading_scales.id'),
        nullable=True,
        index=True,
    )
    total_marks = Column(Numeric(10, 2), nullable=True)
    obtained_marks = Column(Numeric(10, 2), nullable=True)
    percentage = Column(Numeric(5, 2), nullable=True)
    grade = Column(String(20), nullable=True)
    result_status = Column(String(30), nullable=True)
    result_snapshot = Column(JSON(none_as_null=True), nullable=False, default=dict)
    pdf_file = Column(String(500), nullable=True)
    file_size = Column(mysql.BIGINT(unsigned=True), nullable=True)
    checksum = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, index=True, default='pending')
    generation_error = Column(mysql.LONGTEXT, nullable=True)
    generated_by_id = Column(Integer, nullable=True, index=True)
    generated_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    version = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

Exam = ExamSeries


__all__ = [
    'ExamSeries',
    'ExamSection',
    'ExamPaper',
    'ExamSchedule',
    'ExamStudentRegistration',
    'ExamAttendance',
    'ExamGradingScale',
    'ExamGradeRule',
    'ExamResult',
    'ExamResultPublishLog',
    'ExamReportCard',
    'Exam',
]
