# HR AI Assistant — Project Context for Claude Code

## What this project is
An HR time-tracking system with an AI chatbot layer. Employees log daily
start/end times; the system computes weekly/monthly/yearly hours; a Gemini-powered
chatbot answers questions about hours worked, vacation balance, and company policy
(office hours, working days), and also works as a general assistant. Admins get a
weekly report on chatbot usage patterns.

## Current phase
Phase 6 complete: RAG over company policy docs. Policy markdown files live
in `app/ai/policy_docs/` (currently 3 placeholder docs — vacation/leave,
remote work, code of conduct — written as sample content; swap in the real
policies before relying on this for real answers). A new `PolicyChunk`
model/table (`app/models/policy_chunk.py`, migration
`500cd5e17304_add_policy_chunks_table_with_pgvector_`) stores embedded
chunks; embeddings use a pgvector `Vector(settings.embedding_dimensions)`
column on Postgres (the `db` service in `docker-compose.yml` now runs
`pgvector/pgvector:pg16` instead of plain `postgres:16-alpine`, so
`CREATE EXTENSION vector` — run by that migration — succeeds).
`app/services/policy_service.py::chunk_text` splits a doc into
paragraph-sized chunks (merging any paragraph under ~200 chars, e.g. a
markdown header, into its neighbor); `reindex_policies(db)` wipes and
rebuilds the whole table from `app/ai/policy_docs/*.md`, embedding each
chunk via `app/ai/embeddings.py::embed_text(text, task_type=
"RETRIEVAL_DOCUMENT")` — run manually with `python
scripts/reindex_policies.py` whenever the docs change (no admin API
endpoint for this; it's a rare maintenance action, not a user flow).
`search_policies(db, query, top_k=3)` embeds the query with
`task_type="RETRIEVAL_QUERY"` and calls
`policy_chunk_repository.search_similar`, which ranks by
`PolicyChunk.embedding.cosine_distance(...)` (pgvector's `<=>` operator —
Postgres-only, so `tests/test_policy_chunk_repository.py` only covers
plain CRUD against the SQLite fixture, not this query; it's verified
manually against the real dockerized Postgres instead). The new
`search_policy_docs` tool in `app/ai/tools.py` wraps `search_policies` and
is offered to every caller, same tier as the other employee tools;
`SYSTEM_PROMPT` now tells the model to ground policy answers strictly in
what the tool returns and say plainly when nothing relevant comes back,
rather than the old blanket "I can't look that up yet" disclaimer.
Embeddings use the free Gemini `embed_content` API
(`gemini-embedding-001`, same SDK/key as chat) rather than a new provider
or a dedicated vector DB, per the "don't add new third-party services
without checking in" rule below.

Note: `app/main.py` still runs `Base.metadata.create_all(bind=engine)` at
import time (a Phase 0/1 leftover the comment above it says should have
been replaced by `alembic upgrade head` once Alembic was set up in Phase
1 — that follow-up was never done). Any dev DB bootstrapped that way has
no Alembic version history, so a fresh `alembic upgrade head` will try to
replay old migrations against tables that don't match (e.g. the
users/employees rename) and fail; `alembic stamp <current head>` before
upgrading resolves it for an existing dev DB. Worth fixing properly
(swap that call for a real `alembic upgrade head` and drop the
`create_all`) next time this area is touched.

Phase 5 complete: chatbot tool use. `POST /chat/` (any authenticated user,
via `app/api/deps.py::get_current_user`, plus a `db: Session =
Depends(get_db)`) accepts a `message` plus an optional `history` list of
prior `{role, content}` turns and returns `{"reply": ...}`.
`app/services/chat_service.py::send_chat_message(payload, db, user_id,
is_admin)` runs a tool-calling loop (capped at `MAX_TOOL_ROUNDS = 5`,
raising `ChatServiceError` if exceeded): it calls `generate_content` with
`tools=app.ai.tools.build_tools(is_admin)` in the `GenerateContentConfig`;
whenever the response carries `response.function_calls`, it appends the
model's turn plus a `role="user"` turn containing each call's
`types.Part.from_function_response(...)` (that role for function-response
turns is confirmed against the installed SDK's own automatic-function-
calling code, not guessed) and loops; once a response has no function
calls, `response.text` is returned. `app/ai/tools.py` declares the tool
schemas (`types.Tool(function_declarations=[...])`, using
`parameters_json_schema` — a plain JSON-schema dict — for each), split
into `_EMPLOYEE_DECLARATIONS` (always offered) and `_ADMIN_DECLARATIONS`
(only appended by `build_tools` when `is_admin`) — a non-admin caller's
model is never even told the admin tool exists. `call_tool(name, args,
db, user_id, is_admin)` dispatches to `get_my_hours`/`get_hours_between`/
`get_vacation_balance`/`get_office_hours`/`get_employees_hours_report`.
Each is a thin wrapper: `get_my_hours` (period `month`/`year` only —
`week` was dropped in favor of the more flexible `get_hours_between`)
resolves "current period" defaults from `date.today()` when the model
omits year/month, then calls `hours_service.get_hours_for_month/year`;
`get_hours_between` takes arbitrary `start_date`/`end_date` (`YYYY-MM-DD`
strings, parsed with `date.fromisoformat`) and calls
`hours_service.get_hours_between` directly, for any date range the
month/year shortcut doesn't cover; `get_vacation_balance` calls
`vacation_service.get_vacation_balance` (wraps
`employee_profile_repository.get_by_user_id`, returns `None` if the user
has no profile yet); `get_office_hours` just reads
`settings.office_open_time`/`office_close_time`/`working_days`;
`get_employees_hours_report` (admin-only — `call_tool` re-checks
`is_admin` and returns `{"error": "Admin access required for this
tool."}` rather than raising if it's somehow reached anyway, as
defense-in-depth alongside the schema being withheld) lists every user
via `user_service.list_users` and calls `hours_service.get_hours_between`
per user for the (optionally defaulted-to-current-month) range — the
per-user loop lives in `tools.py`, not a new `hours_service` function,
same "orchestration, not domain logic" reasoning as `get_my_hours`'s
period defaulting. Tool `db`/`user_id`/`is_admin` are always server-bound
by `chat_service.py` (computed once in `app/api/chat.py` from
`current.id`/`current.role == Role.admin`), never model-settable
parameters — the model can't act on another user's data or claim admin
access. A `ValueError` from a tool (e.g. an invalid month) is caught in
`call_tool` and turned into `{"error": ...}` returned to the model,
rather than raised, so a bad tool call doesn't fail the whole chat
request. `app/ai/prompts.py`'s `SYSTEM_PROMPT` now tells the model to use
these tools rather than guess real numbers and mentions the admin-only
report tool (policy documents beyond office hours followed in Phase 6;
chat logging is still Phase 7). Any `google.genai.errors.APIError` from the SDK is still
caught in the service, re-raised as `ChatServiceError`, and mapped to a
502 in the route — same as Phase 4.

Phase 4 complete: basic Gemini chat endpoint, no tools yet, via
`app/ai/client.py::get_client()`, a lazily-constructed singleton
`genai.Client` — that indirection exists so tests can monkeypatch
`get_client`/`send_chat_message` instead of hitting the real API.
Conversation history is entirely client-resent; nothing is persisted
server-side yet (chat logging is Phase 7).

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
  are placeholders in `app/core/config.py` — confirm real values.
- The Phase 6 policy docs in `app/ai/policy_docs/` are placeholder/sample
  content too (leave policy, remote work, code of conduct) — swap in the
  real documents before relying on chatbot answers grounded in them, then
  re-run `python scripts/reindex_policies.py`.
- Don't add new third-party services (vector DB, hosting) without checking
  in. (Phase 6's RAG intentionally avoided this — it reuses the existing
  Postgres via the pgvector extension rather than a new vector DB service.)
