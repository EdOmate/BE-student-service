"""SQLAlchemy mappings for the complete student domain."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    JSON,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.modules.auth.model import OrgSchoolStudent, StudentParent
from core.database import Base

SchoolStudentParent = StudentParent

class OrgSchoolStudentConsent(Base):
    __tablename__ = 'org_school_student_consents'
    __table_args__ = (
        UniqueConstraint(
            'student_id',
            'admission_application_id',
            'field_id',
            name='uniq_student_admission_consent_field',
        ),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    admission_application_id = Column(BigInteger, nullable=False, index=True)
    field_id = Column(BigInteger, nullable=False)
    field_key = Column(String(100), nullable=False)
    consent_label = Column(String(500), nullable=False)
    consent_value = Column(Text, nullable=True)
    consented_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentFieldOption(Base):
    __tablename__ = 'org_school_student_field_options'
    __table_args__ = (UniqueConstraint('field_key', 'option_value'),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    field_key = Column(String(100), nullable=False, index=True)
    section_name = Column(String(100), nullable=False, index=True)
    option_value = Column(Integer, nullable=False)
    option_label = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentAddress(Base):
    __tablename__ = 'org_school_student_addresses'
    __table_args__ = (UniqueConstraint('student_id', 'address_type'),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    address_type = Column(String(10), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentMedical(Base):
    __tablename__ = 'org_school_student_medical'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False, unique=True)
    has_disability = Column(Boolean, nullable=False, default=False)
    disability_details = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(SmallInteger, nullable=True)
    blood_group_id = Column(BigInteger, nullable=True)
    height = Column(Numeric(5, 2), nullable=True)
    weight = Column(Numeric(5, 2), nullable=True)
    vaccination_records = Column(Text, nullable=True)
    regular_medications = Column(Text, nullable=True)
    medical_insurance_number = Column(String(100), nullable=True)
    doctor_name = Column(String(100), nullable=True)
    doctor_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentFamily(Base):
    __tablename__ = 'org_school_student_family'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False, unique=True)
    family_income = Column(Numeric(12, 2), nullable=True)
    family_type = Column(SmallInteger, nullable=True)
    number_of_siblings = Column(Integer, nullable=False, default=0)
    sibling_details = Column(Text, nullable=True)
    sibling_studying_in = Column(SmallInteger, nullable=True)
    sibling_admission_number = Column(String(100), nullable=True)
    father_alive = Column(Boolean, nullable=False, default=True)
    mother_alive = Column(Boolean, nullable=False, default=True)
    parents_married = Column(Boolean, nullable=False, default=True)
    economic_status = Column(String(50), nullable=True)
    household_members_count = Column(Integer, nullable=True)
    primary_language_at_home = Column(String(50), nullable=True)
    owns_house = Column(Boolean, nullable=True)
    has_vehicle = Column(Boolean, nullable=True)
    has_internet = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentAcademicHistory(Base):
    __tablename__ = 'org_school_student_academic_history'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    previous_school_name = Column(String(255), nullable=True)
    previous_school_board = Column(String(100), nullable=True)
    previous_class = Column(String(50), nullable=True)
    previous_academic_year = Column(String(20), nullable=True)
    previous_school_address = Column(Text, nullable=True)
    previous_school_leaving_date = Column(Date, nullable=True)
    transfer_certificate_number = Column(String(100), nullable=True)
    reason_for_transfer = Column(Text, nullable=True)
    previous_school_performance = Column(Text, nullable=True)
    subjects_studied = Column(Text, nullable=True)
    extracurricular_activities = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    disciplinary_records = Column(Text, nullable=True)
    attendance_percentage = Column(Numeric(5, 2), nullable=True)
    gaps_in_education = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentDocument(Base):
    __tablename__ = 'org_school_student_documents'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    document_field_id = Column(Integer, nullable=False)
    document_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_status = Column(String(20), nullable=False, default='Pending')
    verification_remarks = Column(Text, nullable=True)
    document_number = Column(String(100), nullable=True)
    issuing_authority = Column(String(150), nullable=True)
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_required = Column(Boolean, nullable=False, default=True)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    uploaded_by_id = Column(Integer, nullable=False)
    verified_by_id = Column(Integer, nullable=False)

class OrgSchoolStudentInteractionLog(Base):
    __tablename__ = 'org_school_student_interaction_logs'
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    student_id = Column(Integer, nullable=False)
    organization_id = Column(Integer, nullable=False)
    action_type = Column(String(30), nullable=False)
    reason = Column(Text, nullable=True)
    action_taken_by = Column(Integer, nullable=True)
    session_year = Column(String(12), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgClassStudentAttendance(Base):
    __tablename__ = 'org_class_student_attendance'
    __table_args__ = (UniqueConstraint('student_id', 'section_id', 'date'),)
    STATUS_PRESENT = 1
    STATUS_ABSENT = 2
    STATUS_HALF_DAY = 3
    STATUS_LEAVE = 4
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    section_id = Column(BigInteger, nullable=False)
    date = Column(Date, nullable=False)
    status = Column(SmallInteger, nullable=False)
    check_in_time = Column(Time, nullable=True)
    check_out_time = Column(Time, nullable=True)
    marked_by_id = Column(BigInteger, nullable=False)
    remarks = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentLeaveRequest(Base):
    __tablename__ = 'org_student_leave_requests'
    LEAVE_TYPE_SICK = 1
    LEAVE_TYPE_CASUAL = 2
    LEAVE_TYPE_MEDICAL = 3
    LEAVE_TYPE_FAMILY = 4
    LEAVE_TYPE_OTHER = 5
    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CANCELLED = 4
    DURATION_FULL_DAY = 1
    DURATION_HALF_DAY = 2
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(SmallInteger, nullable=False)
    reason = Column(Text, nullable=False)
    attachments = Column(JSON, nullable=False, default=list)
    status = Column(SmallInteger, nullable=False, default=1)
    duration = Column(SmallInteger, nullable=False, default=1)
    requested_by_id = Column(BigInteger, nullable=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_by_id = Column(BigInteger, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_remarks = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

class StudentDiaryEntry(Base):
    __tablename__ = 'org_student_diary_entries'
    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    category = Column(SmallInteger, nullable=False, index=True)
    target_type = Column(SmallInteger, nullable=False, index=True)
    target_id = Column(BigInteger, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)
    reference_type = Column(SmallInteger, nullable=False, index=True, default=0)
    reference_id = Column(BigInteger, nullable=True)
    publish_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_published = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    published_by_id = Column(BigInteger, nullable=True)
    created_by_id = Column(BigInteger, nullable=True)
    updated_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentHouse(Base):
    __tablename__ = 'org_student_houses'
    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'academic_year',
            'name',
            name='uniq_student_house_name_year',
        ),
        UniqueConstraint(
            'organization_id',
            'academic_year',
            'code',
            name='uniq_student_house_code_year',
        ),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(30), nullable=False)
    color_code = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    academic_year = Column(String(20), nullable=False, index=True)
    house_master_id = Column(BigInteger, nullable=True)
    capacity = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(BigInteger, nullable=True)
    updated_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentHouseAssignment(Base):
    __tablename__ = 'org_student_house_assignments'
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_TRANSFERRED = 3
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    house_id = Column(BigInteger, nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    status = Column(SmallInteger, nullable=False, index=True, default=1)
    assigned_on = Column(Date, nullable=False)
    ended_on = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    assigned_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentGroup(Base):
    __tablename__ = 'org_student_groups'
    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'academic_year',
            'name',
            name='uniq_student_group_name_year',
        ),
        UniqueConstraint(
            'organization_id',
            'academic_year',
            'code',
            name='uniq_student_group_code_year',
        ),
    )
    TYPE_CLUB = 1
    TYPE_SPORT = 2
    TYPE_ACTIVITY = 3
    TYPE_ACADEMIC = 4
    TYPE_PROJECT = 5
    TYPE_OTHER = 6
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(30), nullable=False)
    group_type = Column(SmallInteger, nullable=False, index=True, default=6)
    description = Column(Text, nullable=True)
    academic_year = Column(String(20), nullable=False, index=True)
    coordinator_id = Column(BigInteger, nullable=True)
    capacity = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(BigInteger, nullable=True)
    updated_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentGroupAssignment(Base):
    __tablename__ = 'org_student_group_assignments'
    ROLE_MEMBER = 1
    ROLE_LEADER = 2
    ROLE_CAPTAIN = 3
    ROLE_SECRETARY = 4
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    group_id = Column(BigInteger, nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    role = Column(SmallInteger, nullable=False, default=1)
    status = Column(SmallInteger, nullable=False, index=True, default=1)
    joined_on = Column(Date, nullable=False)
    left_on = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    assigned_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentWithdrawalRequest(Base):
    __tablename__ = 'org_student_withdrawal_requests'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    request_type = Column(SmallInteger, nullable=False)
    requested_exit_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(SmallInteger, nullable=False, index=True)
    requested_by_id = Column(BigInteger, nullable=True)
    requested_at = Column(DateTime, nullable=False, server_default=func.now())
    reviewed_by_id = Column(BigInteger, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_remarks = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentClearance(Base):
    __tablename__ = 'org_student_clearances'
    __table_args__ = (
        UniqueConstraint(
            'withdrawal_id',
            'clearance_type',
            name='uniq_withdrawal_clearance_type',
        ),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    withdrawal_id = Column(BigInteger, nullable=False)
    clearance_type = Column(SmallInteger, nullable=False)
    status = Column(SmallInteger, nullable=False, index=True)
    remarks = Column(Text, nullable=True)
    metadata_json = Column('metadata', JSON, nullable=False, default=dict)
    cleared_by_id = Column(BigInteger, nullable=True)
    cleared_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentTransferCertificate(Base):
    __tablename__ = 'org_student_transfer_certificates'
    __table_args__ = (
        UniqueConstraint(
            'organization_id',
            'certificate_number',
            name='uniq_org_tc_number',
        ),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    withdrawal_id = Column(BigInteger, nullable=False, unique=True)
    student_id = Column(BigInteger, nullable=False)
    certificate_number = Column(String(100), nullable=False)
    issue_date = Column(Date, nullable=False)
    certificate_url = Column(String(500), nullable=True)
    snapshot = Column(JSON, nullable=False, default=dict)
    revision = Column(Integer, nullable=False, default=1)
    issued_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentExitAuditLog(Base):
    __tablename__ = 'org_student_exit_audit_logs'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    withdrawal_id = Column(BigInteger, nullable=False)
    action = Column(String(50), nullable=False)
    from_status = Column(SmallInteger, nullable=True)
    to_status = Column(SmallInteger, nullable=True)
    remarks = Column(Text, nullable=True)
    metadata_json = Column('metadata', JSON, nullable=False, default=dict)
    action_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

class OrgStudentBehaviorIncident(Base):
    __tablename__ = 'org_student_behavior_incidents'
    TYPE_POSITIVE = 1
    TYPE_NEGATIVE = 2
    TYPE_BULLYING = 3
    TYPE_SAFETY = 4
    TYPE_PEER_CONFLICT = 5
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
    SEVERITY_LOW = 1
    SEVERITY_MEDIUM = 2
    SEVERITY_HIGH = 3
    SEVERITY_CRITICAL = 4
    STATUS_REPORTED = 1
    STATUS_UNDER_REVIEW = 2
    STATUS_ACTION_TAKEN = 3
    STATUS_RESOLVED = 4
    STATUS_CLOSED = 5
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    incident_type = Column(SmallInteger, nullable=False, index=True)
    category = Column(SmallInteger, nullable=False, index=True, default=99)
    severity = Column(SmallInteger, nullable=False, index=True, default=1)
    incident_at = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    reported_by_id = Column(BigInteger, nullable=True)
    assigned_to_id = Column(BigInteger, nullable=True)
    status = Column(SmallInteger, nullable=False, index=True, default=1)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    metadata_json = Column('metadata', JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentBehaviorParticipant(Base):
    __tablename__ = 'org_student_behavior_participants'
    __table_args__ = (
        UniqueConstraint(
            'incident_id',
            'student_id',
            'role',
            name='uniq_behavior_incident_student_role',
        ),
    )
    ROLE_PRIMARY = 1
    ROLE_VICTIM = 2
    ROLE_ACCUSED = 3
    ROLE_WITNESS = 4
    ROLE_REPORTER = 5
    ROLE_MEDIATOR = 6
    ROLE_OTHER = 99
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    incident_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    role = Column(SmallInteger, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

class OrgStudentBehaviorAction(Base):
    __tablename__ = 'org_student_behavior_actions'
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
    STATUS_PENDING = 1
    STATUS_IN_PROGRESS = 2
    STATUS_COMPLETED = 3
    STATUS_CANCELLED = 4
    CONFIDENTIALITY_NORMAL = 1
    CONFIDENTIALITY_RESTRICTED = 2
    CONFIDENTIALITY_CONFIDENTIAL = 3
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    incident_id = Column(BigInteger, nullable=True)
    student_id = Column(BigInteger, nullable=False)
    action_type = Column(SmallInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    action_status = Column(SmallInteger, nullable=False, index=True, default=1)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assigned_to_id = Column(BigInteger, nullable=True)
    created_by_id = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)
    confidentiality_level = Column(SmallInteger, nullable=False, default=1)
    metadata_json = Column('metadata', JSON, nullable=False, default=dict)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class OrgStudentBehaviorPointLog(Base):
    __tablename__ = 'org_student_behavior_point_logs'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    incident_id = Column(BigInteger, nullable=True)
    action_id = Column(BigInteger, nullable=True)
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

class OrgStudentBehaviorNotificationLog(Base):
    __tablename__ = 'org_student_behavior_notification_logs'
    CHANNEL_EMAIL = 1
    CHANNEL_SMS = 2
    CHANNEL_WHATSAPP = 3
    CHANNEL_PUSH = 4
    STATUS_PENDING = 1
    STATUS_SENT = 2
    STATUS_FAILED = 3
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False)
    incident_id = Column(BigInteger, nullable=True)
    action_id = Column(BigInteger, nullable=True)
    channel = Column(SmallInteger, nullable=False, index=True)
    recipient_name = Column(String(150), nullable=True)
    recipient_contact = Column(String(255), nullable=False)
    status = Column(SmallInteger, nullable=False, index=True, default=1)
    message = Column(Text, nullable=True)
    metadata_json = Column('metadata', JSON, nullable=False, default=dict)
    sent_at = Column(DateTime, nullable=True)
    created_by_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
__all__ = [
    "OrgSchoolStudent",
    "StudentParent",
    "SchoolStudentParent",
    "OrgSchoolStudentConsent",
    "OrgSchoolStudentFieldOption",
    "OrgSchoolStudentAddress",
    "OrgSchoolStudentMedical",
    "OrgSchoolStudentFamily",
    "OrgSchoolStudentAcademicHistory",
    "OrgSchoolStudentDocument",
    "OrgSchoolStudentInteractionLog",
    "OrgClassStudentAttendance",
    "OrgStudentLeaveRequest",
    "StudentDiaryEntry",
    "OrgStudentHouse",
    "OrgStudentHouseAssignment",
    "OrgStudentGroup",
    "OrgStudentGroupAssignment",
    "OrgStudentWithdrawalRequest",
    "OrgStudentClearance",
    "OrgStudentTransferCertificate",
    "OrgStudentExitAuditLog",
    "OrgStudentBehaviorIncident",
    "OrgStudentBehaviorParticipant",
    "OrgStudentBehaviorAction",
    "OrgStudentBehaviorPointLog",
    "OrgStudentBehaviorNotificationLog",
]
