"""SQLAlchemy mappings for global and organization master tables.

These models mirror the legacy Django ``mainsite`` models.  ``Organization``
and ``OrgMasterEmailConfig`` are retained here because existing student-service
code already used those mappings.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    udise = Column(String(50), nullable=True)
    logo = Column(String(250), nullable=True)
    email = Column(String(255), nullable=True)
    mobile = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    current_academic_year = Column(String(20), nullable=True)
    session_start_month = Column(String(20), nullable=True)
    session_end_month = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="active")

    def __str__(self):
        return self.name


class SchoolStageMaster(TimestampMixin, Base):
    __tablename__ = "school_stage_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    max_age = Column(Numeric(4, 2), nullable=True)
    class_range = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    classes = relationship(
        "SchoolClassMaster",
        back_populates="stage",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return f"{self.name} ({self.code})"


class SchoolClassMaster(TimestampMixin, Base):
    __tablename__ = "school_class_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(
        Integer,
        ForeignKey("school_stage_master.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    order_level = Column(Integer, nullable=False)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    stage = relationship("SchoolStageMaster", back_populates="classes")

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class SchoolFeeCategoryMaster(TimestampMixin, Base):
    __tablename__ = "school_fee_category_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=True, nullable=False)
    recurring_cycle = Column(SmallInteger, default=1, nullable=False)
    applicable_level = Column(SmallInteger, default=1, nullable=False)
    applicable_student_type = Column(SmallInteger, default=1, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    is_refundable = Column(Boolean, default=False, nullable=False)
    allow_partial_payment = Column(Boolean, default=False, nullable=False)
    default_amount = Column(Numeric(10, 2), default=0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(SmallInteger, default=1, nullable=False)

    def __str__(self):
        return self.name


class SchoolStudentDocumentMaster(TimestampMixin, Base):
    __tablename__ = "school_student_document_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.name


class OrgReligionMaster(TimestampMixin, Base):
    __tablename__ = "org_religion_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    castes = relationship(
        "OrgCasteMaster",
        back_populates="religion",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self):
        return self.name


class OrgCasteMaster(TimestampMixin, Base):
    __tablename__ = "org_caste_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    religion_id = Column(
        Integer,
        ForeignKey("org_religion_master.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    religion = relationship("OrgReligionMaster", back_populates="castes")

    def __str__(self):
        return self.name


class OrgMotherTongueMaster(TimestampMixin, Base):
    __tablename__ = "org_mother_tongue_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.name


class OrgBloodGroupMaster(TimestampMixin, Base):
    __tablename__ = "org_blood_group_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_code = Column(String(5), unique=True, nullable=False)
    description = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.group_code


class OrgEducationLevelMaster(TimestampMixin, Base):
    __tablename__ = "org_education_level_master"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return self.name


class OrgMasterEmailConfig(TimestampMixin, Base):
    __tablename__ = "org_master_email_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
