"""
Exercise all chatbot tools (app/ai/tools.py) directly against the
database, bypassing Gemini entirely. Uses the same SessionLocal as the
running API, so data created via the live server (Swagger UI at /docs,
curl, etc.) is visible here.

get_employees_hours_report is admin-only: call_tool() checks the caller's
role and returns {"error": "Admin access required for this tool."} for a
non-admin, same as the chatbot would. Run this script once with an
employee's email and once with an admin's to see both sides of that gate.

Run from the project root (venv active, DATABASE_URL pointing at your
running Postgres):

    python scripts/try_tools.py you@example.com
"""
import sys

sys.path.insert(0, ".")

from app.ai import tools  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.user import Role  # noqa: E402
from app.repositories import user_repository  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/try_tools.py <user-email>")
        sys.exit(1)

    email = sys.argv[1]
    db = SessionLocal()
    try:
        user = user_repository.get_by_email(db, email)
        if user is None:
            print(f"No user found for email={email!r}")
            return

        is_admin = user.role == Role.admin
        print(f"Testing tools as user id={user.id} email={user.email} is_admin={is_admin}\n")

        print("get_office_hours:")
        print(tools.call_tool("get_office_hours", {}, db, user.id, is_admin), "\n")

        print("get_vacation_balance:")
        print(tools.call_tool("get_vacation_balance", {}, db, user.id, is_admin), "\n")

        print("get_my_hours (current month):")
        print(tools.call_tool("get_my_hours", {"period": "month"}, db, user.id, is_admin), "\n")

        print("get_my_hours (current year):")
        print(tools.call_tool("get_my_hours", {"period": "year"}, db, user.id, is_admin), "\n")

        print("get_hours_between (2026-01-01 to 2026-12-31):")
        print(
            tools.call_tool(
                "get_hours_between",
                {"start_date": "2026-01-01", "end_date": "2026-12-31"},
                db,
                user.id,
                is_admin,
            ),
            "\n",
        )

        print("get_employees_hours_report (admin-only, current month):")
        print(tools.call_tool("get_employees_hours_report", {}, db, user.id, is_admin))
    finally:
        db.close()


if __name__ == "__main__":
    main()
