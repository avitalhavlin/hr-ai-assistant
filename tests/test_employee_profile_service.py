from datetime import date, datetime

import pytest

from app.models.user import Role, User
from app.services import employee_profile_service


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


def test_update_profile_updates_fields(db_session):
    user = _make_user(db_session)
    employee_profile_service.create_profile(db_session, user.id, date(2020, 1, 1), 8.0, 21.0)

    updated = employee_profile_service.update_profile(
        db_session, user.id, {"expected_daily_hours": 6.0, "remaining_vacation_days": 15.0}
    )

    assert updated.expected_daily_hours == 6.0
    assert updated.remaining_vacation_days == 15.0
    assert updated.hire_date == datetime(2020, 1, 1)


def test_update_profile_for_nonexistent_profile_returns_none(db_session):
    user = _make_user(db_session)

    assert employee_profile_service.update_profile(db_session, user.id, {"expected_daily_hours": 6.0}) is None


def test_update_profile_rejects_null_hire_date(db_session):
    user = _make_user(db_session)
    employee_profile_service.create_profile(db_session, user.id, date(2020, 1, 1), 8.0, 21.0)

    with pytest.raises(ValueError):
        employee_profile_service.update_profile(db_session, user.id, {"hire_date": None})
