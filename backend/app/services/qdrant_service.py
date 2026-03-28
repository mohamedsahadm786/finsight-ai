from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    SparseIndexParams,
    SparseVectorParams,
    VectorParams,
)

from backend.app.config import get_settings

settings = get_settings()


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
    )


def ensure_tenant_collection(tenant_id: str) -> None:
    """Create a Qdrant collection for a tenant if it doesn't exist.

    Each tenant gets its own collection for strict data isolation.
    Collection supports both dense vectors (768-dim BGE embeddings)
    and sparse vectors (BM25 keyword scores).
    """
    client = get_qdrant_client()
    collection_name = f"tenant_{tenant_id}"

    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=768,
                distance=Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(),
            ),
        },
    )