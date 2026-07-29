"""
Shared FastAPI dependencies for API routes.

NOTE: real JWT-based auth lands in Phase 3. Until then, admin-only actions
are gated by an X-Admin-User-Id header identifying the acting user, which
must resolve to a user with the admin role. Replace require_admin with a
proper get_current_user()-based check in Phase 3.
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import Role, User
from app.repositories import user_repository


def require_admin(
    x_admin_user_id: int = Header(..., alias="X-Admin-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    admin = user_repository.get_by_id(db, x_admin_user_id)
    if admin is None:
        raise HTTPException(status_code=401, detail="Unknown acting user")
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return admin
