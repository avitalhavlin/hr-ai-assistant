from datetime import timedelta

from app.core.security import create_access_token
from app.models.user import Role
from app.schemas.user import UserCreate
from app.services import user_service

PASSWORD = "supersecret123"


def _make_user(db, **overrides):
    defaults = dict(
        full_name="Test User",
        email="user@example.com",
        password=PASSWORD,
        role=Role.employee,
    )
    defaults.update(overrides)
    user, _profile = user_service.create_user(db, UserCreate(**defaults))
    return user


def _login(client, email, password=PASSWORD):
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success_returns_bearer_token(client, db_session):
    _make_user(db_session, email="login@example.com")

    response = client.post(
        "/auth/token", data={"username": "login@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(client, db_session):
    _make_user(db_session, email="login2@example.com")

    response = client.post(
        "/auth/token", data={"username": "login2@example.com", "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email(client, db_session):
    response = client.post(
        "/auth/token", data={"username": "nobody@example.com", "password": PASSWORD}
    )

    assert response.status_code == 401


def test_protected_route_requires_token(client, db_session):
    user = _make_user(db_session, email="noauth@example.com")

    response = client.get(f"/users/{user.id}")

    assert response.status_code == 401


def test_protected_route_rejects_garbage_token(client, db_session):
    user = _make_user(db_session, email="garbage@example.com")

    response = client.get(f"/users/{user.id}", headers=_auth_headers("not-a-real-token"))

    assert response.status_code == 401


def test_protected_route_rejects_expired_token(client, db_session):
    user = _make_user(db_session, email="expired@example.com")
    expired_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(minutes=-1)
    )

    response = client.get(f"/users/{user.id}", headers=_auth_headers(expired_token))

    assert response.status_code == 401


def test_owner_can_access_own_user(client, db_session):
    user = _make_user(db_session, email="owner@example.com")
    token = _login(client, "owner@example.com")

    response = client.get(f"/users/{user.id}", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["id"] == user.id


def test_non_admin_cannot_access_other_user(client, db_session):
    user = _make_user(db_session, email="self@example.com")
    other = _make_user(db_session, email="other@example.com")
    token = _login(client, "self@example.com")

    response = client.get(f"/users/{other.id}", headers=_auth_headers(token))

    assert response.status_code == 403
    assert user.id != other.id


def test_admin_can_access_any_user(client, db_session):
    admin = _make_user(db_session, email="admin@example.com", role=Role.admin)
    other = _make_user(db_session, email="regular@example.com")
    token = _login(client, "admin@example.com")

    response = client.get(f"/users/{other.id}", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["id"] == other.id
    assert admin.role == Role.admin


def test_unauthenticated_registration_forces_employee_role(client):
    response = client.post(
        "/users/",
        json={
            "full_name": "New Signup",
            "email": "signup@example.com",
            "password": PASSWORD,
            "role": "admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "employee"


def test_admin_can_create_admin_user(client, db_session):
    _make_user(db_session, email="creator-admin@example.com", role=Role.admin)
    token = _login(client, "creator-admin@example.com")

    response = client.post(
        "/users/",
        json={
            "full_name": "New Admin",
            "email": "new-admin@example.com",
            "password": PASSWORD,
            "role": "admin",
        },
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_owner_can_update_own_hire_date(client, db_session):
    user = _make_user(db_session, email="hiredate@example.com")
    token = _login(client, "hiredate@example.com")

    response = client.patch(
        f"/users/{user.id}/profile",
        json={"hire_date": "2026-01-15"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["hire_date"] == "2026-01-15"


def test_owner_cannot_update_expected_daily_hours(client, db_session):
    user = _make_user(db_session, email="hours@example.com")
    token = _login(client, "hours@example.com")

    response = client.patch(
        f"/users/{user.id}/profile",
        json={"expected_daily_hours": 4.0},
        headers=_auth_headers(token),
    )

    assert response.status_code == 403


def test_admin_can_update_expected_daily_hours(client, db_session):
    _make_user(db_session, email="admin2@example.com", role=Role.admin)
    target = _make_user(db_session, email="target@example.com")
    token = _login(client, "admin2@example.com")

    response = client.patch(
        f"/users/{target.id}/profile",
        json={"expected_daily_hours": 4.0},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["expected_daily_hours"] == 4.0


def test_list_users_requires_admin(client, db_session):
    _make_user(db_session, email="lister@example.com")
    token = _login(client, "lister@example.com")

    response = client.get("/users/", headers=_auth_headers(token))

    assert response.status_code == 403


def test_list_users_allows_admin(client, db_session):
    _make_user(db_session, email="admin3@example.com", role=Role.admin)
    token = _login(client, "admin3@example.com")

    response = client.get("/users/", headers=_auth_headers(token))

    assert response.status_code == 200


def test_delete_user_requires_admin(client, db_session):
    user = _make_user(db_session, email="deleteme@example.com")
    token = _login(client, "deleteme@example.com")

    response = client.delete(f"/users/{user.id}", headers=_auth_headers(token))

    assert response.status_code == 403


def test_delete_user_allows_admin(client, db_session):
    _make_user(db_session, email="admin4@example.com", role=Role.admin)
    target = _make_user(db_session, email="target2@example.com")
    token = _login(client, "admin4@example.com")

    response = client.delete(f"/users/{target.id}", headers=_auth_headers(token))

    assert response.status_code == 204


def test_vacation_approve_requires_admin(client, db_session):
    user = _make_user(db_session, email="vacation@example.com")
    token = _login(client, "vacation@example.com")
    create_response = client.post(
        f"/users/{user.id}/vacation-requests/",
        json={"start_date": "2026-09-01", "end_date": "2026-09-05"},
        headers=_auth_headers(token),
    )
    assert create_response.status_code == 200
    request_id = create_response.json()["id"]

    response = client.post(
        f"/vacation-requests/{request_id}/approve", headers=_auth_headers(token)
    )

    assert response.status_code == 403


def test_vacation_approve_allows_admin(client, db_session):
    _make_user(db_session, email="admin5@example.com", role=Role.admin)
    employee = _make_user(db_session, email="employee5@example.com")
    employee_token = _login(client, "employee5@example.com")
    admin_token = _login(client, "admin5@example.com")

    create_response = client.post(
        f"/users/{employee.id}/vacation-requests/",
        json={"start_date": "2026-09-01", "end_date": "2026-09-05"},
        headers=_auth_headers(employee_token),
    )
    request_id = create_response.json()["id"]

    response = client.post(
        f"/vacation-requests/{request_id}/approve", headers=_auth_headers(admin_token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
