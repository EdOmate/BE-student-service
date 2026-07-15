from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Date,
    Text,
    TIMESTAMP,
    DECIMAL,
    ForeignKey,
    text,
    Enum
)
from sqlalchemy.dialects.mysql import BIGINT as MySQLBigInteger
from sqlalchemy.orm import relationship
from core.database import Base

class OrgSchoolStudent(Base):
    __tablename__ = "org_school_students"
    id = Column(MySQLBigInteger(unsigned=True), primary_key=True, autoincrement=True)
    organization_id = Column(MySQLBigInteger(unsigned=True), nullable=False, index=True)
    admission_application_id = Column(MySQLBigInteger(unsigned=True), nullable=True, index=True)
    admission_number = Column(String(50), nullable=False)
    admission_type = Column(
        Integer,
        nullable=False,
        server_default=text("1")
    )
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Integer, nullable=True)
    email = Column(String(255), nullable=True)
    isd_code = Column(String(10), nullable=True)
    mobile = Column(String(20), nullable=True)
    nationality = Column(Integer, nullable=True)
    religion_id = Column(Integer, nullable=True)
    caste_id = Column(Integer, nullable=True)
    mother_tongue_id = Column(Integer, nullable=True)
    blood_group_id = Column(Integer, nullable=True)
    preferred_class_id = Column(BigInteger, nullable=True)
    profile_picture = Column(String(255), nullable=True)
    enrollment_status = Column(
        Integer,
        nullable=False,
        index=True,
        server_default=text("1")
    )
    created_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )
    # One-to-One relationship
    parent = relationship(
        "StudentParent",
        back_populates="student",
        uselist=False,
        cascade="all, delete-orphan"
    )
    @property
    def full_name(self):
        return " ".join(
            filter(
                None,
                [
                    self.first_name,
                    self.middle_name,
                    self.last_name,
                ],
            )
        )


class StudentParent(Base):
    __tablename__ = "org_school_students_parents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    student_id = Column(
        MySQLBigInteger(unsigned=True),
        ForeignKey("org_school_students.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One parent record per student
        index=True,
    )
    # Father
    father_name = Column(String(100), nullable=True)
    father_phone = Column(String(15), nullable=True)
    father_email = Column(String(150), nullable=True)
    father_occupation = Column(String(100), nullable=True)
    father_income = Column(DECIMAL(12, 2), nullable=True)
    # Mother
    mother_name = Column(String(100), nullable=True)
    mother_phone = Column(String(15), nullable=True)
    mother_email = Column(String(150), nullable=True)
    mother_occupation = Column(String(100), nullable=True)
    mother_income = Column(DECIMAL(12, 2), nullable=True)
    # Guardian
    guardian_name = Column(String(100), nullable=True)
    guardian_relation = Column(String(50), nullable=True)
    guardian_phone = Column(String(15), nullable=True)
    guardian_email = Column(String(150), nullable=True)
    guardian_address = Column(Text, nullable=True)
    # Address
    address = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    # Relationship
    student = relationship(
        "OrgSchoolStudent",
        back_populates="parent"
    )

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
