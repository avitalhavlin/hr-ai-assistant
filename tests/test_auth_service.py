from app.models.user import Role
from app.schemas.user import UserCreate
from app.services import auth_service, user_service


def _make_payload(**overrides):
    defaults = dict(
        full_name="Test User",
        email="test@example.com",
        password="supersecret123",
        role=Role.employee,
    )
    defaults.update(overrides)
    return UserCreate(**defaults)


def test_authenticate_user_returns_user_for_correct_credentials(db_session):
    created, _profile = user_service.create_user(db_session, _make_payload())

    user = auth_service.authenticate_user(db_session, "test@example.com", "supersecret123")

    assert user is not None
    assert user.id == created.id


def test_authenticate_user_returns_none_for_unknown_email(db_session):
    user = auth_service.authenticate_user(db_session, "nobody@example.com", "supersecret123")

    assert user is None


def test_authenticate_user_returns_none_for_wrong_password(db_session):
    user_service.create_user(db_session, _make_payload())

    user = auth_service.authenticate_user(db_session, "test@example.com", "wrong-password")

    assert user is None
