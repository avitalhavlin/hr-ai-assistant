"""
Rebuild the policy_chunks table from the markdown docs in
app/ai/policy_docs/: chunks each doc, embeds every chunk via the Gemini
embeddings API, and replaces the table's contents. Run this whenever the
policy docs change.

Requires a running Postgres with the pgvector extension available (the
docker-compose db service uses the pgvector/pgvector:pg16 image) and
`alembic upgrade head` already applied.

Run from the project root (venv active, DATABASE_URL pointing at your
running Postgres):

    python scripts/reindex_policies.py
"""
import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal  # noqa: E402
from app.services import policy_service  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        count = policy_service.reindex_policies(db)
        print(f"Indexed {count} policy chunks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
