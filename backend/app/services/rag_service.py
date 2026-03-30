"""
RAG Service — Orchestrator for the 5-step hybrid RAG pipeline.

This service is called by the /chat API endpoint. It runs all 5 RAG steps
in sequence and integrates with the centralized LLM Registry for token
usage logging (billing).

Flow:
1. HyDE: question → GPT-3.5 hypothetical answer → dense embedding
2. Hybrid Search: dense + sparse Qdrant search → 2 ranked lists
3. RRF Fusion: merge 2 lists → 1 unified ranked list (~40 candidates)
4. Cross-Encoder Re-ranking: score all candidates → top 5
5. Answer Generation: question + top 5 chunks → LLaMA answer

Token usage is logged via LLMRegistry for:
- GPT-3.5 (HyDE) — usage_type="hyde"
- LLaMA (answer generation) — usage_type="chat"
"""

import logging
from typing import Any, Optional

from backend.app.config import get_settings
from backend.app.services.llm_registry import llm_registry
from backend.rag.hyde import generate_hyde_embedding
from backend.rag.retriever import hybrid_search
from backend.rag.fusion import reciprocal_rank_fusion
from backend.rag.reranker import rerank_chunks
from backend.rag.generator import generate_answer
from backend.rag.evaluator import compute_faithfulness

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_rag_pipeline(
    question: str,
    document_id: str,
    tenant_id: str,
) -> tuple[str, list[str], Optional[float], int]:
    """
    Run the complete 5-step hybrid RAG pipeline.

    Args:
        question: the user's question text
        document_id: UUID string of the document to search
        tenant_id: UUID string of the tenant (for collection isolation)

    Returns:
        tuple of:
            - answer: the generated answer text
            - chunk_ids: list of retrieved chunk ID strings (for citations)
            - faithfulness: RAGAS faithfulness score (or None if unavailable)
            - tokens_used: total tokens consumed across all LLM calls
    """
    total_tokens = 0

    logger.info(
        f"RAG pipeline starting — question: '{question[:80]}...', "
        f"document: {document_id}"
    )

    # ── Step 1: HyDE ──────────────────────────────────────────────
    logger.info("RAG Step 1/5: HyDE — generating hypothetical answer + embedding")
    hyde_embedding, hypothetical_text = generate_hyde_embedding(question)

    # Log HyDE token usage (GPT-3.5) — approximate token counts
    # GPT-3.5 input: ~100 tokens (system prompt + question)
    # GPT-3.5 output: ~50 tokens (hypothetical answer)
    hyde_input_tokens = len(question.split()) + 80  # rough estimate
    hyde_output_tokens = len(hypothetical_text.split())
    total_tokens += hyde_input_tokens + hyde_output_tokens

    try:
        llm_registry.log_usage(
            tenant_id=tenant_id,
            document_id=document_id,
            job_id=None,
            model_name="gpt35",
            usage_type="hyde",
            input_tokens=hyde_input_tokens,
            output_tokens=hyde_output_tokens,
        )
    except Exception as e:
        logger.warning(f"Failed to log HyDE token usage: {e}")

    # ── Step 2: Hybrid Search ─────────────────────────────────────
    logger.info("RAG Step 2/5: Hybrid search — dense + sparse Qdrant query")
    dense_results, sparse_results = hybrid_search(
        hyde_embedding=hyde_embedding,
        question=question,
        tenant_id=tenant_id,
        document_id=document_id,
        top_k=20,
    )

    # If both searches returned nothing, return early
    if not dense_results and not sparse_results:
        logger.warning("RAG: No results from either dense or sparse search")
        return (
            "I could not find relevant information in the document to answer "
            "your question. The document may not contain information about this topic.",
            [],
            None,
            total_tokens,
        )

    # ── Step 3: RRF Fusion ────────────────────────────────────────
    logger.info("RAG Step 3/5: RRF fusion — merging dense + sparse results")
    fused_candidates = reciprocal_rank_fusion(dense_results, sparse_results)

    if not fused_candidates:
        logger.warning("RAG: RRF fusion produced no candidates")
        return (
            "I could not find relevant information in the document.",
            [],
            None,
            total_tokens,
        )

    # ── Step 4: Cross-Encoder Re-ranking ──────────────────────────
    logger.info("RAG Step 4/5: Cross-encoder re-ranking")
    top_chunks = rerank_chunks(
        question=question,
        candidates=fused_candidates,
        top_k=5,
    )

    # Collect chunk IDs for citations
    chunk_ids = [str(c["id"]) for c in top_chunks]

    # ── Step 5: Answer Generation ─────────────────────────────────
    logger.info("RAG Step 5/5: Generating answer from top chunks")
    answer, gen_tokens = generate_answer(
        question=question,
        chunks=top_chunks,
    )
    total_tokens += gen_tokens

    # Log answer generation token usage (LLaMA or mock)
    try:
        # Estimate input tokens: system prompt + context chunks + question
        context_text = " ".join(c.get("text", "") for c in top_chunks)
        gen_input_tokens = len(context_text.split()) + len(question.split()) + 50
        gen_output_tokens = len(answer.split())

        llm_registry.log_usage(
            tenant_id=tenant_id,
            document_id=document_id,
            job_id=None,
            model_name="llama",
            usage_type="chat",
            input_tokens=gen_input_tokens,
            output_tokens=gen_output_tokens,
        )
    except Exception as e:
        logger.warning(f"Failed to log generation token usage: {e}")

    # ── RAGAS Evaluation (async-safe, non-blocking) ───────────────
    faithfulness_score = None
    try:
        context_texts = [c.get("text", "") for c in top_chunks]
        faithfulness_score = compute_faithfulness(
            question=question,
            answer=answer,
            contexts=context_texts,
        )
    except Exception as e:
        logger.warning(f"RAGAS evaluation failed: {e}")

    # ── Record faithfulness in Prometheus ─────────────────────────
    if faithfulness_score is not None:
        try:
            from backend.app.core.metrics import rag_faithfulness
            rag_faithfulness.set(faithfulness_score)
        except Exception:
            pass

    logger.info(
        f"RAG pipeline complete — answer: {len(answer)} chars, "
        f"chunks: {len(chunk_ids)}, faithfulness: {faithfulness_score}, "
        f"total tokens: {total_tokens}"
    )

    return answer, chunk_ids, faithfulness_score, total_tokens