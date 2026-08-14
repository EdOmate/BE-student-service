from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from core.database import Base


class ExamSeries(Base):
    __tablename__ = "org_exam_series"
    __table_args__ = (
        Index("ix_exam_series_org_academic_year", "organization_id", "academic_year"),
        Index("ix_exam_series_org_status", "organization_id", "status"),
        Index("ix_exam_series_type_status", "exam_type", "status"),
    )

    TYPE_UNIT_TEST = 1
    TYPE_PERIODIC_TEST = 2
    TYPE_HALF_YEARLY = 3
    TYPE_ANNUAL = 4
    TYPE_PREBOARD = 5
    TYPE_OTHER = 6

    STATUS_SCHEDULED = 2
    STATUS_ONGOING = 3
    STATUS_COMPLETED = 4
    STATUS_PUBLISHED = 5
    STATUS_CANCELLED = 6

    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    academic_year = Column(String(20), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    exam_type = Column(SmallInteger, default=TYPE_OTHER, index=True, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(
        SmallInteger,
        default=STATUS_SCHEDULED,
        index=True,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamSection(Base):
    __tablename__ = "org_exam_sections"
    __table_args__ = (
        UniqueConstraint("exam_id", "section_id"),
        Index("ix_exam_section_exam", "exam_id"),
        Index("ix_exam_section_section", "section_id"),
    )

    STATUS_DRAFT = 1
    STATUS_SCHEDULED = 2
    STATUS_PUBLISHED = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True)
    exam_id = Column(
        BigInteger,
        ForeignKey("org_exam_series.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(SmallInteger, default=STATUS_DRAFT, index=True, nullable=False)
    remarks = Column(Text, nullable=True)
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamPaper(Base):
    __tablename__ = "org_exam_papers"

    STATUS_DRAFT = 1
    STATUS_SCHEDULED = 2
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True)
    section_id = Column(
        BigInteger,
        ForeignKey("org_exam_sections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    subject_mapping_id = Column(
        Integer,
        ForeignKey("org_class_subject_mapping.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_name = Column(String(255), index=True, nullable=False)
    paper_code = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    max_marks = Column(Numeric(8, 2), default=0, nullable=False)
    passing_marks = Column(Numeric(8, 2), default=0, nullable=False)
    status = Column(
        SmallInteger,
        default=STATUS_SCHEDULED,
        index=True,
        nullable=False,
    )
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamSchedule(Base):
    __tablename__ = "org_exam_schedules"
    __table_args__ = (
        UniqueConstraint("exam_paper_id", "section_id", "exam_date"),
        Index("ix_exam_schedule_section_date", "section_id", "exam_date"),
    )

    STATUS_SCHEDULED = 2
    STATUS_PUBLISHED = 3
    STATUS_COMPLETED = 4
    STATUS_CANCELLED = 5

    id = Column(BigInteger, primary_key=True)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey("org_exam_papers.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    exam_date = Column(Date, index=True, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    room_number = Column(String(100), nullable=True)
    invigilator_id = Column(Integer, nullable=True)
    status = Column(
        SmallInteger,
        default=STATUS_SCHEDULED,
        index=True,
        nullable=False,
    )
    remarks = Column(Text, nullable=True)
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamStudentRegistration(Base):
    __tablename__ = "org_exam_student_registrations"
    __table_args__ = (
        UniqueConstraint("exam_section_id", "student_id"),
        Index(
            "ix_exam_registration_section_status",
            "exam_section_id",
            "registration_status",
        ),
    )

    STATUS_REGISTERED = 1
    STATUS_ADMIT_CARD_ISSUED = 2
    STATUS_ABSENT = 3
    STATUS_CANCELLED = 4

    id = Column(BigInteger, primary_key=True)
    exam_section_id = Column(
        BigInteger,
        ForeignKey("org_exam_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    registration_status = Column(
        SmallInteger,
        default=STATUS_REGISTERED,
        index=True,
        nullable=False,
    )
    admit_card_url = Column(Text, nullable=True)
    roll_number = Column(Integer, nullable=True)
    seat_number = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamAttendance(Base):
    __tablename__ = "org_exam_attendance"
    __table_args__ = (
        UniqueConstraint("exam_paper_id", "student_id"),
        Index("ix_exam_attendance_paper_status", "exam_paper_id", "status"),
    )

    STATUS_PRESENT = 1
    STATUS_ABSENT = 2
    STATUS_LATE = 3
    STATUS_WITHDRAWN = 4

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey("org_exam_papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    status = Column(
        SmallInteger,
        default=STATUS_PRESENT,
        index=True,
        nullable=False,
    )
    checked_in_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
    marked_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ExamGradeRule(Base):
    __tablename__ = "org_exam_grade_rules"
    __table_args__ = (
        UniqueConstraint("organization_id", "grade_name"),
        Index("ix_exam_grade_rule_org_active", "organization_id", "is_active"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, index=True)
    grade_name = Column(String(20), nullable=False)
    min_percentage = Column(Numeric(6, 2), nullable=False)
    max_percentage = Column(Numeric(6, 2), nullable=False)
    grade_point = Column(Numeric(6, 2), nullable=True)
    remark = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ExamResult(Base):
    __tablename__ = "org_exam_results"
    __table_args__ = (
        UniqueConstraint("exam_paper_id", "student_id"),
        Index("ix_exam_result_paper_status", "exam_paper_id", "result_status"),
    )

    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_WITHHELD = 3

    id = Column(BigInteger, primary_key=True)
    exam_paper_id = Column(
        BigInteger,
        ForeignKey("org_exam_papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(BigInteger, nullable=False, index=True)
    obtained_marks = Column(Numeric(8, 2), default=0, nullable=False)
    grade_rule_id = Column(
        BigInteger,
        ForeignKey("org_exam_grade_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    grade = Column(String(20), nullable=True)
    remarks = Column(Text, nullable=True)
    result_status = Column(
        SmallInteger,
        default=STATUS_DRAFT,
        index=True,
        nullable=False,
    )
    published_at = Column(DateTime, nullable=True)
    published_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamResultPublishLog(Base):
    __tablename__ = "org_exam_result_publish_logs"
    __table_args__ = (
        Index("ix_exam_publish_log_exam_date", "exam_id", "published_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    exam_id = Column(
        BigInteger,
        ForeignKey("org_exam_series.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    published_by_id = Column(Integer, nullable=True)
    published_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    remarks = Column(Text, nullable=True)


Exam = ExamSeries


__all__ = [
    "ExamSeries",
    "Exam",
    "ExamSection",
    "ExamPaper",
    "ExamSchedule",
    "ExamStudentRegistration",
    "ExamAttendance",
    "ExamGradeRule",
    "ExamResult",
    "ExamResultPublishLog",
]
