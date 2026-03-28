import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class BreachResult(Base):
    __tablename__ = "breach_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False
    )
    breach_detected = Column(Boolean, nullable=False, default=False)
    breach_count = Column(Integer, nullable=False, default=0)
    breach_details = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )