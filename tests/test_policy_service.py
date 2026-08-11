from app.ai import embeddings
from app.models.policy_chunk import PolicyChunk
from app.repositories import policy_chunk_repository
from app.services import policy_service


def test_chunk_text_merges_short_paragraphs():
    text = "## Heading\n\nShort intro.\n\n" + ("Long enough paragraph. " * 15)

    chunks = policy_service.chunk_text(text)

    assert len(chunks) == 1
    assert "## Heading" in chunks[0]
    assert "Short intro." in chunks[0]


def test_chunk_text_splits_once_a_chunk_is_long_enough():
    long_paragraph = "Long enough paragraph. " * 15
    text = f"{long_paragraph}\n\n{long_paragraph}"

    chunks = policy_service.chunk_text(text)

    assert len(chunks) == 2


def test_chunk_text_merges_trailing_short_paragraph_into_previous_chunk():
    long_paragraph = "Long enough paragraph. " * 15
    text = f"{long_paragraph}\n\nShort tail."

    chunks = policy_service.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0].endswith("Short tail.")


def test_chunk_text_empty_input_returns_no_chunks():
    assert policy_service.chunk_text("   \n\n  ") == []


def test_reindex_policies_chunks_embeds_and_replaces_existing_rows(
    db_session, monkeypatch, tmp_path
):
    long_paragraph = "Long enough paragraph. " * 15
    (tmp_path / "sample.md").write_text(
        f"{long_paragraph}\n\n{long_paragraph}", encoding="utf-8"
    )
    monkeypatch.setattr(policy_service, "POLICY_DOCS_DIR", tmp_path)
    monkeypatch.setattr(embeddings, "embed_text", lambda text, task_type: [0.1, 0.2, 0.3])

    db_session.add(
        PolicyChunk(source="stale", chunk_index=0, content="old", embedding=[0.0, 0.0, 0.0])
    )
    db_session.commit()

    count = policy_service.reindex_policies(db_session)

    assert count == 2
    stored = db_session.query(PolicyChunk).order_by(PolicyChunk.chunk_index).all()
    assert [c.source for c in stored] == ["sample", "sample"]
    assert [c.chunk_index for c in stored] == [0, 1]


def test_reindex_policies_embeds_with_retrieval_document_task_type(
    db_session, monkeypatch, tmp_path
):
    long_paragraph = "Long enough paragraph. " * 15
    (tmp_path / "sample.md").write_text(long_paragraph, encoding="utf-8")
    monkeypatch.setattr(policy_service, "POLICY_DOCS_DIR", tmp_path)

    task_types = []
    monkeypatch.setattr(
        embeddings,
        "embed_text",
        lambda text, task_type: task_types.append(task_type) or [0.1],
    )

    policy_service.reindex_policies(db_session)

    assert task_types == ["RETRIEVAL_DOCUMENT"]


def test_search_policies_embeds_query_and_formats_matches(db_session, monkeypatch):
    captured = {}

    def fake_embed_text(text, task_type):
        captured["text"] = text
        captured["task_type"] = task_type
        return [0.1, 0.2]

    monkeypatch.setattr(embeddings, "embed_text", fake_embed_text)

    fake_match = PolicyChunk(
        source="vacation_and_leave", chunk_index=0, content="21 days a year", embedding=[0.1, 0.2]
    )
    monkeypatch.setattr(
        policy_chunk_repository, "search_similar", lambda db, emb, top_k: [fake_match]
    )

    result = policy_service.search_policies(db_session, "how many vacation days do I get")

    assert captured == {"text": "how many vacation days do I get", "task_type": "RETRIEVAL_QUERY"}
    assert result == [{"source": "vacation_and_leave", "content": "21 days a year"}]
