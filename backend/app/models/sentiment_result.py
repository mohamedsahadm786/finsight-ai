import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    job_id = Column(
        UUID(as_uuid=True), ForeignKey("processing_jobs.id"), nullable=False
    )
    overall_sentiment = Column(
        Enum("positive", "neutral", "negative", name="sentiment_enum"),
        nullable=False,
    )
    positive_count = Column(Integer, nullable=False, default=0)
    neutral_count = Column(Integer, nullable=False, default=0)
    negative_count = Column(Integer, nullable=False, default=0)
    confidence_score = Column(Numeric, nullable=False)
    flagged_sentences = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )