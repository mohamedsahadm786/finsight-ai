import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID

from backend.app.database.session import Base


class TokenUsageEvent(Base):
    __tablename__ = "token_usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=True
    )
    model_name = Column(
        Enum(
            "llama",
            "finbert_sentiment",
            "finbert_breach",
            "gpt4",
            "gpt35",
            name="model_name_enum",
        ),
        nullable=False,
    )
    usage_type = Column(
        Enum(
            "extraction",
            "sentiment",
            "breach",
            "report_writing",
            "hyde",
            "chat",
            name="usage_type_enum",
        ),
        nullable=False,
    )
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )