from datetime import date, datetime

from app.ai import tools
from app.core.config import settings
from app.models.employee_profile import EmployeeProfile
from app.models.time_entry import TimeEntry
from app.models.user import Role, User


def _make_user(db):
    user = User(
        full_name="Test User",
        email="test@example.com",
        hashed_password="x",
        role=Role.employee,
    )
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


def test_call_tool_dispatches_get_office_hours(db_session):
    user = _make_user(db_session)

    result = tools.call_tool("get_office_hours", {}, db_session, user.id)

    assert result["open_time"] == settings.office_open_time


def test_call_tool_dispatches_get_my_hours(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_my_hours", {"period": "year", "year": 2026}, db_session, user.id
    )

    assert result == {"period": "2026", "total_hours": 0.0}


def test_call_tool_dispatches_get_hours_between(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_hours_between",
        {"start_date": "2026-07-01", "end_date": "2026-07-31"},
        db_session,
        user.id,
    )

    assert result == {"start_date": "2026-07-01", "end_date": "2026-07-31", "total_hours": 0.0}


def test_call_tool_converts_value_error_to_error_dict(db_session):
    user = _make_user(db_session)

    result = tools.call_tool(
        "get_my_hours", {"period": "month", "year": 2026, "month": 13}, db_session, user.id
    )

    assert "error" in result


def test_call_tool_unknown_name_returns_error_dict(db_session):
    user = _make_user(db_session)

    result = tools.call_tool("delete_everything", {}, db_session, user.id)

    assert result == {"error": "Unknown tool: delete_everything"}
