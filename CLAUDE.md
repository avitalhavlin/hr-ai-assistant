# HR AI Assistant — Project Context for Claude Code

## What this project is
An HR time-tracking system with an AI chatbot layer. Employees log daily
start/end times; the system computes weekly/monthly/yearly hours; a Claude-powered
chatbot answers questions about hours worked, vacation balance, and company policy
(office hours, working days), and also works as a general assistant. Admins get a
weekly report on chatbot usage patterns.

## Current phase
Phase 1 complete: User/EmployeeProfile/TimeEntry/VacationRequest models, hours
calculation service, and VacationRequest endpoints (create, admin
approve/reject) are in place. The former `Employee` model was split into
`User` (login identity: name, email, hashed password, role) and
`EmployeeProfile` (HR data: `hire_date`, `expected_daily_hours`,
`remaining_vacation_days`), one-to-one via `EmployeeProfile.user_id`. All FK
columns and API routes were renamed to match (`/employees` → `/users`,
`employee_id` → `user_id` on `TimeEntry`/`VacationRequest`). User passwords
are hashed with bcrypt (via passlib) on creation — pulled forward from Phase 3
at the user's request — but there is still no login endpoint or JWT auth, so
admin-only actions (vacation approve/reject) are gated by a placeholder
`X-Admin-User-Id` header dependency in `app/api/vacation_requests.py`.
Replace that with real `get_current_user()`-based auth in Phase 3. No AI
wiring yet.

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
- Anthropic Python SDK for the chatbot (added in Phase 4+)
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
