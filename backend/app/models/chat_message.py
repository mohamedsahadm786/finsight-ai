import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.app.database.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id"),
        nullable=False,
        index=True,
    )
    role = Column(
        Enum("user", "assistant", name="chat_role_enum"), nullable=False
    )
    content = Column(Text, nullable=False)
    retrieved_chunk_ids = Column(JSONB, nullable=True)
    ragas_faithfulness = Column(Numeric, nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )