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
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql

from core.database import Base
from core.model_defaults import utc_now, utc_today


class OrgHostel(Base):
    __tablename__ = 'org_hostels'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uniq_org_hostel_code'),
        Index('org_hostels_organiz_7ed045_idx', 'organization_id', 'status'),
        Index('org_hostels_organiz_626005_idx', 'organization_id', 'is_active'),
    )

    TYPE_BOYS = 1
    TYPE_GIRLS = 2
    TYPE_STAFF = 4
    TYPE_CHOICES = ((1, 'Boys'), (2, 'Girls'), (4, 'Staff'))
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_MAINTENANCE = 3
    STATUS_CLOSED = 4
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'), (3, 'Maintenance'), (4, 'Closed'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False)
    hostel_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    description = Column(mysql.LONGTEXT, nullable=True)
    address = Column(mysql.LONGTEXT, nullable=True)
    contact_number = Column(String(30), nullable=True)
    total_capacity = Column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelBlock(Base):
    __tablename__ = 'org_hostel_blocks'
    __table_args__ = (
        UniqueConstraint('hostel_id', 'code', name='uniq_hostel_block_code'),
        Index('org_hostel__organiz_7a25d9_idx', 'organization_id', 'status'),
        Index('org_hostel__hostel__c97a7d_idx', 'hostel_id', 'is_active'),
    )

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_MAINTENANCE = 3
    STATUS_CLOSED = 4
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'), (3, 'Maintenance'), (4, 'Closed'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    hostel_id = Column(BigInteger, ForeignKey('org_hostels.id'), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelFloor(Base):
    __tablename__ = 'org_hostel_floors'
    __table_args__ = (
        UniqueConstraint('block_id', 'floor_no', name='uniq_block_floor_no'),
        Index('org_hostel__organiz_8079a5_idx', 'organization_id', 'status'),
        Index('org_hostel__block_i_a99a67_idx', 'block_id', 'status'),
    )

    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_MAINTENANCE = 3
    STATUS_CLOSED = 4
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'), (3, 'Maintenance'), (4, 'Closed'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    block_id = Column(
        BigInteger,
        ForeignKey('org_hostel_blocks.id'),
        nullable=False,
        index=True,
    )
    floor_no = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelRoom(Base):
    __tablename__ = 'org_hostel_rooms'
    __table_args__ = (
        UniqueConstraint('floor_id', 'room_no', name='uniq_floor_room_no'),
        Index('org_hostel__organiz_82fcc2_idx', 'organization_id', 'status'),
        Index('org_hostel__floor_i_fd9448_idx', 'floor_id', 'status'),
        Index('org_hostel__room_ty_f18ffa_idx', 'room_type', 'gender_allowed'),
    )

    TYPE_SINGLE = 1
    TYPE_DOUBLE = 2
    TYPE_TRIPLE = 3
    TYPE_DORMITORY = 4
    TYPE_STAFF = 5
    TYPE_CHOICES = (
        (1, 'Single'),
        (2, 'Double Sharing'),
        (3, 'Triple Sharing'),
        (4, 'Dormitory'),
        (5, 'Staff'),
    )
    GENDER_ANY = 1
    GENDER_MALE = 2
    GENDER_FEMALE = 3
    GENDER_OTHER = 4
    GENDER_CHOICES = ((1, 'Any'), (2, 'Male'), (3, 'Female'), (4, 'Other'))
    STATUS_AVAILABLE = 1
    STATUS_OCCUPIED = 2
    STATUS_MAINTENANCE = 3
    STATUS_RESERVED = 4
    STATUS_CLOSED = 5
    STATUS_CHOICES = (
        (1, 'Available'),
        (2, 'Occupied'),
        (3, 'Maintenance'),
        (4, 'Reserved'),
        (5, 'Closed'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    floor_id = Column(
        BigInteger,
        ForeignKey('org_hostel_floors.id'),
        nullable=False,
        index=True,
    )
    room_no = Column(String(50), nullable=False)
    room_name = Column(String(150), nullable=True)
    room_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    gender_allowed = Column(
        mysql.SMALLINT(unsigned=True),
        nullable=False,
        index=True,
        default=1,
    )
    sharing_capacity = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    monthly_fee = Column(Numeric(12, 2), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelBed(Base):
    __tablename__ = 'org_hostel_beds'
    __table_args__ = (
        UniqueConstraint('room_id', 'bed_no', name='uniq_room_bed_no'),
        Index('org_hostel__organiz_2812a8_idx', 'organization_id', 'status'),
        Index('org_hostel__room_id_79b99a_idx', 'room_id', 'status'),
    )

    STATUS_AVAILABLE = 1
    STATUS_ALLOCATED = 2
    STATUS_MAINTENANCE = 3
    STATUS_BLOCKED = 4
    STATUS_CHOICES = ((1, 'Available'), (2, 'Allocated'), (3, 'Maintenance'), (4, 'Blocked'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    room_id = Column(BigInteger, ForeignKey('org_hostel_rooms.id'), nullable=False, index=True)
    bed_no = Column(String(50), nullable=False)
    bed_label = Column(String(100), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_active = Column(Boolean, nullable=False, index=True, default=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelStudentAllocation(Base):
    __tablename__ = 'org_hostel_student_allocations'
    __table_args__ = (
        UniqueConstraint('organization_id', 'allocation_no', name='uniq_org_hostel_alloc_no'),
        Index('org_hostel__organiz_a3e7a2_idx', 'organization_id', 'status'),
        Index('org_hostel__organiz_33fa0f_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_hostel__student_ea132c_idx', 'student_id', 'status', 'is_current'),
        Index('org_hostel__bed_id_5ce63b_idx', 'bed_id', 'status', 'is_current'),
    )

    TYPE_REGULAR = 1
    TYPE_TEMPORARY = 2
    TYPE_EMERGENCY = 3
    TYPE_CHOICES = ((1, 'Regular'), (2, 'Temporary'), (3, 'Emergency'))
    STATUS_ACTIVE = 1
    STATUS_TRANSFERRED = 2
    STATUS_CHECKED_OUT = 3
    STATUS_CANCELLED = 4
    STATUS_CHOICES = ((1, 'Active'), (2, 'Transferred'), (3, 'Checked Out'), (4, 'Cancelled'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    allocation_no = Column(String(100), nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=False,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    bed_id = Column(BigInteger, ForeignKey('org_hostel_beds.id'), nullable=False, index=True)
    allocation_type = Column(
        mysql.SMALLINT(unsigned=True),
        nullable=False,
        index=True,
        default=1,
    )
    allocation_date = Column(Date, nullable=False, index=True, default=utc_today)
    expected_checkout_date = Column(Date, nullable=True)
    actual_checkout_date = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_current = Column(Boolean, nullable=False, index=True, default=True)
    previous_allocation_id = Column(
        BigInteger,
        ForeignKey('org_hostel_student_allocations.id'),
        nullable=True,
        index=True,
    )
    allocated_by_id = Column(Integer, nullable=True, index=True)
    checkout_by_id = Column(Integer, nullable=True, index=True)
    checkout_reason = Column(mysql.LONGTEXT, nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)


class OrgHostelWardenAssignment(Base):
    __tablename__ = 'org_hostel_warden_assignments'
    __table_args__ = (
        Index('org_hostel__organiz_6e807c_idx', 'organization_id', 'status'),
        Index('org_hostel__staff_i_a57944_idx', 'staff_id', 'status'),
        Index('org_hostel__hostel__51e245_idx', 'hostel_id', 'status'),
        Index('org_hostel__block_i_abdb0b_idx', 'block_id', 'status'),
        Index('org_hostel__floor_i_5f08ab_idx', 'floor_id', 'status'),
    )

    SCOPE_HOSTEL = 1
    SCOPE_BLOCK = 2
    SCOPE_FLOOR = 3
    SCOPE_MESS = 4
    SCOPE_NIGHT_DUTY = 5
    SCOPE_CHOICES = ((1, 'Hostel'), (2, 'Block'), (3, 'Floor'), (4, 'Mess'), (5, 'Night Duty'))
    STATUS_ACTIVE = 1
    STATUS_INACTIVE = 2
    STATUS_ENDED = 3
    STATUS_CHOICES = ((1, 'Active'), (2, 'Inactive'), (3, 'Ended'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    staff_id = Column(Integer, nullable=False, index=True)
    hostel_id = Column(BigInteger, ForeignKey('org_hostels.id'), nullable=True, index=True)
    block_id = Column(BigInteger, ForeignKey('org_hostel_blocks.id'), nullable=True, index=True)
    floor_id = Column(BigInteger, ForeignKey('org_hostel_floors.id'), nullable=True, index=True)
    scope = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    start_date = Column(Date, nullable=False, default=utc_today)
    end_date = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelComplaint(Base):
    __tablename__ = 'org_hostel_complaints'
    __table_args__ = (
        UniqueConstraint('organization_id', 'complaint_no', name='uniq_org_hostel_complaint_no'),
        Index('org_hostel__organiz_d1e5a8_idx', 'organization_id', 'status'),
        Index('org_hostel__organiz_ff7adf_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_hostel__student_0eb2c7_idx', 'student_id', 'status'),
        Index('org_hostel__target__f0cefe_idx', 'target_type', 'status'),
        Index('org_hostel__assigne_627aed_idx', 'assigned_to_id', 'status'),
    )

    TARGET_HOSTEL = 1
    TARGET_BLOCK = 2
    TARGET_FLOOR = 3
    TARGET_ROOM = 4
    TARGET_BED = 5
    TARGET_CHOICES = ((1, 'Hostel'), (2, 'Block'), (3, 'Floor'), (4, 'Room'), (5, 'Bed'))
    CATEGORY_MAINTENANCE = 1
    CATEGORY_CLEANLINESS = 2
    CATEGORY_MESS_FOOD = 3
    CATEGORY_SECURITY = 4
    CATEGORY_ROOMMATE = 5
    CATEGORY_DISCIPLINE = 6
    CATEGORY_OTHER = 99
    CATEGORY_CHOICES = (
        (1, 'Maintenance'),
        (2, 'Cleanliness'),
        (3, 'Mess/Food'),
        (4, 'Security'),
        (5, 'Roommate'),
        (6, 'Discipline'),
        (99, 'Other'),
    )
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4
    PRIORITY_CHOICES = ((1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Urgent'))
    STATUS_OPEN = 1
    STATUS_ASSIGNED = 2
    STATUS_IN_PROGRESS = 3
    STATUS_RESOLVED = 4
    STATUS_REJECTED = 5
    STATUS_REOPENED = 6
    STATUS_CHOICES = (
        (1, 'Open'),
        (2, 'Assigned'),
        (3, 'In Progress'),
        (4, 'Resolved'),
        (5, 'Rejected'),
        (6, 'Reopened'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    complaint_no = Column(String(100), nullable=False)
    student_id = Column(
        BigInteger,
        ForeignKey('org_school_students.id'),
        nullable=True,
        index=True,
    )
    academic_year = Column(String(20), nullable=False, index=True)
    allocation_id = Column(
        BigInteger,
        ForeignKey('org_hostel_student_allocations.id'),
        nullable=True,
        index=True,
    )
    target_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    hostel_id = Column(BigInteger, ForeignKey('org_hostels.id'), nullable=True, index=True)
    block_id = Column(BigInteger, ForeignKey('org_hostel_blocks.id'), nullable=True, index=True)
    floor_id = Column(BigInteger, ForeignKey('org_hostel_floors.id'), nullable=True, index=True)
    room_id = Column(BigInteger, ForeignKey('org_hostel_rooms.id'), nullable=True, index=True)
    bed_id = Column(BigInteger, ForeignKey('org_hostel_beds.id'), nullable=True, index=True)
    category = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    priority = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    title = Column(String(255), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    assigned_to_id = Column(Integer, nullable=True, index=True)
    assigned_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    resolved_by_id = Column(Integer, nullable=True, index=True)
    resolved_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    resolution_notes = Column(mysql.LONGTEXT, nullable=True)
    rejected_by_id = Column(Integer, nullable=True, index=True)
    rejected_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    rejection_reason = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelComplaintActionLog(Base):
    __tablename__ = 'org_hostel_complaint_action_logs'
    __table_args__ = (
        Index('org_hostel__complai_0afa43_idx', 'complaint_id', 'action'),
        Index('org_hostel__action_15d380_idx', 'action', 'created_at'),
    )

    ACTION_CREATED = 1
    ACTION_ASSIGNED = 2
    ACTION_STATUS_CHANGED = 3
    ACTION_COMMENTED = 4
    ACTION_RESOLVED = 5
    ACTION_REJECTED = 6
    ACTION_REOPENED = 7
    ACTION_CHOICES = (
        (1, 'Created'),
        (2, 'Assigned'),
        (3, 'Status Changed'),
        (4, 'Commented'),
        (5, 'Resolved'),
        (6, 'Rejected'),
        (7, 'Reopened'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    complaint_id = Column(
        BigInteger,
        ForeignKey('org_hostel_complaints.id'),
        nullable=False,
        index=True,
    )
    action = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    previous_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    new_status = Column(mysql.SMALLINT(unsigned=True), nullable=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    metadata_json = Column('metadata', JSON(none_as_null=True), nullable=False, default=dict)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgHostelMessPlan(Base):
    __tablename__ = 'org_hostel_mess_plans'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uniq_org_hostel_mess_plan_code'),
        Index('org_hostel__organiz_2f189f_idx', 'organization_id', 'status'),
        Index('org_hostel__hostel__ef480e_idx', 'hostel_id', 'status'),
    )

    TYPE_REGULAR = 1
    TYPE_SPECIAL = 2
    TYPE_DIET = 3
    TYPE_CHOICES = ((1, 'Regular'), (2, 'Special'), (3, 'Diet'))
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_ARCHIVED = 3
    STATUS_CHOICES = ((1, 'Draft'), (2, 'Published'), (3, 'Archived'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    hostel_id = Column(BigInteger, ForeignKey('org_hostels.id'), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False)
    plan_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    applicable_from = Column(Date, nullable=True)
    applicable_to = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    is_default = Column(Boolean, nullable=False, default=False)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelMessMenu(Base):
    __tablename__ = 'org_hostel_mess_menus'
    __table_args__ = (
        Index('org_hostel__organiz_bc0b5f_idx', 'organization_id', 'status'),
        Index('org_hostel__plan_id_dd69bf_idx', 'plan_id', 'meal_type'),
        Index('org_hostel__menu_da_4b6fef_idx', 'menu_date', 'meal_type'),
        Index('org_hostel__day_of__678da8_idx', 'day_of_week', 'meal_type'),
    )

    MEAL_BREAKFAST = 1
    MEAL_LUNCH = 2
    MEAL_SNACKS = 3
    MEAL_DINNER = 4
    MEAL_CHOICES = ((1, 'Breakfast'), (2, 'Lunch'), (3, 'Snacks'), (4, 'Dinner'))
    DAY_MONDAY = 1
    DAY_TUESDAY = 2
    DAY_WEDNESDAY = 3
    DAY_THURSDAY = 4
    DAY_FRIDAY = 5
    DAY_SATURDAY = 6
    DAY_SUNDAY = 7
    DAY_CHOICES = (
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    )
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_CANCELLED = 3
    STATUS_CHOICES = ((1, 'Draft'), (2, 'Published'), (3, 'Cancelled'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        BigInteger,
        ForeignKey('org_hostel_mess_plans.id'),
        nullable=False,
        index=True,
    )
    menu_date = Column(Date, nullable=True, index=True)
    day_of_week = Column(mysql.SMALLINT(unsigned=True), nullable=True, index=True)
    meal_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True)
    title = Column(String(150), nullable=True)
    items = Column(JSON(none_as_null=True), nullable=False, default=list)
    notes = Column(mysql.LONGTEXT, nullable=True)
    calories = Column(mysql.INTEGER(unsigned=True), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    published_by_id = Column(Integer, nullable=True, index=True)
    published_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgHostelAttendance(Base):
    __tablename__ = 'org_hostel_attendance'
    __table_args__ = (
        UniqueConstraint('allocation_id', 'attendance_date', 'session', name='uniq_hostel_attendance_log'),
        Index('org_hostel__organiz_0993fd_idx', 'organization_id', 'attendance_date', 'session'),
        Index('org_hostel__organiz_d0c3e6_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_hostel__student_5e889e_idx', 'student_id', 'attendance_date'),
        Index('org_hostel__allocat_2f8e44_idx', 'allocation_id', 'status'),
    )

    SESSION_MORNING = 1
    SESSION_NIGHT = 2
    SESSION_CHOICES = ((1, 'Morning'), (2, 'Night'))
    STATUS_PRESENT = 1
    STATUS_ABSENT = 2
    STATUS_LEAVE = 3
    STATUS_LATE = 4
    STATUS_OUTING = 5
    STATUS_CHOICES = ((1, 'Present'), (2, 'Absent'), (3, 'Leave'), (4, 'Late'), (5, 'Outing'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    allocation_id = Column(
        BigInteger,
        ForeignKey('org_hostel_student_allocations.id'),
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
    attendance_date = Column(Date, nullable=False, index=True, default=utc_today)
    session = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    marked_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    marked_by_id = Column(Integer, nullable=True, index=True)
    remarks = Column(mysql.LONGTEXT, nullable=True)


class OrgHostelLeaveRequest(Base):
    __tablename__ = 'org_hostel_leave_requests'
    __table_args__ = (
        Index('org_hostel__organiz_df411a_idx', 'organization_id', 'status'),
        Index('org_hostel__organiz_7f34e0_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_hostel__student_c1d8d7_idx', 'student_id', 'status'),
        Index('org_hostel__allocat_474c36_idx', 'allocation_id', 'start_date', 'end_date'),
    )

    TYPE_OUTING = 1
    TYPE_OVERNIGHT = 2
    TYPE_HOME_VISIT = 3
    TYPE_MEDICAL = 4
    TYPE_OTHER = 99
    TYPE_CHOICES = (
        (1, 'Outing'),
        (2, 'Overnight'),
        (3, 'Home Visit'),
        (4, 'Medical'),
        (99, 'Other'),
    )
    DAY_FULL = 1
    DAY_FIRST_HALF = 2
    DAY_SECOND_HALF = 3
    DAY_CHOICES = ((1, 'Full Day'), (2, 'First Half'), (3, 'Second Half'))
    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CANCELLED = 4
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Approved'), (3, 'Rejected'), (4, 'Cancelled'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
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
    allocation_id = Column(
        BigInteger,
        ForeignKey('org_hostel_student_allocations.id'),
        nullable=False,
        index=True,
    )
    leave_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    day_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    start_time = Column(mysql.TIME(fsp=6), nullable=True)
    end_time = Column(mysql.TIME(fsp=6), nullable=True)
    destination = Column(String(255), nullable=True)
    guardian_contact = Column(String(30), nullable=True)
    reason = Column(mysql.LONGTEXT, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    approved_by_id = Column(Integer, nullable=True, index=True)
    approved_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    rejected_by_id = Column(Integer, nullable=True, index=True)
    rejected_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    rejection_reason = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)

__all__ = [
    'OrgHostel',
    'OrgHostelBlock',
    'OrgHostelFloor',
    'OrgHostelRoom',
    'OrgHostelBed',
    'OrgHostelStudentAllocation',
    'OrgHostelWardenAssignment',
    'OrgHostelComplaint',
    'OrgHostelComplaintActionLog',
    'OrgHostelMessPlan',
    'OrgHostelMessMenu',
    'OrgHostelAttendance',
    'OrgHostelLeaveRequest',
]
