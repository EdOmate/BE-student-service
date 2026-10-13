"""SQLAlchemy mappings aligned with the main backend's Django models.

Django migrations own these tables. Staff/payment references without local models
remain scalar IDs; this service does not create or migrate the shared schema.
"""

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from core.model_defaults import utc_now


class OrgSchoolFeeCategory(Base):
    __tablename__ = 'org_school_fee_categories'
    __table_args__ = (
        UniqueConstraint('organization_id', 'code', name='uniq_org_fee_category_code'),
        UniqueConstraint('organization_id', 'name', name='uniq_org_fee_category_name'),
        CheckConstraint('(`is_security_deposit` = 0 OR `is_refundable` = 1)', name='fee_deposit_is_refundable'),
        Index('org_school__organiz_1a3c55_idx', 'organization_id', 'status'),
        Index('org_school__organiz_df0a58_idx', 'organization_id', 'source_type'),
    )

    class SourceType:
        SCHOOL = 'school'
        TRANSPORT = 'transport'
        HOSTEL = 'hostel'
        LIBRARY = 'library'
        ACTIVITY = 'activity'
        OTHER = 'other'
        choices = [
            ('school', 'School'),
            ('transport', 'Transport'),
            ('hostel', 'Hostel'),
            ('library', 'Library'),
            ('activity', 'Activity'),
            ('other', 'Other'),
        ]

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
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    source_type = Column(String(30), nullable=False, default='school')
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_refundable = Column(Boolean, nullable=False, default=False)
    is_security_deposit = Column(Boolean, nullable=False, default=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgSchoolFeeBillingTerms(Base):
    __tablename__ = 'org_school_fee_billing_terms'
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uniq_org_fee_billing_terms_name'),
        CheckConstraint('(`invoice_generation_day` >= 1 AND `invoice_generation_day` <= 31)', name='fee_generation_day_1_31'),
        CheckConstraint('(`due_day` >= 1 AND `due_day` <= 31)', name='fee_due_day_1_31'),
        Index('org_school__organiz_7508f4_idx', 'organization_id', 'status'),
    )

    class MissingDayBehavior:
        LAST_CALENDAR_DAY = 'last_calendar_day'
        NEXT_CALENDAR_DAY = 'next_calendar_day'
        choices = [
            ('last_calendar_day', 'Use last calendar day'),
            ('next_calendar_day', 'Use next calendar day'),
        ]

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
    invoice_generation_day = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    due_day = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=10)
    grace_period_days = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=0)
    missing_day_behavior = Column(String(30), nullable=False, default='last_calendar_day')
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)


class OrgSchoolFeeLateChargePolicy(Base):
    __tablename__ = 'org_school_fee_late_charge_policies'
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='uniq_org_late_charge_policy_name'),
        CheckConstraint('(`flat_amount` IS NULL OR `flat_amount` >= 0.00)', name='late_policy_flat_nonnegative'),
        CheckConstraint('(`per_day_amount` IS NULL OR `per_day_amount` >= 0.00)', name='late_policy_daily_nonnegative'),
        CheckConstraint('(`maximum_amount` IS NULL OR `maximum_amount` >= 0.00)', name='late_policy_max_nonnegative'),
        Index('org_school__organiz_3a72be_idx', 'organization_id', 'status'),
        Index('org_school__organiz_a01b12_idx', 'organization_id', 'policy_type'),
    )

    class PolicyType:
        FLAT = 1
        PER_DAY = 2
        choices = [(1, 'Flat'), (2, 'Per day')]

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
    policy_type = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    flat_amount = Column(Numeric(12, 2), nullable=True)
    per_day_amount = Column(Numeric(12, 2), nullable=True)
    maximum_amount = Column(Numeric(12, 2), nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)


class OrgSchoolFeeStructure(Base):
    __tablename__ = 'org_school_fee_structures'
    __table_args__ = (
        UniqueConstraint('organization_id', 'academic_year', 'class_id', name='uniq_org_class_fee_structure'),
        CheckConstraint('(`effective_until` IS NULL OR `effective_from` IS NULL OR `effective_until` >= `effective_from`)', name='fee_structure_valid_dates'),
        Index('org_school__organiz_fd24b5_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_school__class_i_8a43db_idx', 'class_id', 'academic_year', 'status'),
    )

    class Status:
        DRAFT = 1
        ACTIVE = 2
        INACTIVE = 3
        ARCHIVED = 4
        choices = [(1, 'Draft'), (2, 'Active'), (3, 'Inactive'), (4, 'Archived')]

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
    academic_year = Column(String(20), nullable=False)
    class_id = Column(Integer, ForeignKey('org_school_classes.id'), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(mysql.LONGTEXT, nullable=True)
    billing_terms_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_billing_terms.id'),
        nullable=False,
        index=True,
    )
    late_charge_policy_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_late_charge_policies.id'),
        nullable=True,
        index=True,
    )
    version = Column(mysql.INTEGER(unsigned=True), nullable=False, default=1)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)


class OrgSchoolFeeStructureItem(Base):
    __tablename__ = 'org_school_fee_structure_items'
    __table_args__ = (
        UniqueConstraint('fee_structure_id', 'fee_category_id', name='uniq_structure_fee_category'),
        CheckConstraint('(`amount` > 0.00)', name='fee_structure_item_amount_positive'),
        Index('org_school__organiz_fd27ef_idx', 'organization_id', 'status'),
        Index('org_school__fee_str_27174c_idx', 'fee_structure_id', 'status'),
    )

    class PaymentCycle:
        MONTHLY = 1
        QUARTERLY = 2
        HALF_YEARLY = 3
        ANNUAL = 4
        ONE_TIME = 5
        choices = [
            (1, 'Monthly'),
            (2, 'Quarterly'),
            (3, 'Half-yearly'),
            (4, 'Annual'),
            (5, 'One-time'),
        ]

    class StudentType:
        ALL = 1
        DAY_SCHOLAR = 2
        HOSTELLER = 3
        choices = [(1, 'All'), (2, 'Day scholar'), (3, 'Hosteller')]

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
    fee_structure_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_structures.id'),
        nullable=False,
        index=True,
    )
    fee_category_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_categories.id'),
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(12, 2), nullable=False)
    payment_cycle = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    applicable_student_type = Column(mysql.SMALLINT(unsigned=True), nullable=False, default=1)
    discount_allowed = Column(Boolean, nullable=False, default=False)
    is_mandatory_override = Column(Boolean, nullable=True)
    display_order = Column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)


class OrgSchoolStudentFeeAssignment(Base):
    __tablename__ = 'org_school_student_fee_assignments'
    __table_args__ = (
        UniqueConstraint('organization_id', 'source_idempotency_key', name='uniq_org_student_fee_source_key'),
        CheckConstraint('(`amount` > 0.00)', name='student_fee_assignment_amount_positive'),
        CheckConstraint('(`effective_until` IS NULL OR `effective_until` >= `effective_from`)', name='student_fee_assignment_valid_dates'),
        Index('org_school__organiz_4f368a_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_school__student_413468_idx', 'student_id', 'academic_year', 'status'),
        Index('org_school__source__876140_idx', 'source_type', 'source_reference_id'),
    )

    class Status:
        DRAFT = 1
        ACTIVE = 2
        ENDED = 3
        CANCELLED = 4
        choices = [(1, 'Draft'), (2, 'Active'), (3, 'Ended'), (4, 'Cancelled')]

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
    academic_year = Column(String(20), nullable=False)
    fee_category_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_categories.id'),
        nullable=False,
        index=True,
    )
    source_type = Column(String(30), nullable=False)
    source_reference_type = Column(String(100), nullable=False)
    source_reference_id = Column(mysql.BIGINT(unsigned=True), nullable=False)
    source_idempotency_key = Column(String(150), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_cycle = Column(mysql.SMALLINT(unsigned=True), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    billing_terms_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_billing_terms.id'),
        nullable=False,
        index=True,
    )
    late_charge_policy_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_late_charge_policies.id'),
        nullable=False,
        index=True,
    )
    source_snapshot = Column(JSON(none_as_null=True), nullable=False, default=dict)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=2)


class OrgSchoolStudentFeeInvoice(Base):
    __tablename__ = 'org_school_student_fee_invoices'
    __table_args__ = (
        UniqueConstraint('organization_id', 'invoice_no', name='uniq_org_student_fee_invoice_no'),
        UniqueConstraint('organization_id', 'generation_key', name='uniq_org_invoice_generation_key'),
        CheckConstraint('(`subtotal_amount` >= 0.00 AND `discount_amount` >= 0.00 AND `late_charge_amount` >= 0.00 AND `total_amount` >= 0.00 AND `paid_amount` >= 0.00 AND `outstanding_amount` >= 0.00)', name='student_invoice_amounts_nonnegative'),
        CheckConstraint('(`grace_end_date` >= `due_date`)', name='student_invoice_grace_after_due'),
        Index('org_school__organiz_d295b6_idx', 'organization_id', 'academic_year', 'billing_period'),
        Index('org_school__student_25ea2e_idx', 'student_id', 'academic_year', 'payment_state'),
        Index('org_school__organiz_ca531c_idx', 'organization_id', 'collection_state', 'due_date'),
    )

    class PaymentState:
        UNPAID = 1
        PARTIALLY_PAID = 2
        PAID = 3
        choices = [(1, 'Unpaid'), (2, 'Partially paid'), (3, 'Paid')]

    class CollectionState:
        CURRENT = 1
        OVERDUE = 2
        CANCELLED = 3
        choices = [(1, 'Current'), (2, 'Overdue'), (3, 'Cancelled')]

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
    fee_structure_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_structures.id'),
        nullable=True,
        index=True,
    )
    class_id_snapshot = Column(mysql.BIGINT(unsigned=True), nullable=True)
    academic_year = Column(String(20), nullable=False)
    invoice_no = Column(String(100), nullable=False)
    billing_period = Column(String(20), nullable=False)
    currency = Column(String(3), nullable=False, default='INR')
    generation_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    grace_end_date = Column(Date, nullable=False)
    subtotal_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    discount_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    adjustment_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    late_charge_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    total_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    paid_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    outstanding_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    payment_state = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    collection_state = Column(
        mysql.SMALLINT(unsigned=True),
        nullable=False,
        index=True,
        default=1,
    )
    generation_key = Column(String(180), nullable=False)
    invoice_url = Column(String(500), nullable=True)
    issued_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    cancelled_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    cancellation_reason = Column(mysql.LONGTEXT, nullable=True)


class OrgSchoolStudentFeeInvoiceItem(Base):
    __tablename__ = 'org_school_student_fee_invoice_items'
    __table_args__ = (
        CheckConstraint('(`quantity` > 0.00 AND `unit_amount` >= 0.00 AND `discount_amount` >= 0.00 AND `line_amount` >= 0.00)', name='student_invoice_item_amounts_valid'),
        CheckConstraint('((`fee_structure_item_id` IS NOT NULL AND `student_fee_assignment_id` IS NULL) OR (`fee_structure_item_id` IS NULL AND `student_fee_assignment_id` IS NOT NULL))', name='invoice_item_has_one_source'),
        Index('org_school__invoice_756393_idx', 'invoice_id', 'fee_category_id'),
        Index('org_school__source__5f12b9_idx', 'source_type', 'source_reference_id'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    invoice_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_invoices.id'),
        nullable=False,
        index=True,
    )
    fee_category_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_categories.id'),
        nullable=False,
        index=True,
    )
    fee_structure_item_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_structure_items.id'),
        nullable=True,
        index=True,
    )
    student_fee_assignment_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_assignments.id'),
        nullable=True,
        index=True,
    )
    fee_code_snapshot = Column(String(50), nullable=False)
    fee_name_snapshot = Column(String(150), nullable=False)
    source_type = Column(String(30), nullable=False)
    source_reference_id = Column(mysql.BIGINT(unsigned=True), nullable=True)
    billing_period = Column(String(20), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=Decimal('1.00'))
    unit_amount = Column(Numeric(14, 2), nullable=False)
    discount_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    line_amount = Column(Numeric(14, 2), nullable=False)
    is_refundable = Column(Boolean, nullable=False, default=False)
    source_snapshot = Column(JSON(none_as_null=True), nullable=False, default=dict)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)


class OrgSchoolInvoiceLateCharge(Base):
    __tablename__ = 'org_school_invoice_late_charges'
    __table_args__ = (
        CheckConstraint('(`calculated_amount` >= 0.00 AND `waived_amount` >= 0.00 AND `net_amount` >= 0.00)', name='invoice_late_charge_amounts_nonnegative'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    invoice_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_invoices.id'),
        nullable=False,
        unique=True,
    )
    policy_id = Column(
        BigInteger,
        ForeignKey('org_school_fee_late_charge_policies.id'),
        nullable=False,
        index=True,
    )
    delayed_days = Column(mysql.INTEGER(unsigned=True), nullable=False, default=0)
    calculated_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    waived_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    net_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    calculated_through = Column(Date, nullable=False)
    policy_snapshot = Column(JSON(none_as_null=True), nullable=False, default=dict)
    assessed_at = Column(mysql.DATETIME(fsp=6), nullable=False)


class OrgSchoolInvoiceAdjustment(Base):
    __tablename__ = 'org_school_invoice_adjustments'
    __table_args__ = (
        CheckConstraint('(`amount` > 0.00)', name='invoice_adjustment_amount_positive'),
        Index('org_school__invoice_50066b_idx', 'invoice_id', 'status'),
    )

    class AdjustmentType:
        CREDIT = 'credit'
        DEBIT = 'debit'
        FEE_WAIVER = 'fee_waiver'
        LATE_CHARGE_WAIVER = 'late_charge_waiver'
        CANCELLATION = 'cancellation'
        choices = [
            ('credit', 'Credit'),
            ('debit', 'Debit'),
            ('fee_waiver', 'Fee waiver'),
            ('late_charge_waiver', 'Late-charge waiver'),
            ('cancellation', 'Cancellation correction'),
        ]

    class Status:
        PENDING = 1
        APPROVED = 2
        REJECTED = 3
        REVERSED = 4
        choices = [(1, 'Pending'), (2, 'Approved'), (3, 'Rejected'), (4, 'Reversed')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    invoice_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_invoices.id'),
        nullable=False,
        index=True,
    )
    adjustment_type = Column(String(30), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    reason = Column(mysql.LONGTEXT, nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    requested_by_id = Column(Integer, nullable=False, index=True)
    approved_by_id = Column(Integer, nullable=True, index=True)
    approved_at = Column(mysql.DATETIME(fsp=6), nullable=True)


class OrgSchoolStudentFeePayment(Base):
    __tablename__ = 'org_school_student_fee_payments'
    __table_args__ = (
        UniqueConstraint('organization_id', 'receipt_no', name='uniq_org_student_fee_receipt_no'),
        CheckConstraint('(`received_amount` > 0.00 AND `allocated_amount` >= 0.00 AND `unapplied_amount` >= 0.00)', name='student_fee_payment_amounts_valid'),
        Index('org_school__organiz_c8abcc_idx', 'organization_id', 'academic_year', 'status'),
        Index('org_school__student_5906a4_idx', 'student_id', 'payment_date'),
    )

    class Status:
        PENDING = 1
        SUCCESS = 2
        REVERSED = 3
        REFUNDED = 4
        choices = [(1, 'Pending'), (2, 'Success'), (3, 'Reversed'), (4, 'Refunded')]

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
    payment_transaction_id = Column(BigInteger, nullable=False, unique=True)
    academic_year = Column(String(20), nullable=False)
    receipt_no = Column(String(100), nullable=False)
    currency = Column(String(3), nullable=False, default='INR')
    received_amount = Column(Numeric(14, 2), nullable=False)
    allocated_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    unapplied_amount = Column(Numeric(14, 2), nullable=False, default=Decimal('0.00'))
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    payment_date = Column(Date, nullable=False)
    receipt_url = Column(String(500), nullable=True)
    created_by_id = Column(Integer, nullable=True, index=True)

    items = relationship(
        'OrgSchoolStudentFeePaymentItem',
        back_populates='payment',
        cascade='all, delete-orphan',
    )


class OrgSchoolStudentCredit(Base):
    __tablename__ = 'org_school_student_credits'
    __table_args__ = (
        CheckConstraint('(`original_amount` > 0.00 AND `available_amount` >= 0.00 AND `available_amount` <= `original_amount`)', name='student_credit_amounts_valid'),
        Index('org_school__organiz_e9cae5_idx', 'organization_id', 'student_id', 'status'),
    )

    class CreditType:
        ADVANCE = 'advance'
        OVERPAYMENT = 'overpayment'
        TRANSFERRED = 'transferred'
        ADJUSTMENT = 'adjustment'
        choices = [
            ('advance', 'Advance'),
            ('overpayment', 'Overpayment'),
            ('transferred', 'Transferred credit'),
            ('adjustment', 'Adjustment credit'),
        ]

    class Status:
        AVAILABLE = 1
        PARTIALLY_USED = 2
        USED = 3
        CANCELLED = 4
        choices = [(1, 'Available'), (2, 'Partially used'), (3, 'Used'), (4, 'Cancelled')]

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
    source_payment_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_payments.id'),
        nullable=True,
        index=True,
    )
    credit_type = Column(String(30), nullable=False)
    original_amount = Column(Numeric(14, 2), nullable=False)
    available_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    reason = Column(mysql.LONGTEXT, nullable=True)


class OrgSchoolFeePaymentAllocation(Base):
    __tablename__ = 'org_school_fee_payment_allocations'
    __table_args__ = (
        UniqueConstraint('payment_id', 'invoice_id', name='uniq_fee_payment_invoice_allocation'),
        CheckConstraint('(`allocated_amount` > 0.00)', name='fee_allocation_amount_positive'),
        Index('org_school__invoice_b2f1dd_idx', 'invoice_id', 'status'),
        Index('org_school__payment_fd191b_idx', 'payment_id', 'status'),
    )

    class Status:
        ACTIVE = 1
        REVERSED = 2
        choices = [(1, 'Active'), (2, 'Reversed')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    payment_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_payments.id'),
        nullable=False,
        index=True,
    )
    invoice_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_invoices.id'),
        nullable=False,
        index=True,
    )
    allocated_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    allocated_at = Column(mysql.DATETIME(fsp=6), nullable=False)
    allocated_by_id = Column(Integer, nullable=False, index=True)
    reversed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    reversed_by_id = Column(Integer, nullable=True, index=True)
    reversal_reason = Column(mysql.LONGTEXT, nullable=True)


class OrgSchoolStudentCreditAllocation(Base):
    __tablename__ = 'org_school_student_credit_allocations'
    __table_args__ = (
        UniqueConstraint('student_credit_id', 'invoice_id', name='uniq_student_credit_invoice_alloc'),
        CheckConstraint('(`allocated_amount` > 0.00)', name='student_credit_alloc_amount_positive'),
        Index('org_school__invoice_a960e6_idx', 'invoice_id', 'status'),
        Index('org_school__student_9f0e11_idx', 'student_credit_id', 'status'),
    )

    class Status:
        ACTIVE = 1
        REVERSED = 2
        choices = [(1, 'Active'), (2, 'Reversed')]

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(mysql.DATETIME(fsp=6), nullable=False, default=utc_now)
    updated_at = Column(
        mysql.DATETIME(fsp=6),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    student_credit_id = Column(
        BigInteger,
        ForeignKey('org_school_student_credits.id'),
        nullable=False,
        index=True,
    )
    invoice_id = Column(
        BigInteger,
        ForeignKey('org_school_student_fee_invoices.id'),
        nullable=False,
        index=True,
    )
    allocated_amount = Column(Numeric(14, 2), nullable=False)
    status = Column(mysql.SMALLINT(unsigned=True), nullable=False, index=True, default=1)
    allocated_at = Column(mysql.DATETIME(fsp=6), nullable=False)
    allocated_by_id = Column(Integer, nullable=False, index=True)
    reversed_at = Column(mysql.DATETIME(fsp=6), nullable=True)
    reversed_by_id = Column(Integer, nullable=True, index=True)
    reversal_reason = Column(mysql.LONGTEXT, nullable=True)


# Existing service-only mapping; retained pending a separate usage/schema migration.
class OrgSchoolStudentFeePaymentItem(Base):
    __tablename__ = 'org_school_student_fee_payment_items'
    id = Column(Integer, primary_key=True)
    payment_id = Column(
        Integer,
        ForeignKey('org_school_student_fee_payments.id', ondelete='CASCADE'),
        nullable=False,
    )
    fee_structure_id = Column(Integer, nullable=False)
    cycle_label = Column(String(100))
    base_amount = Column(Numeric(10, 2))
    late_fee = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    payment = relationship('OrgSchoolStudentFeePayment', back_populates='items')


# Existing service-only mapping; retained pending a separate usage/schema migration.
class OrgStudentFeeInstallment(Base):
    __tablename__ = "org_student_fee_installments"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "fee_structure_id",
            "academic_year",
            "cycle_label",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, nullable=False, index=True)
    fee_structure_id = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False, index=True)
    cycle_label = Column(String(50), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False, default=0)
    late_fee = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    balance_amount = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(Integer, nullable=False, default=1, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

__all__ = [
    'OrgSchoolFeeCategory',
    'OrgSchoolFeeBillingTerms',
    'OrgSchoolFeeLateChargePolicy',
    'OrgSchoolFeeStructure',
    'OrgSchoolFeeStructureItem',
    'OrgSchoolStudentFeeAssignment',
    'OrgSchoolStudentFeeInvoice',
    'OrgSchoolStudentFeeInvoiceItem',
    'OrgSchoolInvoiceLateCharge',
    'OrgSchoolInvoiceAdjustment',
    'OrgSchoolStudentFeePayment',
    'OrgSchoolStudentCredit',
    'OrgSchoolFeePaymentAllocation',
    'OrgSchoolStudentCreditAllocation',
    'OrgSchoolStudentFeePaymentItem',
    'OrgStudentFeeInstallment',
]
