"""
Business logic for vacation requests: creation and admin approve/reject.

Raises plain ValueError for domain errors (not found, invalid dates, already
decided) — the API layer translates these into the appropriate HTTP status.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.vacation_request import VacationRequest, VacationStatus


def create_vacation_request(
    db: Session, employee_id: int, start_date: date, end_date: date
) -> VacationRequest:
    if end_date < start_date:
        raise ValueError("end_date must not be before start_date")

    request = VacationRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        status=VacationStatus.pending,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def list_vacation_requests(db: Session, employee_id: int) -> list[VacationRequest]:
    return (
        db.query(VacationRequest)
        .filter(VacationRequest.employee_id == employee_id)
        .all()
    )


def _get_pending_request(db: Session, request_id: int) -> VacationRequest:
    request = db.get(VacationRequest, request_id)
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
