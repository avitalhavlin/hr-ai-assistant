"""
Thin wrapper around the Gemini SDK. No request-shaping or business logic
here — app/services/chat_service.py owns that. Kept separate so callers
never construct genai.Client() themselves and so tests can monkeypatch
get_client() instead of touching the real API.
"""

from google import genai

from app.core.config import settings

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client
