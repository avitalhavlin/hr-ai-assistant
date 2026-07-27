from datetime import date

from sqlalchemy.orm import Session

from app.models.employee_profile import EmployeeProfile


def create_profile(
    db: Session,
    user_id: int,
    hire_date: date,
    expected_daily_hours: float,
    remaining_vacation_days: float,
) -> EmployeeProfile:
    existing = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == user_id).first()
    if existing is not None:
        raise ValueError("Employee profile already exists for this user")

    profile = EmployeeProfile(
        user_id=user_id,
        hire_date=hire_date,
        expected_daily_hours=expected_daily_hours,
        remaining_vacation_days=remaining_vacation_days,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, user_id: int) -> EmployeeProfile | None:
    return db.query(EmployeeProfile).filter(EmployeeProfile.user_id == user_id).first()
