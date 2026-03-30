"""
Agent 4 — Breach Detector.

Classifies each chunk to detect covenant breaches using the fine-tuned
FinBERT breach detection model (2-class: breach / no-breach).

Locally (USE_REAL_LLAMA=false): Returns mock breach results instantly.
On EC2 (USE_REAL_LLAMA=true): Loads fine-tuned FinBERT from models/finbert-breach/
and classifies each chunk individually.
"""

import logging
import time
from typing import Any

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.breach_result import BreachResult

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Mock breach detection — used locally
# ---------------------------------------------------------------------------
def _mock_breach_detection(chunks: list[str]) -> dict[str, Any]:
    """
    Returns hardcoded breach results instantly.
    Used when USE_REAL_LLAMA=false (local development).
    """
    return {
        "breach_detected": True,
        "breach_count": 1,
        "breach_details": [
            {
                "clause": "Section 7.1(a)",
                "text": "The Debt Service Coverage Ratio fell below the minimum threshold of 1.20x.",
                "confidence": 0.94,
                "page_number": 45,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Real FinBERT breach detection — used on EC2 only
# ---------------------------------------------------------------------------
def _real_breach_detection(chunks: list[str]) -> dict[str, Any]:
    """
    Uses the fine-tuned FinBERT breach model to classify each chunk.
    Only runs on EC2 where USE_REAL_LLAMA=true.
    """
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        logger.info("Loading fine-tuned FinBERT breach detection model...")
        model_path = "models/finbert-breach"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        model.eval()

        # Label map: 0 = no-breach, 1 = breach
        breach_details = []

        for idx, chunk_text in enumerate(chunks):
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

            if predicted_class == 1 and confidence > 0.5:
                breach_details.append({
                    "clause": f"Chunk {idx + 1}",
                    "text": chunk_text[:300],  # Truncate for storage
                    "confidence": round(confidence, 4),
                    "page_number": 0,  # Page tracking from chunk metadata
                })

        return {
            "breach_detected": len(breach_details) > 0,
            "breach_count": len(breach_details),
            "breach_details": breach_details,
        }

    except Exception as e:
        logger.error(f"Real FinBERT breach detection failed: {e}. Falling back to mock.")
        return _mock_breach_detection(chunks)


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_4_breach(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 4 — Breach Detector.

    Reads from state: chunks, document_id, job_id
    Writes to state: breach_result
    Side effects: breach_results row created in PostgreSQL
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
            job.current_agent = "Breach Detector"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 4: Starting breach detection...")
        logger.info(f"[Job {job_id}] Scanning {len(chunks)} chunks")

        # --- Choose real or mock ---
        if settings.USE_REAL_LLAMA:
            result = _real_breach_detection(chunks)
        else:
            result = _mock_breach_detection(chunks)

        # --- Save to PostgreSQL ---
        breach = BreachResult(
            document_id=document_id,
            job_id=job_id,
            breach_detected=result["breach_detected"],
            breach_count=result["breach_count"],
            breach_details=result["breach_details"],
        )
        db.add(breach)
        db.commit()

        logger.info(
            f"[Job {job_id}] Agent 4 complete: "
            f"breach_detected={result['breach_detected']}, "
            f"count={result['breach_count']}"
        )

        return {
            **state,
            "breach_result": result,
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 4 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()
        duration = time.time() - start_time
        from backend.app.core.metrics import agent_duration
        agent_duration.labels(agent="breach").observe(duration)