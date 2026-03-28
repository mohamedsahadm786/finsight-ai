import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from backend.app.database.session import Base


class LLMConfiguration(Base):
    __tablename__ = "llm_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(
        Enum(
            "llama",
            "finbert_sentiment",
            "finbert_breach",
            "gpt4",
            "gpt35",
            name="model_name_enum",
            create_type=False,
        ),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    model_path = Column(String, nullable=True)
    max_tokens = Column(Integer, nullable=False, default=1024)
    temperature = Column(Numeric, nullable=False, default=0.1)
    cost_per_1k_input_tokens = Column(Numeric(10, 6), nullable=False, default=0)
    cost_per_1k_output_tokens = Column(Numeric(10, 6), nullable=False, default=0)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )