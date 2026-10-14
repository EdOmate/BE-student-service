"""Student-facing library services."""

from datetime import date
from math import ceil

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.modules.library.models import (
    OrgLibraryBranch,
    OrgLibraryBook,
    OrgLibraryBookCopy,
    OrgLibraryLoan,
    OrgLibraryMember,
    OrgLibrarySettings,
)


class StudentLibraryService:
    STATUS_LABELS = {
        OrgLibraryMember.STATUS_ACTIVE: "active",
        OrgLibraryMember.STATUS_SUSPENDED: "suspended",
        OrgLibraryMember.STATUS_EXPIRED: "expired",
    }
    LOAN_STATUS_LABELS = dict(OrgLibraryLoan.STATUS_CHOICES)

    @staticmethod
    def _get_member(db: Session, student_id: int, organization_id: int):
        return (
            db.query(OrgLibraryMember)
            .filter(
                OrgLibraryMember.organization_id == organization_id,
                OrgLibraryMember.student_id == student_id,
                OrgLibraryMember.member_type
                == OrgLibraryMember.MEMBER_TYPE_STUDENT,
            )
            .order_by(
                case(
                    (OrgLibraryMember.status == OrgLibraryMember.STATUS_ACTIVE, 0),
                    else_=1,
                ),
                OrgLibraryMember.id.desc(),
            )
            .first()
        )

    @staticmethod
    def _serialize_loan(loan, copy, book) -> dict:
        return {
            "id": loan.id,
            "book_id": book.id,
            "copy_id": copy.id,
            "title": book.title,
            "subtitle": book.subtitle,
            "cover_image": book.cover_image,
            "isbn": book.isbn_13 or book.isbn_10,
            "barcode": copy.barcode,
            "copy_no": copy.copy_no,
            "issue_date": loan.issue_date.isoformat(),
            "due_date": loan.due_date.isoformat(),
            "return_date": loan.return_date.isoformat() if loan.return_date else None,
            "renew_count": loan.renew_count,
            "status": StudentLibraryService.LOAN_STATUS_LABELS.get(
                loan.status, "Unknown"
            ).lower(),
        }

    @staticmethod
    def _loan_query(db: Session, member_id: int, organization_id: int):
        return (
            db.query(OrgLibraryLoan, OrgLibraryBookCopy, OrgLibraryBook)
            .join(OrgLibraryBookCopy, OrgLibraryBookCopy.id == OrgLibraryLoan.copy_id)
            .join(OrgLibraryBook, OrgLibraryBook.id == OrgLibraryBookCopy.book_id)
            .filter(
                OrgLibraryLoan.organization_id == organization_id,
                OrgLibraryLoan.member_id == member_id,
                OrgLibraryBookCopy.organization_id == organization_id,
                OrgLibraryBook.organization_id == organization_id,
            )
        )

    @staticmethod
    def get_membership_details(
        db: Session,
        student_id: int,
        organization_id: int,
    ) -> dict | None:
        member = StudentLibraryService._get_member(
            db, student_id, organization_id
        )
        if not member:
            return None

        branch = None
        settings = None
        if member.branch_id:
            branch = (
                db.query(OrgLibraryBranch)
                .filter(
                    OrgLibraryBranch.id == member.branch_id,
                    OrgLibraryBranch.organization_id == organization_id,
                )
                .first()
            )
            settings = (
                db.query(OrgLibrarySettings)
                .filter(
                    OrgLibrarySettings.branch_id == member.branch_id,
                    OrgLibrarySettings.organization_id == organization_id,
                    OrgLibrarySettings.is_active.is_(True),
                )
                .first()
            )

        today = date.today()
        effective_status = StudentLibraryService.STATUS_LABELS.get(
            member.status, "unknown"
        )
        if member.valid_until and member.valid_until < today:
            effective_status = "expired"
        elif member.valid_from and member.valid_from > today:
            effective_status = "upcoming"

        issued_count = (
            db.query(func.count(OrgLibraryLoan.id))
            .filter(
                OrgLibraryLoan.organization_id == organization_id,
                OrgLibraryLoan.member_id == member.id,
                OrgLibraryLoan.status.in_(
                    [OrgLibraryLoan.STATUS_ISSUED, OrgLibraryLoan.STATUS_OVERDUE]
                ),
            )
            .scalar()
            or 0
        )

        return {
            "id": member.id,
            "membership_no": member.membership_no,
            "member_name": member.name,
            "status": effective_status,
            "valid_from": member.valid_from.isoformat() if member.valid_from else None,
            "valid_until": member.valid_until.isoformat() if member.valid_until else None,
            "branch": (
                {
                    "id": branch.id,
                    "name": branch.name,
                    "code": branch.code,
                    "location_name": branch.location_name,
                }
                if branch
                else None
            ),
            "current_books_issued": int(issued_count),
            "max_books_allowed": (
                int(settings.max_books_per_member) if settings else None
            ),
        }

    @staticmethod
    def get_current_issued_books(
        db: Session, student_id: int, organization_id: int
    ) -> list[dict]:
        member = StudentLibraryService._get_member(db, student_id, organization_id)
        if not member:
            return []
        rows = (
            StudentLibraryService._loan_query(db, member.id, organization_id)
            .filter(
                OrgLibraryLoan.status.in_(
                    [OrgLibraryLoan.STATUS_ISSUED, OrgLibraryLoan.STATUS_OVERDUE]
                )
            )
            .order_by(OrgLibraryLoan.due_date.asc(), OrgLibraryLoan.id.desc())
            .all()
        )
        return [StudentLibraryService._serialize_loan(*row) for row in rows]

    @staticmethod
    def get_past_issued_books(
        db: Session,
        student_id: int,
        organization_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        member = StudentLibraryService._get_member(db, student_id, organization_id)
        if not member:
            return {
                "results": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False,
                },
            }
        query = StudentLibraryService._loan_query(db, member.id, organization_id).filter(
            OrgLibraryLoan.status == OrgLibraryLoan.STATUS_RETURNED
        )
        total_items = query.count()
        rows = (
            query.order_by(
                OrgLibraryLoan.return_date.desc(), OrgLibraryLoan.id.desc()
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = ceil(total_items / page_size) if total_items else 0
        return {
            "results": [StudentLibraryService._serialize_loan(*row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1 and total_pages > 0,
            },
        }
