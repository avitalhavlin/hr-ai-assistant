from datetime import date

import pytest
from pydantic import ValidationError

from app.core.security import verify_password
from app.models.user import Role
from app.schemas.employee_profile import EmployeeProfileUpdate
from app.schemas.user import UserCreate
from app.services import user_service


def _make_payload(**overrides):
    defaults = dict(
        full_name="Test User",
        email="test@example.com",
        password="supersecret123",
        role=Role.employee,
    )
    defaults.update(overrides)
    return UserCreate(**defaults)


def test_create_user_creates_user_and_profile_together(db_session):
    user = user_service.create_user(db_session, _make_payload())

    assert user.id is not None
    assert user.profile is not None
    assert user.profile.user_id == user.id
    assert user.profile.expected_daily_hours == 8.0
    assert user.profile.remaining_vacation_days == 21.0


def test_create_user_hashes_password(db_session):
    user = user_service.create_user(db_session, _make_payload(password="supersecret123"))

    assert user.hashed_password != "supersecret123"
    assert verify_password("supersecret123", user.hashed_password)


def test_create_user_rejects_duplicate_email(db_session):
    user_service.create_user(db_session, _make_payload(email="dup@example.com"))

    with pytest.raises(ValueError):
        user_service.create_user(db_session, _make_payload(email="dup@example.com"))


def test_get_user_returns_user(db_session):
    created = user_service.create_user(db_session, _make_payload())

    user = user_service.get_user(db_session, created.id)

    assert user.id == created.id


def test_get_user_raises_when_not_found(db_session):
    with pytest.raises(ValueError):
        user_service.get_user(db_session, 999)


def test_get_user_profile_returns_profile(db_session):
    created = user_service.create_user(db_session, _make_payload())

    profile = user_service.get_user_profile(db_session, created.id)

    assert profile.user_id == created.id


def test_get_user_profile_raises_when_not_found(db_session):
    with pytest.raises(ValueError):
        user_service.get_user_profile(db_session, 999)


def test_update_user_profile_applies_partial_fields(db_session):
    created = user_service.create_user(db_session, _make_payload())

    updated = user_service.update_user_profile(
        db_session,
        created.id,
        EmployeeProfileUpdate(hire_date=date(2026, 1, 15)),
    )

    assert updated.hire_date.date() == date(2026, 1, 15)
    # untouched fields keep their existing values
    assert updated.expected_daily_hours == 8.0


def test_update_user_profile_raises_when_not_found(db_session):
    with pytest.raises(ValueError):
        user_service.update_user_profile(db_session, 999, EmployeeProfileUpdate())


def test_employee_profile_update_rejects_explicit_null():
    with pytest.raises(ValidationError):
        EmployeeProfileUpdate(expected_daily_hours=None)

    with pytest.raises(ValidationError):
        EmployeeProfileUpdate(remaining_vacation_days=None)


def test_get_user_full_returns_user_with_profile(db_session):
    created = user_service.create_user(db_session, _make_payload())

    user = user_service.get_user_full(db_session, created.id)

    assert user.id == created.id
    assert user.profile is not None


def test_get_user_full_raises_when_not_found(db_session):
    with pytest.raises(ValueError):
        user_service.get_user_full(db_session, 999)


def test_list_users_returns_all_users(db_session):
    user_service.create_user(db_session, _make_payload(email="a@example.com"))
    user_service.create_user(db_session, _make_payload(email="b@example.com"))

    users = user_service.list_users(db_session)

    assert {u.email for u in users} == {"a@example.com", "b@example.com"}


def test_delete_user_removes_user_and_profile(db_session):
    from app.repositories import employee_profile_repository, user_repository

    created = user_service.create_user(db_session, _make_payload())
    user_id = created.id

    user_service.delete_user(db_session, user_id)

    assert user_repository.get_by_id(db_session, user_id) is None
    assert employee_profile_repository.get_by_user_id(db_session, user_id) is None


def test_delete_user_raises_when_not_found(db_session):
    with pytest.raises(ValueError):
        user_service.delete_user(db_session, 999)


def test_delete_user_cascades_vacation_requests(db_session):
    from app.services import vacation_service

    created = user_service.create_user(db_session, _make_payload())
    user_id = created.id
    vacation_service.create_vacation_request(
        db_session, user_id, date(2026, 8, 1), date(2026, 8, 5)
    )

    user_service.delete_user(db_session, user_id)

    assert vacation_service.list_vacation_requests(db_session, user_id) == []
