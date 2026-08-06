"""
Login credential verification. Kept separate from app/core/security.py
because this needs a Session to look up the user; core/security.py has no
DB access.

Returns None for both "no such user" and "wrong password" rather than
raising ValueError (the usual service convention) — a login failure isn't a
domain error to distinguish, and not distinguishing avoids leaking which
emails are registered.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories import user_repository


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
