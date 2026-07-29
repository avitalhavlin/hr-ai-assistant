"""
Business logic for TimeEntry create/list.
"""

from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.repositories import time_entry_repository
from app.schemas.time_entry import TimeEntryCreate


def create_time_entry(db: Session, user_id: int, payload: TimeEntryCreate) -> TimeEntry:
    entry = time_entry_repository.add(
        db, TimeEntry(user_id=user_id, **payload.model_dump())
    )
    db.commit()
    db.refresh(entry)
    return entry


def list_time_entries(db: Session, user_id: int) -> list[TimeEntry]:
    return time_entry_repository.list_by_user(db, user_id)
