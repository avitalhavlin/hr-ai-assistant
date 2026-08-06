"""
Shared FastAPI dependencies for API routes.

get_current_user decodes the bearer JWT and loads the corresponding User
fresh from the DB on every call (no role/claims are trusted from the token
itself beyond identity) — so a role change or user deletion takes effect
immediately, without waiting for token expiry or any revocation mechanism.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import Role, User
from app.repositories import user_repository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _user_from_token(token: str, db: Session) -> Optional[User]:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    return user_repository.get_by_id(db, user_id)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_token(token, db)
    if user is None:
        raise _CREDENTIALS_EXCEPTION
    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if token is None:
        return None
    return _user_from_token(token, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_owner_or_admin(
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Only use on routes where user_id is one of the route's own path
    parameters — FastAPI binds this dependency's user_id the same way it
    binds the route function's parameters, so on a route without a user_id
    path segment this would silently become a required query parameter
    instead.
    """
    if current_user.role != Role.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this user",
        )
    return current_user
