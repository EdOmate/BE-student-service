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
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship, synonym

from core.database import Base
from core.model_defaults import utc_now
from app.modules.auth.model import OrgSchoolStudent
from app.modules.mainsite.models import Organization, SchoolClassMaster


class OrgSchoolClass(Base):
    __tablename__ = 'org_school_classes'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(Integer, nullable=False)
    master_class_id = Column(
        BigInteger,
        ForeignKey('school_class_master.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=True, default=utc_now)
    updated_at = Column(mysql.DATETIME(fsp=6), nullable=True, default=utc_now, onupdate=utc_now)

    master_class = relationship('SchoolClassMaster')

    sections = relationship(
        'OrgSchoolSection',
        back_populates='org_class',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    subject_mappings = relationship(
        'OrgClassSubjectMapping',
        back_populates='class_obj',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def __str__(self):
        return str(self.master_class)


class OrgSchoolSection(Base):
    __tablename__ = 'org_school_sections'

    SHIFT_CHOICES = [('Morning', 'Morning'), ('Afternoon', 'Afternoon'), ('Evening', 'Evening')]

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    org_class_id = Column(
        Integer,
        ForeignKey('org_school_classes.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(50), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    capacity = Column(Integer, nullable=False, default=60)
    current_strength = Column(Integer, nullable=False, default=0)
    class_teacher_id = Column(Integer, nullable=False, index=True)
    assistant_teacher_id = Column(Integer, nullable=False, index=True)
    cr_student_id = Column(Integer, nullable=True)
    vice_cr_student_id = Column(Integer, nullable=True)
    shift = Column(String(10), nullable=False, default='Morning')
    room_no = Column(String(20), nullable=True)
    timetable_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_id = Column(Integer, nullable=False, index=True)
    updated_by_id = Column(Integer, nullable=False, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    org_class = relationship('OrgSchoolClass', back_populates='sections')

    student_mappings = relationship(
        'SchoolStudentSectionMapping',
        back_populates='section',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    timetables = relationship(
        'OrgSchoolTimetable',
        back_populates='section',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def __str__(self):
        return f'{self.name} ({self.org_class.academic_year})'


class OrgSubject(Base):
    __tablename__ = 'org_school_subject'
    __table_args__ = (
        UniqueConstraint('organization_id', 'name'),
    )

    SUBJECT_MODE_CORE = 1
    SUBJECT_MODE_ELECTIVE = 2
    SUBJECT_MODE = [(1, 'Core'), (2, 'Elective')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(mysql.LONGTEXT, nullable=True)
    subject_mode = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    organization = relationship('Organization')

    class_mappings = relationship(
        'OrgClassSubjectMapping',
        back_populates='subject',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def __str__(self):
        return self.name


class OrgClassSubjectMapping(Base):
    __tablename__ = 'org_class_subject_mapping'
    __table_args__ = (
        UniqueConstraint('class_id', 'subject_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    class_id = Column(Integer, ForeignKey('org_school_classes.id'), nullable=False, index=True)
    subject_id = Column(
        BigInteger,
        ForeignKey('org_school_subject.id'),
        nullable=False,
        index=True,
    )
    status = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    class_obj = relationship('OrgSchoolClass', back_populates='subject_mappings')

    subject = relationship('OrgSubject', back_populates='class_mappings')

    curriculums = relationship(
        'CurriculumSyllabus',
        back_populates='class_subject_mapping',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    def __str__(self):
        return f'{self.class_obj} - {self.subject}'


class CurriculumSyllabus(Base):
    __tablename__ = 'org_curriculum_syllabus'
    __table_args__ = (
        UniqueConstraint('subject_mapping_id', 'academic_year', 'version'),
        Index('org_curricu_academi_183dfb_idx', 'academic_year'),
        Index('org_curricu_status_ee6b23_idx', 'status'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    version = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    booklet_pdf = Column(String(255), nullable=True)
    status = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Keep the existing Python attribute without querying the obsolete column.
    class_subject_mapping_id = synonym("subject_mapping_id")

    class_subject_mapping = relationship('OrgClassSubjectMapping', back_populates='curriculums')

    units = relationship(
        'CurriculumUnit',
        back_populates='curriculum',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='(CurriculumUnit.sorting_weight_index, CurriculumUnit.id)',
    )

    def __str__(self):
        return f'{self.title} ({self.academic_year})'


class CurriculumUnit(Base):
    __tablename__ = 'org_curriculum_units'
    __table_args__ = (
        UniqueConstraint('curriculum_id', 'sorting_weight_index'),
        Index('org_curricu_curricu_037024_idx', 'curriculum_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    curriculum_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_syllabus.id'),
        nullable=False,
        index=True,
    )
    title = Column(String(150), nullable=False)
    sorting_weight_index = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    overview_text = Column(String(500), nullable=True)
    allocated_hours = Column(mysql.INTEGER(unsigned=True), nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    curriculum = relationship('CurriculumSyllabus', back_populates='units')

    chapters = relationship(
        'CurriculumChapter',
        back_populates='unit',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='(CurriculumChapter.sorting_weight_index, CurriculumChapter.id)',
    )

    def __str__(self):
        return self.title


class CurriculumChapter(Base):
    __tablename__ = 'org_curriculum_chapters'
    __table_args__ = (
        UniqueConstraint('unit_id', 'sorting_weight_index'),
        Index('org_curricu_unit_id_eedf57_idx', 'unit_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    unit_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_units.id'),
        nullable=False,
        index=True,
    )
    title = Column(String(150), nullable=False)
    sorting_weight_index = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    overview_text = Column(String(500), nullable=True)
    allocated_hours = Column(mysql.INTEGER(unsigned=True), nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    unit = relationship('CurriculumUnit', back_populates='chapters')

    topics = relationship(
        'CurriculumTopic',
        back_populates='chapter',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='(CurriculumTopic.sorting_sub_index, CurriculumTopic.id)',
    )

    def __str__(self):
        return self.title


class CurriculumTopic(Base):
    __tablename__ = 'org_curriculum_topics'
    __table_args__ = (
        UniqueConstraint('chapter_id', 'sorting_sub_index'),
        Index('org_curricu_chapter_ab3e66_idx', 'chapter_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    chapter_id = Column(
        BigInteger,
        ForeignKey('org_curriculum_chapters.id'),
        nullable=False,
        index=True,
    )
    title = Column(String(150), nullable=False)
    sorting_sub_index = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    page_marker = Column(String(30), nullable=True)
    learning_outcomes = Column(JSON(none_as_null=True), nullable=False, default=list)
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    chapter = relationship('CurriculumChapter', back_populates='topics')

    def __str__(self):
        return self.title


class SchoolStudentSectionMapping(Base):
    __tablename__ = 'school_student_section_mapping'

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Transferred', 'Transferred'),
        ('Passed Out', 'Passed Out'),
        ('Dropped', 'Dropped'),
    ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    roll_number = Column(Integer, nullable=False)
    admission_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default='Active')
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    student = relationship('OrgSchoolStudent')

    section = relationship('OrgSchoolSection', back_populates='student_mappings')

    def __str__(self):
        return f'Student {self.student_id} - Section {self.section_id} - Roll {self.roll_number}'


class OrgSchoolTimetable(Base):
    __tablename__ = 'org_school_timetable'

    STATUS_CHOICES = ((0, 'Inactive'), (1, 'Active'), (2, 'Draft'), (3, 'Archived'))

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    section_id = Column(
        Integer,
        ForeignKey('org_school_sections.id'),
        nullable=False,
        index=True,
    )
    off_days = Column(String(255), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    total_periods = Column(Integer, nullable=False, default=8)
    period_duration = Column(Integer, nullable=True)
    break_count = Column(Integer, nullable=False, default=0)
    start_time = Column(mysql.TIME(fsp=6), nullable=False)
    end_time = Column(mysql.TIME(fsp=6), nullable=False)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by = Column(Integer, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    section = relationship('OrgSchoolSection', back_populates='timetables')

    breaks = relationship(
        'OrgSchoolTimetableBreak',
        back_populates='timetable',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    slots = relationship(
        'OrgSchoolTimetableSlot',
        back_populates='timetable',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )


class OrgSchoolTimetableBreak(Base):
    __tablename__ = 'org_school_timetable_breaks'
    __table_args__ = (
        UniqueConstraint('timetable_id', 'after_period'),
        Index('org_school__timetab_00f243_idx', 'timetable_id', 'status'),
        Index('org_school__timetab_6af9cd_idx', 'timetable_id', 'after_period'),
    )

    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_CHOICES = ((0, 'Inactive'), (1, 'Active'))

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    timetable_id = Column(
        Integer,
        ForeignKey('org_school_timetable.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    after_period = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    duration = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    timetable = relationship('OrgSchoolTimetable', back_populates='breaks')

    def __str__(self):
        return f'{self.timetable_id} - {self.name} after period {self.after_period}'


class OrgSchoolTimetableSlot(Base):
    __tablename__ = 'org_school_timetable_slots'
    __table_args__ = (
        UniqueConstraint('timetable_id', 'day_of_week', 'period_number'),
        Index('org_school__timetab_f4fa14_idx', 'timetable_id', 'day_of_week'),
    )

    PERIOD_SUBJECT_TYPE_CHOICES = [('core', 'Core'), ('elective', 'Elective')]
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    timetable_id = Column(
        Integer,
        ForeignKey('org_school_timetable.id'),
        nullable=False,
        index=True,
    )
    subject_mapping_id = Column(
        BigInteger,
        ForeignKey('org_class_subject_mapping.id'),
        nullable=True,
        index=True,
    )
    duration = Column(Integer, nullable=True)
    teacher_id = Column(Integer, nullable=True, index=True)
    substitute_teacher_id = Column(Integer, nullable=True, index=True)
    is_break = Column(Boolean, nullable=False, default=False)
    remarks = Column(String(255), nullable=True)
    period_number = Column(Integer, nullable=False)
    period_subject_type = Column(String(20), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    status = Column(SmallInteger, nullable=False, default=1)
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    timetable = relationship('OrgSchoolTimetable', back_populates='slots')

    def __str__(self):
        return f'{self.timetable_id} - {self.day_of_week} - Period {self.period_number}'

__all__ = [
    'OrgSchoolClass',
    'OrgSchoolSection',
    'OrgSubject',
    'OrgClassSubjectMapping',
    'CurriculumSyllabus',
    'CurriculumUnit',
    'CurriculumChapter',
    'CurriculumTopic',
    'SchoolStudentSectionMapping',
    'OrgSchoolTimetable',
    'OrgSchoolTimetableBreak',
    'OrgSchoolTimetableSlot',
]
