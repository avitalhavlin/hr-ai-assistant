"""
Thin wrapper around the Gemini embeddings API. No business logic here —
app/services/policy_service.py owns chunking/indexing/search orchestration.
Kept separate so tests can monkeypatch embed_text() instead of touching the
real API, same reasoning as app/ai/client.py.
"""

from app.ai.client import get_client
from app.core.config import settings


def embed_text(text: str, task_type: str) -> list[float]:
    response = get_client().models.embed_content(
        model=settings.gemini_embedding_model,
        contents=[text],
        config={
            "task_type": task_type,
            "output_dimensionality": settings.embedding_dimensions,
        },
    )
    return response.embeddings[0].values
