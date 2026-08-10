"""
Orchestrates a single chat turn: builds the Gemini generate_content request
from the caller's message plus any prior turns they resend, and returns
Gemini's reply as plain text.

No conversation persistence yet — chat logging lands in Phase 7, so the
caller is responsible for resending history on each request. No tool use
yet either (Phase 5), so Gemini can only draw on the system prompt and the
conversation so far, not live employee data.
"""

from google.genai import errors, types

from app.ai.client import get_client
from app.ai.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.schemas.chat import ChatRequest

_GEMINI_ROLES = {"user": "user", "assistant": "model"}


class ChatServiceError(Exception):
    pass


def send_chat_message(payload: ChatRequest) -> str:
    if not settings.gemini_api_key:
        raise ChatServiceError("Gemini API key is not configured")

    contents = [
        {"role": _GEMINI_ROLES[m.role], "parts": [{"text": m.content}]} for m in payload.history
    ]
    contents.append({"role": "user", "parts": [{"text": payload.message}]})

    try:
        response = get_client().models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1024,
            ),
        )
    except errors.APIError as exc:
        raise ChatServiceError("Could not reach the AI service") from exc

    return response.text or ""
