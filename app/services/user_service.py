"""
Business logic for User + EmployeeProfile.

Raises plain ValueError for domain errors (not found, email already
registered) — the API layer translates these into the appropriate HTTP
status, same convention as vacation_service.

User and EmployeeProfile are created/deleted together in one transaction:
create_user() flushes the user (via the repository) to get user.id before
building the profile, then commits once at the end; delete_user() relies on
User.profile's cascade="all, delete-orphan" to remove the profile in the
same commit.
"""

from app.core.security import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.user import User
from app.repositories import employee_profile_repository, user_repository
from app.schemas.employee_profile import EmployeeProfileUpdate
from app.schemas.user import UserCreate
from sqlalchemy.orm import Session


def create_user(db: Session, payload: UserCreate) -> User:
    print("create user", flush=True)
    if user_repository.get_by_email(db, payload.email) is not None:
        raise ValueError("Email already registered")

    user = user_repository.add(
        db,
        User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        ),
    )

    profile = employee_profile_repository.add(
        db,
        EmployeeProfile(
            user_id=user.id,
            hire_date=payload.hire_date,
            expected_daily_hours=payload.expected_daily_hours,
            remaining_vacation_days=payload.remaining_vacation_days,
        ),
    )

    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return user


def get_user(db: Session, user_id: int) -> User:
    print("get user", flush=True)
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise ValueError("User not found")
    return user


def get_user_profile(db: Session, user_id: int) -> EmployeeProfile:
    print("get user profile", flush=True)
    profile = employee_profile_repository.get_by_user_id(db, user_id)
    if profile is None:
        raise ValueError("Employee profile not found")
    return profile


def update_user_profile(db: Session, user_id: int, payload: EmployeeProfileUpdate) -> EmployeeProfile:
    print("update user profile", flush=True)
    profile = employee_profile_repository.get_by_user_id(db, user_id)
    if profile is None:
        raise ValueError("Employee profile not found")

    employee_profile_repository.update(db, profile, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(profile)
    return profile


def get_user_full(db: Session, user_id: int) -> User:
    print("get user full" , flush=True)
    user = user_repository.get_by_id(db, user_id)
    if user is None or user.profile is None:
        raise ValueError("User not found")
    return user


def list_users(db: Session) -> list[User]:
    print("list users", flush=True)
    return user_repository.list_all(db)


def delete_user(db: Session, user_id: int) -> None:
    print("delete user", flush=True)
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise ValueError("User not found")
    user_repository.delete(db, user)
    db.commit()
