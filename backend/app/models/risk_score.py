import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False
    )
    risk_score = Column(Numeric, nullable=False)
    risk_tier = Column(
        Enum("low", "medium", "high", "distress", name="risk_tier_enum"),
        nullable=False,
    )
    ratios_used_count = Column(Integer, nullable=False)
    imputed_features = Column(JSONB, nullable=True)
    shap_values = Column(JSONB, nullable=True)
    score_reliability = Column(
        Enum("high", "partial", "low", name="score_reliability_enum"),
        nullable=False,
        default="high",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )