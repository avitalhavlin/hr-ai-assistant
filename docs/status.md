# Status

Running log of what's built, what's in progress, and what's next. Update this
at the end of each feature/phase discussion — append, don't rewrite history.
See `docs/decisions.md` for the reasoning behind key choices referenced here.

## Built

- **Initial project setup** (`791ddc7`) — FastAPI + SQLAlchemy 2.0 + Alembic +
  Pydantic v2 scaffold, docker-compose Postgres for local dev.
- **Core data model** — `Employee` model with `expected_daily_hours` (`c61d99f`),
  later split into `User` (login identity) + `EmployeeProfile` (HR data) via
  `1180bcb` — see [[user-employee-profile-split]]. `TimeEntry` and
  `VacationRequest` models in place, FK columns renamed `employee_id` → `user_id`.
- **Hours calculation service** — week/month/year aggregation in
  `app/services/hours_service.py`, exposed via `/users/{user_id}/time-entries/summary/*`.
- **Vacation requests** — create + admin approve/reject endpoints in
  `app/api/vacation_requests.py`, backed by `app/services/vacation_service.py`.
- **Password hashing** — `User` passwords bcrypt-hashed via passlib on
  creation (pulled forward from Phase 3, see [[password-hashing-pulled-forward]]).
  No login endpoint or JWT verification yet.

## In progress

- **`ah/create-user` branch** (`e506c93`, unmerged) — merges `User` +
  `EmployeeProfile` creation into a single `POST /users/` call, splits GET
  into `/profile` and `/full` variants. Code review (2026-07-27) found two
  blocking issues before merge:
  1. Deleted the only endpoint that could attach a profile to a user that
     doesn't already have one (no backfill path).
  2. Profile-creation logic moved inline into the route handler instead of
     staying in `app/services/`, violating the CLAUDE.md convention, and
     shipped with no test.
  Not merged to `main` as of 2026-07-27.

## Not started

- **Phase 3 — real auth & roles**: login endpoint, JWT issuance,
  `get_current_user()` dependency. Must replace the placeholder
  `X-Admin-User-Id` header check in `app/api/vacation_requests.py::require_admin`.
- **Phase 4 — Claude chat endpoint** (no tools yet).
- **Phase 5 — tool use**: `get_my_hours`, `get_vacation_balance`, `get_office_hours`.
- **Phase 6 — RAG over company policy docs**.
- **Phase 7 — chat logging + weekly admin usage report**.
- **Phase 8 — guardrails**: rate limiting, cost tracking, eval set.
- **Phase 9 — frontend**.
- **Phase 10 — deployment**.

## Open questions blocking future phases

- Company-specific policy numbers (vacation accrual rate, office hours,
  holidays) are placeholders in `app/core/config.py` — confirm before Phase 5/6.
- No new third-party services (vector DB, hosting) without checking in first.
