"""Defaults for shared models stored by the Django backend in UTC."""

from datetime import datetime, timezone


def utc_now():
    # MySQL DATETIME stores the main backend's UTC values without an offset.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_today():
    return utc_now().date()
