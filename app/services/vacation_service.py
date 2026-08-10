"""
Business logic for vacation requests: creation and admin approve/reject.

Raises plain ValueError for domain errors (not found, invalid dates, already
decided) — the API layer translates these into the appropriate HTTP status.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.vacation_request import VacationRequest, VacationStatus
from app.repositories import employee_profile_repository, vacation_request_repository


def get_vacation_balance(db: Session, user_id: int) -> float | None:
    """Remaining vacation days for a user, or None if they have no profile yet."""
    profile = employee_profile_repository.get_by_user_id(db, user_id)
    return profile.remaining_vacation_days if profile else None


def create_vacation_request(
    db: Session, user_id: int, start_date: date, end_date: date
) -> VacationRequest:
    if end_date < start_date:
        raise ValueError("end_date must not be before start_date")

    request = vacation_request_repository.add(
        db,
        VacationRequest(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            status=VacationStatus.pending,
        ),
    )
    db.commit()
    db.refresh(request)
    return request


def list_vacation_requests(db: Session, user_id: int) -> list[VacationRequest]:
    return vacation_request_repository.list_by_user(db, user_id)


def _get_pending_request(db: Session, request_id: int) -> VacationRequest:
    request = vacation_request_repository.get_by_id(db, request_id)
    if request is None:
        raise ValueError("Vacation request not found")
    if request.status != VacationStatus.pending:
        raise ValueError(f"Vacation request is already {request.status.value}")
    return request


def approve_vacation_request(db: Session, request_id: int) -> VacationRequest:
    request = _get_pending_request(db, request_id)
    request.status = VacationStatus.approved
    db.commit()
    db.refresh(request)
    return request


def reject_vacation_request(db: Session, request_id: int) -> VacationRequest:
    request = _get_pending_request(db, request_id)
    request.status = VacationStatus.rejected
    db.commit()
    db.refresh(request)
    return request
