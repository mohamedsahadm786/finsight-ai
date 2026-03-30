"""
RAGAS Evaluation Helper.

Computes quality metrics for RAG responses:
- Faithfulness (target > 0.85): Does the answer only use information from chunks?
- Answer Relevancy (target > 0.80): Does the answer address the question?
- Context Recall (target > 0.75): Did retrieval find the right chunks?

These metrics are logged per chat message and exposed as Prometheus metrics.
A Grafana alert fires if faithfulness drops below 0.85.

NOTE: RAGAS evaluation requires OPENAI_API_KEY to be set because it uses
an LLM to judge answer quality. If the key is not set, returns None scores.
"""

import logging
from typing import Any, Optional

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def compute_faithfulness(
    question: str,
    answer: str,
    contexts: list[str],
) -> Optional[float]:
    """
    Compute RAGAS faithfulness score for a single RAG response.

    Faithfulness measures what fraction of the claims in the answer
    are supported by the provided context chunks.

    Score range: 0.0 to 1.0 (higher is better, target > 0.85).

    Returns None if RAGAS evaluation cannot run (e.g., no OpenAI key).
    """
    if not settings.OPENAI_API_KEY:
        logger.info("RAGAS: Skipping evaluation — OPENAI_API_KEY not set")
        return None

    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness
        from datasets import Dataset

        # RAGAS expects a Dataset with specific column names
        eval_dataset = Dataset.from_dict({
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        })

        result = evaluate(
            dataset=eval_dataset,
            metrics=[faithfulness],
        )

        score = result.get("faithfulness", None)
        if score is not None:
            score = float(score)
            logger.info(f"RAGAS faithfulness score: {score:.4f}")

        return score

    except Exception as e:
        logger.error(f"RAGAS evaluation failed: {e}")
        return None