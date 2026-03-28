import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    original_filename = Column(String, nullable=False)
    minio_object_key = Column(String, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    page_count = Column(Integer, nullable=True)
    document_type = Column(
        Enum(
            "annual_report",
            "earnings_call",
            "credit_agreement",
            "other",
            name="document_type_enum",
        ),
        nullable=False,
        default="other",
    )
    qdrant_collection_id = Column(String, nullable=True)
    status = Column(
        Enum(
            "uploaded",
            "processing",
            "completed",
            "failed",
            name="document_status_enum",
        ),
        nullable=False,
        default="uploaded",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )