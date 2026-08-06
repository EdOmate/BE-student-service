from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
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
    __tablename__ = 'org_exam_series'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    academic_year = Column(String(20))
    title = Column(String(255))
    exam_type = Column(Integer)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ExamSection(Base):
    __tablename__ = 'org_exam_sections'
    id = Column(BigInteger, primary_key=True)
    exam_id = Column(BigInteger, ForeignKey('org_exam_series.id', ondelete='CASCADE'))
    section_id = Column(Integer)
    title = Column(String(255))
    instructions = Column(Text)
    exam_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    room_number = Column(String(50))
    status = Column(Integer)
    remarks = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ExamPaper(Base):
    __tablename__ = 'org_exam_papers'
    id = Column(BigInteger, primary_key=True)
    section_id = Column(BigInteger, ForeignKey('org_exam_sections.id', ondelete='CASCADE'))
    subject_mapping_id = Column(Integer)
    subject_name = Column(String(255))
    paper_code = Column(String(100))
    description = Column(Text)
    max_marks = Column(Numeric(8, 2))
    passing_marks = Column(Numeric(8, 2))
    status = Column(Integer)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ExamSchedule(Base):
    __tablename__ = 'org_exam_schedules'
    id = Column(BigInteger, primary_key=True)
    exam_paper_id = Column(BigInteger, ForeignKey('org_exam_papers.id', ondelete='CASCADE'))
    section_id = Column(Integer)
    exam_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    room_number = Column(String(50))
    invigilator_id = Column(Integer)
    status = Column(Integer)
    remarks = Column(Text)
    created_by_id = Column(Integer)
    updated_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ExamStudentRegistration(Base):
    __tablename__ = 'org_exam_student_registrations'
    __table_args__ = (UniqueConstraint('exam_paper_id', 'student_id'),)
    id = Column(BigInteger, primary_key=True)
    exam_paper_id = Column(BigInteger, ForeignKey('org_exam_papers.id'))
    student_id = Column(BigInteger, nullable=False, index=True)
    registration_status = Column(Integer)
    admit_card_url = Column(Text)
    roll_number = Column(Integer)
    seat_number = Column(String(50))
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamAttendance(Base):
    __tablename__ = "org_exam_attendance"
    __table_args__ = (
        UniqueConstraint("exam_paper_id", "student_id"),
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
    status = Column(SmallInteger, default=STATUS_PRESENT, nullable=False)
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
    __tablename__ = 'org_exam_results'
    __table_args__ = (UniqueConstraint('exam_paper_id', 'student_id'),)
    id = Column(BigInteger, primary_key=True)
    exam_paper_id = Column(BigInteger, ForeignKey('org_exam_papers.id'))
    student_id = Column(BigInteger, nullable=False, index=True)
    obtained_marks = Column(Numeric(8, 2))
    grade_rule_id = Column(BigInteger)
    grade = Column(String(20))
    remarks = Column(Text)
    result_status = Column(Integer)
    published_at = Column(DateTime)
    published_by_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ExamResultPublishLog(Base):
    __tablename__ = "org_exam_result_publish_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    exam_id = Column(
        BigInteger,
        ForeignKey("org_exam_series.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id = Column(Integer, nullable=False, index=True)
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
