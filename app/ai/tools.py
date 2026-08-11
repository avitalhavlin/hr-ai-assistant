"""
Tool/function definitions the chatbot can call. Each tool is a thin wrapper
around app/services/* — no business logic lives here. `db`/`user_id` are
bound by chat_service.py from the authenticated request, never exposed as
model-settable parameters, so the model can never act on another user's
data.

Admin-only tools are gated twice: build_tools() only includes their schema
for admin callers (so the model is never even told the tool exists), and
call_tool() re-checks is_admin before dispatching, so a bad tool call can
never reach admin-only data even if it's somehow requested.

Tool errors (ValueError from the underlying service) are turned into an
{"error": ...} result rather than raised, so a bad tool call becomes
something the model can see and react to instead of a failed chat request.
"""

from datetime import date

from google.genai import types
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import hours_service, policy_service, user_service, vacation_service

_EMPLOYEE_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_my_hours",
        description=(
            "Get the total hours the authenticated employee worked in a "
            "given month or year. If year/month are omitted, defaults to "
            "the current period."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["month", "year"],
                    "description": "Which period to total hours for.",
                },
                "year": {
                    "type": "integer",
                    "description": "Calendar year. Defaults to the current year.",
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
        name="get_hours_between",
        description=(
            "Get the total hours the authenticated employee worked between "
            "two dates (inclusive), for any arbitrary date range."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start of the range, as YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End of the range (inclusive), as YYYY-MM-DD.",
                },
            },
            "required": ["start_date", "end_date"],
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
    types.FunctionDeclaration(
        name="search_policy_docs",
        description=(
            "Search company policy documents (vacation/leave, remote work, "
            "code of conduct, etc.) for content relevant to a question. "
            "Returns the most relevant excerpts, not a direct answer — base "
            "the answer only on what's returned."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The policy question to search for.",
                },
            },
            "required": ["query"],
        },
    ),
]

_ADMIN_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_employees_hours_report",
        description=(
            "Admin only. Get every employee's total worked hours between two "
            "dates (inclusive). If start_date/end_date are omitted, defaults "
            "to the current month."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start of the range, as YYYY-MM-DD. Defaults to the 1st of the current month.",
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End of the range (inclusive), as YYYY-MM-DD. Defaults to today.",
                },
            },
        },
    ),
]


def build_tools(is_admin: bool) -> list[types.Tool]:
    declarations = list(_EMPLOYEE_DECLARATIONS)
    if is_admin:
        declarations += _ADMIN_DECLARATIONS
    return [types.Tool(function_declarations=declarations)]


def get_my_hours(
    db: Session,
    user_id: int,
    period: str,
    year: int | None = None,
    month: int | None = None,
) -> dict:
    today = date.today()
    year = year or today.year

    if period == "month":
        month = month or today.month
        hours = hours_service.get_hours_for_month(db, user_id, year, month)
        label = f"{year}-{month:02d}"
    elif period == "year":
        hours = hours_service.get_hours_for_year(db, user_id, year)
        label = str(year)
    else:
        raise ValueError(f"Unknown period: {period!r} (expected month or year)")

    return {"period": label, "total_hours": hours}


def get_hours_between(db: Session, user_id: int, start_date: str, end_date: str) -> dict:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must not be before start_date")

    hours = hours_service.get_hours_between(db, user_id, start, end)
    return {"start_date": start_date, "end_date": end_date, "total_hours": hours}


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


def search_policy_docs(db: Session, query: str) -> dict:
    matches = policy_service.search_policies(db, query)
    return {"matches": matches}


def get_employees_hours_report(
    db: Session, start_date: str | None = None, end_date: str | None = None
) -> dict:
    today = date.today()
    start = date.fromisoformat(start_date) if start_date else today.replace(day=1)
    end = date.fromisoformat(end_date) if end_date else today
    if end < start:
        raise ValueError("end_date must not be before start_date")

    employees = [
        {
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "total_hours": hours_service.get_hours_between(db, user.id, start, end),
        }
        for user in user_service.list_users(db)
    ]
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "employees": employees,
    }


def call_tool(name: str, args: dict, db: Session, user_id: int, is_admin: bool) -> dict:
    try:
        if name == "get_my_hours":
            return get_my_hours(db, user_id, **args)
        if name == "get_hours_between":
            return get_hours_between(db, user_id, **args)
        if name == "get_vacation_balance":
            return get_vacation_balance(db, user_id)
        if name == "get_office_hours":
            return get_office_hours()
        if name == "search_policy_docs":
            return search_policy_docs(db, **args)
        if name == "get_employees_hours_report":
            if not is_admin:
                return {"error": "Admin access required for this tool."}
            return get_employees_hours_report(db, **args)
        return {"error": f"Unknown tool: {name}"}
    except ValueError as exc:
        return {"error": str(exc)}
