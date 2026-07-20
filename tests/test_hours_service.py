from datetime import date, datetime

from app.models.employee import Employee, Role
from app.models.time_entry import TimeEntry
from app.services import hours_service


def _make_employee(db):
    employee = Employee(
        full_name="Test Employee",
        email="test@example.com",
        hashed_password="x",
        hire_date=date(2024, 1, 1),
        role=Role.employee,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def test_get_hours_for_week_sums_entries(db_session):
    employee = _make_employee(db_session)

    # Two entries in the same ISO week: Mon 9-5, Tue 9-1
    db_session.add_all(
        [
            TimeEntry(
                employee_id=employee.id,
                work_date=date(2026, 7, 13),
                start_time=datetime(2026, 7, 13, 9, 0),
                end_time=datetime(2026, 7, 13, 17, 0),
            ),
            TimeEntry(
                employee_id=employee.id,
                work_date=date(2026, 7, 14),
                start_time=datetime(2026, 7, 14, 9, 0),
                end_time=datetime(2026, 7, 14, 13, 0),
            ),
        ]
    )
    db_session.commit()

    total = hours_service.get_hours_for_week(db_session, employee.id, 2026, 29)
    assert total == 12.0


def test_open_entry_counts_zero_hours(db_session):
    employee = _make_employee(db_session)
    db_session.add(
        TimeEntry(
            employee_id=employee.id,
            work_date=date(2026, 7, 13),
            start_time=datetime(2026, 7, 13, 9, 0),
            end_time=None,
        )
    )
    db_session.commit()

    total = hours_service.get_hours_for_week(db_session, employee.id, 2026, 29)
    assert total == 0.0
