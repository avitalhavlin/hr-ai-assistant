"""
Data access for VacationRequest. No business rules, no transaction control —
callers (services) own flush()/commit().
"""

from sqlalchemy.orm import Session

from app.models.vacation_request import VacationRequest


def get_by_id(db: Session, request_id: int) -> VacationRequest | None:
    return db.get(VacationRequest, request_id)


def list_by_user(db: Session, user_id: int) -> list[VacationRequest]:
    return db.query(VacationRequest).filter(VacationRequest.user_id == user_id).all()


def add(db: Session, request: VacationRequest) -> VacationRequest:
    db.add(request)
    db.flush()
    return request
