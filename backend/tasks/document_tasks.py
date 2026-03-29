import time
import json
import logging
from datetime import datetime, timezone

import redis as redis_lib
from backend.tasks.celery_app import celery_app
from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.document import Document
from backend.app.models.extracted_ratio import ExtractedRatio
from backend.app.models.sentiment_result import SentimentResult
from backend.app.models.breach_result import BreachResult
from backend.app.models.risk_score import RiskScore
from backend.app.models.report import Report

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_dlq_redis():
    """Connect to Redis DB 1 (Dead Letter Queue)."""
    return redis_lib.Redis.from_url(settings.redis_url(db=1), decode_responses=True)


def _mock_langgraph_pipeline(document_id: str, tenant_id: str, job_id: str, db):
    """
    MOCK LangGraph pipeline — replaces real agent execution during local development.
    Simulates all 6 agents with hardcoded outputs and short sleeps.
    Will be replaced with real graph.invoke() in Phase 7.
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()

    # --- Agent 1: Document Parser ---
    job.current_agent = "Document Parser"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 1: Document Parser — parsing and indexing...")
    time.sleep(1)

    # --- Agent 2: Financial Ratio Extractor ---
    job.current_agent = "Financial Ratio Extractor"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 2: Financial Ratio Extractor — extracting ratios...")
    time.sleep(1)

    extracted_ratio = ExtractedRatio(
        document_id=document_id,
        job_id=job_id,
        dscr=1.34,
        leverage_ratio=4.8,
        interest_coverage=3.2,
        current_ratio=0.92,
        net_profit_margin=0.08,
        ratios_found_count=5,
        raw_extraction={"mock": True, "source": "hardcoded_values"},
    )
    db.add(extracted_ratio)
    db.commit()

    # --- Agent 3: Sentiment Analyst ---
    job.current_agent = "Sentiment Analyst"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 3: Sentiment Analyst — classifying sentiment...")
    time.sleep(0.5)

    sentiment_result = SentimentResult(
        document_id=document_id,
        job_id=job_id,
        overall_sentiment="neutral",
        positive_count=42,
        neutral_count=85,
        negative_count=23,
        confidence_score=0.72,
        flagged_sentences=[
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
    )
    db.add(sentiment_result)
    db.commit()

    # --- Agent 4: Breach Detector ---
    job.current_agent = "Breach Detector"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 4: Breach Detector — scanning for covenant breaches...")
    time.sleep(0.5)

    breach_result = BreachResult(
        document_id=document_id,
        job_id=job_id,
        breach_detected=True,
        breach_count=1,
        breach_details=[
            {
                "clause": "Section 7.1(a)",
                "text": "The Debt Service Coverage Ratio fell below the minimum threshold of 1.20x.",
                "confidence": 0.94,
                "page_number": 45,
            }
        ],
    )
    db.add(breach_result)
    db.commit()

    # --- Agent 5: Risk Scorer ---
    job.current_agent = "Risk Scorer"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 5: Risk Scorer — computing XGBoost risk score...")
    time.sleep(0.5)

    risk_score = RiskScore(
        document_id=document_id,
        job_id=job_id,
        risk_score=0.62,
        risk_tier="high",
        ratios_used_count=5,
        imputed_features={},
        shap_values={
            "dscr": -0.12,
            "leverage_ratio": 0.25,
            "interest_coverage": -0.08,
            "current_ratio": 0.18,
            "net_profit_margin": -0.05,
        },
        score_reliability="high",
    )
    db.add(risk_score)
    db.commit()

    # --- Agent 6: Report Writer ---
    job.current_agent = "Report Writer"
    db.commit()
    logger.info(f"[Job {job_id}] Agent 6: Report Writer — generating final report...")
    time.sleep(0.5)

    report = Report(
        document_id=document_id,
        job_id=job_id,
        tenant_id=tenant_id,
        summary_text=(
            "Based on the analysis of the uploaded financial document, the company presents "
            "a HIGH risk profile. The Debt Service Coverage Ratio of 1.34x is above the minimum "
            "covenant threshold but leaves limited headroom. The leverage ratio of 4.8x indicates "
            "significant debt burden. One covenant breach was detected in Section 7.1(a). "
            "Overall document sentiment is neutral with notable negative language around debt "
            "obligations and declining revenue. Recommend enhanced monitoring and quarterly review."
        ),
        overall_risk_tier="high",
        key_findings=[
            "DSCR of 1.34x — above 1.20x minimum but limited headroom",
            "Leverage ratio of 4.8x — elevated debt burden",
            "One covenant breach detected (Section 7.1(a))",
            "Neutral overall sentiment with negative flags on debt and revenue",
            "XGBoost risk score: 0.62 (HIGH tier)",
        ],
        llm_tokens_used=0,
    )
    db.add(report)
    db.commit()

    logger.info(f"[Job {job_id}] All 6 agents completed successfully.")


@celery_app.task(
    bind=True,
    name="tasks.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document(self, document_id: str, tenant_id: str, job_id: str):
    """
    Main Celery task: processes an uploaded document through the LangGraph pipeline.

    - On success: job status → "completed"
    - On failure with retries left: Celery retries with exponential backoff
    - After 3 failures: job → "dead_letter", pushed to Redis DB 1
    """
    db = SyncSessionLocal()
    try:
        # --- Mark job as running ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"[Job {job_id}] Started processing document {document_id}")

        # --- Run the pipeline (mocked for now) ---
        _mock_langgraph_pipeline(document_id, tenant_id, job_id, db)

        # --- Mark job as completed ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = "completed"
        job.current_agent = None
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        # --- Update document status ---
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "completed"
            db.commit()

        logger.info(f"[Job {job_id}] Processing completed successfully.")

    except Exception as exc:
        db.rollback()
        logger.error(f"[Job {job_id}] Error during processing: {exc}")

        # --- Update retry count ---
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.retry_count = self.request.retries
                job.error_message = str(exc)
                db.commit()
        except Exception:
            pass

        # --- Check if retries exhausted ---
        if self.request.retries >= self.max_retries:
            logger.error(f"[Job {job_id}] Max retries exhausted. Moving to dead letter queue.")
            try:
                dlq = _get_dlq_redis()
                dlq.set(
                    f"dlq:{job_id}",
                    json.dumps({
                        "job_id": job_id,
                        "document_id": document_id,
                        "tenant_id": tenant_id,
                        "error": str(exc),
                        "retries": self.request.retries,
                        "failed_at": datetime.now(timezone.utc).isoformat(),
                    }),
                    ex=2592000,  # 30 days TTL
                )
            except Exception as dlq_err:
                logger.error(f"[Job {job_id}] Failed to write to DLQ: {dlq_err}")

            try:
                job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
                if job:
                    job.status = "dead_letter"
                    db.commit()
            except Exception:
                pass

            return

        # --- Retry with exponential backoff ---
        retry_delay = 30 * (2 ** self.request.retries)
        logger.info(f"[Job {job_id}] Retrying in {retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})")
        raise self.retry(exc=exc, countdown=retry_delay)

    finally:
        db.close()