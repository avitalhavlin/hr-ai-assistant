# HR AI Assistant

Employee time-tracking system with a Claude-powered chatbot for hours,
vacation, and policy questions.

## Roadmap
See `CLAUDE.md` for the phase-by-phase build plan and current status.

## Status & decisions
- `docs/status.md` — running log of what's built, in progress, and next.
- `docs/decisions.md` — key decisions and the reasoning behind them.

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
