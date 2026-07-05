from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
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
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SchoolStageMaster(Base):
    __tablename__ = "school_stage_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)
    max_age = Column(String(10), nullable=True)
    class_range = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SchoolClassMaster(Base):
    __tablename__ = "school_class_master"

    id = Column(Integer, primary_key=True, index=True)
    stage_id = Column(Integer, ForeignKey("school_stage_master.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    order_level = Column(Integer, nullable=False)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    stage = relationship("SchoolStageMaster")


class OrgReligionMaster(Base):
    __tablename__ = "org_religion_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class OrgCasteMaster(Base):
    __tablename__ = "org_caste_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    religion_id = Column(Integer, ForeignKey("org_religion_master.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    religion = relationship("OrgReligionMaster")


class OrgMotherTongueMaster(Base):
    __tablename__ = "org_mother_tongue_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class OrgBloodGroupMaster(Base):
    __tablename__ = "org_blood_group_master"

    id = Column(Integer, primary_key=True, index=True)
    group_code = Column(String(5), unique=True, nullable=False)
    description = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class OrgEducationLevelMaster(Base):
    __tablename__ = "org_education_level_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class OrgMasterEmailConfig(Base):
    __tablename__ = "org_master_email_config"

    id = Column(Integer, primary_key=True, index=True)
    email_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)