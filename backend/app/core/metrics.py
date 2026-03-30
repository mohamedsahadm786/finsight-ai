"""
Prometheus metrics definitions for FinSight AI.

These custom metrics track business-specific data:
- Document processing duration
- Per-agent timing
- RAG quality scores
- Queue depth
- Token usage per model
- Risk tier distribution

Full instrumentation happens in Phase 9. For now, this file
provides the metric objects that agents and services will use.
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Pipeline Metrics ──────────────────────────────────────────────

document_processing_duration = Histogram(
    "finsight_document_processing_duration_seconds",
    "Total time to process a document through all agents",
    buckets=[30, 60, 120, 180, 240, 300, 600],
)

agent_duration = Histogram(
    "finsight_agent_duration_seconds",
    "Processing time per individual agent",
    ["agent"],  # Label: agent name (parser, extractor, sentiment, etc.)
    buckets=[5, 10, 30, 60, 120, 180],
)

# ── RAG Quality Metrics ──────────────────────────────────────────

rag_faithfulness = Gauge(
    "finsight_rag_faithfulness_score",
    "RAGAS faithfulness score of the latest RAG response",
)

# ── Queue Metrics ─────────────────────────────────────────────────

queue_depth = Gauge(
    "finsight_queue_depth",
    "Number of jobs waiting in the Celery queue",
)

# ── Token Usage Metrics ───────────────────────────────────────────

llm_tokens_total = Counter(
    "finsight_llm_tokens_total",
    "Total tokens used across all LLM calls",
    ["model"],  # Label: model name (llama, finbert_sentiment, gpt4, etc.)
)

# ── Business Metrics ──────────────────────────────────────────────

risk_tier_total = Counter(
    "finsight_risk_tier_total",
    "Count of documents by predicted risk tier",
    ["tier"],  # Label: low, medium, high, distress
)

# ── Queue Depth Updater ─────────────────────────────────────────

def update_queue_depth() -> None:
    """
    Check Redis DB 0 (Celery broker) for the number of waiting tasks
    and update the Prometheus gauge.

    Called periodically by a background task in main.py.
    """
    try:
        import redis as redis_lib
        from backend.app.config import get_settings

        settings = get_settings()
        r = redis_lib.Redis.from_url(settings.redis_url(db=0), decode_responses=True)

        # Celery stores tasks in a list named 'celery'
        depth = r.llen("celery")
        queue_depth.set(depth)
    except Exception:
        # If Redis is unavailable, don't crash — just skip this update
        pass