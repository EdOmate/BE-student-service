"""Business logic for student event calendar APIs."""

from calendar import monthrange
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.modules.auth.dependencies import AuthenticatedStudent
from app.modules.events.repository import EventRepository
from app.modules.students.repository import StudentRepository


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
            event_start = event.start_at.date()
            event_end = event.end_at.date() if event.end_at else event_start
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
        days = []
        current = start_date
        while current <= end_date:
            day_holidays = [
                {
                    **item,
                    "start_date": item["start_date"].isoformat(),
                    "end_date": item["end_date"].isoformat(),
                }
                for item in holidays
                if item["start_date"] <= current <= item["end_date"]
            ]
            days.append(
                {
                    "date": current.isoformat(),
                    "day": current.day,
                    "day_name": current.strftime("%A"),
                    "is_weekend": current.weekday() >= 5,
                    "is_holiday": bool(day_holidays),
                    "holidays": day_holidays,
                }
            )
            current += timedelta(days=1)
        return {"month": month, "days": days}

    @staticmethod
    def get_upcoming_holidays(
        db: Session,
        auth: AuthenticatedStudent,
        limit: int,
    ) -> list[dict]:
        today = date.today()
        end_date = today + timedelta(days=366)
        holidays = EventService._holiday_items(db, auth, today, end_date)
        upcoming = [item for item in holidays if item["start_date"] >= today]
        upcoming.sort(key=lambda item: (item["start_date"], item["name"]))
        return [
            {
                **item,
                "start_date": item["start_date"].isoformat(),
                "end_date": item["end_date"].isoformat(),
                "days_remaining": (item["start_date"] - today).days,
            }
            for item in upcoming[:limit]
        ]

    @staticmethod
    def get_upcoming_events(
        db: Session,
        auth: AuthenticatedStudent,
    ) -> dict:
        today = date.today()
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

        events = EventRepository.get_upcoming_published_events(
            db,
            context["organization_id"],
            datetime.combine(today, time.min),
            datetime.combine(end_date, time.max),
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
                "start_at": event.start_at.isoformat() if event.start_at else None,
                "end_at": event.end_at.isoformat() if event.end_at else None,
                "is_all_day": event.is_all_day,
                "location": event.location,
                "published_at": (
                    event.published_at.isoformat() if event.published_at else None
                ),
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
                if not ptm or ptm.scheduled_start_at.date() < today:
                    continue
                item.update(
                    {
                        "ptm_id": ptm.id,
                        "section_id": ptm.section_id,
                        "scheduled_start_at": ptm.scheduled_start_at.isoformat(),
                        "scheduled_end_at": ptm.scheduled_end_at.isoformat(),
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
                        "auto_expire_at": (
                            channel.auto_expire_at.isoformat()
                            if channel.auto_expire_at
                            else None
                        ),
                    }
                )
                grouped["broadcast"].append(item)

        return {
            "days": 15,
            "from_date": today.isoformat(),
            "to_date": end_date.isoformat(),
            **grouped,
        }
