# Decisions

Running log of key decisions made during feature discussions — what was
decided and why, so later sessions don't re-litigate settled questions. One
entry per decision, newest last. Cross-reference `docs/status.md` for what's
currently built as a result.

## User/EmployeeProfile split
<a id="user-employee-profile-split"></a>

**Decision:** Split the original `Employee` model into `User` (login
identity: name, email, hashed password, role) and `EmployeeProfile` (HR data:
`hire_date`, `expected_daily_hours`, `remaining_vacation_days`), joined
one-to-one via `EmployeeProfile.user_id`. FK columns and routes renamed to
match (`/employees` → `/users`, `employee_id` → `user_id`).

**Why:** Keeps login/auth concerns (Phase 3) separate from HR data, so auth
work doesn't need to touch HR fields and vice versa. `remaining_vacation_days`
was added at the same time since it belongs conceptually with the other HR
profile fields, not login identity.

**Landed:** `1180bcb`, merged to `main` via PR #1 (`f4bcd9b`), 2026-07-27.

---

## Password hashing pulled forward from Phase 3
<a id="password-hashing-pulled-forward"></a>

**Decision:** Hash `User` passwords with bcrypt (via passlib) at creation
time now, even though the roadmap originally scheduled this as part of
Phase 3 (auth & roles).

**Why:** User explicitly requested this be done early — no reason to store
plaintext passwords even before login/JWT verification exists. Login
endpoint and JWT issuance are still deferred to Phase 3.

**Landed:** part of `1180bcb`.

---

## Admin-only actions gated by placeholder header, not real auth
<a id="placeholder-admin-header"></a>

**Decision:** Until real JWT auth lands, `app/api/vacation_requests.py`
gates admin-only actions (approve/reject) with a `require_admin` dependency
that reads an `X-Admin-User-Id` header, looks up that user, and checks
`role == Role.admin`.

**Why:** Vacation approve/reject needed *some* access control to be usable
for testing before Phase 3 auth exists, without building real auth early.
Explicitly a placeholder — `get_current_user()`-based auth is intended to
replace it directly, not layer on top of it.

**Status:** Still in place as of 2026-07-27. Replace in Phase 3 — see
`docs/status.md` "Not started".

---

## `ah/create-user` merge blocked pending fixes
<a id="create-user-review-2026-07-27"></a>

**Decision:** Do not merge `ah/create-user` (`e506c93`) as-is. Code review
(2026-07-27, via `/code-review`) surfaced two issues to fix first:

1. The branch deletes `app/api/employee_profiles.py`, removing the only way
   to attach an `EmployeeProfile` to a `User` that doesn't already have one
   (no backfill path for pre-existing or future users created outside
   `create_user`).
2. Profile-creation logic was inlined into the `POST /users/` route handler
   instead of staying in `app/services/`, contradicting the CLAUDE.md
   convention that business logic never lives inline in API routes. No test
   was added for the new path, and it silently drops the old explicit
   duplicate-profile check in favor of relying on the DB unique constraint.

**Why:** Both are conventions/behavior regressions, not style nitpicks —
losing the backfill path is a real functional gap, and the inline logic is
untestable without spinning up the full route/DB stack.

**Status:** Open as of 2026-07-27 — see `docs/status.md` "In progress".

---

## PATCH endpoints added for Users, EmployeeProfile, TimeEntry, VacationRequest
<a id="patch-endpoints-2026-07-27"></a>

**Decision:** Added `PATCH` endpoints for all four core resources, each
backed by a service-layer update function (`user_service.update_user`,
`employee_profile_service.update_profile`, `time_entry_service.update_time_entry`,
`vacation_service.update_vacation_request`) using partial-update schemas
(`model_dump(exclude_unset=True)`). A shared `app/services/update_utils.py::apply_updates`
helper applies the update dict and rejects an explicit `null` for any
non-nullable field with a `ValueError` (→ 400), instead of letting it hit a
NOT NULL column and crash.

Follow-up code review (2026-07-27) found the initial cut had no access
control on any of the four routes, so:
- `role` and `password` were removed from `UserUpdate` entirely — role
  changes now go through a separate `PATCH /users/{user_id}/role`, gated by
  `require_admin` (extracted to shared `app/api/deps.py` from
  `vacation_requests.py` — see [[placeholder-admin-header]]); password
  changes are deferred until real auth exists (Phase 3), since verifying
  "you are this user" needs a session.
- `PATCH /users/{user_id}/profile` now requires `require_admin`, since HR
  fields like `remaining_vacation_days` shouldn't be self-editable outside
  the vacation approve/reject workflow.
- `PATCH /vacation-requests/{request_id}` was moved under
  `/users/{user_id}/vacation-requests/{request_id}` and scoped by `user_id`
  (like time-entry updates already were), closing an IDOR where any caller
  could edit any user's pending request by guessing the request id.

**Why:** The initial PATCH routes matched the existing (intentional,
pre-Phase-3) pattern of leaving non-admin actions unauthenticated, but that
pattern was only ever safe for low-risk fields (name, dates). `role`,
`password`, and `remaining_vacation_days` are high-risk enough that they
needed gating even before real auth lands.

**Landed:** branch `ah/update-apis`, 2026-07-27.

---

## EmployeeProfile: user_id is the primary key, not a separate id
<a id="employee-profile-shared-pk"></a>

**Decision:** Dropped `EmployeeProfile`'s surrogate `id` column. `user_id` is
now both the primary key and the FK to `users.id`. Migration
`8d058e9f1ffa` drops the old `id` PK/unique constraints and column, adds
`user_id` as PK.

**Why:** The relationship is truly one-to-one (see
[[user-employee-profile-split]]) and every route/service function already
looked profiles up by `user_id` only — the separate `id` was a redundant
surrogate key that no code ever used. Making `user_id` the PK directly
matches the classic "shared primary key" pattern for 1:1 relationships and
simplified `get_profile`/`create_profile`'s existence check to a plain
`db.get(EmployeeProfile, user_id)`.

**Landed:** branch `ah/update-apis`, 2026-07-27.
