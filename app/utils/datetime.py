"""Timezone helpers for timestamps stored as UTC in shared service tables."""

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def utc_now_naive() -> datetime:
    """Return the current UTC instant for naïve UTC database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ist_today() -> date:
    return datetime.now(IST).date()


def as_ist(value: datetime | None) -> datetime | None:
    """Convert a UTC database timestamp to an IST-aware datetime."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(IST)


def ist_isoformat(value: datetime | None) -> str | None:
    converted = as_ist(value)
    return converted.isoformat() if converted else None


def ist_date(value: datetime | None) -> date | None:
    converted = as_ist(value)
    return converted.date() if converted else None


def ist_day_bounds_utc(value: date) -> tuple[datetime, datetime]:
    """Return the UTC-naïve range covering one calendar day in IST."""
    start = datetime.combine(value, time.min, tzinfo=IST).astimezone(timezone.utc)
    end = datetime.combine(value, time.max, tzinfo=IST).astimezone(timezone.utc)
    return (
        start.replace(tzinfo=None),
        end.replace(tzinfo=None),
    )
