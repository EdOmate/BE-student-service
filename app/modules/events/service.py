"""Business logic for student event calendar APIs."""

from calendar import monthrange
from datetime import date, timedelta
from math import ceil

from sqlalchemy.orm import Session

from app.modules.auth.dependencies import AuthenticatedStudent
from app.modules.events.repository import EventRepository
from app.modules.students.repository import StudentRepository
from app.utils.datetime import ist_date, ist_day_bounds_utc, ist_isoformat, ist_today


class EventService:
    HOLIDAY_TYPES = {1: "Public", 2: "School", 3: "Restricted"}

    @staticmethod
    def _student_context(db: Session, auth: AuthenticatedStudent):
        mapping = StudentRepository.get_active_section_mapping(db, auth.student_id)
        section_id = mapping.section_id if mapping else None
        org_class = mapping.section.org_class if mapping and mapping.section else None
        return {
            "organization_id": auth.student.organization_id,
            "academic_year": org_class.academic_year if org_class else None,
            "section_id": section_id,
            "class_id": org_class.id if org_class else None,
        }

    @staticmethod
    def _is_relevant(targets: list, section_id: int | None, class_id: int | None) -> bool:
        if not targets:
            return True
        return any(
            (target.target_type == 1 and target.target_id == section_id)
            or (target.target_type == 3 and target.target_id == class_id)
            for target in targets
        )

    @staticmethod
    def _holiday_items(db, auth, start_date: date, end_date: date) -> list[dict]:
        context = EventService._student_context(db, auth)
        public_holidays = EventRepository.get_public_holidays(
            db,
            context["organization_id"],
            start_date,
            end_date,
            context["academic_year"],
        )
        event_rows = EventRepository.get_event_holidays(
            db,
            context["organization_id"],
            start_date,
            end_date,
        )
        targets = EventRepository.get_targets_by_event_ids(
            db,
            [event.id for event, _ in event_rows],
        )

        items = [
            {
                "source": "public_holiday",
                "id": holiday.id,
                "name": holiday.name,
                "description": holiday.description,
                "start_date": holiday.holiday_date,
                "end_date": holiday.holiday_date,
                "half_day": holiday.half_day,
                "holiday_type": "Public",
            }
            for holiday in public_holidays
        ]
        for event, holiday in event_rows:
            if not EventService._is_relevant(
                targets.get(event.id, []),
                context["section_id"],
                context["class_id"],
            ):
                continue
            event_start = ist_date(event.start_at)
            event_end = ist_date(event.end_at) if event.end_at else event_start
            items.append(
                {
                    "source": "event_holiday",
                    "id": event.id,
                    "name": event.title,
                    "description": event.description,
                    "start_date": event_start,
                    "end_date": event_end,
                    "half_day": False,
                    "holiday_type": EventService.HOLIDAY_TYPES.get(
                        holiday.holiday_type,
                        "Unknown",
                    ),
                    "is_paid_leave": bool(holiday.is_paid_leave),
                    "location": event.location,
                }
            )
        return items

    @staticmethod
    def get_month_calendar(db: Session, auth: AuthenticatedStudent, month: str) -> dict:
        try:
            year, month_number = (int(value) for value in month.split("-", 1))
            start_date = date(year, month_number, 1)
        except (TypeError, ValueError):
            raise ValueError("month must be in YYYY-MM format")

        end_date = date(year, month_number, monthrange(year, month_number)[1])
        holidays = EventService._holiday_items(db, auth, start_date, end_date)
        context = EventService._student_context(db, auth)
        range_start = ist_day_bounds_utc(start_date)[0]
        range_end = ist_day_bounds_utc(end_date)[1]
        calendar_events = EventRepository.get_published_events_for_month(
            db,
            context["organization_id"],
            range_start,
            range_end,
        )
        event_ids = [event.id for event in calendar_events]
        targets = EventRepository.get_targets_by_event_ids(db, event_ids)
        details = EventRepository.get_event_details(db, event_ids)

        dated_events: list[dict] = []
        for item in holidays:
            dated_events.append(
                {
                    **item,
                    "category": "holiday",
                    "event_date": item["start_date"],
                }
            )

        for event in calendar_events:
            if not EventService._is_relevant(
                targets.get(event.id, []),
                context["section_id"],
                context["class_id"],
            ):
                continue

            event_date = (
                ist_date(event.start_at)
                if event.start_at
                else ist_date(event.published_at) if event.published_at else None
            )
            if event_date is None:
                continue

            item = {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_at": ist_isoformat(event.start_at),
                "end_at": ist_isoformat(event.end_at),
                "is_all_day": event.is_all_day,
                "location": event.location,
                "published_at": ist_isoformat(event.published_at),
                "event_date": event_date,
                "attachments": [
                    {
                        "id": attachment.id,
                        "file_name": attachment.file_name,
                        "file_url": attachment.file_url,
                        "mime_type": attachment.mime_type,
                        "size": attachment.size,
                    }
                    for attachment in details["attachments"].get(event.id, [])
                ],
            }

            if event.event_type == 2:
                notice = details["notices"].get(event.id)
                if not notice:
                    continue
                item.update(
                    {
                        "category": "formal_circular",
                        "notice_id": notice.id,
                        "authorized_signee": notice.authorized_signee,
                        "expiration_date": notice.expiration_date.isoformat(),
                        "is_pinned": notice.is_pinned,
                    }
                )
            elif event.event_type == 3:
                ptm = details["ptms"].get(event.id)
                if not ptm:
                    continue
                item.update(
                    {
                        "category": "ptm",
                        "ptm_id": ptm.id,
                        "section_id": ptm.section_id,
                        "scheduled_start_at": ist_isoformat(ptm.scheduled_start_at),
                        "scheduled_end_at": ist_isoformat(ptm.scheduled_end_at),
                        "meeting_mode": ptm.meeting_mode,
                        "venue": ptm.venue,
                        "meeting_link": ptm.meeting_link,
                        "agenda": ptm.agenda,
                        "instructions": ptm.instructions,
                        "requires_appointment": ptm.requires_appointment,
                        "appointment_duration_minutes": (
                            ptm.appointment_duration_minutes
                        ),
                        "event_date": ist_date(ptm.scheduled_start_at),
                    }
                )
            elif event.event_type == 5:
                channel = details["broadcasts"].get(event.id)
                if not channel or not channel.is_active_flag:
                    continue
                item.update(
                    {
                        "category": "broadcast",
                        "channel_id": channel.id,
                        "channel_name": channel.channel_name_tag,
                        "lifecycle_state": channel.lifecycle_state,
                        "auto_expire_at": ist_isoformat(channel.auto_expire_at),
                    }
                )
            else:
                continue

            dated_events.append(item)

        days = []
        current = start_date
        while current <= end_date:
            day_events = [
                {
                    **item,
                    **(
                        {
                            "start_date": item["start_date"].isoformat(),
                            "end_date": item["end_date"].isoformat(),
                        }
                        if item["category"] == "holiday"
                        else {}
                    ),
                }
                for item in dated_events
                if (
                    item["start_date"] <= current <= item["end_date"]
                    if item["category"] == "holiday"
                    else item["event_date"] == current
                )
            ]
            for item in day_events:
                item.pop("event_date", None)
            days.append(
                {
                    "date": current.isoformat(),
                    "day": current.day,
                    "day_name": current.strftime("%A"),
                    "is_weekend": current.weekday() >= 5,
                    "has_events": bool(day_events),
                    "events": day_events,
                }
            )
            current += timedelta(days=1)
        return {"month": month, "days": days}

    @staticmethod
    def get_month_event_listing(
        db: Session,
        auth: AuthenticatedStudent,
        category: str,
        year: int,
        month: int,
        page: int,
        page_size: int,
    ) -> dict:
        if month < 1 or month > 12:
            raise ValueError("month must be between 1 and 12")

        calendar = EventService.get_month_calendar(
            db,
            auth,
            f"{year:04d}-{month:02d}",
        )
        unique_items: dict[tuple, dict] = {}
        for day in calendar["days"]:
            for item in day["events"]:
                if item["category"] != category:
                    continue
                identity = (
                    item["category"],
                    item.get("source"),
                    item["id"],
                )
                if identity in unique_items:
                    continue
                event_date = (
                    item.get("scheduled_start_at")
                    or item.get("start_at")
                    or item.get("start_date")
                    or item.get("published_at")
                    or day["date"]
                )
                event_day = date.fromisoformat(event_date[:10])
                unique_items[identity] = {
                    **item,
                    "event_date": event_day.isoformat(),
                    "timeline_status": (
                        "past" if event_day < ist_today() else "upcoming"
                    ),
                }

        items = list(unique_items.values())
        previous = sorted(
            (item for item in items if item["timeline_status"] == "past"),
            key=lambda item: (item["event_date"], item["id"]),
            reverse=True,
        )
        upcoming = sorted(
            (item for item in items if item["timeline_status"] == "upcoming"),
            key=lambda item: (item["event_date"], item["id"]),
        )
        ordered_items = previous + upcoming
        total_items = len(ordered_items)
        total_pages = ceil(total_items / page_size) if total_items else 0
        start = (page - 1) * page_size

        return {
            "year": year,
            "month": month,
            "items": ordered_items[start : start + page_size],
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
    def get_upcoming_events(
        db: Session,
        auth: AuthenticatedStudent,
    ) -> dict:
        today = ist_today()
        end_date = today + timedelta(days=14)
        context = EventService._student_context(db, auth)

        holidays = EventService._holiday_items(db, auth, today, end_date)
        holiday_items = [
            {
                **item,
                "start_date": item["start_date"].isoformat(),
                "end_date": item["end_date"].isoformat(),
            }
            for item in holidays
            if item["start_date"] >= today
        ]

        range_start = ist_day_bounds_utc(today)[0]
        range_end = ist_day_bounds_utc(end_date)[1]
        events = EventRepository.get_upcoming_published_events(
            db,
            context["organization_id"],
            range_start,
            range_end,
        )
        event_ids = [event.id for event in events]
        targets = EventRepository.get_targets_by_event_ids(db, event_ids)
        details = EventRepository.get_event_details(db, event_ids)
        grouped = {
            "holiday": holiday_items,
            "formal_circular": [],
            "ptm": [],
            "broadcast": [],
        }

        for event in events:
            if not EventService._is_relevant(
                targets.get(event.id, []),
                context["section_id"],
                context["class_id"],
            ):
                continue

            item = {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "start_at": ist_isoformat(event.start_at),
                "end_at": ist_isoformat(event.end_at),
                "is_all_day": event.is_all_day,
                "location": event.location,
                "published_at": ist_isoformat(event.published_at),
                "attachments": [
                    {
                        "id": attachment.id,
                        "file_name": attachment.file_name,
                        "file_url": attachment.file_url,
                        "mime_type": attachment.mime_type,
                        "size": attachment.size,
                    }
                    for attachment in details["attachments"].get(event.id, [])
                ],
            }

            if event.event_type == 2:
                notice = details["notices"].get(event.id)
                if not notice or notice.expiration_date < today:
                    continue
                item.update(
                    {
                        "notice_id": notice.id,
                        "authorized_signee": notice.authorized_signee,
                        "expiration_date": notice.expiration_date.isoformat(),
                        "is_pinned": notice.is_pinned,
                    }
                )
                grouped["formal_circular"].append(item)
            elif event.event_type == 3:
                ptm = details["ptms"].get(event.id)
                if not ptm or ist_date(ptm.scheduled_start_at) < today:
                    continue
                item.update(
                    {
                        "ptm_id": ptm.id,
                        "section_id": ptm.section_id,
                        "scheduled_start_at": ist_isoformat(ptm.scheduled_start_at),
                        "scheduled_end_at": ist_isoformat(ptm.scheduled_end_at),
                        "meeting_mode": ptm.meeting_mode,
                        "venue": ptm.venue,
                        "meeting_link": ptm.meeting_link,
                        "agenda": ptm.agenda,
                        "instructions": ptm.instructions,
                        "requires_appointment": ptm.requires_appointment,
                        "appointment_duration_minutes": ptm.appointment_duration_minutes,
                    }
                )
                grouped["ptm"].append(item)
            elif event.event_type == 5:
                channel = details["broadcasts"].get(event.id)
                if not channel or not channel.is_active_flag:
                    continue
                item.update(
                    {
                        "channel_id": channel.id,
                        "channel_name": channel.channel_name_tag,
                        "lifecycle_state": channel.lifecycle_state,
                        "auto_expire_at": ist_isoformat(channel.auto_expire_at),
                    }
                )
                grouped["broadcast"].append(item)

        return {
            "days": 15,
            "from_date": today.isoformat(),
            "to_date": end_date.isoformat(),
            **grouped,
        }
