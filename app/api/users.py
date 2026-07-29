from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.employee_profile import EmployeeProfile
from app.models.user import User
from app.schemas.employee_profile import EmployeeProfileOut, EmployeeProfileUpdate
from app.schemas.user import UserCreate, UserOut, UserWithProfileOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

# NOTE: JWT auth/login wiring lands in Phase 3. Passwords are hashed for
# storage here, but there's no login endpoint yet to verify them against.


def _to_user_with_profile_out(user: User, profile: EmployeeProfile) -> UserWithProfileOut:
    return UserWithProfileOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        hire_date=profile.hire_date,
        expected_daily_hours=profile.expected_daily_hours,
        remaining_vacation_days=profile.remaining_vacation_days,
    )


@router.post("/", response_model=UserWithProfileOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = user_service.create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_user_with_profile_out(user, user.profile)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    
    try:
        return user_service.get_user(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{user_id}/profile", response_model=EmployeeProfileOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    
    try:
        return user_service.get_user_profile(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{user_id}/profile", response_model=EmployeeProfileOut)
def update_user_profile(user_id: int, payload: EmployeeProfileUpdate, db: Session = Depends(get_db)):
    try:
        return user_service.update_user_profile(db, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{user_id}/full", response_model=UserWithProfileOut)
def get_user_full(user_id: int, db: Session = Depends(get_db)):
    
    try:
        user = user_service.get_user_full(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_user_with_profile_out(user, user.profile)


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    
    return user_service.list_users(db)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    try:
        user_service.delete_user(db, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
