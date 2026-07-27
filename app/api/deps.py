from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import Role, User

# NOTE: real JWT-based auth lands in Phase 3. Until then, admin-only actions
# are gated by an X-Admin-User-Id header identifying the acting user, which
# must resolve to a user with the admin role. Replace this dependency with a
# proper get_current_user()-based check in Phase 3.


def require_admin(
    x_admin_user_id: int = Header(..., alias="X-Admin-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    admin = db.get(User, x_admin_user_id)
    if admin is None:
        raise HTTPException(status_code=401, detail="Unknown acting user")
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return admin
