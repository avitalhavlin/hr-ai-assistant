"""
Minimal MCP server exposing the HR API's admin-only GET /users/ endpoint
as a single tool: list_users.

This is a test harness for connecting Claude directly to the running
FastAPI app over MCP (as an alternative to the in-app chatbot planned
for Phase 4+ in CLAUDE.md). Not wired into the app itself — it's a
standalone client that calls the same HTTP API any other client would.

Requires the FastAPI app running locally (uvicorn app.main:app --reload)
and an admin user's credentials (see scripts/create_admin.py) in the
ADMIN_EMAIL / ADMIN_PASSWORD env vars.

Run directly for a quick manual check:
    python mcp_server/server.py

In practice this is spawned by the Claude client (Desktop/Cowork) over
stdio per the mcpServers config — see project README for the exact
config snippet.
"""
import os

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


def _authed_get(path: str) -> httpx.Response:
    global _token
    if _token is None:
        _token = _login()

    resp = httpx.get(f"{API_BASE_URL}{path}", headers={"Authorization": f"Bearer {_token}"})
    if resp.status_code == 401:
        # Token expired (ACCESS_TOKEN_EXPIRE_MINUTES) — re-login once and retry.
        _token = _login()
        resp = httpx.get(f"{API_BASE_URL}{path}", headers={"Authorization": f"Bearer {_token}"})

    resp.raise_for_status()
    return resp


@mcp.tool()
def list_users() -> list[dict]:
    """List all users in the HR system (admin only). Returns id, full_name, email, role, created_at per user."""
    return _authed_get("/users/").json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
