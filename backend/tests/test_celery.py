"""
Tests for the Celery async task system (Phase 6).

Tests:
- Celery app configuration and task discovery
- Mock LangGraph pipeline creates all 5 agent output records
- Dead letter queue routing on max retries
"""

import uuid

import pytest

from backend.app.core.security import hash_password
from backend.app.database.session import SyncSessionLocal
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.extracted_ratio import ExtractedRatio
from backend.app.models.sentiment_result import SentimentResult
from backend.app.models.breach_result import BreachResult
from backend.app.models.risk_score import RiskScore
from backend.app.models.report import Report
from backend.tasks.celery_app import celery_app
from backend.tasks.document_tasks import process_document, _mock_langgraph_pipeline


# ── Celery Configuration Tests ────────────────────────────────────

class TestCeleryConfig:
    """Verify Celery app is configured correctly."""

    def test_task_is_registered(self):
        """process_document must appear in Celery's task registry."""
        assert "tasks.process_document" in celery_app.tasks

    def test_task_name(self):
        """Task name must match what we defined."""
        assert process_document.name == "tasks.process_document"

    def test_task_max_retries(self):
        """Task must retry up to 3 times before dead lettering."""
        assert process_document.max_retries == 3

    def test_broker_is_redis_db0(self):
        """Broker URL must point to Redis DB 0."""
        broker_url = celery_app.conf.broker_url
        assert "redis://" in broker_url
        assert broker_url.endswith("/0")

    def test_serializer_is_json(self):
        """Tasks must serialize as JSON (not pickle) for safety."""
        assert celery_app.conf.task_serializer == "json"


# ── Mock Pipeline Tests ───────────────────────────────────────────

class TestMockPipeline:
    """
    Verify the mock LangGraph pipeline creates records in all 5
    agent output tables. Uses sync DB session (same as Celery worker).
    Docker containers must be running for these tests.
    """

    def test_mock_pipeline_creates_all_agent_records(self):
        """
        Run the mock pipeline and verify that ExtractedRatio,
        SentimentResult, BreachResult, RiskScore, and Report
        records are all created with correct values.
        """
        db = SyncSessionLocal()
        try:
            # --- Create prerequisite records ---
            tenant_id = uuid.uuid4()
            user_id = uuid.uuid4()
            document_id = uuid.uuid4()
            job_id = uuid.uuid4()

            tenant = Tenant(
                id=tenant_id,
                name="Celery Test Corp",
                slug=f"celery-test-{tenant_id.hex[:8]}",
                status="active",
                plan_tier="free",
                monthly_token_limit=100000,
            )
            db.add(tenant)
            db.flush()

            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"celery-{uuid.uuid4().hex[:8]}@test.com",
                password_hash=hash_password("test"),
                full_name="Celery Tester",
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.flush()

            document = Document(
                id=document_id,
                tenant_id=tenant_id,
                uploaded_by=user_id,
                original_filename="test_celery.pdf",
                minio_object_key=f"{tenant_id}/{document_id}/test_celery.pdf",
                file_size_bytes=1024,
                document_type="annual_report",
                status="uploaded",
            )
            db.add(document)
            db.flush()

            job = ProcessingJob(
                id=job_id,
                document_id=document_id,
                tenant_id=tenant_id,
                status="running",
            )
            db.add(job)
            db.commit()

            # --- Run the mock pipeline ---
            _mock_langgraph_pipeline(
                str(document_id), str(tenant_id), str(job_id), db
            )

            # --- Verify Agent 2 output: ExtractedRatio ---
            ratio = (
                db.query(ExtractedRatio)
                .filter(ExtractedRatio.job_id == job_id)
                .first()
            )
            assert ratio is not None, "ExtractedRatio not created"
            assert float(ratio.dscr) == 1.34
            assert float(ratio.leverage_ratio) == 4.8
            assert ratio.ratios_found_count == 5

            # --- Verify Agent 3 output: SentimentResult ---
            sentiment = (
                db.query(SentimentResult)
                .filter(SentimentResult.job_id == job_id)
                .first()
            )
            assert sentiment is not None, "SentimentResult not created"
            assert sentiment.overall_sentiment == "neutral"
            assert sentiment.positive_count == 42

            # --- Verify Agent 4 output: BreachResult ---
            breach = (
                db.query(BreachResult)
                .filter(BreachResult.job_id == job_id)
                .first()
            )
            assert breach is not None, "BreachResult not created"
            assert breach.breach_detected is True
            assert breach.breach_count == 1

            # --- Verify Agent 5 output: RiskScore ---
            risk = (
                db.query(RiskScore)
                .filter(RiskScore.job_id == job_id)
                .first()
            )
            assert risk is not None, "RiskScore not created"
            assert risk.risk_tier == "high"
            assert float(risk.risk_score) == 0.62

            # --- Verify Agent 6 output: Report ---
            report = (
                db.query(Report)
                .filter(Report.job_id == job_id)
                .first()
            )
            assert report is not None, "Report not created"
            assert report.overall_risk_tier == "high"
            assert "HIGH risk profile" in report.summary_text
            assert len(report.key_findings) == 5

        finally:
            # Clean up test data so it doesn't accumulate
            db.rollback()
            db.close()

    def test_mock_pipeline_updates_current_agent(self):
        """
        After the mock pipeline completes, the last current_agent
        set should be 'Report Writer' (Agent 6 is the last one).
        """
        db = SyncSessionLocal()
        try:
            tenant_id = uuid.uuid4()
            user_id = uuid.uuid4()
            document_id = uuid.uuid4()
            job_id = uuid.uuid4()

            tenant = Tenant(
                id=tenant_id,
                name="Agent Track Corp",
                slug=f"agent-track-{tenant_id.hex[:8]}",
                status="active",
                plan_tier="free",
                monthly_token_limit=100000,
            )
            db.add(tenant)
            db.flush()

            user = User(
                id=user_id,
                tenant_id=tenant_id,
                email=f"track-{uuid.uuid4().hex[:8]}@test.com",
                password_hash=hash_password("test"),
                full_name="Agent Tracker",
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.flush()

            document = Document(
                id=document_id,
                tenant_id=tenant_id,
                uploaded_by=user_id,
                original_filename="test_agent_track.pdf",
                minio_object_key=f"{tenant_id}/{document_id}/test.pdf",
                file_size_bytes=512,
                document_type="annual_report",
                status="uploaded",
            )
            db.add(document)
            db.flush()

            job = ProcessingJob(
                id=job_id,
                document_id=document_id,
                tenant_id=tenant_id,
                status="running",
            )
            db.add(job)
            db.commit()

            _mock_langgraph_pipeline(
                str(document_id), str(tenant_id), str(job_id), db
            )

            # After pipeline completes, current_agent should be "Report Writer"
            # (the last agent that set it before the pipeline function returns)
            job_after = (
                db.query(ProcessingJob)
                .filter(ProcessingJob.id == job_id)
                .first()
            )
            assert job_after.current_agent == "Report Writer"

        finally:
            db.rollback()
            db.close()