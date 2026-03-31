"""
RefreshToken model.

IMPORTANT DESIGN DECISION:
user_id is a plain UUID — NOT a foreign key to users.id.

Both regular users (stored in the 'users' table) and superadmins
(stored in the 'superadmins' table) can have refresh tokens stored here.
Making it a FK to users.id would prevent superadmins from ever getting
a refresh token, forcing their sessions to expire every 15 minutes.

The Alembic migration 'drop_fk_refresh_tokens_user_id' removed the
FK constraint from the database to match this model definition.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.database.session import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        # NO ForeignKey here — intentional.
        # Both regular users AND superadmins store refresh tokens here.
        # See module docstring above for full explanation.
    )
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )