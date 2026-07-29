from datetime import date, datetime

from app.models.user import Role, User
from app.schemas.time_entry import TimeEntryCreate
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


def test_create_time_entry_persists_entry(db_session):
    user = _make_user(db_session)

    entry = time_entry_service.create_time_entry(
        db_session,
        user.id,
        TimeEntryCreate(
            work_date=date(2026, 7, 13),
            start_time=datetime(2026, 7, 13, 9, 0),
            end_time=datetime(2026, 7, 13, 17, 0),
        ),
    )

    assert entry.id is not None
    assert entry.user_id == user.id
    assert entry.work_date == date(2026, 7, 13)


def test_create_time_entry_allows_open_entry_without_end_time(db_session):
    user = _make_user(db_session)

    entry = time_entry_service.create_time_entry(
        db_session,
        user.id,
        TimeEntryCreate(work_date=date(2026, 7, 13), start_time=datetime(2026, 7, 13, 9, 0)),
    )

    assert entry.end_time is None


def test_list_time_entries_filters_by_user(db_session):
    user = _make_user(db_session)
    other = User(
        full_name="Other User",
        email="other@example.com",
        hashed_password="x",
        role=Role.employee,
    )
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    time_entry_service.create_time_entry(
        db_session,
        user.id,
        TimeEntryCreate(work_date=date(2026, 7, 13), start_time=datetime(2026, 7, 13, 9, 0)),
    )
    time_entry_service.create_time_entry(
        db_session,
        other.id,
        TimeEntryCreate(work_date=date(2026, 7, 14), start_time=datetime(2026, 7, 14, 9, 0)),
    )

    entries = time_entry_service.list_time_entries(db_session, user.id)

    assert len(entries) == 1
    assert entries[0].user_id == user.id
