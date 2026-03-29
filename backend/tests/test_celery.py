"""
Tests for the Celery async task system and LangGraph agents (Phase 6 + Phase 7).

Tests:
- Celery app configuration and task discovery
- Individual agent functions (mock mode)
- LangGraph pipeline state flow
- Risk scorer with real XGBoost model
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
from backend.tasks.document_tasks import process_document


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


# ── Agent Unit Tests (Mock Mode) ─────────────────────────────────

class TestAgentFunctions:
    """
    Test individual agent functions in mock mode.
    Each agent reads from a state dict and returns an updated state dict.
    Docker containers must be running for these tests (PostgreSQL, Qdrant, MinIO).
    """

    def _create_test_records(self, db):
        """Helper: create tenant, user, document, and job for testing."""
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        document_id = uuid.uuid4()
        job_id = uuid.uuid4()

        tenant = Tenant(
            id=tenant_id,
            name="Agent Test Corp",
            slug=f"agent-test-{tenant_id.hex[:8]}",
            status="active",
            plan_tier="free",
            monthly_token_limit=100000,
        )
        db.add(tenant)
        db.flush()

        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=f"agent-{uuid.uuid4().hex[:8]}@test.com",
            password_hash=hash_password("test"),
            full_name="Agent Tester",
            role="admin",
            is_active=True,
        )
        db.add(user)
        db.flush()

        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            uploaded_by=user_id,
            original_filename="test_agent.pdf",
            minio_object_key=f"{tenant_id}/{document_id}/test_agent.pdf",
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

        return str(tenant_id), str(user_id), str(document_id), str(job_id)

    def test_agent_2_extractor_mock(self):
        """Agent 2 should return mock ratios and save to DB."""
        from backend.agents.agent_2_extractor import agent_2_extractor

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": ["Sample financial text chunk 1", "Sample chunk 2"],
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

            result = agent_2_extractor(state)

            # Verify state was updated
            assert result["ratios_found_count"] == 5
            assert result["extracted_ratios"]["dscr"] == 1.34
            assert result["extracted_ratios"]["leverage_ratio"] == 4.8
            assert result["extracted_ratios"]["interest_coverage"] == 3.2

            # Verify DB record was created
            ratio = (
                db.query(ExtractedRatio)
                .filter(ExtractedRatio.job_id == job_id)
                .first()
            )
            assert ratio is not None
            assert float(ratio.dscr) == 1.34
            assert ratio.ratios_found_count == 5

        finally:
            db.rollback()
            db.close()

    def test_agent_3_sentiment_mock(self):
        """Agent 3 should return mock sentiment and save to DB."""
        from backend.agents.agent_3_sentiment import agent_3_sentiment

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": ["Sample text"],
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

            result = agent_3_sentiment(state)

            assert result["sentiment_result"]["overall_sentiment"] == "neutral"
            assert result["sentiment_result"]["positive_count"] == 42

            sentiment = (
                db.query(SentimentResult)
                .filter(SentimentResult.job_id == job_id)
                .first()
            )
            assert sentiment is not None
            assert sentiment.overall_sentiment == "neutral"

        finally:
            db.rollback()
            db.close()

    def test_agent_4_breach_mock(self):
        """Agent 4 should return mock breach results and save to DB."""
        from backend.agents.agent_4_breach import agent_4_breach

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": ["Sample text"],
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

            result = agent_4_breach(state)

            assert result["breach_result"]["breach_detected"] is True
            assert result["breach_result"]["breach_count"] == 1

            breach = (
                db.query(BreachResult)
                .filter(BreachResult.job_id == job_id)
                .first()
            )
            assert breach is not None
            assert breach.breach_detected is True

        finally:
            db.rollback()
            db.close()

    def test_agent_5_risk_scorer_real_model(self):
        """Agent 5 should run the REAL XGBoost model and save to DB."""
        from backend.agents.agent_5_risk_scorer import agent_5_risk_scorer

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": [],
                "chunk_metadata": [],
                "chunk_ids": [],
                "extracted_ratios": {
                    "dscr": 1.34,
                    "leverage_ratio": 4.8,
                    "interest_coverage": 3.2,
                    "current_ratio": 0.92,
                    "net_profit_margin": 0.08,
                },
                "ratios_found_count": 5,
                "raw_extraction": {},
                "sentiment_result": {},
                "breach_result": {},
                "risk_score": {},
                "final_report": {},
                "errors": [],
            }

            result = agent_5_risk_scorer(state)

            # Verify risk score is computed
            assert result["risk_score"]["risk_score"] is not None
            assert result["risk_score"]["risk_tier"] in ("low", "medium", "high", "distress")
            assert result["risk_score"]["score_reliability"] in ("high", "partial", "low")
            assert len(result["risk_score"]["shap_values"]) == 5

            # Verify DB record
            risk = (
                db.query(RiskScore)
                .filter(RiskScore.job_id == job_id)
                .first()
            )
            assert risk is not None
            assert risk.risk_tier in ("low", "medium", "high", "distress")

        finally:
            db.rollback()
            db.close()

    def test_agent_6_report_writer_mock(self):
        """Agent 6 should return mock report and save to DB."""
        from backend.agents.agent_6_report_writer import agent_6_report_writer

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": [],
                "chunk_metadata": [],
                "chunk_ids": [],
                "extracted_ratios": {
                    "dscr": 1.34,
                    "leverage_ratio": 4.8,
                    "interest_coverage": 3.2,
                    "current_ratio": 0.92,
                    "net_profit_margin": 0.08,
                },
                "ratios_found_count": 5,
                "raw_extraction": {},
                "sentiment_result": {
                    "overall_sentiment": "neutral",
                    "positive_count": 42,
                    "neutral_count": 85,
                    "negative_count": 23,
                    "confidence_score": 0.72,
                    "flagged_sentences": [],
                },
                "breach_result": {
                    "breach_detected": True,
                    "breach_count": 1,
                    "breach_details": [],
                },
                "risk_score": {
                    "risk_score": 0.62,
                    "risk_tier": "high",
                    "shap_values": {},
                    "score_reliability": "high",
                },
                "final_report": {},
                "errors": [],
            }

            result = agent_6_report_writer(state)

            assert result["final_report"]["overall_risk_tier"] == "high"
            assert len(result["final_report"]["summary_text"]) > 50
            assert len(result["final_report"]["key_findings"]) > 0

            report = (
                db.query(Report)
                .filter(Report.job_id == job_id)
                .first()
            )
            assert report is not None
            assert report.overall_risk_tier == "high"

        finally:
            db.rollback()
            db.close()

    def test_agent_5_insufficient_ratios(self):
        """Agent 5 should handle insufficient ratios gracefully."""
        from backend.agents.agent_5_risk_scorer import agent_5_risk_scorer

        db = SyncSessionLocal()
        try:
            tenant_id, user_id, document_id, job_id = self._create_test_records(db)

            state = {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "job_id": job_id,
                "chunks": [],
                "chunk_metadata": [],
                "chunk_ids": [],
                "extracted_ratios": {"dscr": 1.34},
                "ratios_found_count": 1,
                "raw_extraction": {},
                "sentiment_result": {},
                "breach_result": {},
                "risk_score": {},
                "final_report": {},
                "errors": [],
            }

            result = agent_5_risk_scorer(state)

            # Should still return a result but with low reliability
            assert result["risk_score"]["score_reliability"] == "low"

        finally:
            db.rollback()
            db.close()


# ── LangGraph Pipeline Tests ─────────────────────────────────────

class TestLangGraphPipeline:
    """Test the LangGraph graph compilation and state schema."""

    def test_pipeline_graph_compiles(self):
        """The LangGraph pipeline should compile without errors."""
        from backend.agents.graph import pipeline_graph
        assert pipeline_graph is not None

    def test_pipeline_state_schema(self):
        """PipelineState should accept all required fields."""
        from backend.agents.state import PipelineState

        state: PipelineState = {
            "document_id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
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

        assert state["document_id"] is not None
        assert isinstance(state["errors"], list)