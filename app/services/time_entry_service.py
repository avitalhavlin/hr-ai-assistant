"""
Business logic for TimeEntry create/list.

Raises plain ValueError for domain errors — the API layer translates these
into the appropriate HTTP status, same convention as vacation_service.
"""

from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.repositories import time_entry_repository
from app.schemas.time_entry import TimeEntryCreate


def create_time_entry(db: Session, user_id: int, payload: TimeEntryCreate) -> TimeEntry:
    if payload.end_time is not None and payload.end_time < payload.start_time:
        raise ValueError("end_time must not be before start_time")

    entry = time_entry_repository.add(
        db, TimeEntry(user_id=user_id, **payload.model_dump())
    )
    db.commit()
    db.refresh(entry)
    return entry


def list_time_entries(db: Session, user_id: int) -> list[TimeEntry]:
    return time_entry_repository.list_by_user(db, user_id)
