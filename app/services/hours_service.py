"""
Business logic for aggregating worked hours.

This module is the single source of truth for "how many hours did employee X
work in period Y". Both the REST API and the chatbot's tools (Phase 5) call
into these functions — never duplicate this logic in the AI layer.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry

# NOTE: we deliberately avoid SQL-side extract("week"/"isoyear", ...) here.
# SQLite (used in tests) doesn't support those extract fields, and relying on
# DB-specific date functions makes this code fragile across Postgres/SQLite.
# Instead we compute the date range in Python (using ISO week semantics) and
# do a plain date >= / <= filter, which every backend supports identically.


def _entry_hours(entry: TimeEntry) -> float:
    """Hours worked for a single time entry. Returns 0 if not yet clocked out."""
    if entry.end_time is None:
        return 0.0
    delta = entry.end_time - entry.start_time
    return round(delta.total_seconds() / 3600, 2)


def _iso_week_range(year: int, week: int) -> tuple[date, date]:
    """Return (monday, sunday) for a given ISO year/week."""
    monday = date.fromisocalendar(year, week, 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_hours_for_week(db: Session, user_id: int, year: int, week: int) -> float:
    start, end = _iso_week_range(year, week)
    return get_hours_between(db, user_id, start, end)


def get_hours_for_month(db: Session, user_id: int, year: int, month: int) -> float:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
    return get_hours_between(db, user_id, start, end)


def get_hours_for_year(db: Session, user_id: int, year: int) -> float:
    return get_hours_between(db, user_id, date(year, 1, 1), date(year, 12, 31))


def get_hours_between(db: Session, user_id: int, start: date, end: date) -> float:
    entries = (
        db.query(TimeEntry)
        .filter(
            TimeEntry.user_id == user_id,
            TimeEntry.work_date >= start,
            TimeEntry.work_date <= end,
        )
        .all()
    )
    return round(sum(_entry_hours(e) for e in entries), 2)
