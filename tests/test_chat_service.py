from types import SimpleNamespace

import pytest
from google.genai import errors

from app.core.config import settings
from app.schemas.chat import ChatMessage, ChatRequest
from app.services import chat_service


@pytest.fixture(autouse=True)
def _configured_api_key(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")


class _FakeModels:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeClient:
    def __init__(self, response):
        self.models = _FakeModels(response)


def _fake_response(text: str):
    return SimpleNamespace(text=text)


def test_send_chat_message_single_turn(monkeypatch):
    fake_client = _FakeClient(_fake_response("Hello there!"))
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    reply = chat_service.send_chat_message(ChatRequest(message="Hi"))

    assert reply == "Hello there!"
    assert fake_client.models.last_kwargs["contents"] == [
        {"role": "user", "parts": [{"text": "Hi"}]}
    ]


def test_send_chat_message_includes_history(monkeypatch):
    fake_client = _FakeClient(_fake_response("Sure, following up."))
    monkeypatch.setattr(chat_service, "get_client", lambda: fake_client)

    payload = ChatRequest(
        message="And now?",
        history=[
            ChatMessage(role="user", content="What's my vacation balance?"),
            ChatMessage(role="assistant", content="I can't look that up yet."),
        ],
    )

    chat_service.send_chat_message(payload)

    assert fake_client.models.last_kwargs["contents"] == [
        {"role": "user", "parts": [{"text": "What's my vacation balance?"}]},
        {"role": "model", "parts": [{"text": "I can't look that up yet."}]},
        {"role": "user", "parts": [{"text": "And now?"}]},
    ]


def test_send_chat_message_raises_service_error_on_api_error(monkeypatch):
    class _BrokenModels:
        def generate_content(self, **kwargs):
            raise errors.ClientError(429, {"error": {"message": "rate limited"}})

    monkeypatch.setattr(
        chat_service, "get_client", lambda: SimpleNamespace(models=_BrokenModels())
    )

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.send_chat_message(ChatRequest(message="Hi"))


def test_send_chat_message_raises_service_error_when_key_missing(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")

    with pytest.raises(chat_service.ChatServiceError):
        chat_service.send_chat_message(ChatRequest(message="Hi"))
