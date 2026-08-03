"""SQLAlchemy mappings for the legacy Django academics tables."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.modules.auth.model import OrgSchoolStudent
from app.modules.mainsite.models import Organization, SchoolClassMaster
from core.database import Base


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OrgSchoolClass(TimestampMixin, Base):
    __tablename__ = "org_school_classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False)
    master_class_id = Column(
        Integer,
        ForeignKey("school_class_master.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    master_class = relationship("SchoolClassMaster")
    sections = relationship(
        "OrgSchoolSection",
        back_populates="org_class",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    subject_mappings = relationship(
        "OrgClassSubjectMapping",
        back_populates="class_obj",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return str(self.master_class)


class OrgSchoolSection(TimestampMixin, Base):
    __tablename__ = "org_school_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_class_id = Column(
        Integer,
        ForeignKey("org_school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    capacity = Column(Integer, default=60, nullable=False)
    current_strength = Column(Integer, default=0, nullable=False)
    # These reference organization.OrgSchoolStaff (org_school_faculty), whose
    # model has not yet been ported to the student service.
    class_teacher_id = Column(Integer, nullable=False)
    assistant_teacher_id = Column(Integer, nullable=False)
    cr_student_id = Column(Integer, nullable=True)
    vice_cr_student_id = Column(Integer, nullable=True)
    shift = Column(String(10), default="Morning", nullable=False)
    room_no = Column(String(20), nullable=True)
    timetable_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, nullable=False)
    updated_by_id = Column(Integer, nullable=False)

    org_class = relationship("OrgSchoolClass", back_populates="sections")
    student_mappings = relationship(
        "SchoolStudentSectionMapping",
        back_populates="section",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    timetables = relationship(
        "OrgSchoolTimetable",
        back_populates="section",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return f"{self.name} ({self.org_class.academic_year})"


class OrgSubject(TimestampMixin, Base):
    __tablename__ = "org_school_subject"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_org_school_subject_organization_name",
        ),
    )

    SUBJECT_MODE_CORE = 1
    SUBJECT_MODE_ELECTIVE = 2

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    subject_mode = Column(SmallInteger, default=SUBJECT_MODE_CORE, nullable=False)
    status = Column(Boolean, default=True, nullable=False)

    organization = relationship("Organization")
    class_mappings = relationship(
        "OrgClassSubjectMapping",
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return self.name


class OrgClassSubjectMapping(TimestampMixin, Base):
    __tablename__ = "org_class_subject_mapping"
    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "subject_id",
            name="uq_org_class_subject_mapping_class_subject",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        Integer,
        ForeignKey("org_school_classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id = Column(
        Integer,
        ForeignKey("org_school_subject.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(Boolean, default=True, nullable=False)

    class_obj = relationship("OrgSchoolClass", back_populates="subject_mappings")
    subject = relationship("OrgSubject", back_populates="class_mappings")
    curriculums = relationship(
        "CurriculumSyllabus",
        back_populates="class_subject_mapping",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return f"{self.class_obj} - {self.subject}"


class CurriculumSyllabus(TimestampMixin, Base):
    __tablename__ = "org_curriculum_syllabus"
    __table_args__ = (
        UniqueConstraint(
            "class_subject_mapping_id",
            "academic_year",
            "version",
            name="uq_curriculum_mapping_year_version",
        ),
        Index("ix_org_curriculum_syllabus_academic_year", "academic_year"),
        Index("ix_org_curriculum_syllabus_status", "status"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_subject_mapping_id = Column(
        Integer,
        ForeignKey("org_class_subject_mapping.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    booklet_pdf = Column(String(255), nullable=True)
    status = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, nullable=True)

    class_subject_mapping = relationship(
        "OrgClassSubjectMapping",
        back_populates="curriculums",
    )
    units = relationship(
        "CurriculumUnit",
        back_populates="curriculum",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(CurriculumUnit.sorting_weight_index, CurriculumUnit.id)",
    )

    def __str__(self):
        return f"{self.title} ({self.academic_year})"


class CurriculumUnit(TimestampMixin, Base):
    __tablename__ = "org_curriculum_units"
    __table_args__ = (
        UniqueConstraint(
            "curriculum_id",
            "sorting_weight_index",
            name="uq_curriculum_unit_sorting_weight",
        ),
        Index("ix_org_curriculum_units_curriculum_id", "curriculum_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    curriculum_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_syllabus.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(150), nullable=False)
    sorting_weight_index = Column(Integer, default=1, nullable=False)
    overview_text = Column(String(500), nullable=True)
    allocated_hours = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    curriculum = relationship("CurriculumSyllabus", back_populates="units")
    chapters = relationship(
        "CurriculumChapter",
        back_populates="unit",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(CurriculumChapter.sorting_weight_index, CurriculumChapter.id)",
    )

    def __str__(self):
        return self.title


class CurriculumChapter(TimestampMixin, Base):
    __tablename__ = "org_curriculum_chapters"
    __table_args__ = (
        UniqueConstraint(
            "unit_id",
            "sorting_weight_index",
            name="uq_curriculum_chapter_sorting_weight",
        ),
        Index("ix_org_curriculum_chapters_unit_id", "unit_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    unit_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_units.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(150), nullable=False)
    sorting_weight_index = Column(Integer, default=1, nullable=False)
    overview_text = Column(String(500), nullable=True)
    allocated_hours = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    unit = relationship("CurriculumUnit", back_populates="chapters")
    topics = relationship(
        "CurriculumTopic",
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="(CurriculumTopic.sorting_sub_index, CurriculumTopic.id)",
    )

    def __str__(self):
        return self.title


class CurriculumTopic(TimestampMixin, Base):
    __tablename__ = "org_curriculum_topics"
    __table_args__ = (
        UniqueConstraint(
            "chapter_id",
            "sorting_sub_index",
            name="uq_curriculum_topic_sorting_sub_index",
        ),
        Index("ix_org_curriculum_topics_chapter_id", "chapter_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chapter_id = Column(
        BigInteger,
        ForeignKey("org_curriculum_chapters.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(150), nullable=False)
    sorting_sub_index = Column(Integer, default=1, nullable=False)
    page_marker = Column(String(30), nullable=True)
    learning_outcomes = Column(JSON, default=list, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    chapter = relationship("CurriculumChapter", back_populates="topics")

    def __str__(self):
        return self.title


class SchoolStudentSectionMapping(TimestampMixin, Base):
    __tablename__ = "school_student_section_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        BigInteger,
        ForeignKey("org_school_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    roll_number = Column(Integer, nullable=False)
    admission_date = Column(Date, nullable=True)
    status = Column(String(20), default="Active", nullable=False)

    student = relationship("OrgSchoolStudent")
    section = relationship("OrgSchoolSection", back_populates="student_mappings")

    def __str__(self):
        return (
            f"Student {self.student_id} - Section {self.section_id} "
            f"- Roll {self.roll_number}"
        )


class OrgSchoolTimetable(TimestampMixin, Base):
    __tablename__ = "org_school_timetable"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    section_id = Column(
        Integer,
        ForeignKey("org_school_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    off_days = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    total_periods = Column(Integer, default=8, nullable=False)
    period_duration = Column(Integer, nullable=True)
    break_count = Column(Integer, default=0, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    remarks = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    status = Column(SmallInteger, default=1, nullable=False)

    section = relationship("OrgSchoolSection", back_populates="timetables")
    breaks = relationship(
        "OrgSchoolTimetableBreak",
        back_populates="timetable",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    slots = relationship(
        "OrgSchoolTimetableSlot",
        back_populates="timetable",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrgSchoolTimetableBreak(TimestampMixin, Base):
    __tablename__ = "org_school_timetable_breaks"
    __table_args__ = (
        UniqueConstraint(
            "timetable_id",
            "after_period",
            name="uq_timetable_break_after_period",
        ),
        Index("ix_timetable_break_timetable_status", "timetable_id", "status"),
        Index(
            "ix_timetable_break_timetable_after_period",
            "timetable_id",
            "after_period",
        ),
    )

    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_id = Column(
        Integer,
        ForeignKey("org_school_timetable.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    after_period = Column(SmallInteger, nullable=False)
    duration = Column(SmallInteger, nullable=False)
    status = Column(SmallInteger, default=STATUS_ACTIVE, nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    timetable = relationship("OrgSchoolTimetable", back_populates="breaks")

    def __str__(self):
        return f"{self.timetable_id} - {self.name} after period {self.after_period}"


class OrgSchoolTimetableSlot(TimestampMixin, Base):
    __tablename__ = "org_school_timetable_slots"
    __table_args__ = (
        UniqueConstraint(
            "timetable_id",
            "day_of_week",
            "period_number",
            name="uq_timetable_slot_day_period",
        ),
        Index("ix_timetable_slot_timetable_day", "timetable_id", "day_of_week"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    timetable_id = Column(
        Integer,
        ForeignKey("org_school_timetable.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    teacher_id = Column(Integer, nullable=True)
    substitute_teacher_id = Column(Integer, nullable=True)
    is_break = Column(Boolean, default=False, nullable=False)
    remarks = Column(String(255), nullable=True)
    period_number = Column(Integer, nullable=False)
    period_subject_type = Column(String(20), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)

    timetable = relationship("OrgSchoolTimetable", back_populates="slots")

    def __str__(self):
        return (
            f"{self.timetable_id} - {self.day_of_week} "
            f"- Period {self.period_number}"
        )


__all__ = [
    "OrgSchoolClass",
    "OrgSchoolSection",
    "OrgSubject",
    "OrgClassSubjectMapping",
    "CurriculumSyllabus",
    "CurriculumUnit",
    "CurriculumChapter",
    "CurriculumTopic",
    "SchoolStudentSectionMapping",
    "OrgSchoolTimetable",
    "OrgSchoolTimetableBreak",
    "OrgSchoolTimetableSlot",
]
