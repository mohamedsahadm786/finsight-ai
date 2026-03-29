"""
Pydantic schemas for the RAG chat endpoint.

The chat system lets users ask questions about a specific document.
The hybrid RAG pipeline retrieves relevant chunks and generates
a grounded answer using LLaMA.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Chat Request ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    What the frontend sends when the user asks a question.
    Example:
    {
        "question": "What is the minimum DSCR covenant threshold?",
        "document_id": "abc-123-...",
        "session_id": null  ← null for first message, then reuse the returned session_id
    }
    """
    question: str = Field(..., min_length=1, max_length=2000)
    document_id: UUID
    session_id: UUID | None = None  # Null = create new session


# ── Chat Response ─────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """
    What we return after the RAG pipeline generates an answer.
    Includes the answer text and source citations for the frontend.
    """
    session_id: UUID
    message_id: UUID
    answer: str
    retrieved_chunk_ids: list[str] | None = None  # Qdrant point IDs
    ragas_faithfulness: float | None = None
    tokens_used: int | None = None
    latency_ms: int | None = None


# ── Chat History ──────────────────────────────────────────────────

class ChatMessageSchema(BaseModel):
    """One message in the chat history (either user question or assistant answer)."""
    id: UUID
    role: str  # "user" or "assistant"
    content: str
    retrieved_chunk_ids: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Full conversation history for a session."""
    session_id: UUID
    document_id: UUID
    messages: list[ChatMessageSchema]