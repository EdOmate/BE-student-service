from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class OrgSchoolFeeStructure(Base):
    __tablename__ = 'org_school_fee_structure'
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False)
    class_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)
    custom_name = Column(String(100))
    amount = Column(Numeric(10, 2), nullable=False)
    recurring_cycle = Column(Integer)
    applicable_student_type = Column(Integer)
    grace_period = Column(Integer)
    late_fee = Column(Numeric(10, 2), default=0)
    discount_allowed = Column(Integer, default=0)
    is_mandatory = Column(Integer, default=1)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OrgSchoolStudentFeePayment(Base):
    __tablename__ = 'org_school_student_fee_payments'
    id = Column(Integer, primary_key=True)
    student_id = Column(BigInteger, nullable=False, index=True)
    session_year = Column(String(20), nullable=False)
    payment_status = Column(Integer)
    payment_method = Column(Integer)
    transaction_id = Column(String(255))
    payment_reference_id = Column(String(255))
    receipt_no = Column(String(100))
    receipt_url = Column(String(255))
    payment_date = Column(Date)
    total_amount = Column(Numeric(10, 2))
    late_fee_amount = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2))
    net_payment_amount = Column(Numeric(10, 2))
    created_by = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    items = relationship('OrgSchoolStudentFeePaymentItem', back_populates='payment', cascade='all, delete-orphan')

class OrgSchoolStudentFeePaymentItem(Base):
    __tablename__ = 'org_school_student_fee_payment_items'
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey('org_school_student_fee_payments.id', ondelete='CASCADE'), nullable=False)
    fee_structure_id = Column(Integer, nullable=False)
    cycle_label = Column(String(100))
    base_amount = Column(Numeric(10, 2))
    late_fee = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    payment = relationship('OrgSchoolStudentFeePayment', back_populates='items')


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
