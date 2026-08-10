from app.models.user import Role
from app.schemas.user import UserCreate
from app.services import chat_service, user_service

PASSWORD = "supersecret123"


def _make_user(db, **overrides):
    defaults = dict(
        full_name="Test User",
        email="chatuser@example.com",
        password=PASSWORD,
        role=Role.employee,
    )
    defaults.update(overrides)
    user, _profile = user_service.create_user(db, UserCreate(**defaults))
    return user


def _login(client, email, password=PASSWORD):
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_chat_requires_auth(client, db_session):
    response = client.post("/chat/", json={"message": "Hi"})

    assert response.status_code == 401


def test_chat_returns_reply(client, db_session, monkeypatch):
    _make_user(db_session)
    token = _login(client, "chatuser@example.com")
    monkeypatch.setattr(
        chat_service,
        "send_chat_message",
        lambda payload, db, user_id: "Hello, how can I help?",
    )

    response = client.post(
        "/chat/", json={"message": "Hi"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "Hello, how can I help?"}


def test_chat_maps_service_error_to_502(client, db_session, monkeypatch):
    _make_user(db_session, email="chaterror@example.com")
    token = _login(client, "chaterror@example.com")

    def _raise(payload, db, user_id):
        raise chat_service.ChatServiceError("Could not reach the AI service")

    monkeypatch.setattr(chat_service, "send_chat_message", _raise)

    response = client.post(
        "/chat/", json={"message": "Hi"}, headers=_auth_headers(token)
    )

    assert response.status_code == 502
