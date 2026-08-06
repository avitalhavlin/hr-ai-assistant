"""
Minimal MCP server exposing HR API endpoints as tools: list_users,
create_user.

Packaged as an MCPB (uv runtime) extension - see ../manifest.json. The
three env vars below (HR_API_BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD) are
supplied by Claude Desktop at launch, sourced from the user_config values
entered in the extension's install dialog.

This is a test harness for connecting Claude directly to the running
FastAPI app over MCP (as an alternative to the in-app chatbot planned
for Phase 4+ in CLAUDE.md). Not wired into the app itself - it's a
standalone client that calls the same HTTP API any other client would,
authenticated as whatever admin user's credentials are configured above.
"""
import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.environ.get("HR_API_BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

mcp = FastMCP("hr-ai-assistant")

_token: str | None = None


def _login() -> str:
    resp = httpx.post(
        f"{API_BASE_URL}/auth/token",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _authed_request(method: str, path: str, **kwargs) -> httpx.Response:
    global _token
    if _token is None:
        _token = _login()

    headers = {"Authorization": f"Bearer {_token}"}
    resp = httpx.request(method, f"{API_BASE_URL}{path}", headers=headers, **kwargs)
    if resp.status_code == 401:
        # Token expired (ACCESS_TOKEN_EXPIRE_MINUTES) - re-login once and retry.
        _token = _login()
        headers = {"Authorization": f"Bearer {_token}"}
        resp = httpx.request(method, f"{API_BASE_URL}{path}", headers=headers, **kwargs)

    resp.raise_for_status()
    return resp


@mcp.tool()
def list_users() -> list[dict]:
    """List all users in the HR system (admin only). Returns id, full_name, email, role, created_at per user."""
    return _authed_request("GET", "/users/").json()


@mcp.tool()
def create_user(
    full_name: str,
    email: str,
    password: str,
    role: str = "employee",
    hire_date: Optional[str] = None,
    expected_daily_hours: float = 8.0,
    remaining_vacation_days: float = 21.0,
) -> dict:
    """Create a new user in the HR system (admin only).

    role must be "employee" or "admin" - since this tool always calls the
    API as an authenticated admin, it CAN create other admins, unlike an
    unauthenticated signup which is always forced to role=employee.
    password must be at least 8 characters. hire_date, if given, is an
    ISO date string like "2026-01-15".
    """
    payload = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "role": role,
        "expected_daily_hours": expected_daily_hours,
        "remaining_vacation_days": remaining_vacation_days,
    }
    if hire_date is not None:
        payload["hire_date"] = hire_date
    return _authed_request("POST", "/users/", json=payload).json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
