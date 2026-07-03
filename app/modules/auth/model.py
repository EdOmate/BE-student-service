from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Date,
    TIMESTAMP,
    text
)
from core.database import Base

class OrgSchoolStudent(Base):
    __tablename__ = "org_school_students"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    admission_application_id = Column(BigInteger, nullable=True, index=True)
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
    nationality = Column(String(100), nullable=True)
    religion = Column(String(100), nullable=True)
    caste = Column(String(100), nullable=True)
    mother_tongue = Column(String(100), nullable=True)
    blood_group = Column(String(20), nullable=True)
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
        server_default=text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )
    )
    @property
    def full_name(self):
        return " ".join(
            filter(
                None,
                [
                    self.first_name,
                    self.middle_name,
                    self.last_name
                ]
            )
        )