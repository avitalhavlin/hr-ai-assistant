"""Database layer for EmployeeProfile: raw persistence only, no business rules."""

from sqlalchemy.orm import Session

from app.models.employee_profile import EmployeeProfile


def get_by_user_id(db: Session, user_id: int) -> EmployeeProfile | None:
    return db.query(EmployeeProfile).filter(EmployeeProfile.user_id == user_id).first()


def add(db: Session, profile: EmployeeProfile) -> EmployeeProfile:
    db.add(profile)
    db.flush()
    return profile
