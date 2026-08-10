from types import SimpleNamespace

import pytest
from google.genai import errors

from app.core.config import settings
from app.models.user import Role, User
from app.schemas.chat import ChatMessage, ChatRequest
from app.services import chat_service


@pytest.fixture(autouse=True)
def _configured_api_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")


def _make_user(db):
    user = User(
        full_name="Test User",
        email="chat-service-test@example.com",
        hashed_password="x",
        role=Role.employee,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class _FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.models = _FakeModels(responses)


def _text_response(text: str):
    return SimpleNamespace(text=text, function_calls=None)


def _function_call_response(name: str, args: dict):
    call = SimpleNamespace(name=name, args=args)
    content = SimpleNamespace(role="model", parts=[])
    return SimpleNamespace(
        text=None,
        function_calls=[call],
        candidates=[SimpleNamespace(content=content)],
    )


def test_send_chat_message_single_turn(db_session, monkeypatch):
    user = _make_user(db_session)
    fake_client = _FakeClient([_text_response("Hello there!")])
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    reply = chat_service.send_chat_message(ChatRequest(message="Hi"), db_session, user.id)

    assert reply == "Hello there!"
    assert fake_client.models.calls[0]["contents"] == [
        {"role": "user", "parts": [{"text": "Hi"}]}
    ]


def test_send_chat_message_includes_history(db_session, monkeypatch):
    user = _make_user(db_session)
    fake_client = _FakeClient([_text_response("Sure, following up.")])
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    payload = ChatRequest(
        message="And now?",
        history=[
            ChatMessage(role="user", content="What's my vacation balance?"),
            ChatMessage(role="assistant", content="I can't look that up yet."),
        ],
    )

    chat_service.send_chat_message(payload, db_session, user.id)

    assert fake_client.models.calls[0]["contents"] == [
        {"role": "user", "parts": [{"text": "What's my vacation balance?"}]},
        {"role": "model", "parts": [{"text": "I can't look that up yet."}]},
        {"role": "user", "parts": [{"text": "And now?"}]},
    ]


def test_send_chat_message_runs_a_tool_call_and_returns_final_text(db_session, monkeypatch):
    user = _make_user(db_session)
    fake_client = _FakeClient(
        [
            _function_call_response("get_office_hours", {}),
            _text_response("Office hours are 09:00 to 18:00."),
        ]
    )
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    reply = chat_service.send_chat_message(
        ChatRequest(message="What are the office hours?"), db_session, user.id
    )

    assert reply == "Office hours are 09:00 to 18:00."
    assert len(fake_client.models.calls) == 2

    second_call_contents = fake_client.models.calls[1]["contents"]
    function_response_turn = second_call_contents[-1]
    assert function_response_turn["role"] == "user"
    function_response = function_response_turn["parts"][0].function_response
    assert function_response.name == "get_office_hours"
    assert function_response.response["open_time"] == settings.office_open_time


def test_send_chat_message_raises_when_tool_calls_never_stop(db_session, monkeypatch):
    user = _make_user(db_session)
    responses = [_function_call_response("get_office_hours", {}) for _ in range(10)]
    fake_client = _FakeClient(responses)
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.send_chat_message(ChatRequest(message="Hi"), db_session, user.id)


def test_send_chat_message_raises_service_error_on_api_error(db_session, monkeypatch):
    user = _make_user(db_session)

    class _BrokenModels:
        def generate_content(self, **kwargs):
            raise errors.ClientError(429, {"error": {"message": "rate limited"}})

    monkeypatch.setattr(
        chat_service, "get_client", lambda: SimpleNamespace(models=_BrokenModels())
    )

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.send_chat_message(ChatRequest(message="Hi"), db_session, user.id)


def test_send_chat_message_raises_service_error_when_key_missing(db_session, monkeypatch):
    user = _make_user(db_session)
    monkeypatch.setattr(settings, "gemini_api_key", "")

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.send_chat_message(ChatRequest(message="Hi"), db_session, user.id)
