"""Database access for student calendar and holiday APIs."""

from datetime import date, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.events.models import (
    EventTarget,
    OrgEvent,
    OrgEventAttachment,
    OrgEventPTM,
    OrgEventHoliday,
    OrgPublicHoliday,
    BroadcastChannel,
    Notice,
)


class EventRepository:
    @staticmethod
    def get_public_holidays(
        db: Session,
        organization_id: int,
        start_date: date,
        end_date: date,
        academic_year: str | None = None,
    ):
        query = db.query(OrgPublicHoliday).filter(
            OrgPublicHoliday.organization_id == organization_id,
            OrgPublicHoliday.holiday_date.between(start_date, end_date),
        )
        if academic_year:
            query = query.filter(
                OrgPublicHoliday.academic_year == academic_year,
            )
        return query.order_by(OrgPublicHoliday.holiday_date, OrgPublicHoliday.id).all()

    @staticmethod
    def get_event_holidays(
        db: Session,
        organization_id: int,
        start_date: date,
        end_date: date,
    ):
        start_at = datetime.combine(start_date, datetime.min.time())
        end_at = datetime.combine(end_date, datetime.max.time())
        return (
            db.query(OrgEvent, OrgEventHoliday)
            .join(OrgEventHoliday, OrgEventHoliday.event_id == OrgEvent.id)
            .filter(
                OrgEvent.organization_id == organization_id,
                OrgEvent.event_type == 1,
                OrgEvent.status == 3,
                OrgEvent.start_at.is_not(None),
                OrgEvent.start_at <= end_at,
                (OrgEvent.end_at.is_(None)) | (OrgEvent.end_at >= start_at),
            )
            .order_by(OrgEvent.start_at, OrgEvent.id)
            .all()
        )

    @staticmethod
    def get_targets_by_event_ids(db: Session, event_ids: list[int]) -> dict[int, list]:
        if not event_ids:
            return {}
        targets = (
            db.query(EventTarget)
            .filter(
                EventTarget.event_id.in_(event_ids),
                EventTarget.status == 1,
            )
            .all()
        )
        grouped: dict[int, list] = {}
        for target in targets:
            grouped.setdefault(target.event_id, []).append(target)
        return grouped

    @staticmethod
    def get_upcoming_published_events(
        db: Session,
        organization_id: int,
        start_at: datetime,
        end_at: datetime,
    ):
        return (
            db.query(OrgEvent)
            .filter(
                OrgEvent.organization_id == organization_id,
                OrgEvent.status == 3,
                OrgEvent.event_type.in_((2, 3, 5)),
                or_(
                    OrgEvent.start_at.between(start_at, end_at),
                    OrgEvent.published_at.between(start_at, end_at),
                ),
                or_(OrgEvent.expires_at.is_(None), OrgEvent.expires_at >= start_at),
            )
            .order_by(OrgEvent.start_at, OrgEvent.id)
            .all()
        )

    @staticmethod
    def get_event_details(db: Session, event_ids: list[int]) -> dict:
        if not event_ids:
            return {"notices": {}, "ptms": {}, "broadcasts": {}, "attachments": {}}

        notices = {
            row.event_id: row
            for row in db.query(Notice).filter(Notice.event_id.in_(event_ids)).all()
        }
        ptms = {
            row.event_id: row
            for row in db.query(OrgEventPTM).filter(OrgEventPTM.event_id.in_(event_ids)).all()
        }
        broadcasts = {
            row.event_id: row
            for row in db.query(BroadcastChannel)
            .filter(BroadcastChannel.event_id.in_(event_ids))
            .all()
        }
        attachments: dict[int, list] = {}
        for row in (
            db.query(OrgEventAttachment)
            .filter(
                OrgEventAttachment.event_id.in_(event_ids),
                OrgEventAttachment.status == 1,
            )
            .all()
        ):
            attachments.setdefault(row.event_id, []).append(row)
        return {
            "notices": notices,
            "ptms": ptms,
            "broadcasts": broadcasts,
            "attachments": attachments,
        }
