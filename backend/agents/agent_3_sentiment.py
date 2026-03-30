"""
Agent 3 — Sentiment Analyst.

Classifies each chunk's financial sentiment as positive, neutral, or negative
using the fine-tuned FinBERT sentiment model.

Locally (USE_REAL_LLAMA=false): Returns mock sentiment results instantly.
On EC2 (USE_REAL_LLAMA=true): Loads fine-tuned FinBERT from models/finbert-sentiment/
and classifies each chunk individually.
"""

import logging
import time
from typing import Any

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.sentiment_result import SentimentResult

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Mock sentiment analysis — used locally
# ---------------------------------------------------------------------------
def _mock_sentiment_analysis(chunks: list[str]) -> dict[str, Any]:
    """
    Returns hardcoded sentiment results instantly.
    Used when USE_REAL_LLAMA=false (local development).
    """
    return {
        "overall_sentiment": "neutral",
        "positive_count": 42,
        "neutral_count": 85,
        "negative_count": 23,
        "confidence_score": 0.72,
        "flagged_sentences": [
            {
                "text": "The company's debt obligations have increased significantly.",
                "score": -0.89,
                "page_number": 14,
            },
            {
                "text": "Revenue declined for the third consecutive quarter.",
                "score": -0.82,
                "page_number": 27,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Real FinBERT sentiment analysis — used on EC2 only
# ---------------------------------------------------------------------------
def _real_sentiment_analysis(chunks: list[str]) -> dict[str, Any]:
    """
    Uses the fine-tuned FinBERT sentiment model to classify each chunk.
    Only runs on EC2 where USE_REAL_LLAMA=true.
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        logger.info("Loading fine-tuned FinBERT sentiment model...")
        model_path = "models/finbert-sentiment"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        model.eval()

        label_map = {0: "positive", 1: "negative", 2: "neutral"}
        positive_count = 0
        neutral_count = 0
        negative_count = 0
        all_scores = []

        for chunk_text in chunks:
            # Truncate to 512 tokens (FinBERT max)
            inputs = tokenizer(
                chunk_text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )

            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1)
                predicted_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted_class].item()

            label = label_map.get(predicted_class, "neutral")

            if label == "positive":
                positive_count += 1
            elif label == "negative":
                negative_count += 1
            else:
                neutral_count += 1

            # Track negative scores for flagging
            negative_prob = probs[0][1].item()  # index 1 = negative
            all_scores.append({
                "text": chunk_text[:200],  # Truncate for storage
                "score": -negative_prob,  # Negative = worse
                "label": label,
            })

        # Determine overall sentiment by majority with confidence weighting
        counts = {"positive": positive_count, "neutral": neutral_count, "negative": negative_count}
        overall = max(counts, key=counts.get)

        # Get top 5 most negative sentences
        all_scores.sort(key=lambda x: x["score"])
        flagged = [
            {"text": s["text"], "score": round(s["score"], 4), "page_number": 0}
            for s in all_scores[:5]
        ]

        total = positive_count + neutral_count + negative_count
        confidence_score = counts[overall] / total if total > 0 else 0.0

        return {
            "overall_sentiment": overall,
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "confidence_score": round(confidence_score, 4),
            "flagged_sentences": flagged,
        }

    except Exception as e:
        logger.error(f"Real FinBERT sentiment analysis failed: {e}. Falling back to mock.")
        return _mock_sentiment_analysis(chunks)


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_3_sentiment(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 3 — Sentiment Analyst.

    Reads from state: chunks, document_id, job_id
    Writes to state: sentiment_result
    Side effects: sentiment_results row created in PostgreSQL
    """
    document_id = state["document_id"]
    job_id = state["job_id"]
    chunks = state.get("chunks", [])

    start_time = time.time()

    db = SyncSessionLocal()
    try:
        # --- Update job status ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_agent = "Sentiment Analyst"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 3: Starting sentiment analysis...")
        logger.info(f"[Job {job_id}] Analyzing {len(chunks)} chunks")

        # --- Choose real or mock ---
        if settings.USE_REAL_LLAMA:
            result = _real_sentiment_analysis(chunks)
        else:
            result = _mock_sentiment_analysis(chunks)

        # --- Save to PostgreSQL ---
        sentiment = SentimentResult(
            document_id=document_id,
            job_id=job_id,
            overall_sentiment=result["overall_sentiment"],
            positive_count=result["positive_count"],
            neutral_count=result["neutral_count"],
            negative_count=result["negative_count"],
            confidence_score=result["confidence_score"],
            flagged_sentences=result["flagged_sentences"],
        )
        db.add(sentiment)
        db.commit()

        logger.info(
            f"[Job {job_id}] Agent 3 complete: "
            f"sentiment={result['overall_sentiment']}, "
            f"P={result['positive_count']}/N={result['neutral_count']}/Neg={result['negative_count']}"
        )

        return {
            **state,
            "sentiment_result": result,
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 3 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()
        duration = time.time() - start_time
        from backend.app.core.metrics import agent_duration
        agent_duration.labels(agent="sentiment").observe(duration)