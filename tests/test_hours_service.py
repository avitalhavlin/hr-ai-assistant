from datetime import date, datetime

import pytest

from app.models.user import Role, User
from app.models.time_entry import TimeEntry
from app.services import hours_service


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


def test_get_hours_for_week_sums_entries(db_session):
    user = _make_user(db_session)

    # Two entries in the same ISO week: Mon 9-5, Tue 9-1
    db_session.add_all(
        [
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 7, 13),
                start_time=datetime(2026, 7, 13, 9, 0),
                end_time=datetime(2026, 7, 13, 17, 0),
            ),
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 7, 14),
                start_time=datetime(2026, 7, 14, 9, 0),
                end_time=datetime(2026, 7, 14, 13, 0),
            ),
        ]
    )
    db_session.commit()

    total = hours_service.get_hours_for_week(db_session, user.id, 2026, 29)
    assert total == 12.0


def test_open_entry_counts_zero_hours(db_session):
    user = _make_user(db_session)
    db_session.add(
        TimeEntry(
            user_id=user.id,
            work_date=date(2026, 7, 13),
            start_time=datetime(2026, 7, 13, 9, 0),
            end_time=None,
        )
    )
    db_session.commit()

    total = hours_service.get_hours_for_week(db_session, user.id, 2026, 29)
    assert total == 0.0


def test_get_hours_for_week_raises_on_invalid_week(db_session):
    user = _make_user(db_session)

    with pytest.raises(ValueError):
        hours_service.get_hours_for_week(db_session, user.id, 2026, 54)


def test_get_hours_for_month_sums_entries_within_month_only(db_session):
    user = _make_user(db_session)

    db_session.add_all(
        [
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 7, 1),
                start_time=datetime(2026, 7, 1, 9, 0),
                end_time=datetime(2026, 7, 1, 17, 0),
            ),
            # Outside the month — must not be counted.
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 8, 1),
                start_time=datetime(2026, 8, 1, 9, 0),
                end_time=datetime(2026, 8, 1, 17, 0),
            ),
        ]
    )
    db_session.commit()

    total = hours_service.get_hours_for_month(db_session, user.id, 2026, 7)
    assert total == 8.0


def test_get_hours_for_month_raises_on_invalid_month(db_session):
    user = _make_user(db_session)

    with pytest.raises(ValueError):
        hours_service.get_hours_for_month(db_session, user.id, 2026, 13)


def test_get_hours_for_year_sums_entries_within_year_only(db_session):
    user = _make_user(db_session)

    db_session.add_all(
        [
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 1, 15),
                start_time=datetime(2026, 1, 15, 9, 0),
                end_time=datetime(2026, 1, 15, 17, 0),
            ),
            # Outside the year — must not be counted.
            TimeEntry(
                user_id=user.id,
                work_date=date(2027, 1, 15),
                start_time=datetime(2027, 1, 15, 9, 0),
                end_time=datetime(2027, 1, 15, 17, 0),
            ),
        ]
    )
    db_session.commit()

    total = hours_service.get_hours_for_year(db_session, user.id, 2026)
    assert total == 8.0
