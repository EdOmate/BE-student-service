"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql

from core.database import Base
from core.model_defaults import utc_now
from app.modules.auth.model import OrgSchoolStudent, StudentParent


class OrgSchoolStudentConsent(Base):
    __tablename__ = 'org_school_student_consents'
    __table_args__ = (
        UniqueConstraint('student_id', 'admission_application_id', 'field_id', name='uniq_student_admission_consent_field'),
        Index('org_school__student_bb546b_idx', 'student_id', 'admission_application_id'),
        Index('org_school__field_i_664f37_idx', 'field_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    admission_application_id = Column(BigInteger, nullable=False, index=True)
    field_id = Column(BigInteger, nullable=False)
    field_key = Column(String(100), nullable=False)
    consent_label = Column(String(500), nullable=False)
    consent_value = Column(mysql.LONGTEXT, nullable=True)
    consented_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentFieldOption(Base):
    __tablename__ = 'org_school_student_field_options'
    __table_args__ = (
        UniqueConstraint('field_key', 'option_value'),
        Index('org_school__field_k_7a40cf_idx', 'field_key'),
        Index('org_school__section_e442ab_idx', 'section_name'),
        Index('org_school__field_k_cdabb8_idx', 'field_key', 'option_value'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    field_key = Column(String(100), nullable=False, index=True)
    section_name = Column(String(100), nullable=False, index=True)
    option_value = Column(mysql.INTEGER(unsigned=True), nullable=False)
    option_label = Column(String(255), nullable=False)
    sort_order = Column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentAddress(Base):
    __tablename__ = 'org_school_student_addresses'
    __table_args__ = (
        UniqueConstraint('student_id', 'address_type'),
    )

    ADDRESS_TYPE_CHOICES = [('Current', 'Current'), ('Permanent', 'Permanent')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    address_type = Column(String(10), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentMedical(Base):
    __tablename__ = 'org_school_student_medical'

    EMERGENCY_CONTACT_RELATION = (
        (1, 'Father'),
        (2, 'Mother'),
        (3, 'Brother'),
        (4, 'Sister'),
        (5, 'Grandfather'),
        (6, 'Grandmother'),
        (7, 'Uncle'),
        (8, 'Aunt'),
        (9, 'Other'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        unique=True,
    )
    has_disability = Column(Boolean, nullable=False, default=False)
    disability_details = Column(mysql.LONGTEXT, nullable=True)
    allergies = Column(mysql.LONGTEXT, nullable=True)
    medical_conditions = Column(mysql.LONGTEXT, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    blood_group_id = Column(
        BigInteger,
        ForeignKey('org_blood_group_master.id'),
        nullable=True,
        index=True,
    )
    height = Column(Numeric(5, 2), nullable=True)
    weight = Column(Numeric(5, 2), nullable=True)
    vaccination_records = Column(mysql.LONGTEXT, nullable=True)
    regular_medications = Column(mysql.LONGTEXT, nullable=True)
    medical_insurance_number = Column(String(100), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    doctor_phone = Column(String(20), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentFamily(Base):
    __tablename__ = 'org_school_student_family'

    FAMILY_TYPE_CHOICES = (
        (1, 'Nuclear Family'),
        (2, 'Joint Family'),
        (3, 'Extended Family'),
        (4, 'Single Parent Family'),
        (5, 'Guardian Family'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        unique=True,
    )
    family_income = Column(Numeric(12, 2), nullable=True)
    family_type = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    father_alive = Column(Boolean, nullable=False, default=True)
    mother_alive = Column(Boolean, nullable=False, default=True)
    parents_married = Column(Boolean, nullable=False, default=True)
    economic_status = Column(String(50), nullable=True)
    household_members_count = Column(Integer, nullable=True)
    primary_language_at_home = Column(String(50), nullable=True)
    owns_house = Column(Boolean, nullable=True)
    has_vehicle = Column(Boolean, nullable=True)
    has_internet = Column(Boolean, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentSibling(Base):
    __tablename__ = 'org_school_student_siblings'
    __table_args__ = (
        UniqueConstraint('student_id', 'sibling_id', name='uniq_org_school_student_sibling'),
        CheckConstraint('NOT (`student_id` = `sibling_id`)', name='student_cannot_be_own_sibling'),
        Index('org_school__student_a2746c_idx', 'student_id'),
        Index('org_school__sibling_6997cf_idx', 'sibling_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    sibling_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentAcademicHistory(Base):
    __tablename__ = 'org_school_student_academic_history'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    previous_school_name = Column(String(255), nullable=True)
    previous_school_board = Column(String(100), nullable=True)
    previous_class = Column(String(50), nullable=True)
    previous_academic_year = Column(String(20), nullable=True)
    previous_school_address = Column(mysql.LONGTEXT, nullable=True)
    previous_school_leaving_date = Column(Date, nullable=True)
    transfer_certificate_number = Column(String(100), nullable=True)
    reason_for_transfer = Column(mysql.LONGTEXT, nullable=True)
    previous_school_performance = Column(mysql.LONGTEXT, nullable=True)
    subjects_studied = Column(mysql.LONGTEXT, nullable=True)
    extracurricular_activities = Column(mysql.LONGTEXT, nullable=True)
    achievements = Column(mysql.LONGTEXT, nullable=True)
    disciplinary_records = Column(mysql.LONGTEXT, nullable=True)
    attendance_percentage = Column(Numeric(5, 2), nullable=True)
    gaps_in_education = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgSchoolStudentDocument(Base):
    __tablename__ = 'org_school_student_documents'

    VERIFICATION_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
        ('Under Review', 'Under Review'),
    ]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    document_field_id = Column(Integer, nullable=False)
    document_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_status = Column(String(20), nullable=False, default='Pending')
    verification_remarks = Column(mysql.LONGTEXT, nullable=True)
    document_number = Column(String(100), nullable=True)
    issuing_authority = Column(String(150), nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_required = Column(Boolean, nullable=False, default=True)
    uploaded_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    verified_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    uploaded_by_id = Column(Integer, nullable=False)
    verified_by_id = Column(Integer, nullable=False)


class OrgSchoolStudentInteractionLog(Base):
    __tablename__ = 'org_school_student_interaction_logs'
    __table_args__ = (
        Index('org_school__student_cfc16c_idx', 'student_id'),
        Index('org_school__organiz_cd6a0b_idx', 'organization_id'),
        Index('org_school__action__be89d5_idx', 'action_type'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(Integer, nullable=False)
    organization_id = Column(Integer, nullable=False)
    action_type = Column(String(30), nullable=False)
    reason = Column(mysql.LONGTEXT, nullable=True)
    action_taken_by = Column(Integer, nullable=True)
    session_year = Column(String(12), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgClassStudentAttendance(Base):
    __tablename__ = 'org_class_student_attendance'
    __table_args__ = (
        UniqueConstraint('student_id', 'section_id', 'date'),
    )

    STATUS_PRESENT = 1
    STATUS_ABSENT = 2
    STATUS_HALF_DAY = 3
    STATUS_LEAVE = 4
    STATUS_WEEKLY_OFF = 5
    STATUS_CHOICES = [
        (1, 'Present'),
        (2, 'Absent'),
        (3, 'Half Day'),
        (4, 'Leave'),
        (5, 'Weekly Off'),
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
    date = Column(Date, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    check_in_time = Column(mysql.TIME(fsp=6), nullable=True)
    check_out_time = Column(mysql.TIME(fsp=6), nullable=True)
    marked_by_id = Column(Integer, nullable=False, index=True)
    remarks = Column(String(255), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentLeaveRequest(Base):
    __tablename__ = 'org_student_leave_requests'
    __table_args__ = (
        Index('org_student_organiz_c72182_idx', 'organization_id', 'status'),
        Index('org_student_student_04ad25_idx', 'student_id', 'start_date', 'end_date'),
    )

    LEAVE_TYPE_SICK = 1
    LEAVE_TYPE_CASUAL = 2
    LEAVE_TYPE_MEDICAL = 3
    LEAVE_TYPE_FAMILY = 4
    LEAVE_TYPE_OTHER = 5
    LEAVE_TYPE_CHOICES = (
        (1, 'Sick Leave'),
        (2, 'Emergency Leave'),
        (3, 'Medical Leave'),
        (4, 'Family Function'),
        (5, 'Other'),
    )
    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CANCELLED = 4
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Approved'), (3, 'Rejected'), (4, 'Cancelled'))
    DURATION_FULL_DAY = 1
    DURATION_HALF_DAY = 2
    DURATION_CHOICES = ((1, 'Full Day'), (2, 'Half Day'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    reason = Column(mysql.LONGTEXT, nullable=False)
    attachments = Column(JSON(none_as_null=True), nullable=False, default=list)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    duration = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    requested_by_id = Column(BigInteger, nullable=True)
    requested_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    reviewed_by_id = Column(Integer, nullable=True, index=True)
    reviewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    review_remarks = Column(mysql.LONGTEXT, nullable=True)
    cancelled_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentHouse(Base):
    __tablename__ = 'org_student_houses'
    __table_args__ = (
        UniqueConstraint('organization_id', 'academic_year', 'name', name='uniq_student_house_name_year'),
        UniqueConstraint('organization_id', 'academic_year', 'code', name='uniq_student_house_code_year'),
        Index('org_student_organiz_9dd925_idx', 'organization_id', 'academic_year', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    code = Column(String(30), nullable=False)
    color_code = Column(String(20), nullable=True)
    description = Column(mysql.LONGTEXT, nullable=True)
    academic_year = Column(String(20), nullable=False, index=True)
    house_master_id = Column(Integer, nullable=True, index=True)
    capacity = Column(mysql.INTEGER(unsigned=True), nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentHouseAssignment(Base):
    __tablename__ = 'org_student_house_assignments'
    __table_args__ = (
        Index('org_student_organiz_1cee67_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_student_student_7a389e_idx', 'student_id', 'academic_year', 'status'),
        Index('org_student_house_i_4fb11b_idx', 'house_id', 'academic_year', 'status'),
    )

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_TRANSFERRED = 3
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'), (3, 'Transferred'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    house_id = Column(
        BigInteger,
        ForeignKey('org_student_houses.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    assigned_on = Column(Date, nullable=False)
    ended_on = Column(Date, nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    assigned_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentGroup(Base):
    __tablename__ = 'org_student_groups'
    __table_args__ = (
        UniqueConstraint('organization_id', 'academic_year', 'name', name='uniq_student_group_name_year'),
        UniqueConstraint('organization_id', 'academic_year', 'code', name='uniq_student_group_code_year'),
        Index('org_student_organiz_d39836_idx', 'organization_id', 'academic_year', 'is_active'),
    )

    TYPE_CLUB = 1
    TYPE_SPORT = 2
    TYPE_ACTIVITY = 3
    TYPE_ACADEMIC = 4
    TYPE_PROJECT = 5
    TYPE_OTHER = 6
    TYPE_CHOICES = (
        (1, 'Club'),
        (2, 'Sport'),
        (3, 'Activity'),
        (4, 'Academic'),
        (5, 'Project'),
        (6, 'Other'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    code = Column(String(30), nullable=False)
    group_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=6)
    description = Column(mysql.LONGTEXT, nullable=True)
    academic_year = Column(String(20), nullable=False, index=True)
    coordinator_id = Column(Integer, nullable=True, index=True)
    capacity = Column(mysql.INTEGER(unsigned=True), nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentGroupAssignment(Base):
    __tablename__ = 'org_student_group_assignments'
    __table_args__ = (
        Index('org_student_organiz_e11f1e_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_student_student_1052ca_idx', 'student_id', 'academic_year', 'status'),
        Index('org_student_group_i_87fc4e_idx', 'group_id', 'academic_year', 'status'),
    )

    ROLE_MEMBER = 1
    ROLE_LEADER = 2
    ROLE_CAPTAIN = 3
    ROLE_SECRETARY = 4
    ROLE_CHOICES = ((1, 'Member'), (2, 'Leader'), (3, 'Captain'), (4, 'Secretary'))
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    group_id = Column(
        BigInteger,
        ForeignKey('org_student_groups.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    role = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    joined_on = Column(Date, nullable=False)
    left_on = Column(Date, nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    assigned_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentWithdrawalRequest(Base):
    __tablename__ = 'org_student_withdrawal_requests'
    __table_args__ = (
        Index('org_student_organiz_29f799_idx', 'organization_id', 'status'),
        Index('org_student_student_516b79_idx', 'student_id', 'academic_year'),
    )

    TYPE_CHOICES = ((1, 'Withdrawal'), (2, 'Transfer'), (3, 'Passed Out'))
    STATUS_CHOICES = (
        (1, 'Pending'),
        (2, 'Clearance In Progress'),
        (3, 'Approved'),
        (4, 'Rejected'),
        (6, 'Completed'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    request_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    requested_exit_date = Column(Date, nullable=False)
    reason = Column(mysql.LONGTEXT, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    requested_by_id = Column(BigInteger, nullable=True)
    requested_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    reviewed_by_id = Column(Integer, nullable=True, index=True)
    reviewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    review_remarks = Column(mysql.LONGTEXT, nullable=True)
    completed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentClearance(Base):
    __tablename__ = 'org_student_clearances'
    __table_args__ = (
        UniqueConstraint('withdrawal_id', 'clearance_type', name='uniq_withdrawal_clearance_type'),
    )

    TYPE_CHOICES = (
        (4, 'Academic'),
        (1, 'Fees'),
        (2, 'Library'),
        (3, 'Transport'),
        (5, 'Hostel'),
    )
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Cleared'), (3, 'Blocked'), (4, 'Waived'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    withdrawal_id = Column(
        BigInteger,
        ForeignKey('org_student_withdrawal_requests.id'),
        nullable=False,
        index=True,
    )
    clearance_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    cleared_by_id = Column(Integer, nullable=True, index=True)
    cleared_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentTransferCertificate(Base):
    __tablename__ = 'org_student_transfer_certificates'
    __table_args__ = (
        UniqueConstraint('organization_id', 'certificate_number', name='uniq_org_tc_number'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    withdrawal_id = Column(
        BigInteger,
        ForeignKey('org_student_withdrawal_requests.id'),
        nullable=False,
        unique=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    certificate_number = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    certificate_url = Column(String(500), nullable=True)
    snapshot = Column(JSON(none_as_null=True), nullable=False, default=dict)
    revision = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    issued_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentExitAuditLog(Base):
    __tablename__ = 'org_student_exit_audit_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    withdrawal_id = Column(
        BigInteger,
        ForeignKey('org_student_withdrawal_requests.id'),
        nullable=False,
        index=True,
    )
    action = Column(String(50), nullable=False)
    from_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    to_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    action_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgStudentBehaviorIncident(Base):
    __tablename__ = 'org_student_behavior_incidents'
    __table_args__ = (
        Index('org_student_organiz_732874_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_student_student_176e58_idx', 'student_id', 'academic_year', 'incident_type'),
        Index('org_student_organiz_5b8594_idx', 'organization_id', 'severity', 'status'),
    )

    TYPE_POSITIVE = 1
    TYPE_NEGATIVE = 2
    TYPE_BULLYING = 3
    TYPE_SAFETY = 4
    TYPE_PEER_CONFLICT = 5
    INCIDENT_TYPE_CHOICES = (
        (1, 'Positive'),
        (2, 'Negative'),
        (3, 'Bullying'),
        (4, 'Safety'),
        (5, 'Peer Conflict'),
    )
    CATEGORY_ACADEMIC_BEHAVIOR = 1
    CATEGORY_CLASSROOM = 2
    CATEGORY_ATTENDANCE = 3
    CATEGORY_RESPECT = 4
    CATEGORY_AGGRESSION = 5
    CATEGORY_HARASSMENT = 6
    CATEGORY_PROPERTY = 7
    CATEGORY_DIGITAL = 8
    CATEGORY_LEADERSHIP = 9
    CATEGORY_HELPFULNESS = 10
    CATEGORY_OTHER = 99
    CATEGORY_CHOICES = (
        (1, 'Academic Behavior'),
        (2, 'Classroom'),
        (3, 'Attendance'),
        (4, 'Respect'),
        (5, 'Aggression'),
        (6, 'Harassment'),
        (7, 'Property'),
        (8, 'Digital'),
        (9, 'Leadership'),
        (10, 'Helpfulness'),
        (99, 'Other'),
    )
    SEVERITY_LOW = 1
    SEVERITY_MEDIUM = 2
    SEVERITY_HIGH = 3
    SEVERITY_CRITICAL = 4
    SEVERITY_CHOICES = ((1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Critical'))
    STATUS_REPORTED = 1
    STATUS_UNDER_REVIEW = 2
    STATUS_ACTION_TAKEN = 3
    STATUS_RESOLVED = 4
    STATUS_CLOSED = 5
    STATUS_CHOICES = (
        (1, 'Reported'),
        (2, 'Under Review'),
        (3, 'Action Taken'),
        (4, 'Resolved'),
        (5, 'Closed'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    incident_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    category = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=99)
    severity = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    incident_at = Column(mysql.DATETIME(fsp=6), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=False)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    reported_by_id = Column(Integer, nullable=True, index=True)
    assigned_to_id = Column(Integer, nullable=True, index=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    resolution_notes = Column(mysql.LONGTEXT, nullable=True)
    resolved_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentBehaviorParticipant(Base):
    __tablename__ = 'org_student_behavior_participants'
    __table_args__ = (
        UniqueConstraint('incident_id', 'student_id', 'role', name='uniq_behavior_incident_student_role'),
        Index('org_student_inciden_4521cc_idx', 'incident_id', 'role'),
        Index('org_student_student_81eaf1_idx', 'student_id', 'role'),
    )

    ROLE_PRIMARY = 1
    ROLE_VICTIM = 2
    ROLE_ACCUSED = 3
    ROLE_WITNESS = 4
    ROLE_REPORTER = 5
    ROLE_MEDIATOR = 6
    ROLE_OTHER = 99
    ROLE_CHOICES = (
        (1, 'Primary Student'),
        (2, 'Victim'),
        (3, 'Accused'),
        (4, 'Witness'),
        (5, 'Reporter'),
        (6, 'Mediator'),
        (99, 'Other'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    incident_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_incidents.id'),
        nullable=False,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    role = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    notes = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgStudentBehaviorAction(Base):
    __tablename__ = 'org_student_behavior_actions'
    __table_args__ = (
        Index('org_student_student_3bb3d2_idx', 'student_id', 'action_type', 'action_status'),
        Index('org_student_inciden_8e0bd4_idx', 'incident_id', 'action_type'),
        Index('org_student_assigne_b447eb_idx', 'assigned_to_id', 'action_status'),
    )

    TYPE_WARNING = 1
    TYPE_DETENTION = 2
    TYPE_SUSPENSION = 3
    TYPE_EXPULSION_RECOMMENDED = 4
    TYPE_PARENT_MEETING = 5
    TYPE_COUNSELING = 6
    TYPE_PEER_MEDIATION = 7
    TYPE_RESTORATIVE_PRACTICE = 8
    TYPE_RECOGNITION = 9
    TYPE_REWARD = 10
    ACTION_TYPE_CHOICES = (
        (1, 'Warning'),
        (2, 'Detention'),
        (3, 'Suspension'),
        (4, 'Expulsion Recommended'),
        (5, 'Parent Meeting'),
        (6, 'Counseling'),
        (7, 'Peer Mediation'),
        (8, 'Restorative Practice'),
        (9, 'Recognition'),
        (10, 'Reward'),
    )
    STATUS_PENDING = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETED = 3
    STATUS_CANCELLED = 4
    STATUS_CHOICES = ((1, 'Pending'), (2, 'In Progress'), (3, 'Completed'), (4, 'Cancelled'))
    CONFIDENTIALITY_NORMAL = 1
    CONFIDENTIALITY_RESTRICTED = 2
    CONFIDENTIALITY_CONFIDENTIAL = 3
    CONFIDENTIALITY_CHOICES = ((1, 'Normal'), (2, 'Restricted'), (3, 'Confidential'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    incident_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_incidents.id'),
        nullable=True,
        index=True,
    )
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    action_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    action_status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assigned_to_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    notes = Column(mysql.LONGTEXT, nullable=True)
    outcome = Column(mysql.LONGTEXT, nullable=True)
    confidentiality_level = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    completed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgStudentBehaviorPointLog(Base):
    __tablename__ = 'org_student_behavior_point_logs'
    __table_args__ = (
        Index('org_student_student_c62b35_idx', 'student_id', 'created_at'),
        Index('org_student_inciden_66ba03_idx', 'incident_id'),
        Index('org_student_action__824151_idx', 'action_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    incident_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_incidents.id'),
        nullable=True,
        index=True,
    )
    action_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_actions.id'),
        nullable=True,
        index=True,
    )
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgStudentBehaviorNotificationLog(Base):
    __tablename__ = 'org_student_behavior_notification_logs'
    __table_args__ = (
        Index('org_student_student_25d012_idx', 'student_id', 'status'),
        Index('org_student_inciden_3edea3_idx', 'incident_id', 'status'),
        Index('org_student_action__345e8f_idx', 'action_id', 'status'),
        Index('org_student_channel_60ad3c_idx', 'channel', 'status'),
    )

    CHANNEL_EMAIL = 1
    CHANNEL_SMS = 2
    CHANNEL_WHATSAPP = 3
    CHANNEL_PUSH = 4
    CHANNEL_CHOICES = ((1, 'Email'), (2, 'SMS'), (3, 'WhatsApp'), (4, 'Push'))
    STATUS_PENDING = 1
    STATUS_SENT = 2
    STATUS_FAILED = 3
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Sent'), (3, 'Failed'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    incident_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_incidents.id'),
        nullable=True,
        index=True,
    )
    action_id = Column(
        BigInteger,
        ForeignKey('org_student_behavior_actions.id'),
        nullable=True,
        index=True,
    )
    channel = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    recipient_name = Column(String(150), nullable=True)
    recipient_contact = Column(String(255), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    message = Column(mysql.LONGTEXT, nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    sent_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

__all__ = [
    'OrgSchoolStudentConsent',
    'OrgSchoolStudentFieldOption',
    'OrgSchoolStudentAddress',
    'OrgSchoolStudentMedical',
    'OrgSchoolStudentFamily',
    'OrgSchoolStudentSibling',
    'OrgSchoolStudentAcademicHistory',
    'OrgSchoolStudentDocument',
    'OrgSchoolStudentInteractionLog',
    'OrgClassStudentAttendance',
    'OrgStudentLeaveRequest',
    'OrgStudentHouse',
    'OrgStudentHouseAssignment',
    'OrgStudentGroup',
    'OrgStudentGroupAssignment',
    'OrgStudentWithdrawalRequest',
    'OrgStudentClearance',
    'OrgStudentTransferCertificate',
    'OrgStudentExitAuditLog',
    'OrgStudentBehaviorIncident',
    'OrgStudentBehaviorParticipant',
    'OrgStudentBehaviorAction',
    'OrgStudentBehaviorPointLog',
    'OrgStudentBehaviorNotificationLog',
]
