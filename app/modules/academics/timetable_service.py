"""Business logic for timetables, breaks, and timetable slots."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, joinedload

from app.modules.academics.models import (
    OrgClassSubjectMapping,
    OrgSchoolClass,
    OrgSchoolSection,
    OrgSchoolTimetable,
    OrgSchoolTimetableBreak,
    OrgSchoolTimetableSlot,
    OrgSubject,
    SchoolStudentSectionMapping,
)
from app.modules.auth.model import OrgSchoolStudent


IST = ZoneInfo("Asia/Kolkata")


class TimetableService:
    @staticmethod
    def get_today_timetable(
        db: Session,
        student_id: int,
        target_date: date | None = None,
        *,
        organization_id: int | None = None,
    ) -> dict:
        selected_date = target_date or datetime.now(IST).date()
        day_of_week = selected_date.strftime("%A").lower()

        mapping = TimetableService._get_active_section_mapping(
            db, student_id, organization_id
        )
        if not mapping:
            return TimetableService._empty_response(
                student_id,
                selected_date,
                day_of_week,
                message="Student is not assigned to an active section",
            )

        timetable = TimetableService._get_active_timetable(db, mapping.section_id)
        if not timetable:
            return TimetableService._empty_response(
                student_id,
                selected_date,
                day_of_week,
                section_id=mapping.section_id,
                section=mapping.section,
                message="No active timetable found",
            )

        off_days = TimetableService._off_days(timetable)
        if day_of_week in off_days:
            return TimetableService._empty_response(
                student_id,
                selected_date,
                day_of_week,
                timetable=timetable,
                message="Today is an off day",
            )

        breaks = (
            db.query(OrgSchoolTimetableBreak)
            .filter(
                OrgSchoolTimetableBreak.timetable_id == timetable.id,
                OrgSchoolTimetableBreak.status == 1,
            )
            .order_by(
                OrgSchoolTimetableBreak.after_period,
                OrgSchoolTimetableBreak.id,
            )
            .all()
        )
        schedule = TimetableService._build_period_schedule(timetable, breaks)
        if not schedule:
            return TimetableService._empty_response(
                student_id,
                selected_date,
                day_of_week,
                timetable=timetable,
                message="Timetable period duration is not configured",
            )
        slots = (
            db.query(OrgSchoolTimetableSlot)
            .filter(
                OrgSchoolTimetableSlot.timetable_id == timetable.id,
                OrgSchoolTimetableSlot.day_of_week == day_of_week,
                OrgSchoolTimetableSlot.status == 1,
                OrgSchoolTimetableSlot.is_break.is_(False),
                OrgSchoolTimetableSlot.period_number.between(1, timetable.total_periods),
            )
            .order_by(
                OrgSchoolTimetableSlot.period_number,
                OrgSchoolTimetableSlot.id,
            )
            .all()
        )
        subjects = TimetableService._subjects_for_slots(db, timetable, slots)

        serialized_slots = [
            TimetableService._serialize_slot(
                slot,
                subjects.get(slot.subject_mapping_id),
                schedule.get(slot.period_number),
            )
            for slot in slots
        ]
        current_slot, next_slot = TimetableService._current_and_next_slots(
            serialized_slots,
            selected_date,
        )

        section = timetable.section
        org_class = section.org_class if section else None
        master_class = org_class.master_class if org_class else None
        return {
            "student_id": student_id,
            "academic_year": org_class.academic_year if org_class else None,
            "date": selected_date.isoformat(),
            "day_of_week": day_of_week,
            "is_working_day": bool(serialized_slots),
            "message": None,
            "timetable": {
                "id": timetable.id,
                "name": timetable.name,
                "section_id": timetable.section_id,
                "section_name": section.name if section else None,
                "class_id": org_class.id if org_class else None,
                "class_name": master_class.name if master_class else None,
                "start_time": TimetableService._format_time(timetable.start_time),
                "end_time": TimetableService._format_time(timetable.end_time),
            },
            "current_slot": current_slot,
            "next_slot": next_slot,
            "slots": serialized_slots,
            "total_slots": len(serialized_slots),
        }

    @staticmethod
    def get_weekly_timetable(
        db: Session,
        student_id: int,
        target_date: date | None = None,
        *,
        organization_id: int | None = None,
    ) -> dict:
        selected_date = target_date or datetime.now(IST).date()
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)

        mapping = TimetableService._get_active_section_mapping(
            db, student_id, organization_id
        )
        if not mapping:
            return TimetableService._empty_weekly_response(
                week_start,
                week_end,
                message="Student is not assigned to an active section",
            )

        timetable = TimetableService._get_active_timetable(db, mapping.section_id)
        if not timetable:
            return TimetableService._empty_weekly_response(
                week_start,
                week_end,
                section_id=mapping.section_id,
                section=mapping.section,
                message="No active timetable found",
            )

        breaks = (
            db.query(OrgSchoolTimetableBreak)
            .filter(
                OrgSchoolTimetableBreak.timetable_id == timetable.id,
                OrgSchoolTimetableBreak.status == 1,
            )
            .order_by(
                OrgSchoolTimetableBreak.after_period,
                OrgSchoolTimetableBreak.id,
            )
            .all()
        )
        schedule = TimetableService._build_period_schedule(timetable, breaks)
        if not schedule:
            return TimetableService._empty_weekly_response(
                week_start,
                week_end,
                section=mapping.section,
                message="Timetable period duration is not configured",
            )
        off_days = TimetableService._off_days(timetable)
        slots = (
            db.query(OrgSchoolTimetableSlot)
            .filter(
                OrgSchoolTimetableSlot.timetable_id == timetable.id,
                OrgSchoolTimetableSlot.status == 1,
                OrgSchoolTimetableSlot.is_break.is_(False),
                OrgSchoolTimetableSlot.day_of_week.notin_(off_days),
                OrgSchoolTimetableSlot.period_number.between(1, timetable.total_periods),
            )
            .order_by(
                OrgSchoolTimetableSlot.day_of_week,
                OrgSchoolTimetableSlot.period_number,
                OrgSchoolTimetableSlot.id,
            )
            .all()
        )
        subjects = TimetableService._subjects_for_slots(db, timetable, slots)

        slot_lookup = {}
        for slot in slots:
            payload = TimetableService._serialize_slot(
                slot,
                subjects.get(slot.subject_mapping_id),
                schedule.get(slot.period_number),
            )
            slot_lookup.setdefault(
                (slot.period_number, slot.day_of_week),
                [],
            ).append(payload)

        days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        periods = []
        for period_number in range(1, timetable.total_periods + 1):
            period_meta = schedule.get(period_number, {})
            row = {
                "period_number": period_number,
                "duration": period_meta.get("duration"),
                "start_time": period_meta.get("start_time"),
                "end_time": period_meta.get("end_time"),
                "break_after": period_meta.get("break_after"),
            }
            for day in days:
                day_slots = slot_lookup.get((period_number, day), [])
                core = next(
                    (slot for slot in day_slots if slot["type"] == "core"),
                    None,
                )
                electives = [
                    slot for slot in day_slots if slot["type"] == "elective"
                ]
                row[day] = (
                    {"core": core, "electives": electives}
                    if day_slots
                    else None
                )
            periods.append(row)

        section = timetable.section
        org_class = section.org_class if section else None
        return {
            "timetable": {
                "id": timetable.id,
                "name": timetable.name,
                "section_id": timetable.section_id,
                "section_name": section.name if section else None,
                "class_id": org_class.id if org_class else None,
                "class_name": (
                    org_class.master_class.name
                    if org_class and org_class.master_class
                    else None
                ),
                "academic_year": (
                    org_class.academic_year if org_class else None
                ),
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_periods": timetable.total_periods,
                "period_duration": timetable.period_duration,
                "break_count": sum(
                    meta["break_after"] is not None for meta in schedule.values()
                ),
                "start_time": TimetableService._format_time(
                    timetable.start_time
                ),
                "end_time": TimetableService._format_time(timetable.end_time),
                "status": timetable.status,
                "is_default": timetable.is_default,
            },
            "off_days": off_days,
            "breaks": [
                meta["break_after"] for meta in schedule.values() if meta["break_after"]
            ],
            "periods": periods,
        }

    @staticmethod
    def _get_active_section_mapping(db, student_id, organization_id):
        query = (
            db.query(SchoolStudentSectionMapping)
            .join(SchoolStudentSectionMapping.student)
            .join(SchoolStudentSectionMapping.section)
            .join(OrgSchoolSection.org_class)
            .options(
                joinedload(SchoolStudentSectionMapping.section)
                .joinedload(OrgSchoolSection.org_class)
                .joinedload(OrgSchoolClass.master_class)
            )
            .filter(
                SchoolStudentSectionMapping.student_id == student_id,
                SchoolStudentSectionMapping.status == "Active",
                OrgSchoolSection.is_active.is_(True),
                OrgSchoolClass.is_active.is_(True),
                OrgSchoolClass.organization_id == OrgSchoolStudent.organization_id,
            )
        )
        if organization_id is not None:
            query = query.filter(OrgSchoolClass.organization_id == organization_id)
        return query.order_by(SchoolStudentSectionMapping.id.desc()).first()

    @staticmethod
    def _get_active_timetable(db, section_id):
        return (
            db.query(OrgSchoolTimetable)
            .options(
                joinedload(OrgSchoolTimetable.section)
                .joinedload(OrgSchoolSection.org_class)
                .joinedload(OrgSchoolClass.master_class)
            )
            .filter(
                OrgSchoolTimetable.section_id == section_id,
                # Draft (2), archived (3), and inactive (0) are not student-facing.
                OrgSchoolTimetable.status == 1,
            )
            .order_by(
                OrgSchoolTimetable.is_default.desc(),
                OrgSchoolTimetable.created_at.desc(),
                OrgSchoolTimetable.id.desc(),
            )
            .first()
        )

    @staticmethod
    def _subjects_for_slots(db, timetable, slots):
        mapping_ids = {slot.subject_mapping_id for slot in slots if slot.subject_mapping_id}
        if not mapping_ids:
            return {}
        org_class = timetable.section.org_class
        rows = (
            db.query(OrgClassSubjectMapping.id, OrgSubject.id, OrgSubject.name)
            .join(OrgSubject, OrgClassSubjectMapping.subject_id == OrgSubject.id)
            .filter(
                OrgClassSubjectMapping.id.in_(mapping_ids),
                OrgClassSubjectMapping.class_id == org_class.id,
                OrgSubject.organization_id == org_class.organization_id,
            )
            .all()
        )
        return {
            mapping_id: {"subject_id": subject_id, "subject_name": subject_name}
            for mapping_id, subject_id, subject_name in rows
        }

    @staticmethod
    def _off_days(timetable):
        return list(
            dict.fromkeys(
                value.strip().lower()
                for value in (timetable.off_days or "").split(",")
                if value.strip()
            )
        )

    @staticmethod
    def _build_period_schedule(timetable, breaks) -> dict:
        period_duration = timetable.period_duration
        if not period_duration or period_duration < 0 or timetable.total_periods <= 0:
            return {}

        break_by_period = {item.after_period: item for item in breaks}
        cursor = datetime.combine(date.today(), timetable.start_time)
        schedule = {}
        for period_number in range(1, timetable.total_periods + 1):
            period_start = cursor
            period_end = period_start + timedelta(minutes=period_duration)
            break_data = None
            break_row = break_by_period.get(period_number)
            if break_row:
                break_end = period_end + timedelta(minutes=break_row.duration)
                break_data = {
                    "id": break_row.id,
                    "name": break_row.name,
                    "after_period": break_row.after_period,
                    "duration": break_row.duration,
                    "start_time": TimetableService._format_time(period_end.time()),
                    "end_time": TimetableService._format_time(break_end.time()),
                }
                cursor = break_end
            else:
                cursor = period_end

            schedule[period_number] = {
                "duration": period_duration,
                "start_time": TimetableService._format_time(period_start.time()),
                "end_time": TimetableService._format_time(period_end.time()),
                "break_after": break_data,
            }
        return schedule

    @staticmethod
    def _serialize_slot(slot, subject, period_meta) -> dict:
        period_meta = period_meta or {}
        subject = subject or {}
        return {
            "slot_id": slot.id,
            "timetable_id": slot.timetable_id,
            "subject_mapping_id": slot.subject_mapping_id,
            "subject_id": subject.get("subject_id"),
            "subject_name": subject.get("subject_name"),
            "teacher_id": slot.teacher_id,
            "teacher_name": None,
            "substitute_teacher_id": slot.substitute_teacher_id,
            "substitute_teacher_name": None,
            "day_of_week": slot.day_of_week,
            "period_number": slot.period_number,
            "duration": period_meta.get("duration") or slot.duration,
            "start_time": period_meta.get("start_time"),
            "end_time": period_meta.get("end_time"),
            "period_subject_type": slot.period_subject_type,
            "type": slot.period_subject_type,
            "is_break": slot.is_break,
            "remarks": slot.remarks,
            "break_after": period_meta.get("break_after"),
        }

    @staticmethod
    def _current_and_next_slots(slots: list[dict], selected_date: date):
        if not slots or selected_date != datetime.now(IST).date():
            return None, slots[0] if slots else None

        current_time = datetime.now(IST).time().replace(tzinfo=None)
        current_slot = None
        next_slot = None
        for slot in slots:
            start_time = TimetableService._parse_time(slot["start_time"])
            end_time = TimetableService._parse_time(slot["end_time"])
            if start_time and end_time and start_time <= current_time < end_time:
                current_slot = slot
            elif start_time and start_time > current_time and next_slot is None:
                next_slot = slot
        return current_slot, next_slot

    @staticmethod
    def _empty_response(
        student_id: int,
        selected_date: date,
        day_of_week: str,
        section_id: int | None = None,
        section=None,
        timetable=None,
        message: str | None = None,
    ) -> dict:
        section = timetable.section if timetable and timetable.section else section
        org_class = section.org_class if section else None
        master_class = org_class.master_class if org_class else None
        return {
            "student_id": student_id,
            "academic_year": (
                org_class.academic_year if org_class else None
            ),
            "date": selected_date.isoformat(),
            "day_of_week": day_of_week,
            "is_working_day": False,
            "message": message,
            "timetable": {
                "id": timetable.id if timetable else None,
                "name": timetable.name if timetable else None,
                "section_id": (
                    timetable.section_id
                    if timetable
                    else section.id if section else section_id
                ),
                "section_name": section.name if section else None,
                "class_id": org_class.id if org_class else None,
                "class_name": master_class.name if master_class else None,
                "start_time": (
                    TimetableService._format_time(timetable.start_time)
                    if timetable
                    else None
                ),
                "end_time": (
                    TimetableService._format_time(timetable.end_time)
                    if timetable
                    else None
                ),
            },
            "current_slot": None,
            "next_slot": None,
            "slots": [],
            "total_slots": 0,
        }

    @staticmethod
    def _empty_weekly_response(
        week_start: date,
        week_end: date,
        section_id: int | None = None,
        section=None,
        message: str | None = None,
    ) -> dict:
        org_class = section.org_class if section else None
        master_class = org_class.master_class if org_class else None
        return {
            "timetable": {
                "id": None,
                "name": None,
                "section_id": section.id if section else section_id,
                "section_name": section.name if section else None,
                "class_id": org_class.id if org_class else None,
                "class_name": master_class.name if master_class else None,
                "academic_year": (
                    org_class.academic_year if org_class else None
                ),
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_periods": 0,
                "period_duration": None,
                "break_count": 0,
                "start_time": None,
                "end_time": None,
                "status": None,
                "is_default": False,
            },
            "off_days": [],
            "breaks": [],
            "periods": [],
            "message": message,
        }

    @staticmethod
    def _format_time(value) -> str | None:
        return value.strftime("%H:%M") if value else None

    @staticmethod
    def _parse_time(value: str | None):
        return datetime.strptime(value, "%H:%M").time() if value else None
