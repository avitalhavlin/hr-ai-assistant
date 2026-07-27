import pytest

from app.models.user import Role, User
from app.services import user_service


def _make_user(db, email="test@example.com"):
    user = User(
        full_name="Test User",
        email=email,
        hashed_password="x",
        role=Role.employee,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_update_user_updates_fields(db_session):
    user = _make_user(db_session)

    updated = user_service.update_user(db_session, user.id, {"full_name": "New Name"})

    assert updated.full_name == "New Name"
    assert updated.email == "test@example.com"


def test_update_user_role(db_session):
    user = _make_user(db_session)

    updated = user_service.update_user_role(db_session, user.id, Role.admin)

    assert updated.role == Role.admin


def test_update_user_role_for_nonexistent_user_returns_none(db_session):
    assert user_service.update_user_role(db_session, 999, Role.admin) is None


def test_update_user_rejects_null_full_name(db_session):
    user = _make_user(db_session)

    with pytest.raises(ValueError):
        user_service.update_user(db_session, user.id, {"full_name": None})


def test_update_user_rejects_duplicate_email(db_session):
    _make_user(db_session, email="taken@example.com")
    other = _make_user(db_session, email="other@example.com")

    with pytest.raises(ValueError):
        user_service.update_user(db_session, other.id, {"email": "taken@example.com"})


def test_update_user_allows_same_email(db_session):
    user = _make_user(db_session)

    updated = user_service.update_user(db_session, user.id, {"email": "test@example.com"})

    assert updated.email == "test@example.com"


def test_update_nonexistent_user_returns_none(db_session):
    assert user_service.update_user(db_session, 999, {"full_name": "Nobody"}) is None
