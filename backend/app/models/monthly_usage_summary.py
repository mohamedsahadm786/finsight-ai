import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.database.session import Base


class MonthlyUsageSummary(Base):
    __tablename__ = "monthly_usage_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    year_month = Column(String, nullable=False)
    total_tokens = Column(BigInteger, nullable=False, default=0)
    llama_tokens = Column(BigInteger, nullable=False, default=0)
    finbert_tokens = Column(BigInteger, nullable=False, default=0)
    gpt4_tokens = Column(BigInteger, nullable=False, default=0)
    gpt35_tokens = Column(BigInteger, nullable=False, default=0)
    total_cost_usd = Column(Numeric(10, 4), nullable=False, default=0)
    documents_processed = Column(Integer, nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )