"""
One-off bootstrap: create the first admin user directly via the service
layer, bypassing the API's rule that an unauthenticated POST /users/
always creates role=employee (see CLAUDE.md). Only needed once per
fresh database — after this admin exists, further admins can be created
through the API by an authenticated admin.

Run from the project root (venv active, DATABASE_URL pointing at your
running Postgres):

    python scripts/create_admin.py
"""
import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import Role  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services import user_service  # noqa: E402


def main() -> None:
    email = input("Admin email: ").strip()
    password = input("Admin password (min 8 chars): ").strip()
    full_name = input("Full name: ").strip()

    db = SessionLocal()
    try:
        payload = UserCreate(full_name=full_name, email=email, password=password, role=Role.admin)
        user, _profile = user_service.create_user(db, payload)
    except ValueError as exc:
        print(f"Failed: {exc}")
        return
    finally:
        db.close()

    print(f"Created admin user id={user.id} email={user.email}")


if __name__ == "__main__":
    main()
