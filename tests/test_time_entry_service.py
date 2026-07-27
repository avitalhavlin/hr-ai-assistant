from datetime import date, datetime

import pytest

from app.models.time_entry import TimeEntry
from app.models.user import Role, User
from app.services import time_entry_service


def _make_user(db):
    user = User(
        full_name="Test User",
        email="test@example.com",
        hashed_password="x",
        role=Role.employee,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_entry(db, user_id):
    entry = TimeEntry(
        user_id=user_id,
        work_date=date(2026, 8, 1),
        start_time=datetime(2026, 8, 1, 9, 0),
        end_time=None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def test_update_time_entry_sets_end_time(db_session):
    user = _make_user(db_session)
    entry = _make_entry(db_session, user.id)

    updated = time_entry_service.update_time_entry(
        db_session, user.id, entry.id, {"end_time": datetime(2026, 8, 1, 17, 0)}
    )

    assert updated.end_time == datetime(2026, 8, 1, 17, 0)


def test_update_time_entry_rejects_end_before_start(db_session):
    user = _make_user(db_session)
    entry = _make_entry(db_session, user.id)

    with pytest.raises(ValueError):
        time_entry_service.update_time_entry(
            db_session, user.id, entry.id, {"end_time": datetime(2026, 8, 1, 8, 0)}
        )


def test_update_time_entry_for_wrong_user_returns_none(db_session):
    user = _make_user(db_session)
    entry = _make_entry(db_session, user.id)

    assert time_entry_service.update_time_entry(db_session, 999, entry.id, {"end_time": None}) is None


def test_update_nonexistent_time_entry_returns_none(db_session):
    user = _make_user(db_session)

    assert time_entry_service.update_time_entry(db_session, user.id, 999, {"end_time": None}) is None
