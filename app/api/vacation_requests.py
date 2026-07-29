from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import Role, User
from app.repositories import user_repository
from app.schemas.vacation_request import VacationRequestCreate, VacationRequestOut
from app.services import vacation_service

router = APIRouter(tags=["vacation-requests"])

# NOTE: real JWT-based auth lands in Phase 3. Until then, admin-only actions
# are gated by an X-Admin-User-Id header identifying the acting user, which
# must resolve to a user with the admin role. Replace this dependency with a
# proper get_current_user()-based check in Phase 3.


def require_admin(
    x_admin_user_id: int = Header(..., alias="X-Admin-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    admin = user_repository.get_by_id(db, x_admin_user_id)
    if admin is None:
        raise HTTPException(status_code=401, detail="Unknown acting user")
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return admin


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
