import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class ExtractedRatio(Base):
    __tablename__ = "extracted_ratios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False
    )
    dscr = Column(Numeric, nullable=True)
    leverage_ratio = Column(Numeric, nullable=True)
    interest_coverage = Column(Numeric, nullable=True)
    current_ratio = Column(Numeric, nullable=True)
    net_profit_margin = Column(Numeric, nullable=True)
    ratios_found_count = Column(Integer, nullable=False, default=0)
    raw_extraction = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )