from sqlalchemy.orm import Session

from app.models.user import Role, User
from app.services.update_utils import apply_updates

# NOTE: password changes need to verify the caller's identity, which requires
# real auth (Phase 3) — not exposed via update_user until then.


def update_user(db: Session, user_id: int, updates: dict) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    if "email" in updates and updates["email"] != user.email:
        existing = db.query(User).filter(User.email == updates["email"]).first()
        if existing is not None:
            raise ValueError("Email already registered")

    apply_updates(user, updates)

    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user_id: int, role: Role) -> User | None:
    user = db.get(User, user_id)
    if user is None:
        return None

    user.role = role
    db.commit()
    db.refresh(user)
    return user
