"""
CRUD-only coverage for policy_chunk_repository against the SQLite in-memory
fixture. pgvector's SQLAlchemy Vector type stores/reads values as plain
strings with no Postgres-specific driver logic, so bulk_create/delete_all
work fine here — but search_similar's cosine_distance()/`<=>` comparator is
Postgres-only and has no SQLite equivalent, so it isn't covered by this
suite. Verify it manually against the dockerized Postgres (pgvector image)
instead, e.g. via scripts/reindex_policies.py plus a real chat request.
"""

from app.models.policy_chunk import PolicyChunk
from app.repositories import policy_chunk_repository


def test_bulk_create_inserts_rows(db_session):
    rows = [
        {"source": "doc1", "chunk_index": 0, "content": "hello", "embedding": [0.1, 0.2]},
        {"source": "doc1", "chunk_index": 1, "content": "world", "embedding": [0.3, 0.4]},
    ]

    created = policy_chunk_repository.bulk_create(db_session, rows)
    db_session.commit()

    assert len(created) == 2
    assert db_session.query(PolicyChunk).count() == 2


def test_delete_all_removes_every_row(db_session):
    policy_chunk_repository.bulk_create(
        db_session,
        [{"source": "doc1", "chunk_index": 0, "content": "hello", "embedding": [0.1, 0.2]}],
    )
    db_session.commit()

    policy_chunk_repository.delete_all(db_session)
    db_session.commit()

    assert db_session.query(PolicyChunk).count() == 0
