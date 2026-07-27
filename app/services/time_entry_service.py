from sqlalchemy.orm import Session

from app.models.time_entry import TimeEntry
from app.services.update_utils import apply_updates


def update_time_entry(db: Session, user_id: int, entry_id: int, updates: dict) -> TimeEntry | None:
    entry = (
        db.query(TimeEntry)
        .filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id)
        .first()
    )
    if entry is None:
        return None

    apply_updates(entry, updates, nullable_fields=frozenset({"end_time"}))

    if entry.end_time is not None and entry.end_time < entry.start_time:
        raise ValueError("end_time must not be before start_time")

    db.commit()
    db.refresh(entry)
    return entry
