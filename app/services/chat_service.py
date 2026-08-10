"""
Orchestrates a single chat turn: builds the Gemini generate_content request
from the caller's message plus any prior turns they resend, lets Gemini call
the tools in app/ai/tools.py for real employee data, and returns the final
reply as plain text.

No conversation persistence yet — chat logging lands in Phase 7, so the
caller is responsible for resending history on each request. No RAG yet
either (Phase 6), so anything beyond the three tools (hours, vacation
balance, office hours) is still out of the model's reach.
"""

from google.genai import errors, types
from sqlalchemy.orm import Session

from app.ai import tools
from app.ai.client import get_client
from app.ai.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.schemas.chat import ChatRequest

_GEMINI_ROLES = {"user": "user", "assistant": "model"}

# Caps how many tool round trips a single chat turn can take, so a model
# stuck calling tools in a loop fails cleanly instead of hanging the request.
MAX_TOOL_ROUNDS = 5


class ChatServiceError(Exception):
    pass


def send_chat_message(payload: ChatRequest, db: Session, user_id: int) -> str:
    if not settings.gemini_api_key:
        raise ChatServiceError("Gemini API key is not configured")

    contents = [
        {"role": _GEMINI_ROLES[m.role], "parts": [{"text": m.content}]} for m in payload.history
    ]
    contents.append({"role": "user", "parts": [{"text": payload.message}]})

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=1024,
        tools=tools.TOOLS,
    )

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = get_client().models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            )
        except errors.APIError as exc:
            raise ChatServiceError("Could not reach the AI service") from exc

        calls = response.function_calls
        if not calls:
            return response.text or ""

        contents.append(response.candidates[0].content)
        contents.append(
            {
                "role": "user",
                "parts": [
                    types.Part.from_function_response(
                        name=call.name,
                        response=tools.call_tool(call.name, call.args or {}, db, user_id),
                    )
                    for call in calls
                ],
            }
        )

    raise ChatServiceError("The assistant could not complete the request (too many tool calls)")
