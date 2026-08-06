"""
Business logic for users and their HR profiles.

User and EmployeeProfile are one entity split into two tables (see CLAUDE.md)
and must always be created/deleted together — this module owns that
transaction boundary; it never runs raw queries itself, only the
repositories it calls do. Raises plain ValueError for domain errors (not
found, email taken) — the API layer translates these into HTTP responses.
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.employee_profile import EmployeeProfile
from app.models.user import User
from app.repositories import employee_profile_repository, user_repository
from app.schemas.employee_profile import EmployeeProfileUpdate
from app.schemas.user import UserCreate


def create_user(db: Session, payload: UserCreate) -> tuple[User, EmployeeProfile]:
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

    # add() only flushes (no commit), so this stays in the same transaction
    # as the user insert above: the commit() below creates both rows or
    # neither.
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
    return user, profile


def get_user(db: Session, user_id: int) -> User:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise ValueError("User not found")
    return user


def get_profile(db: Session, user_id: int) -> EmployeeProfile:
    profile = employee_profile_repository.get_by_user_id(db, user_id)
    if profile is None:
        raise ValueError("Employee profile not found")
    return profile


def get_user_with_profile(db: Session, user_id: int) -> tuple[User, EmployeeProfile]:
    user = get_user(db, user_id)
    if user.profile is None:
        raise ValueError("Employee profile not found")
    return user, user.profile


def list_users(db: Session) -> list[User]:
    return user_repository.list_all(db)


def delete_user(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    # User.profile has cascade="all, delete-orphan", so this removes the
    # matching employee_profiles row in the same commit.
    user_repository.delete(db, user)
    db.commit()


def update_profile(db: Session, user_id: int, payload: EmployeeProfileUpdate) -> EmployeeProfile:
    profile = get_profile(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
