"""
Reciprocal Rank Fusion (RRF).

Step 3 of the RAG pipeline.

Takes two ranked lists (dense top-20 and sparse top-20) and merges them
into one unified list using the RRF formula:

    RRF_score(chunk) = 1/(k + rank_in_dense) + 1/(k + rank_in_sparse)

Where k=60 is a constant that controls how much weight is given to
high-ranked items vs lower-ranked ones. k=60 is the standard value
from the original RRF paper (Cormack et al., 2009).

Why RRF works well:
- Chunks appearing in BOTH lists get higher combined scores
- A chunk ranked #1 in dense and #15 in sparse still scores well
- Chunks appearing in only one list get 0 for the missing component
  but can still make the final list if their single-list rank is high

Output: One ranked list of up to 40 unique candidate chunks, sorted
by RRF score descending.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# RRF constant — 60 is the standard from the original paper
RRF_K = 60


def reciprocal_rank_fusion(
    dense_results: list[dict[str, Any]],
    sparse_results: list[dict[str, Any]],
    rrf_k: int = RRF_K,
) -> list[dict[str, Any]]:
    """
    Merge dense and sparse search results using Reciprocal Rank Fusion.

    Args:
        dense_results: ranked list from dense (cosine) search
        sparse_results: ranked list from sparse (BM25) search
        rrf_k: constant for RRF formula (default 60)

    Returns:
        Unified list of unique chunks, sorted by RRF score descending.
        Each dict has all original keys plus:
            - rrf_score: the computed fusion score
            - dense_rank: rank in dense results (None if not present)
            - sparse_rank: rank in sparse results (None if not present)
    """
    # Build a lookup by chunk ID, tracking rank in each list
    chunk_map: dict[str, dict[str, Any]] = {}

    # Process dense results — rank is 1-indexed (first result = rank 1)
    for rank, result in enumerate(dense_results, start=1):
        chunk_id = str(result["id"])
        if chunk_id not in chunk_map:
            chunk_map[chunk_id] = {
                "id": result["id"],
                "text": result["text"],
                "page_number": result["page_number"],
                "section": result["section"],
                "has_table": result["has_table"],
                "dense_rank": None,
                "sparse_rank": None,
                "dense_score": 0.0,
                "sparse_score": 0.0,
            }
        chunk_map[chunk_id]["dense_rank"] = rank
        chunk_map[chunk_id]["dense_score"] = result.get("score", 0.0)

    # Process sparse results
    for rank, result in enumerate(sparse_results, start=1):
        chunk_id = str(result["id"])
        if chunk_id not in chunk_map:
            chunk_map[chunk_id] = {
                "id": result["id"],
                "text": result["text"],
                "page_number": result["page_number"],
                "section": result["section"],
                "has_table": result["has_table"],
                "dense_rank": None,
                "sparse_rank": None,
                "dense_score": 0.0,
                "sparse_score": 0.0,
            }
        chunk_map[chunk_id]["sparse_rank"] = rank
        chunk_map[chunk_id]["sparse_score"] = result.get("score", 0.0)

    # Compute RRF score for each chunk
    for chunk_id, chunk in chunk_map.items():
        rrf_score = 0.0

        if chunk["dense_rank"] is not None:
            rrf_score += 1.0 / (rrf_k + chunk["dense_rank"])

        if chunk["sparse_rank"] is not None:
            rrf_score += 1.0 / (rrf_k + chunk["sparse_rank"])

        chunk["rrf_score"] = rrf_score

    # Sort by RRF score descending
    fused = sorted(chunk_map.values(), key=lambda x: x["rrf_score"], reverse=True)

    logger.info(
        f"RRF fusion: {len(dense_results)} dense + {len(sparse_results)} sparse "
        f"→ {len(fused)} unique candidates"
    )

    return fused