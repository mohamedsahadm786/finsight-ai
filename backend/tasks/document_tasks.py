import json
import logging
from datetime import datetime, timezone

import redis as redis_lib
from backend.tasks.celery_app import celery_app
from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.document import Document

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_dlq_redis():
    """Connect to Redis DB 1 (Dead Letter Queue)."""
    return redis_lib.Redis.from_url(settings.redis_url(db=1), decode_responses=True)


def _run_langgraph_pipeline(document_id: str, tenant_id: str, job_id: str):
    """
    Run the real LangGraph pipeline with all 6 agents.

    Each agent handles its own database writes via SyncSessionLocal.
    The graph passes a shared state dict through all agents.
    Agents use mock functions when USE_REAL_LLAMA=false (local dev)
    and real models when USE_REAL_LLAMA=true (EC2).
    """
    from backend.agents.graph import pipeline_graph

    initial_state = {
        "document_id": document_id,
        "tenant_id": tenant_id,
        "job_id": job_id,
        "chunks": [],
        "chunk_metadata": [],
        "chunk_ids": [],
        "extracted_ratios": {},
        "ratios_found_count": 0,
        "raw_extraction": {},
        "sentiment_result": {},
        "breach_result": {},
        "risk_score": {},
        "final_report": {},
        "errors": [],
    }

    logger.info(f"[Job {job_id}] Invoking LangGraph pipeline...")
    result = pipeline_graph.invoke(initial_state)

    # Check for errors accumulated during the pipeline
    errors = result.get("errors", [])
    if errors:
        logger.warning(f"[Job {job_id}] Pipeline completed with errors: {errors}")

    return result


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

        # --- Run the LangGraph pipeline ---
        _run_langgraph_pipeline(document_id, tenant_id, job_id)

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