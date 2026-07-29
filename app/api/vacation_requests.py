from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.repositories import user_repository
from app.schemas.vacation_request import VacationRequestCreate, VacationRequestOut
from app.services import vacation_service

router = APIRouter(tags=["vacation-requests"])


@router.post(
    "/users/{user_id}/vacation-requests/",
    response_model=VacationRequestOut,
)
def create_vacation_request(
    user_id: int, payload: VacationRequestCreate, db: Session = Depends(get_db)
):
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        return vacation_service.create_vacation_request(
            db, user_id, payload.start_date, payload.end_date
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/users/{user_id}/vacation-requests/",
    response_model=list[VacationRequestOut],
)
def list_vacation_requests(user_id: int, db: Session = Depends(get_db)):
    return vacation_service.list_vacation_requests(db, user_id)


@router.post("/vacation-requests/{request_id}/approve", response_model=VacationRequestOut)
def approve_vacation_request(
    request_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    try:
        return vacation_service.approve_vacation_request(db, request_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/vacation-requests/{request_id}/reject", response_model=VacationRequestOut)
def reject_vacation_request(
    request_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    try:
        return vacation_service.reject_vacation_request(db, request_id)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
