"""
Business logic for RAG over company policy docs: chunking, (re)indexing the
markdown source files into policy_chunks, and searching them for the
search_policy_docs chatbot tool.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.ai import embeddings
from app.repositories import policy_chunk_repository

POLICY_DOCS_DIR = Path(__file__).resolve().parent.parent / "ai" / "policy_docs"

# Paragraphs shorter than this (e.g. markdown headers) get merged into the
# next paragraph instead of becoming their own near-empty chunk.
_MIN_CHUNK_CHARS = 200


def chunk_text(text: str) -> list[str]:
    """Split doc text into paragraph-sized chunks, merging short paragraphs."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(buffer) >= _MIN_CHUNK_CHARS:
            chunks.append(buffer)
            buffer = ""

    if buffer:
        if chunks:
            chunks[-1] = f"{chunks[-1]}\n\n{buffer}"
        else:
            chunks.append(buffer)

    return chunks


def reindex_policies(db: Session) -> int:
    """Re-chunk and re-embed every policy doc, replacing the indexed table."""
    policy_chunk_repository.delete_all(db)

    rows = []
    for path in sorted(POLICY_DOCS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for index, chunk in enumerate(chunk_text(text)):
            rows.append(
                {
                    "source": path.stem,
                    "chunk_index": index,
                    "content": chunk,
                    "embedding": embeddings.embed_text(chunk, task_type="RETRIEVAL_DOCUMENT"),
                }
            )

    policy_chunk_repository.bulk_create(db, rows)
    db.commit()
    return len(rows)


def search_policies(db: Session, query: str, top_k: int = 3) -> list[dict]:
    """Top-k policy chunks most relevant to query, as {source, content} dicts."""
    query_embedding = embeddings.embed_text(query, task_type="RETRIEVAL_QUERY")
    matches = policy_chunk_repository.search_similar(db, query_embedding, top_k)
    return [{"source": match.source, "content": match.content} for match in matches]
