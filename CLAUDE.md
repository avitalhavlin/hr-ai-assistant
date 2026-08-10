# HR AI Assistant — Project Context for Claude Code

## What this project is
An HR time-tracking system with an AI chatbot layer. Employees log daily
start/end times; the system computes weekly/monthly/yearly hours; a Gemini-powered
chatbot answers questions about hours worked, vacation balance, and company policy
(office hours, working days), and also works as a general assistant. Admins get a
weekly report on chatbot usage patterns.

## Current phase
Phase 4 complete: basic Gemini chat endpoint, no tools yet. `POST /chat/`
(any authenticated user, via `app/api/deps.py::get_current_user`) accepts a
`message` plus an optional `history` list of prior `{role, content}` turns
and returns `{"reply": ...}`. `app/services/chat_service.py::
send_chat_message` builds the `generate_content` request (fixed system
prompt from `app/ai/prompts.py` as `system_instruction`, `model=
settings.gemini_model`, `max_output_tokens=1024`, history roles mapped
`assistant`→`model` since that's Gemini's convention) and calls it through
`app/ai/client.py::get_client()`, a lazily-constructed singleton
`genai.Client` — that indirection exists so tests can monkeypatch
`get_client`/`send_chat_message` instead of hitting the real API.
Conversation history is entirely client-resent; nothing is persisted
server-side (chat logging is Phase 7) and there's no tool use yet (Phase 5)
or RAG (Phase 6), so the system prompt tells the model to say plainly it
can't look up real hours/vacation/policy data rather than guessing. Any
`google.genai.errors.APIError` from the SDK is caught in the service,
re-raised as `ChatServiceError`, and mapped to a 502 in the route.

Phase 3 complete: real JWT-based auth. `POST /auth/token` (OAuth2
password-form login — `username` field carries the email) issues a bearer
access token via `app/core/security.py::create_access_token` (HS256, signed
with `settings.secret_key`/`settings.algorithm`, expiry from
`settings.access_token_expire_minutes`); `app/services/auth_service.py`
checks credentials with the existing `verify_password`. `app/api/deps.py`'s
`get_current_user` decodes the token and loads the `User` fresh from the DB
on every request, so a role change or deletion takes effect immediately —
no refresh tokens or revocation list. `require_admin` (same name as before,
now backed by real auth) and the new `require_owner_or_admin` (reads
`user_id` from each route's own path parameter) gate every endpoint; the
placeholder `X-Admin-User-Id` header is gone. Unauthenticated `POST /users/`
always creates `role=employee` regardless of payload — only an authenticated
admin caller may set another role. `PATCH /users/{id}/profile` is
owner-or-admin, but only an admin may include `expected_daily_hours`/
`remaining_vacation_days` in the payload (checked in the route via
`payload.model_fields_set`, not in `user_service`, since it's authorization
policy, not a domain invariant); an owner may still update their own
`hire_date`. `GET /users/` and `DELETE /users/{id}` are admin-only; all other
`/users/{id}...`, time-entry, and vacation-request "own resource" routes are
owner-or-admin.

The former `Employee` model was split into `User` (login identity: name,
email, hashed password, role) and `EmployeeProfile` (HR data: `hire_date`,
`expected_daily_hours`, `remaining_vacation_days`), one-to-one via
`EmployeeProfile.user_id`. All FK columns and API routes were renamed to
match (`/employees` → `/users`, `employee_id` → `user_id` on
`TimeEntry`/`VacationRequest`).

`User` and `EmployeeProfile` are conceptually one entity split into two tables
only because profile data isn't needed on every query. They must always be
created and deleted together: `POST /users` creates both rows in a single DB
transaction (via `flush()` to get `user.id` before the profile insert, one
`commit()` at the end — see `app/api/users.py`), and `DELETE /users/{id}`
relies on `User.profile`'s `cascade="all, delete-orphan"` to remove the
profile in the same commit. Profile fields with no sensible default
(`hire_date`) are nullable and can be filled in later via an update
endpoint (not built yet); `expected_daily_hours`/`remaining_vacation_days`
keep their policy defaults (8.0 / 21.0) since those are meaningful even
when not explicitly provided. `user_id` is the only field guaranteed
non-null on `EmployeeProfile`.
Update this section as phases complete so future sessions know where we left off.

## Tech stack
- Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 / pydantic-settings
- PostgreSQL (docker-compose for local dev)
- JWT auth (python-jose + passlib)
- Google Gemini API (`google-genai` SDK) for the chatbot (basic chat endpoint since Phase 4)
- pytest for tests

## Conventions
- All business logic (hours calculation, vacation calculation) lives in
  `app/services/`, never inline in API routes. The chatbot's tools call these
  same service functions — never reimplement logic in the AI layer.
- Pydantic schemas in `app/schemas/`, SQLAlchemy models in `app/models/`.
- One router per resource in `app/api/`, included in `app/main.py`.
- Every new service function gets a matching test in `tests/`.
- Env vars are read only through `app/core/config.py` (`Settings` class) — never
  `os.getenv` scattered around the codebase.
- Commit in small, working slices per phase/feature, not one giant pass.

## Roadmap (see README for full detail)
0. Setup (this scaffold)
1. Core data model: Employee, TimeEntry, VacationRequest
2. Hours calculation service (week/month/year aggregation)
3. Auth & roles (employee/admin)
4. Basic Claude chat endpoint (no tools)
5. Tool use: get_my_hours, get_vacation_balance, get_office_hours
6. RAG over company policy docs
7. Chat logging + weekly admin usage report
8. Guardrails: rate limiting, cost tracking, eval set
9. Frontend
10. Deployment

## Things to ask the human about before assuming
- Company-specific policy numbers (vacation accrual rate, office hours, holidays)
  are placeholders in `app/core/config.py` — confirm real values before Phase 5/6.
- Don't add new third-party services (vector DB, hosting) without checking in.
