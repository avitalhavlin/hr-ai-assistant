"""
Tool/function definitions the chatbot can call. Each tool is a thin wrapper
around app/services/* — no business logic lives here. `db`/`user_id` are
bound by chat_service.py from the authenticated request, never exposed as
model-settable parameters, so the model can never act on another user's
data.

Tool errors (ValueError from the underlying service) are turned into an
{"error": ...} result rather than raised, so a bad tool call becomes
something the model can see and react to instead of a failed chat request.
"""

from datetime import date

from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import hours_service, vacation_service

TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_my_hours",
                description=(
                    "Get the total hours the authenticated employee worked in a "
                    "given period. If year/week/month are omitted, defaults to "
                    "the current period."
                ),
                parameters_json_schema={
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["week", "month", "year"],
                            "description": "Which period to total hours for.",
                        },
                        "year": {
                            "type": "integer",
                            "description": "Calendar year. Defaults to the current year.",
                        },
                        "week": {
                            "type": "integer",
                            "description": (
                                "ISO week number (1-53), only used when period is "
                                "'week'. Defaults to the current ISO week."
                            ),
                        },
                        "month": {
                            "type": "integer",
                            "description": (
                                "Month number (1-12), only used when period is "
                                "'month'. Defaults to the current month."
                            ),
                        },
                    },
                    "required": ["period"],
                },
            ),
            types.FunctionDeclaration(
                name="get_vacation_balance",
                description="Get the authenticated employee's remaining vacation days.",
                parameters_json_schema={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="get_office_hours",
                description="Get the company's office hours and working days policy.",
                parameters_json_schema={"type": "object", "properties": {}},
            ),
        ]
    )
]


def get_my_hours(
    db: Session,
    user_id: int,
    period: str,
    year: int | None = None,
    week: int | None = None,
    month: int | None = None,
) -> dict:
    today = date.today()
    year = year or today.year

    if period == "week":
        week = week or today.isocalendar().week
        hours = hours_service.get_hours_for_week(db, user_id, year, week)
        label = f"{year}-W{week:02d}"
    elif period == "month":
        month = month or today.month
        hours = hours_service.get_hours_for_month(db, user_id, year, month)
        label = f"{year}-{month:02d}"
    elif period == "year":
        hours = hours_service.get_hours_for_year(db, user_id, year)
        label = str(year)
    else:
        raise ValueError(f"Unknown period: {period!r} (expected week, month, or year)")

    return {"period": label, "total_hours": hours}


def get_vacation_balance(db: Session, user_id: int) -> dict:
    balance = vacation_service.get_vacation_balance(db, user_id)
    if balance is None:
        return {"error": "No employee profile on file for this user yet."}
    return {"remaining_vacation_days": balance}


def get_office_hours() -> dict:
    return {
        "open_time": settings.office_open_time,
        "close_time": settings.office_close_time,
        "working_days": settings.working_days.split(","),
    }


def call_tool(name: str, args: dict, db: Session, user_id: int) -> dict:
    try:
        if name == "get_my_hours":
            return get_my_hours(db, user_id, **args)
        if name == "get_vacation_balance":
            return get_vacation_balance(db, user_id)
        if name == "get_office_hours":
            return get_office_hours()
        return {"error": f"Unknown tool: {name}"}
    except ValueError as exc:
        return {"error": str(exc)}
