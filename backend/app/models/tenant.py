import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    status = Column(
        Enum("active", "suspended", "deleted", name="tenant_status_enum"),
        nullable=False,
        default="active",
    )
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    suspended_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    plan_tier = Column(
        Enum("free", "pro", "enterprise", name="plan_tier_enum"),
        nullable=False,
        default="free",
    )
    monthly_token_limit = Column(BigInteger, nullable=False, default=1_000_000)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")