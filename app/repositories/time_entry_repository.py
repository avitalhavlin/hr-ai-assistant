"""
Data access for TimeEntry. No business rules, no transaction control —
callers (services) own flush()/commit().
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry


def add(db: Session, entry: TimeEntry) -> TimeEntry:
    db.add(entry)
    db.flush()
    return entry


def list_by_user(db: Session, user_id: int) -> list[TimeEntry]:
    return db.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()


def list_by_user_in_range(db: Session, user_id: int, start: date, end: date) -> list[TimeEntry]:
    return (
        db.query(TimeEntry)
        .filter(
            TimeEntry.user_id == user_id,
            TimeEntry.work_date >= start,
            TimeEntry.work_date <= end,
        )
        .all()
    )
