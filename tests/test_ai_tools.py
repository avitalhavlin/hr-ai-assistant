from datetime import date, datetime

from app.ai import tools
from app.core.config import settings
from app.models.employee_profile import EmployeeProfile
from app.models.time_entry import TimeEntry
from app.models.user import Role, User
from app.services import policy_service


def _make_user(db, **overrides):
    defaults = dict(
        full_name="Test User",
        email="test@example.com",
        hashed_password="x",
        role=Role.employee,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_get_my_hours_with_explicit_period(db_session):
    user = _make_user(db_session)
    db_session.add(
        TimeEntry(
            user_id=user.id,
            work_date=date(2026, 7, 13),
            start_time=datetime(2026, 7, 13, 9, 0),
            end_time=datetime(2026, 7, 13, 17, 0),
        )
    )
    db_session.commit()

    result = tools.get_my_hours(db_session, user.id, period="month", year=2026, month=7)

    assert result == {"period": "2026-07", "total_hours": 8.0}


def test_get_hours_between_sums_entries_in_range(db_session):
    user = _make_user(db_session)
    db_session.add_all(
        [
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 7, 13),
                start_time=datetime(2026, 7, 13, 9, 0),
                end_time=datetime(2026, 7, 13, 17, 0),
            ),
            # Outside the range — must not be counted.
            TimeEntry(
                user_id=user.id,
                work_date=date(2026, 8, 1),
                start_time=datetime(2026, 8, 1, 9, 0),
                end_time=datetime(2026, 8, 1, 17, 0),
            ),
        ]
    )
    db_session.commit()

    result = tools.get_hours_between(db_session, user.id, "2026-07-01", "2026-07-31")

    assert result == {"start_date": "2026-07-01", "end_date": "2026-07-31", "total_hours": 8.0}


def test_get_hours_between_rejects_end_before_start(db_session):
    user = _make_user(db_session)

    try:
        tools.get_hours_between(db_session, user.id, "2026-07-31", "2026-07-01")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_get_my_hours_defaults_to_current_period(db_session, monkeypatch):
    user = _make_user(db_session)

    class _FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 10)

    monkeypatch.setattr(tools, "date", _FixedDate)

    result = tools.get_my_hours(db_session, user.id, period="month")

    assert result == {"period": "2026-08", "total_hours": 0.0}


def test_get_my_hours_invalid_period_raises(db_session):
    user = _make_user(db_session)

    try:
        tools.get_my_hours(db_session, user.id, period="fortnight")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_get_vacation_balance_with_profile(db_session):
    user = _make_user(db_session)
    db_session.add(EmployeeProfile(user_id=user.id, remaining_vacation_days=12.5))
    db_session.commit()

    result = tools.get_vacation_balance(db_session, user.id)

    assert result == {"remaining_vacation_days": 12.5}


def test_get_vacation_balance_without_profile(db_session):
    user = _make_user(db_session)

    result = tools.get_vacation_balance(db_session, user.id)

    assert result == {"error": "No employee profile on file for this user yet."}


def test_get_office_hours_reads_settings():
    result = tools.get_office_hours()

    assert result == {
        "open_time": settings.office_open_time,
        "close_time": settings.office_close_time,
        "working_days": settings.working_days.split(","),
    }


def test_search_policy_docs_returns_matches(db_session, monkeypatch):
    fake_matches = [{"source": "vacation_and_leave", "content": "21 days a year"}]
    monkeypatch.setattr(policy_service, "search_policies", lambda db, query: fake_matches)

    result = tools.search_policy_docs(db_session, "how many vacation days do I get")

    assert result == {"matches": fake_matches}


def test_get_employees_hours_report_sums_each_employee(db_session):
    alice = _make_user(db_session, full_name="Alice", email="alice@example.com")
    bob = _make_user(db_session, full_name="Bob", email="bob@example.com")
    db_session.add_all(
        [
            TimeEntry(
                user_id=alice.id,
                work_date=date(2026, 7, 13),
                start_time=datetime(2026, 7, 13, 9, 0),
                end_time=datetime(2026, 7, 13, 17, 0),
            ),
            TimeEntry(
                user_id=bob.id,
                work_date=date(2026, 7, 14),
                start_time=datetime(2026, 7, 14, 9, 0),
                end_time=datetime(2026, 7, 14, 13, 0),
            ),
        ]
    )
    db_session.commit()

    result = tools.get_employees_hours_report(db_session, "2026-07-01", "2026-07-31")

    assert result["start_date"] == "2026-07-01"
    assert result["end_date"] == "2026-07-31"
    by_email = {e["email"]: e["total_hours"] for e in result["employees"]}
    assert by_email == {"alice@example.com": 8.0, "bob@example.com": 4.0}


def test_get_employees_hours_report_defaults_to_current_month(db_session, monkeypatch):
    _make_user(db_session)

    class _FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 8, 10)

    monkeypatch.setattr(tools, "date", _FixedDate)

    result = tools.get_employees_hours_report(db_session)

    assert result["start_date"] == "2026-08-01"
    assert result["end_date"] == "2026-08-10"


def test_get_employees_hours_report_rejects_end_before_start(db_session):
    try:
        tools.get_employees_hours_report(db_session, "2026-07-31", "2026-07-01")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_call_tool_dispatches_get_office_hours(db_session):
    user = _make_user(db_session)

    result = tools.call_tool("get_office_hours", {}, db_session, user.id, is_admin=False)

    assert result["open_time"] == settings.office_open_time


def test_call_tool_dispatches_get_my_hours(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_my_hours", {"period": "year", "year": 2026}, db_session, user.id, is_admin=False
    )

    assert result == {"period": "2026", "total_hours": 0.0}


def test_call_tool_dispatches_get_hours_between(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_hours_between",
        {"start_date": "2026-07-01", "end_date": "2026-07-31"},
        db_session,
        user.id,
        is_admin=False,
    )

    assert result == {"start_date": "2026-07-01", "end_date": "2026-07-31", "total_hours": 0.0}


def test_call_tool_dispatches_search_policy_docs(db_session, monkeypatch):
    user = _make_user(db_session)
    monkeypatch.setattr(policy_service, "search_policies", lambda db, query: [])

    result = tools.call_tool(
        "search_policy_docs", {"query": "remote work"}, db_session, user.id, is_admin=False
    )

    assert result == {"matches": []}


def test_call_tool_rejects_employees_report_for_non_admin(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_employees_hours_report", {}, db_session, user.id, is_admin=False
    )

    assert result == {"error": "Admin access required for this tool."}


def test_call_tool_dispatches_employees_report_for_admin(db_session):
    admin = _make_user(db_session, role=Role.admin, email="admin@example.com")

    result = tools.call_tool(
        "get_employees_hours_report",
        {"start_date": "2026-07-01", "end_date": "2026-07-31"},
        db_session,
        admin.id,
        is_admin=True,
    )

    assert result["start_date"] == "2026-07-01"
    assert len(result["employees"]) == 1


def test_call_tool_converts_value_error_to_error_dict(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_my_hours",
        {"period": "month", "year": 2026, "month": 13},
        db_session,
        user.id,
        is_admin=False,
    )

    assert "error" in result


def test_call_tool_unknown_name_returns_error_dict(db_session):
    user = _make_user(db_session)

    result = tools.call_tool("delete_everything", {}, db_session, user.id, is_admin=False)

    assert result == {"error": "Unknown tool: delete_everything"}


def test_build_tools_omits_admin_report_for_non_admin():
    declared = _declared_names(tools.build_tools(is_admin=False))

    assert "get_employees_hours_report" not in declared
    assert {
        "get_my_hours",
        "get_hours_between",
        "get_vacation_balance",
        "get_office_hours",
        "search_policy_docs",
    } <= declared


def test_build_tools_includes_admin_report_for_admin():
    declared = _declared_names(tools.build_tools(is_admin=True))

    assert "get_employees_hours_report" in declared


def _declared_names(built_tools):
    return {fd.name for t in built_tools for fd in t.function_declarations}
