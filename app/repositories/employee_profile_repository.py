"""
Data access for EmployeeProfile. No business rules, no transaction control —
callers (services) own flush()/commit() so multi-entity operations can share
one transaction.
"""

from sqlalchemy.orm import Session

from app.models.employee_profile import EmployeeProfile


def get_by_user_id(db: Session, user_id: int) -> EmployeeProfile | None:
    return db.query(EmployeeProfile).filter(EmployeeProfile.user_id == user_id).first()


def add(db: Session, profile: EmployeeProfile) -> EmployeeProfile:
    db.add(profile)
    db.flush()
    return profile


def update(db: Session, profile: EmployeeProfile, fields: dict) -> EmployeeProfile:
    for field, value in fields.items():
        setattr(profile, field, value)
    db.flush()
    return profile
