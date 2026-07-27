from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.user import User
from app.schemas.employee_profile import EmployeeProfileOut
from app.schemas.user import UserCreate, UserOut, UserWithProfileOut

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
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.flush()

    profile = EmployeeProfile(
        user_id=user.id,
        hire_date=payload.hire_date,
        expected_daily_hours=payload.expected_daily_hours,
        remaining_vacation_days=payload.remaining_vacation_days,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return _to_user_with_profile_out(user, profile)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/profile", response_model=EmployeeProfileOut)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return profile


@router.get("/{user_id}/full", response_model=UserWithProfileOut)
def get_user_full(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user or not user.profile:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_user_with_profile_out(user, user.profile)


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
