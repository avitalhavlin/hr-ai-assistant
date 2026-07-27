from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.employee_profile import EmployeeProfileCreate, EmployeeProfileOut
from app.services import employee_profile_service

router = APIRouter(prefix="/users/{user_id}/profile", tags=["employee-profiles"])


@router.post("/", response_model=EmployeeProfileOut)
def create_employee_profile(user_id: int, payload: EmployeeProfileCreate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        return employee_profile_service.create_profile(
            db,
            user_id,
            payload.hire_date,
            payload.expected_daily_hours,
            payload.remaining_vacation_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/", response_model=EmployeeProfileOut)
def get_employee_profile(user_id: int, db: Session = Depends(get_db)):
    profile = employee_profile_service.get_profile(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return profile
