"""
Cross-Encoder Re-ranker.

Step 4 of the RAG pipeline.

Takes the ~40 RRF candidates and scores each one as a (question, chunk_text)
pair using a cross-encoder model.

Why cross-encoder is better than bi-encoder for re-ranking:
- Bi-encoder (like BGE) encodes question and chunk SEPARATELY, then compares.
  This is fast but misses fine-grained interactions between question and chunk.
- Cross-encoder sees question AND chunk TOGETHER as one input. It can detect
  subtle relevance signals like "the question asks about DSCR and this chunk
  mentions debt service coverage ratio" — which a bi-encoder might miss.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (22M parameters)
- Runs on CPU in ~1-2 seconds for 40 chunks
- No GPU needed, no API cost
- Pre-trained on MS MARCO passage ranking dataset

Output: Top 5 most relevant chunks by cross-encoder score.
"""

import logging
from typing import Any

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Lazy-loaded cross-encoder model
# ---------------------------------------------------------------------------
_cross_encoder = None


def _get_cross_encoder():
    """
    Lazy-load the cross-encoder model on first use.

    sentence-transformers CrossEncoder is installed locally
    (it's in requirements.txt). The model downloads on first use
    (~80MB) and is cached by sentence-transformers automatically.
    """
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512,
            )
            logger.info("Cross-encoder model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            _cross_encoder = "FAILED"
    return _cross_encoder


# ---------------------------------------------------------------------------
# Re-rank candidates
# ---------------------------------------------------------------------------
def rerank_chunks(
    question: str,
    candidates: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Re-rank RRF candidates using the cross-encoder model.

    Args:
        question: the ORIGINAL user question (not the HyDE hypothetical)
        candidates: list of chunk dicts from RRF fusion
        top_k: number of top results to return (default 5)

    Returns:
        Top-k chunks sorted by cross-encoder relevance score descending.
        Each dict gets an additional 'rerank_score' key.
    """
    if not candidates:
        logger.warning("Reranker received empty candidates list")
        return []

    model = _get_cross_encoder()

    if model == "FAILED" or model is None:
        # Fallback: return top-k by RRF score (skip re-ranking)
        logger.warning("Cross-encoder unavailable, falling back to RRF order")
        for candidate in candidates:
            candidate["rerank_score"] = candidate.get("rrf_score", 0.0)
        return candidates[:top_k]

    try:
        # Build (question, chunk_text) pairs for the cross-encoder
        pairs = [(question, c["text"]) for c in candidates]

        # Score all pairs at once (batched inference)
        scores = model.predict(pairs)

        # Attach scores to candidates
        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(scores[i])

        # Sort by cross-encoder score descending
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(
            f"Reranker: scored {len(candidates)} candidates, "
            f"top score={reranked[0]['rerank_score']:.4f}, "
            f"returning top {top_k}"
        )

        return reranked[:top_k]

    except Exception as e:
        logger.error(f"Cross-encoder re-ranking failed: {e}")
        # Fallback to RRF order
        for candidate in candidates:
            candidate["rerank_score"] = candidate.get("rrf_score", 0.0)
        return candidates[:top_k]