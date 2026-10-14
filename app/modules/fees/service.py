"""Student-facing fee services."""

from datetime import datetime
from decimal import Decimal
from math import ceil
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.fees.models import (
    OrgSchoolStudentFeeInvoice,
    OrgSchoolStudentFeeInvoiceItem,
    OrgSchoolStudentFeePayment,
    OrgSchoolFeePaymentAllocation,
    OrgSchoolStudentCredit,
)
from app.modules.students.repository import StudentRepository
from core.storage import S3StorageService


IST = ZoneInfo("Asia/Kolkata")
ZERO = Decimal("0.00")


class StudentFeeService:
    @staticmethod
    def list_credit_transactions(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        query = db.query(OrgSchoolStudentCredit).filter(
            OrgSchoolStudentCredit.student_id == student_id,
            OrgSchoolStudentCredit.organization_id == organization_id,
        )
        total_items = query.count()
        credits = (
            query.order_by(
                OrgSchoolStudentCredit.created_at.desc(),
                OrgSchoolStudentCredit.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        status_labels = {
            OrgSchoolStudentCredit.Status.AVAILABLE: "available",
            OrgSchoolStudentCredit.Status.PARTIALLY_USED: "partially_used",
            OrgSchoolStudentCredit.Status.USED: "used",
            OrgSchoolStudentCredit.Status.CANCELLED: "cancelled",
        }
        type_labels = dict(OrgSchoolStudentCredit.CreditType.choices)
        results = [
            {
                "id": credit.id,
                "credit_type": credit.credit_type,
                "credit_type_label": type_labels.get(
                    credit.credit_type, credit.credit_type.replace("_", " ").title()
                ),
                "reason": credit.reason,
                "original_amount": float(credit.original_amount or ZERO),
                "available_amount": float(credit.available_amount or ZERO),
                "used_amount": float(
                    Decimal(credit.original_amount or ZERO)
                    - Decimal(credit.available_amount or ZERO)
                ),
                "status": status_labels.get(credit.status, "unknown"),
                "created_at": credit.created_at.isoformat(),
            }
            for credit in credits
        ]
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1 and total_pages > 0,
            },
        }

    @staticmethod
    def get_credit_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
        limit: int = 2,
    ) -> dict:
        total_available = sum(
            (
                Decimal(value or ZERO)
                for (value,) in db.query(
                    OrgSchoolStudentCredit.available_amount
                ).filter(
                    OrgSchoolStudentCredit.student_id == student_id,
                    OrgSchoolStudentCredit.organization_id == organization_id,
                    OrgSchoolStudentCredit.status.in_(
                        [
                            OrgSchoolStudentCredit.Status.AVAILABLE,
                            OrgSchoolStudentCredit.Status.PARTIALLY_USED,
                        ]
                    ),
                )
            ),
            ZERO,
        )
        data = StudentFeeService.list_credit_transactions(
            db, student_id, organization_id, 1, limit
        )
        return {
            "currency": "INR",
            "available_balance": float(total_available),
            "transactions": data["results"],
        }

    @staticmethod
    def get_invoice_detail(
        db: Session,
        invoice_id: int,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        invoice = (
            db.query(OrgSchoolStudentFeeInvoice)
            .filter(
                OrgSchoolStudentFeeInvoice.id == invoice_id,
                OrgSchoolStudentFeeInvoice.student_id == student_id,
                OrgSchoolStudentFeeInvoice.organization_id == organization_id,
                OrgSchoolStudentFeeInvoice.collection_state
                != OrgSchoolStudentFeeInvoice.CollectionState.CANCELLED,
            )
            .first()
        )
        if not invoice:
            return None

        items = (
            db.query(OrgSchoolStudentFeeInvoiceItem)
            .filter(OrgSchoolStudentFeeInvoiceItem.invoice_id == invoice.id)
            .order_by(OrgSchoolStudentFeeInvoiceItem.id)
            .all()
        )
        payment_rows = (
            db.query(
                OrgSchoolFeePaymentAllocation,
                OrgSchoolStudentFeePayment,
            )
            .join(
                OrgSchoolStudentFeePayment,
                OrgSchoolStudentFeePayment.id
                == OrgSchoolFeePaymentAllocation.payment_id,
            )
            .filter(
                OrgSchoolFeePaymentAllocation.invoice_id == invoice.id,
                OrgSchoolFeePaymentAllocation.status
                == OrgSchoolFeePaymentAllocation.Status.ACTIVE,
                OrgSchoolStudentFeePayment.student_id == student_id,
                OrgSchoolStudentFeePayment.organization_id == organization_id,
                OrgSchoolStudentFeePayment.status
                == OrgSchoolStudentFeePayment.Status.SUCCESS,
            )
            .order_by(
                OrgSchoolStudentFeePayment.payment_date.desc(),
                OrgSchoolStudentFeePayment.id.desc(),
            )
            .all()
        )
        today = datetime.now(IST).date()
        if invoice.payment_state == OrgSchoolStudentFeeInvoice.PaymentState.PAID:
            status = "paid"
        elif (
            invoice.collection_state
            == OrgSchoolStudentFeeInvoice.CollectionState.OVERDUE
            or invoice.due_date < today
        ):
            status = "overdue"
        elif (
            invoice.payment_state
            == OrgSchoolStudentFeeInvoice.PaymentState.PARTIALLY_PAID
        ):
            status = "partially_paid"
        else:
            status = "unpaid"

        return {
            "id": invoice.id,
            "invoice_no": invoice.invoice_no,
            "academic_year": invoice.academic_year,
            "billing_period": invoice.billing_period,
            "currency": invoice.currency,
            "generation_date": invoice.generation_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "grace_end_date": invoice.grace_end_date.isoformat(),
            "status": status,
            "payment_state": invoice.payment_state,
            "collection_state": invoice.collection_state,
            "subtotal_amount": float(invoice.subtotal_amount or ZERO),
            "discount_amount": float(invoice.discount_amount or ZERO),
            "adjustment_amount": float(invoice.adjustment_amount or ZERO),
            "late_charge_amount": float(invoice.late_charge_amount or ZERO),
            "total_amount": float(invoice.total_amount or ZERO),
            "paid_amount": float(invoice.paid_amount or ZERO),
            "outstanding_amount": float(invoice.outstanding_amount or ZERO),
            "invoice_pdf_url": (
                S3StorageService.file_url(invoice.invoice_url)
                if invoice.invoice_url
                else None
            ),
            "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
            "items": [
                {
                    "id": item.id,
                    "fee_category_id": item.fee_category_id,
                    "fee_code": item.fee_code_snapshot,
                    "fee_name": item.fee_name_snapshot,
                    "billing_period": item.billing_period,
                    "quantity": float(item.quantity),
                    "unit_amount": float(item.unit_amount),
                    "discount_amount": float(item.discount_amount),
                    "line_amount": float(item.line_amount),
                    "is_refundable": item.is_refundable,
                }
                for item in items
            ],
            "receipts": [
                {
                    "payment_id": payment.id,
                    "receipt_no": payment.receipt_no,
                    "payment_date": payment.payment_date.isoformat(),
                    "currency": payment.currency,
                    "received_amount": float(payment.received_amount or ZERO),
                    "allocated_amount": float(allocation.allocated_amount or ZERO),
                    "receipt_url": (
                        S3StorageService.file_url(payment.receipt_url)
                        if payment.receipt_url
                        else None
                    ),
                }
                for allocation, payment in payment_rows
            ],
        }

    @staticmethod
    def get_invoice_snapshot(
        db: Session,
        student_id: int,
        organization_id: int,
        limit: int = 5,
    ) -> dict:
        data = StudentFeeService.list_invoices(
            db, student_id, organization_id, "all", 1, limit
        )
        return {
            "academic_year": data["academic_year"],
            "invoices": data["results"],
        }

    @staticmethod
    def list_invoices(
        db: Session,
        student_id: int,
        organization_id: int,
        status_filter: str,
        page: int,
        page_size: int,
    ) -> dict:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        academic_year = (
            mapping.section.org_class.academic_year
            if mapping and mapping.section and mapping.section.org_class
            else None
        )
        query = db.query(OrgSchoolStudentFeeInvoice).filter(
            OrgSchoolStudentFeeInvoice.student_id == student_id,
            OrgSchoolStudentFeeInvoice.organization_id == organization_id,
            OrgSchoolStudentFeeInvoice.collection_state
            != OrgSchoolStudentFeeInvoice.CollectionState.CANCELLED,
        )
        if not academic_year:
            latest = query.order_by(
                OrgSchoolStudentFeeInvoice.generation_date.desc(),
                OrgSchoolStudentFeeInvoice.id.desc(),
            ).first()
            academic_year = latest.academic_year if latest else None
        if academic_year:
            query = query.filter(
                OrgSchoolStudentFeeInvoice.academic_year == academic_year
            )
        today = datetime.now(IST).date()
        overdue_expression = and_(
            OrgSchoolStudentFeeInvoice.payment_state
            != OrgSchoolStudentFeeInvoice.PaymentState.PAID,
            or_(
                OrgSchoolStudentFeeInvoice.collection_state
                == OrgSchoolStudentFeeInvoice.CollectionState.OVERDUE,
                OrgSchoolStudentFeeInvoice.due_date < today,
            ),
        )
        if status_filter == "paid":
            query = query.filter(
                OrgSchoolStudentFeeInvoice.payment_state
                == OrgSchoolStudentFeeInvoice.PaymentState.PAID
            )
        elif status_filter == "overdue":
            query = query.filter(overdue_expression)
        elif status_filter == "partially_paid":
            query = query.filter(
                OrgSchoolStudentFeeInvoice.payment_state
                == OrgSchoolStudentFeeInvoice.PaymentState.PARTIALLY_PAID,
                ~overdue_expression,
            )
        elif status_filter == "unpaid":
            query = query.filter(
                OrgSchoolStudentFeeInvoice.payment_state
                == OrgSchoolStudentFeeInvoice.PaymentState.UNPAID,
                ~overdue_expression,
            )

        total_items = query.count()
        invoices = (
            query.order_by(
                OrgSchoolStudentFeeInvoice.generation_date.desc(),
                OrgSchoolStudentFeeInvoice.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        invoice_ids = [invoice.id for invoice in invoices]
        items = (
            db.query(OrgSchoolStudentFeeInvoiceItem)
            .filter(OrgSchoolStudentFeeInvoiceItem.invoice_id.in_(invoice_ids))
            .order_by(
                OrgSchoolStudentFeeInvoiceItem.invoice_id,
                OrgSchoolStudentFeeInvoiceItem.id,
            )
            .all()
            if invoice_ids
            else []
        )
        item_count_by_invoice: dict[int, int] = {}
        for item in items:
            item_count_by_invoice[item.invoice_id] = (
                item_count_by_invoice.get(item.invoice_id, 0) + 1
            )

        results = []
        for invoice in invoices:
            if invoice.payment_state == OrgSchoolStudentFeeInvoice.PaymentState.PAID:
                status = "paid"
            elif (
                invoice.collection_state
                == OrgSchoolStudentFeeInvoice.CollectionState.OVERDUE
                or invoice.due_date < today
            ):
                status = "overdue"
            elif (
                invoice.payment_state
                == OrgSchoolStudentFeeInvoice.PaymentState.PARTIALLY_PAID
            ):
                status = "partially_paid"
            else:
                status = "unpaid"
            results.append(
                {
                    "id": invoice.id,
                    "invoice_no": invoice.invoice_no,
                    "label": "Fee Invoice",
                    "item_count": item_count_by_invoice.get(invoice.id, 0),
                    "billing_period": invoice.billing_period,
                    "due_date": invoice.due_date.isoformat(),
                    "generation_date": invoice.generation_date.isoformat(),
                    "currency": invoice.currency,
                    "total_amount": float(invoice.total_amount or ZERO),
                    "paid_amount": float(invoice.paid_amount or ZERO),
                    "outstanding_amount": float(invoice.outstanding_amount or ZERO),
                    "status": status,
                }
            )
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "academic_year": academic_year,
            "results": results,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1 and total_pages > 0,
            },
        }

    @staticmethod
    def get_overview(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict:
        mapping = StudentRepository.get_active_section_mapping(db, student_id)
        academic_year = (
            mapping.section.org_class.academic_year
            if mapping and mapping.section and mapping.section.org_class
            else None
        )

        query = db.query(OrgSchoolStudentFeeInvoice).filter(
            OrgSchoolStudentFeeInvoice.student_id == student_id,
            OrgSchoolStudentFeeInvoice.organization_id == organization_id,
            OrgSchoolStudentFeeInvoice.collection_state
            != OrgSchoolStudentFeeInvoice.CollectionState.CANCELLED,
        )
        if not academic_year:
            latest = query.order_by(
                OrgSchoolStudentFeeInvoice.generation_date.desc(),
                OrgSchoolStudentFeeInvoice.id.desc(),
            ).first()
            academic_year = latest.academic_year if latest else None
        if academic_year:
            query = query.filter(
                OrgSchoolStudentFeeInvoice.academic_year == academic_year
            )

        invoices = query.all()
        pending = [
            invoice
            for invoice in invoices
            if invoice.payment_state
            != OrgSchoolStudentFeeInvoice.PaymentState.PAID
            and Decimal(invoice.outstanding_amount or ZERO) > ZERO
        ]
        total_outstanding = sum(
            (Decimal(invoice.outstanding_amount or ZERO) for invoice in pending),
            ZERO,
        )
        today = datetime.now(IST).date()
        upcoming_dates = [
            invoice.due_date
            for invoice in pending
            if invoice.due_date and invoice.due_date >= today
        ]

        payment_query = db.query(OrgSchoolStudentFeePayment).filter(
            OrgSchoolStudentFeePayment.student_id == student_id,
            OrgSchoolStudentFeePayment.organization_id == organization_id,
            OrgSchoolStudentFeePayment.status
            == OrgSchoolStudentFeePayment.Status.SUCCESS,
        )
        if academic_year:
            payment_query = payment_query.filter(
                OrgSchoolStudentFeePayment.academic_year == academic_year
            )
        paid_amount = sum(
            (
                Decimal(payment.received_amount or ZERO)
                for payment in payment_query.all()
            ),
            ZERO,
        )

        currency = next(
            (invoice.currency for invoice in invoices if invoice.currency),
            "INR",
        )
        return {
            "academic_year": academic_year,
            "currency": currency,
            "total_outstanding": float(total_outstanding),
            "next_due_date": min(upcoming_dates).isoformat()
            if upcoming_dates
            else None,
            "pending_invoice_count": len(pending),
            "paid_amount": float(paid_amount),
        }
