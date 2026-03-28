import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    summary_text = Column(Text, nullable=False)
    overall_risk_tier = Column(
        Enum("low", "medium", "high", "distress", name="risk_tier_enum",
             create_type=False),
        nullable=False,
    )
    key_findings = Column(JSONB, nullable=True)
    llm_tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )