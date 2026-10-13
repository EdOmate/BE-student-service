"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship

from core.database import Base
from core.model_defaults import utc_now


class OrgSchoolStudent(Base):
    __tablename__ = 'org_school_students'
    __table_args__ = (
        Index('org_school__organiz_5f9035_idx', 'organization_id'),
        Index('org_school__admissi_e2e3f7_idx', 'admission_application_id'),
        Index('org_school__preferr_e0aadd_idx', 'preferred_class_id'),
        Index('org_school__enrollm_89df99_idx', 'enrollment_status'),
    )

    ADMISSION_TYPE_CHOICES = (
        (1, 'Admission Workflow'),
        (2, 'Direct Admission'),
        (3, 'Bulk Import'),
    )
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_GRADUATED = 3
    STATUS_TRANSFERRED = 4
    STATUS_WITHDRAWN = 5
    STATUS_CHOICES = (
        (1, 'Active'),
        (2, 'Inactive'),
        (3, 'Graduated'),
        (4, 'Transferred'),
        (5, 'Withdrawn'),
    )
    GENDER_CHOICE = ((1, 'Male'), (2, 'Female'), (3, 'Other'))
    NATIONALITY_CHOICE = ((1, 'Indian'), (2, 'Foreigner'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    admission_application_id = Column(Integer, nullable=False)
    admission_number = Column(String(50), nullable=False, unique=True)
    admission_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    email = Column(String(254), nullable=True)
    isd_code = Column(String(10), nullable=True)
    mobile = Column(String(20), nullable=True)
    nationality = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    religion_id = Column(
        BigInteger,
        ForeignKey('org_religion_master.id'),
        nullable=True,
        index=True,
    )
    caste_id = Column(BigInteger, ForeignKey('org_caste_master.id'), nullable=True, index=True)
    mother_tongue_id = Column(
        BigInteger,
        ForeignKey('org_mother_tongue_master.id'),
        nullable=True,
        index=True,
    )
    blood_group_id = Column(
        BigInteger,
        ForeignKey('org_blood_group_master.id'),
        nullable=True,
        index=True,
    )
    preferred_class_id = Column(BigInteger, nullable=True)
    profile_picture = Column(String(255), nullable=True)
    enrollment_status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    parents = relationship(
        'StudentParent',
        back_populates='student',
        cascade='all, delete-orphan',
    )

    religion = relationship('OrgReligionMaster', foreign_keys=[religion_id])

    caste = relationship('OrgCasteMaster', foreign_keys=[caste_id])

    mother_tongue = relationship('OrgMotherTongueMaster', foreign_keys=[mother_tongue_id])

    blood_group = relationship('OrgBloodGroupMaster', foreign_keys=[blood_group_id])

    @property
    def full_name(self):
        return ' '.join(filter(None, [self.first_name, self.middle_name, self.last_name]))


class StudentParent(Base):
    __tablename__ = 'org_school_students_parents'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(150), nullable=True, unique=True)
    password = Column(String(255), nullable=True)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    father_name = Column(String(100), nullable=True)
    father_phone = Column(String(15), nullable=True)
    father_email = Column(String(150), nullable=True)
    father_occupation = Column(String(100), nullable=True)
    father_income = Column(Numeric(12, 2), nullable=True)
    mother_name = Column(String(100), nullable=True)
    mother_phone = Column(String(15), nullable=True)
    mother_email = Column(String(150), nullable=True)
    mother_occupation = Column(String(100), nullable=True)
    mother_income = Column(Numeric(12, 2), nullable=True)
    guardian_name = Column(String(100), nullable=True)
    guardian_relation = Column(String(50), nullable=True)
    guardian_phone = Column(String(15), nullable=True)
    guardian_email = Column(String(150), nullable=True)
    address = Column(mysql.LONGTEXT, nullable=True)
    guardian_address = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    student = relationship('OrgSchoolStudent', back_populates='parents')


# Existing service-only mapping; retained pending a separate usage/schema migration.
class OrgStudentLoginToken(Base):
    __tablename__ = "org_student_login_tokens"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    parent_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    device_id = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)
    qr_code_version = Column(Integer, nullable=False, server_default=text("1"))
    status = Column(
        Enum(
            "ACTIVE",
            "USED",
            "EXPIRED",
            "REVOKED",
            name="student_login_token_status",
        ),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    expires_at = Column(TIMESTAMP, nullable=False)
    used_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ),
    )

__all__ = ['OrgSchoolStudent', 'StudentParent', 'OrgStudentLoginToken']
