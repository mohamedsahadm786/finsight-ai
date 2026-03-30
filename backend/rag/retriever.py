"""
Hybrid Qdrant Retriever.

Step 2 of the RAG pipeline.

Runs TWO searches simultaneously against the tenant's Qdrant collection:

1. Dense search — uses the HyDE embedding (768-dim vector from Step 1)
   to find the top-20 chunks by cosine similarity. This catches chunks
   that are semantically similar to what the answer might look like.

2. Sparse BM25 search — uses the original question's keyword tokens
   to find the top-20 chunks by BM25 scoring. This catches chunks
   containing exact financial terms like "DSCR", "Clause 4.2(b)",
   or "1.20x" that dense search might miss.

Both searches filter by tenant_id AND document_id for strict isolation.
Result: up to 40 candidate chunks (some may appear in both lists).
"""

import logging
from typing import Any

from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    MatchValue,
    SearchRequest,
    SparseVector,
)

from backend.app.config import get_settings
from backend.app.services.qdrant_service import get_qdrant_client

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Sparse embedding for the original question (BM25 keywords)
# ---------------------------------------------------------------------------
_sparse_model = None


def _get_sparse_model():
    """Lazy-load the fastembed sparse model (same as Agent 1)."""
    global _sparse_model
    if _sparse_model is None:
        try:
            from fastembed import SparseTextEmbedding
            _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        except Exception as e:
            logger.error(f"Failed to load sparse embedding model: {e}")
            _sparse_model = "FAILED"
    return _sparse_model


def _generate_sparse_query(question: str) -> dict[str, Any]:
    """
    Generate sparse BM25 vector for the original question text.
    Same logic as Agent 1's _generate_sparse_embedding.
    """
    model = _get_sparse_model()
    if model == "FAILED" or model is None:
        return {"indices": [0], "values": [0.1]}

    try:
        results = list(model.embed([question]))
        if results and len(results) > 0:
            sparse_emb = results[0]
            return {
                "indices": sparse_emb.indices.tolist(),
                "values": sparse_emb.values.tolist(),
            }
    except Exception as e:
        logger.error(f"Sparse query embedding failed: {e}")

    return {"indices": [0], "values": [0.1]}


# ---------------------------------------------------------------------------
# Hybrid search — dense + sparse against Qdrant
# ---------------------------------------------------------------------------
def hybrid_search(
    hyde_embedding: list[float],
    question: str,
    tenant_id: str,
    document_id: str,
    top_k: int = 20,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run dense + sparse searches against the tenant's Qdrant collection.

    Args:
        hyde_embedding: 768-dim vector from HyDE step (for dense search)
        question: original user question text (for sparse BM25 search)
        tenant_id: UUID string — determines which Qdrant collection to search
        document_id: UUID string — filters chunks to this specific document
        top_k: number of results per search type (default 20)

    Returns:
        tuple of (dense_results, sparse_results)
        Each is a list of dicts with keys:
            - id: Qdrant point ID (matches document_chunks.id)
            - score: similarity/relevance score
            - text: the chunk text from payload
            - page_number: page the chunk came from
            - section: section heading
            - has_table: whether the chunk contains table data
    """
    collection_name = f"tenant_{tenant_id}"
    qdrant_client = get_qdrant_client()

    # Filter: only chunks from this specific document
    search_filter = Filter(
        must=[
            FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            ),
        ]
    )

    # --- Dense search (cosine similarity with HyDE embedding) ---
    dense_results = []
    try:
        dense_response = qdrant_client.search(
            collection_name=collection_name,
            query_vector=("dense", hyde_embedding),
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        for point in dense_response:
            dense_results.append({
                "id": point.id,
                "score": point.score,
                "text": point.payload.get("text", ""),
                "page_number": point.payload.get("page_number", 0),
                "section": point.payload.get("section", ""),
                "has_table": point.payload.get("has_table", False),
            })

        logger.info(f"Dense search returned {len(dense_results)} results")

    except Exception as e:
        logger.error(f"Dense search failed: {e}")

    # --- Sparse BM25 search (keyword matching with original question) ---
    sparse_results = []
    try:
        sparse_data = _generate_sparse_query(question)
        sparse_vector = SparseVector(
            indices=sparse_data["indices"],
            values=sparse_data["values"],
        )

        sparse_response = qdrant_client.search(
            collection_name=collection_name,
            query_vector=("sparse", sparse_vector),
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        for point in sparse_response:
            sparse_results.append({
                "id": point.id,
                "score": point.score,
                "text": point.payload.get("text", ""),
                "page_number": point.payload.get("page_number", 0),
                "section": point.payload.get("section", ""),
                "has_table": point.payload.get("has_table", False),
            })

        logger.info(f"Sparse search returned {len(sparse_results)} results")

    except Exception as e:
        logger.error(f"Sparse search failed: {e}")

    return dense_results, sparse_results