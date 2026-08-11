"""
Data access for PolicyChunk. No business rules, no transaction control —
callers (services) own flush()/commit().
"""

from sqlalchemy.orm import Session

from app.models.policy_chunk import PolicyChunk


def delete_all(db: Session) -> None:
    db.query(PolicyChunk).delete()


def bulk_create(db: Session, rows: list[dict]) -> list[PolicyChunk]:
    chunks = [PolicyChunk(**row) for row in rows]
    db.add_all(chunks)
    db.flush()
    return chunks


def search_similar(db: Session, query_embedding: list[float], top_k: int) -> list[PolicyChunk]:
    return (
        db.query(PolicyChunk)
        .order_by(PolicyChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
