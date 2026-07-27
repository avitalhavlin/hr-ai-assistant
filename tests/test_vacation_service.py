from datetime import date

import pytest

from app.models.user import Role, User
from app.models.vacation_request import VacationStatus
from app.services import vacation_service


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


def test_create_vacation_request_defaults_to_pending(db_session):
    user = _make_user(db_session)

    request = vacation_service.create_vacation_request(
        db_session, user.id, date(2026, 8, 1), date(2026, 8, 5)
    )

    assert request.id is not None
    assert request.status == VacationStatus.pending


def test_create_vacation_request_rejects_end_before_start(db_session):
    user = _make_user(db_session)

    with pytest.raises(ValueError):
        vacation_service.create_vacation_request(
            db_session, user.id, date(2026, 8, 5), date(2026, 8, 1)
        )


def test_approve_vacation_request(db_session):
    user = _make_user(db_session)
    request = vacation_service.create_vacation_request(
        db_session, user.id, date(2026, 8, 1), date(2026, 8, 5)
    )

    approved = vacation_service.approve_vacation_request(db_session, request.id)

    assert approved.status == VacationStatus.approved


def test_reject_vacation_request(db_session):
    user = _make_user(db_session)
    request = vacation_service.create_vacation_request(
        db_session, user.id, date(2026, 8, 1), date(2026, 8, 5)
    )

    rejected = vacation_service.reject_vacation_request(db_session, request.id)

    assert rejected.status == VacationStatus.rejected


def test_cannot_decide_already_decided_request(db_session):
    user = _make_user(db_session)
    request = vacation_service.create_vacation_request(
        db_session, user.id, date(2026, 8, 1), date(2026, 8, 5)
    )
    vacation_service.approve_vacation_request(db_session, request.id)

    with pytest.raises(ValueError):
        vacation_service.reject_vacation_request(db_session, request.id)


def test_decide_nonexistent_request_raises(db_session):
    with pytest.raises(ValueError):
        vacation_service.approve_vacation_request(db_session, 999)


def test_list_vacation_requests_filters_by_user(db_session):
    user = _make_user(db_session)
    other = User(
        full_name="Other User",
        email="other@example.com",
        hashed_password="x",
        role=Role.employee,
    )
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    vacation_service.create_vacation_request(db_session, user.id, date(2026, 8, 1), date(2026, 8, 5))
    vacation_service.create_vacation_request(db_session, other.id, date(2026, 9, 1), date(2026, 9, 5))

    requests = vacation_service.list_vacation_requests(db_session, user.id)

    assert len(requests) == 1
    assert requests[0].user_id == user.id
