"""Student-facing hostel overview service."""

from datetime import date, datetime, timedelta
from math import ceil
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.modules.fees.models import (
    OrgSchoolStudentFeeInvoice,
    OrgSchoolStudentFeeInvoiceItem,
)
from app.modules.hostel.models import (
    OrgHostel,
    OrgHostelAttendance,
    OrgHostelBed,
    OrgHostelBlock,
    OrgHostelFloor,
    OrgHostelLeaveRequest,
    OrgHostelMessMenu,
    OrgHostelMessPlan,
    OrgHostelRoom,
    OrgHostelStudentAllocation,
    OrgHostelWardenAssignment,
    OrgHostelComplaint,
    OrgHostelComplaintActionLog,
    OrgSchoolStaff,
)


class StudentHostelService:
    @staticmethod
    def today() -> date:
        return datetime.now(ZoneInfo("Asia/Kolkata")).date()

    @staticmethod
    def _active_allocation_location(db: Session, student_id: int, organization_id: int):
        return (
            db.query(
                OrgHostelStudentAllocation,
                OrgHostelBed,
                OrgHostelRoom,
                OrgHostelFloor,
                OrgHostelBlock,
                OrgHostel,
            )
            .join(OrgHostelBed, OrgHostelBed.id == OrgHostelStudentAllocation.bed_id)
            .join(OrgHostelRoom, OrgHostelRoom.id == OrgHostelBed.room_id)
            .join(OrgHostelFloor, OrgHostelFloor.id == OrgHostelRoom.floor_id)
            .join(OrgHostelBlock, OrgHostelBlock.id == OrgHostelFloor.block_id)
            .join(OrgHostel, OrgHostel.id == OrgHostelBlock.hostel_id)
            .filter(
                OrgHostelStudentAllocation.student_id == student_id,
                OrgHostelStudentAllocation.organization_id == organization_id,
                OrgHostelStudentAllocation.status == OrgHostelStudentAllocation.STATUS_ACTIVE,
                OrgHostelStudentAllocation.is_current.is_(True),
            )
            .order_by(OrgHostelStudentAllocation.id.desc())
            .first()
        )

    @staticmethod
    def get_overview(db: Session, student_id: int, organization_id: int) -> dict | None:
        row = StudentHostelService._active_allocation_location(
            db, student_id, organization_id
        )
        if not row:
            return None

        allocation, bed, room, floor, block, hostel = row
        today = StudentHostelService.today()
        month_start = today.replace(day=1)

        attendance_counts = dict(
            db.query(OrgHostelAttendance.status, func.count(OrgHostelAttendance.id))
            .filter(
                OrgHostelAttendance.organization_id == organization_id,
                OrgHostelAttendance.student_id == student_id,
                OrgHostelAttendance.allocation_id == allocation.id,
                OrgHostelAttendance.attendance_date >= month_start,
                OrgHostelAttendance.attendance_date <= today,
            )
            .group_by(OrgHostelAttendance.status)
            .all()
        )
        total_marked = sum(attendance_counts.values())
        attended = attendance_counts.get(OrgHostelAttendance.STATUS_PRESENT, 0) + attendance_counts.get(
            OrgHostelAttendance.STATUS_LATE, 0
        )
        attendance_percentage = round((attended / total_marked) * 100) if total_marked else 0

        today_attendance = (
            db.query(OrgHostelAttendance)
            .filter(
                OrgHostelAttendance.organization_id == organization_id,
                OrgHostelAttendance.student_id == student_id,
                OrgHostelAttendance.allocation_id == allocation.id,
                OrgHostelAttendance.attendance_date == today,
            )
            .order_by(OrgHostelAttendance.session.desc(), OrgHostelAttendance.marked_at.desc())
            .first()
        )

        active_leave = (
            db.query(OrgHostelLeaveRequest)
            .filter(
                OrgHostelLeaveRequest.organization_id == organization_id,
                OrgHostelLeaveRequest.student_id == student_id,
                OrgHostelLeaveRequest.allocation_id == allocation.id,
                OrgHostelLeaveRequest.status.in_([
                    OrgHostelLeaveRequest.STATUS_PENDING,
                    OrgHostelLeaveRequest.STATUS_APPROVED,
                ]),
                OrgHostelLeaveRequest.end_date >= today,
            )
            .order_by(OrgHostelLeaveRequest.start_date, OrgHostelLeaveRequest.id.desc())
            .first()
        )

        hostel_invoice_ids = (
            db.query(OrgSchoolStudentFeeInvoiceItem.invoice_id)
            .join(
                OrgSchoolStudentFeeInvoice,
                OrgSchoolStudentFeeInvoice.id == OrgSchoolStudentFeeInvoiceItem.invoice_id,
            )
            .filter(
                OrgSchoolStudentFeeInvoice.student_id == student_id,
                OrgSchoolStudentFeeInvoice.organization_id == organization_id,
                OrgSchoolStudentFeeInvoice.collection_state
                != OrgSchoolStudentFeeInvoice.CollectionState.CANCELLED,
                OrgSchoolStudentFeeInvoiceItem.source_type == "hostel",
            )
            .distinct()
        )
        hostel_dues = (
            db.query(func.coalesce(func.sum(OrgSchoolStudentFeeInvoice.outstanding_amount), 0))
            .filter(OrgSchoolStudentFeeInvoice.id.in_(hostel_invoice_ids))
            .scalar()
        )

        attendance_labels = dict(OrgHostelAttendance.STATUS_CHOICES)
        leave_status_labels = dict(OrgHostelLeaveRequest.STATUS_CHOICES)
        leave_type_labels = dict(OrgHostelLeaveRequest.TYPE_CHOICES)
        return {
            "allocation": {
                "id": allocation.id,
                "allocation_no": allocation.allocation_no,
                "allocation_type": allocation.allocation_type,
                "allocation_type_label": dict(OrgHostelStudentAllocation.TYPE_CHOICES).get(allocation.allocation_type),
                "academic_year": allocation.academic_year,
                "allocation_date": allocation.allocation_date.isoformat(),
                "expected_checkout_date": allocation.expected_checkout_date.isoformat() if allocation.expected_checkout_date else None,
                "hostel": {"id": hostel.id, "name": hostel.name, "code": hostel.code, "address": hostel.address, "contact_number": hostel.contact_number},
                "block": {"id": block.id, "name": block.name, "code": block.code},
                "floor": {"id": floor.id, "number": floor.floor_no, "name": floor.name},
                "room": {"id": room.id, "number": room.room_no, "name": room.room_name, "type": room.room_type, "type_label": dict(OrgHostelRoom.TYPE_CHOICES).get(room.room_type)},
                "bed": {"id": bed.id, "number": bed.bed_no, "label": bed.bed_label},
            },
            "monthly_attendance": {"percentage": attendance_percentage, "attended": attended, "total_marked": total_marked},
            "dues": {"currency": "INR", "amount": float(Decimal(hostel_dues or 0))},
            "today_attendance": ({"status": today_attendance.status, "status_label": attendance_labels.get(today_attendance.status), "session": today_attendance.session, "marked_at": today_attendance.marked_at.isoformat()} if today_attendance else None),
            "active_leave": ({"id": active_leave.id, "type": active_leave.leave_type, "type_label": leave_type_labels.get(active_leave.leave_type), "status": active_leave.status, "status_label": leave_status_labels.get(active_leave.status), "start_date": active_leave.start_date.isoformat(), "end_date": active_leave.end_date.isoformat()} if active_leave else None),
        }

    @staticmethod
    def get_wardens(db: Session, student_id: int, organization_id: int) -> list[dict] | None:
        location = StudentHostelService._active_allocation_location(
            db, student_id, organization_id
        )
        if not location:
            return None

        _, _, _, floor, block, hostel = location
        today = StudentHostelService.today()
        scope_rank = case(
            (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_FLOOR, 0),
            (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_BLOCK, 1),
            (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_HOSTEL, 2),
            else_=3,
        )
        rows = (
            db.query(OrgHostelWardenAssignment, OrgSchoolStaff)
            .join(OrgSchoolStaff, OrgSchoolStaff.id == OrgHostelWardenAssignment.staff_id)
            .filter(
                OrgHostelWardenAssignment.organization_id == organization_id,
                OrgHostelWardenAssignment.status == OrgHostelWardenAssignment.STATUS_ACTIVE,
                OrgHostelWardenAssignment.start_date <= today,
                or_(
                    OrgHostelWardenAssignment.end_date.is_(None),
                    OrgHostelWardenAssignment.end_date >= today,
                ),
                OrgSchoolStaff.organization_id == organization_id,
                OrgSchoolStaff.employment_status == 1,
                OrgSchoolStaff.is_active.is_(True),
                or_(
                    (
                        (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_FLOOR)
                        & (OrgHostelWardenAssignment.floor_id == floor.id)
                    ),
                    (
                        (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_BLOCK)
                        & (OrgHostelWardenAssignment.block_id == block.id)
                    ),
                    (
                        (OrgHostelWardenAssignment.scope == OrgHostelWardenAssignment.SCOPE_HOSTEL)
                        & (OrgHostelWardenAssignment.hostel_id == hostel.id)
                    ),
                ),
            )
            .order_by(scope_rank, OrgHostelWardenAssignment.is_primary.desc(), OrgHostelWardenAssignment.id.desc())
            .all()
        )

        scope_labels = dict(OrgHostelWardenAssignment.SCOPE_CHOICES)
        wardens = []
        for assignment, staff in rows:
            name = " ".join(part for part in [staff.first_name, staff.last_name] if part).strip()
            contact = " ".join(part for part in [staff.isd_code, staff.mobile] if part).strip()
            wardens.append({
                "assignment_id": assignment.id,
                "staff_id": staff.id,
                "name": name or f"Staff #{staff.id}",
                "contact": contact or None,
                "scope": assignment.scope,
                "scope_label": scope_labels.get(assignment.scope),
                "is_primary": assignment.is_primary,
                "level": (
                    {"id": floor.id, "name": floor.name or f"Floor {floor.floor_no}"}
                    if assignment.scope == OrgHostelWardenAssignment.SCOPE_FLOOR
                    else {"id": block.id, "name": block.name}
                    if assignment.scope == OrgHostelWardenAssignment.SCOPE_BLOCK
                    else {"id": hostel.id, "name": hostel.name}
                ),
            })
        return wardens

    @staticmethod
    def _menu_for_date(db: Session, organization_id: int, hostel_id: int, menu_date: date) -> dict:
        plan = (
            db.query(OrgHostelMessPlan)
            .filter(
                OrgHostelMessPlan.organization_id == organization_id,
                OrgHostelMessPlan.status == OrgHostelMessPlan.STATUS_PUBLISHED,
                or_(OrgHostelMessPlan.hostel_id == hostel_id, OrgHostelMessPlan.hostel_id.is_(None)),
                or_(OrgHostelMessPlan.applicable_from.is_(None), OrgHostelMessPlan.applicable_from <= menu_date),
                or_(OrgHostelMessPlan.applicable_to.is_(None), OrgHostelMessPlan.applicable_to >= menu_date),
            )
            .order_by(
                case((OrgHostelMessPlan.hostel_id == hostel_id, 0), else_=1),
                OrgHostelMessPlan.is_default.desc(),
                OrgHostelMessPlan.id,
            )
            .first()
        )
        if not plan:
            return {"date": menu_date.isoformat(), "day": menu_date.strftime("%A"), "plan": None, "meals": []}

        menus = (
            db.query(OrgHostelMessMenu)
            .filter(
                OrgHostelMessMenu.organization_id == organization_id,
                OrgHostelMessMenu.plan_id == plan.id,
                OrgHostelMessMenu.status == OrgHostelMessMenu.STATUS_PUBLISHED,
                or_(
                    OrgHostelMessMenu.menu_date == menu_date,
                    (
                        OrgHostelMessMenu.menu_date.is_(None)
                        & (OrgHostelMessMenu.day_of_week == menu_date.isoweekday())
                    ),
                ),
            )
            .order_by(OrgHostelMessMenu.meal_type, OrgHostelMessMenu.menu_date.desc(), OrgHostelMessMenu.id.desc())
            .all()
        )
        by_meal = {}
        for menu in menus:
            existing = by_meal.get(menu.meal_type)
            if existing is None or (menu.menu_date is not None and existing.menu_date is None):
                by_meal[menu.meal_type] = menu

        meal_labels = dict(OrgHostelMessMenu.MEAL_CHOICES)
        meals = [
            {
                "id": menu.id,
                "meal_type": menu.meal_type,
                "meal_type_label": meal_labels.get(menu.meal_type),
                "title": menu.title,
                "items": menu.items or [],
                "notes": menu.notes,
                "calories": menu.calories,
                "is_date_specific": menu.menu_date is not None,
                "menu_date": menu.menu_date.isoformat() if menu.menu_date else None,
            }
            for menu in sorted(by_meal.values(), key=lambda item: item.meal_type)
        ]
        return {
            "date": menu_date.isoformat(),
            "day": menu_date.strftime("%A"),
            "plan": {"id": plan.id, "name": plan.name, "code": plan.code, "plan_type": plan.plan_type},
            "meals": meals,
        }

    @staticmethod
    def get_mess_for_date(db: Session, student_id: int, organization_id: int, menu_date: date) -> dict | None:
        location = StudentHostelService._active_allocation_location(db, student_id, organization_id)
        if not location:
            return None
        hostel = location[-1]
        return StudentHostelService._menu_for_date(db, organization_id, hostel.id, menu_date)

    @staticmethod
    def get_weekly_mess(db: Session, student_id: int, organization_id: int, week_start: date) -> dict | None:
        location = StudentHostelService._active_allocation_location(db, student_id, organization_id)
        if not location:
            return None
        hostel = location[-1]
        monday = week_start - timedelta(days=week_start.weekday())
        days = [
            StudentHostelService._menu_for_date(
                db, organization_id, hostel.id, monday + timedelta(days=offset)
            )
            for offset in range(7)
        ]
        today = StudentHostelService.today()
        for day in days:
            day["is_today"] = day["date"] == today.isoformat()
        return {
            "week_start": monday.isoformat(),
            "week_end": (monday + timedelta(days=6)).isoformat(),
            "hostel": {"id": hostel.id, "name": hostel.name},
            "days": days,
        }

    @staticmethod
    def _staff_name(db: Session, staff_id: int | None) -> str | None:
        if not staff_id:
            return None
        staff = db.query(OrgSchoolStaff).filter(OrgSchoolStaff.id == staff_id).first()
        if not staff:
            return None
        return " ".join(part for part in (staff.first_name, staff.last_name) if part).strip() or f"Staff #{staff.id}"

    @staticmethod
    def _serialize_complaint(db: Session, complaint: OrgHostelComplaint, detail: bool = False) -> dict:
        data = {
            "id": complaint.id,
            "complaint_no": complaint.complaint_no,
            "academic_year": complaint.academic_year,
            "allocation_id": complaint.allocation_id,
            "target_type": complaint.target_type,
            "target_type_label": dict(OrgHostelComplaint.TARGET_CHOICES).get(complaint.target_type),
            "category": complaint.category,
            "category_label": dict(OrgHostelComplaint.CATEGORY_CHOICES).get(complaint.category),
            "priority": complaint.priority,
            "priority_label": dict(OrgHostelComplaint.PRIORITY_CHOICES).get(complaint.priority),
            "title": complaint.title,
            "description": complaint.description,
            "status": complaint.status,
            "status_label": dict(OrgHostelComplaint.STATUS_CHOICES).get(complaint.status),
            "assigned_to_id": complaint.assigned_to_id,
            "assigned_to_name": StudentHostelService._staff_name(db, complaint.assigned_to_id),
            "assigned_at": complaint.assigned_at,
            "resolved_at": complaint.resolved_at,
            "resolution_notes": complaint.resolution_notes,
            "rejected_at": complaint.rejected_at,
            "rejection_reason": complaint.rejection_reason,
            "created_at": complaint.created_at,
            "updated_at": complaint.updated_at,
        }
        if detail:
            logs = (
                db.query(OrgHostelComplaintActionLog)
                .filter(OrgHostelComplaintActionLog.complaint_id == complaint.id)
                .order_by(OrgHostelComplaintActionLog.created_at.desc(), OrgHostelComplaintActionLog.id.desc())
                .all()
            )
            status_labels = dict(OrgHostelComplaint.STATUS_CHOICES)
            action_labels = dict(OrgHostelComplaintActionLog.ACTION_CHOICES)
            data["action_logs"] = [
                {
                    "id": log.id,
                    "action": log.action,
                    "action_label": action_labels.get(log.action),
                    "previous_status": log.previous_status,
                    "previous_status_label": status_labels.get(log.previous_status),
                    "new_status": log.new_status,
                    "new_status_label": status_labels.get(log.new_status),
                    "remarks": log.remarks,
                    "metadata": log.metadata_json or {},
                    "created_by_name": StudentHostelService._staff_name(db, log.created_by_id),
                    "created_at": log.created_at,
                }
                for log in logs
            ]
        return data

    @staticmethod
    def create_complaint(db: Session, student_id: int, organization_id: int, payload) -> dict | None:
        location = StudentHostelService._active_allocation_location(db, student_id, organization_id)
        if not location:
            return None
        allocation, bed, room, floor, block, hostel = location
        targets = {
            OrgHostelComplaint.TARGET_HOSTEL: ("hostel_id", hostel.id),
            OrgHostelComplaint.TARGET_BLOCK: ("block_id", block.id),
            OrgHostelComplaint.TARGET_FLOOR: ("floor_id", floor.id),
            OrgHostelComplaint.TARGET_ROOM: ("room_id", room.id),
            OrgHostelComplaint.TARGET_BED: ("bed_id", bed.id),
        }
        target = targets.get(payload.target_type)
        if not target:
            raise ValueError("Invalid complaint target")
        now = datetime.now()
        complaint = OrgHostelComplaint(
            organization_id=organization_id,
            complaint_no=f"HCOMP-{organization_id}-{now.strftime('%Y%m%d%H%M%S%f')}",
            student_id=student_id,
            academic_year=allocation.academic_year,
            allocation_id=allocation.id,
            target_type=payload.target_type,
            category=payload.category,
            priority=payload.priority,
            title=payload.title,
            description=payload.description,
            status=OrgHostelComplaint.STATUS_OPEN,
        )
        setattr(complaint, target[0], target[1])
        try:
            db.add(complaint)
            db.flush()
            db.add(OrgHostelComplaintActionLog(
                complaint_id=complaint.id,
                action=OrgHostelComplaintActionLog.ACTION_CREATED,
                new_status=OrgHostelComplaint.STATUS_OPEN,
                remarks="Complaint raised by student",
                metadata_json={},
            ))
            db.commit()
            db.refresh(complaint)
        except Exception:
            db.rollback()
            raise
        return StudentHostelService._serialize_complaint(db, complaint, detail=True)

    @staticmethod
    def get_complaint_snapshot(db: Session, student_id: int, organization_id: int) -> dict:
        query = db.query(OrgHostelComplaint).filter(
            OrgHostelComplaint.organization_id == organization_id,
            OrgHostelComplaint.student_id == student_id,
        )
        total = query.count()
        complaints = query.order_by(OrgHostelComplaint.created_at.desc(), OrgHostelComplaint.id.desc()).limit(3).all()
        return {"complaints": [StudentHostelService._serialize_complaint(db, item) for item in complaints], "total": total}

    @staticmethod
    def list_complaints(db: Session, student_id: int, organization_id: int, page: int, page_size: int, status: int | None = None) -> dict:
        query = db.query(OrgHostelComplaint).filter(
            OrgHostelComplaint.organization_id == organization_id,
            OrgHostelComplaint.student_id == student_id,
        )
        if status is not None:
            query = query.filter(OrgHostelComplaint.status == status)
        total = query.count()
        complaints = query.order_by(OrgHostelComplaint.created_at.desc(), OrgHostelComplaint.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        total_pages = ceil(total / page_size) if total else 0
        return {
            "results": [StudentHostelService._serialize_complaint(db, item) for item in complaints],
            "pagination": {
                "page": page, "page_size": page_size, "total_items": total,
                "total_pages": total_pages, "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    @staticmethod
    def get_complaint_detail(db: Session, student_id: int, organization_id: int, complaint_id: int) -> dict | None:
        complaint = db.query(OrgHostelComplaint).filter(
            OrgHostelComplaint.id == complaint_id,
            OrgHostelComplaint.organization_id == organization_id,
            OrgHostelComplaint.student_id == student_id,
        ).first()
        return StudentHostelService._serialize_complaint(db, complaint, detail=True) if complaint else None
