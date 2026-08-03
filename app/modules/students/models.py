from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from core.database import Base


class OrgClassStudentAttendance(Base):
    __tablename__ = "org_class_student_attendance"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "section_id",
            "date",
            name="uq_student_section_attendance_date",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger,
        ForeignKey("org_school_students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False, index=True)
    status = Column(Integer, nullable=False)
    check_in_time = Column(Time, nullable=True)
    check_out_time = Column(Time, nullable=True)
    marked_by_id = Column(Integer, nullable=False)
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
