"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""


from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.sql import func

from core.database import Base
from core.model_defaults import utc_now


class OrgLibrarySettings(Base):
    __tablename__ = 'org_library_settings'

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        BigInteger,
        ForeignKey('org_library_branches.id'),
        nullable=False,
        unique=True,
    )
    default_issue_days = Column(mysql.INTEGER(unsigned=True), nullable=False, default=14)
    max_renewals = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=2)
    max_books_per_member = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=3)
    allow_student_members = Column(Boolean, nullable=False, default=True)
    allow_staff_members = Column(Boolean, nullable=False, default=True)
    allow_external_members = Column(Boolean, nullable=False, default=False)
    fine_per_day = Column(Numeric(10, 2), nullable=False, default=0)
    grace_period_days = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=0)
    allow_same_day_issue_return = Column(Boolean, nullable=False, default=True)
    allow_overdue_renewal = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryBranch(Base):
    __tablename__ = 'org_library_branches'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uniq_org_library_branch_code'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    address = Column(mysql.LONGTEXT, nullable=True)
    location_name = Column(String(255), nullable=True)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryFloor(Base):
    __tablename__ = 'org_library_floors'
    __table_args__ = (
        UniqueConstraint('branch_id', 'floor_no', name='uniq_library_floor_branch_number'),
        UniqueConstraint('branch_id', 'code', name='uniq_library_floor_branch_code'),
        Index('org_library_organiz_b10f8c_idx', 'organization_id', 'branch_id', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        BigInteger,
        ForeignKey('org_library_branches.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)
    floor_no = Column(Integer, nullable=False)
    code = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibrarySection(Base):
    __tablename__ = 'org_library_sections'
    __table_args__ = (
        UniqueConstraint('floor_id', 'code', name='uniq_library_section_floor_code'),
        Index('org_library_organiz_b52757_idx', 'organization_id', 'floor_id', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    floor_id = Column(
        BigInteger,
        ForeignKey('org_library_floors.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryRack(Base):
    __tablename__ = 'org_library_racks'
    __table_args__ = (
        UniqueConstraint('section_id', 'code', name='uniq_library_rack_section_code'),
        Index('org_library_organiz_e4d776_idx', 'organization_id', 'section_id', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    section_id = Column(
        BigInteger,
        ForeignKey('org_library_sections.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryShelf(Base):
    __tablename__ = 'org_library_shelves'
    __table_args__ = (
        UniqueConstraint('rack_id', 'code', name='uniq_library_shelf_rack_code'),
        Index('org_library_organiz_bf5521_idx', 'organization_id', 'rack_id', 'is_active'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    rack_id = Column(BigInteger, ForeignKey('org_library_racks.id'), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryCategory(Base):
    __tablename__ = 'org_library_categories'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uniq_org_library_category_code'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    parent_id = Column(
        BigInteger,
        ForeignKey('org_library_categories.id'),
        nullable=True,
        index=True,
    )
    description = Column(mysql.LONGTEXT, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryPublisher(Base):
    __tablename__ = 'org_library_publishers'
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uniq_org_library_publisher_name'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(254), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(mysql.LONGTEXT, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryBook(Base):
    __tablename__ = 'org_library_books'
    __table_args__ = (
        Index('org_library_organiz_4e645d_idx', 'organization_id', 'title'),
        Index('org_library_organiz_fdf61c_idx', 'organization_id', 'isbn_13'),
        Index('org_library_organiz_b2cbca_idx', 'organization_id', 'accession_no'),
    )

    LANGUAGE_ENGLISH = 1
    LANGUAGE_HINDI = 2
    LANGUAGE_OTHER = 3
    LANGUAGE_CHOICES = ((1, 'English'), (2, 'Hindi'), (3, 'Other'))
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
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    isbn_10 = Column(String(20), nullable=True)
    isbn_13 = Column(String(20), nullable=True)
    accession_no = Column(String(100), nullable=True)
    call_number = Column(String(100), nullable=True)
    edition = Column(String(50), nullable=True)
    language = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    description = Column(mysql.LONGTEXT, nullable=True)
    cover_image = Column(String(255), nullable=True)
    publication_year = Column(mysql.INTEGER(unsigned=True), nullable=True)
    pages = Column(mysql.INTEGER(unsigned=True), nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    category_id = Column(
        BigInteger,
        ForeignKey('org_library_categories.id'),
        nullable=True,
        index=True,
    )
    publisher_id = Column(
        BigInteger,
        ForeignKey('org_library_publishers.id'),
        nullable=True,
        index=True,
    )
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    is_reference_only = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryBookCopy(Base):
    __tablename__ = 'org_library_book_copies'
    __table_args__ = (
        UniqueConstraint('organization_id', 'barcode', name='uniq_org_library_copy_barcode'),
        UniqueConstraint('book_id', 'copy_no', name='uniq_org_library_copy_no'),
    )

    CONDITION_NEW = 1
    CONDITION_GOOD = 2
    CONDITION_FAIR = 3
    CONDITION_DAMAGED = 4
    CONDITION_LOST = 5
    CONDITION_CHOICES = ((1, 'New'), (2, 'Good'), (3, 'Fair'), (4, 'Damaged'), (5, 'Lost'))
    STATUS_AVAILABLE = 1
    STATUS_ISSUED = 2
    STATUS_MAINTENANCE = 4
    STATUS_LOST = 5
    STATUS_DISCARDED = 6
    STATUS_CHOICES = (
        (1, 'Available'),
        (2, 'Issued'),
        (4, 'Maintenance'),
        (5, 'Lost'),
        (6, 'Discarded'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    book_id = Column(BigInteger, ForeignKey('org_library_books.id'), nullable=False, index=True)
    barcode = Column(String(100), nullable=False)
    copy_no = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    branch_id = Column(
        BigInteger,
        ForeignKey('org_library_branches.id'),
        nullable=True,
        index=True,
    )
    shelf_id = Column(
        BigInteger,
        ForeignKey('org_library_shelves.id'),
        nullable=True,
        index=True,
    )
    condition = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    acquired_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryMember(Base):
    __tablename__ = 'org_library_members'
    __table_args__ = (
        UniqueConstraint('organization_id', 'membership_no', name='uniq_org_library_membership_no'),
    )

    MEMBER_TYPE_STUDENT = 1
    MEMBER_TYPE_STAFF = 2
    MEMBER_TYPE_EXTERNAL = 3
    MEMBER_TYPE_CHOICES = ((1, 'Student'), (2, 'Staff'), (3, 'External'))
    STATUS_ACTIVE = 1
    STATUS_SUSPENDED = 2
    STATUS_EXPIRED = 3
    STATUS_CHOICES = ((1, 'Active'), (2, 'Suspended'), (3, 'Expired'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    branch_id = Column(
        BigInteger,
        ForeignKey('org_library_branches.id'),
        nullable=True,
        index=True,
    )
    member_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    student_id = Column(BigInteger, nullable=True)
    staff_id = Column(BigInteger, nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(254), nullable=True)
    phone = Column(String(50), nullable=True)
    membership_no = Column(String(100), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    current_books_issued = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=0)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    notes = Column(mysql.LONGTEXT, nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryLoan(Base):
    __tablename__ = 'org_library_loans'
    __table_args__ = (
        Index('org_library_organiz_c7fd44_idx', 'organization_id', 'status'),
        Index('org_library_member__5cff36_idx', 'member_id', 'status'),
        Index('org_library_copy_id_4a74eb_idx', 'copy_id', 'status'),
    )

    STATUS_ISSUED = 1
    STATUS_RETURNED = 2
    STATUS_OVERDUE = 3
    STATUS_LOST = 4
    STATUS_CANCELLED = 5
    STATUS_CHOICES = (
        (1, 'Issued'),
        (2, 'Returned'),
        (3, 'Overdue'),
        (4, 'Lost'),
        (5, 'Cancelled'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    copy_id = Column(
        BigInteger,
        ForeignKey('org_library_book_copies.id'),
        nullable=False,
        index=True,
    )
    member_id = Column(
        BigInteger,
        ForeignKey('org_library_members.id'),
        nullable=False,
        index=True,
    )
    issued_by_id = Column(Integer, nullable=True, index=True)
    returned_by_id = Column(Integer, nullable=True, index=True)
    issue_date = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    due_date = Column(mysql.DATETIME(fsp=6), nullable=False)
    return_date = Column(mysql.DATETIME(fsp=6), nullable=True)
    renew_count = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=0)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    issue_notes = Column(mysql.LONGTEXT, nullable=True)
    return_notes = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryFine(Base):
    __tablename__ = 'org_library_fines'
    __table_args__ = (
        Index('org_library_organiz_3fe924_idx', 'organization_id', 'status'),
        Index('org_library_member__8d142d_idx', 'member_id', 'status'),
    )

    STATUS_PENDING = 1
    STATUS_PAID = 2
    STATUS_WAIVED = 3
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Paid'), (3, 'Waived'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    member_id = Column(
        BigInteger,
        ForeignKey('org_library_members.id'),
        nullable=False,
        index=True,
    )
    loan_id = Column(BigInteger, ForeignKey('org_library_loans.id'), nullable=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False, default=0)
    reason = Column(String(255), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    due_date = Column(Date, nullable=True)
    paid_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    waived_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryMembershipRenewal(Base):
    __tablename__ = 'org_library_membership_renewals'
    __table_args__ = (
        Index('org_library_organiz_05beea_idx', 'organization_id', 'status'),
        Index('org_library_member__b0d896_idx', 'member_id', 'status'),
    )

    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Approved'), (3, 'Rejected'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    member_id = Column(
        BigInteger,
        ForeignKey('org_library_members.id'),
        nullable=False,
        index=True,
    )
    requested_by_id = Column(Integer, nullable=True, index=True)
    reviewed_by_id = Column(Integer, nullable=True, index=True)
    old_valid_until = Column(Date, nullable=True)
    new_valid_until = Column(Date, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    requested_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    reviewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryFineWaiver(Base):
    __tablename__ = 'org_library_fine_waivers'
    __table_args__ = (
        Index('org_library_organiz_9f5550_idx', 'organization_id', 'status'),
        Index('org_library_fine_id_b4d9d3_idx', 'fine_id', 'status'),
    )

    STATUS_PENDING = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Approved'), (3, 'Rejected'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    fine_id = Column(BigInteger, ForeignKey('org_library_fines.id'), nullable=False, index=True)
    requested_by_id = Column(Integer, nullable=True, index=True)
    reviewed_by_id = Column(Integer, nullable=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    requested_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    reviewed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class OrgLibraryLoanRenewal(Base):
    __tablename__ = 'org_library_loan_renewals'
    __table_args__ = (
        UniqueConstraint('loan_id', 'renewal_no', name='uniq_org_library_loan_renewal_no'),
        Index('org_library_organiz_fc7c50_idx', 'organization_id', 'loan_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    loan_id = Column(BigInteger, ForeignKey('org_library_loans.id'), nullable=False, index=True)
    renewed_by_id = Column(Integer, nullable=True, index=True)
    old_due_date = Column(mysql.DATETIME(fsp=6), nullable=False)
    new_due_date = Column(mysql.DATETIME(fsp=6), nullable=False)
    renewal_no = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgLibraryFinePayment(Base):
    __tablename__ = 'org_library_fine_payments'
    __table_args__ = (
        UniqueConstraint('fine_id', 'payment_reference', name='uniq_org_library_fine_payment_reference'),
        Index('org_library_organiz_b02c75_idx', 'organization_id', 'status'),
        Index('org_library_fine_id_c391e0_idx', 'fine_id', 'status'),
    )

    STATUS_PENDING = 1
    STATUS_PAID = 2
    STATUS_FAILED = 3
    STATUS_CHOICES = ((1, 'Pending'), (2, 'Paid'), (3, 'Failed'))

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey('organizations.id'),
        nullable=False,
        index=True,
    )
    fine_id = Column(BigInteger, ForeignKey('org_library_fines.id'), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_reference = Column(String(100), nullable=True)
    paid_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    remarks = Column(mysql.LONGTEXT, nullable=True)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


# Existing service-only mapping; retained pending a separate usage/schema migration.
class OrgLibraryReservation(Base):
    __tablename__ = 'org_library_reservations'
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(Integer)
    book_id = Column(BigInteger, ForeignKey('org_library_books.id'))
    member_id = Column(BigInteger, ForeignKey('org_library_members.id'))
    queue_position = Column(Integer)
    reserved_at = Column(DateTime)
    expires_at = Column(DateTime)
    status = Column(Integer)
    fulfilled_copy_id = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

__all__ = [
    'OrgLibrarySettings',
    'OrgLibraryBranch',
    'OrgLibraryFloor',
    'OrgLibrarySection',
    'OrgLibraryRack',
    'OrgLibraryShelf',
    'OrgLibraryCategory',
    'OrgLibraryPublisher',
    'OrgLibraryBook',
    'OrgLibraryBookCopy',
    'OrgLibraryMember',
    'OrgLibraryLoan',
    'OrgLibraryFine',
    'OrgLibraryMembershipRenewal',
    'OrgLibraryFineWaiver',
    'OrgLibraryLoanRenewal',
    'OrgLibraryFinePayment',
    'OrgLibraryReservation',
]
