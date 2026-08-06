# HR AI Assistant

Employee time-tracking system with a Claude-powered chatbot for hours,
vacation, and policy questions.

## Roadmap
See `CLAUDE.md` for the phase-by-phase build plan and current status.

## Local development

1. Copy `.env.example` to `.env` and fill in values (at minimum `SECRET_KEY`
   and, once you reach Phase 4, `ANTHROPIC_API_KEY`).
2. Start Postgres:
   ```bash
   docker compose up -d db
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run database migrations (once Alembic is initialized in Phase 1):
   ```bash
   alembic upgrade head
   ```
5. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
6. Open http://localhost:8000/docs for the interactive Swagger UI.

### First admin user (local dev)

`POST /users/` always forces `role=employee` when called without an admin
token — this is intentional (see CLAUDE.md), so nobody can self-register as
admin over the API. That means a fresh database has no admin at all until
you bootstrap one directly, bypassing the API:

```bash
python scripts/create_admin.py
```

It prompts for an email/password/name and creates the user straight through
the service layer with `role=admin`. Log in with those credentials at
`POST /auth/token` (or via the **Authorize** button in Swagger UI, using the
OAuth2 password flow) to get a bearer token for admin-only routes like
`GET /users/`. Only needs to be run once per database — that admin can then
create further admins through the normal API.

## Running with Docker (full stack)

```bash
docker compose up --build
```

## Tests

```bash
pytest
```

## Project structure

```
app/
├── api/        # FastAPI routers (one file per resource)
├── core/       # config, db session, security
├── models/     # SQLAlchemy ORM models
├── schemas/    # Pydantic request/response schemas
├── services/   # business logic (hours calc, vacation calc, etc.)
├── ai/         # Claude client, tool definitions, prompts, RAG (Phase 4+)
└── main.py     # app entrypoint
tests/          # pytest suite
```
