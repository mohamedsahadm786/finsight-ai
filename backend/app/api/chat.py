"""
RAG Chat API endpoint.

- POST /chat/          — Ask a question about a document
- GET  /chat/{session_id}/history — Get chat history for a session
"""

import time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundError
from backend.app.dependencies.auth import require_role
from backend.app.dependencies.database import get_db
from backend.app.middleware.tenant import get_tenant_id
from backend.app.models.chat_message import ChatMessage
from backend.app.models.chat_session import ChatSession
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.services.rag_service import run_rag_pipeline
from backend.app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageSchema,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/chat", tags=["RAG Chat"])


# ── Ask a Question ────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask a question about a specific document using hybrid RAG.

    Flow:
    1. Validate the document exists and belongs to the user's tenant
    2. Get or create a chat session
    3. Save the user's question
    4. Run the hybrid RAG pipeline:
       HyDE → hybrid search → RRF → cross-encoder → LLaMA generation
    5. Save the assistant's answer with citation chunk IDs
    6. Return the answer

    All roles can use chat (including viewers).
    """
    tenant_id = get_tenant_id(current_user)
    start_time = time.time()

    # Step 1: Verify document belongs to this tenant
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id,
            Document.tenant_id == tenant_id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise NotFoundError("Document", str(request.document_id))

    # Step 2: Get or create chat session
    if request.session_id:
        # Existing session — verify it belongs to this user
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.tenant_id == tenant_id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundError("Chat session", str(request.session_id))
    else:
        # Create new session
        session = ChatSession(
            id=uuid4(),
            document_id=request.document_id,
            user_id=current_user.id,
            tenant_id=tenant_id,
        )
        db.add(session)
        await db.flush()  # Get the session ID without full commit

    # Step 3: Save user's question
    user_message = ChatMessage(
        id=uuid4(),
        session_id=session.id,
        role="user",
        content=request.question,
    )
    db.add(user_message)

    # Step 4: Run the real hybrid RAG pipeline
    # HyDE → hybrid search → RRF fusion → cross-encoder → generation
    rag_answer, chunk_ids, faithfulness_score, tokens_used = await run_rag_pipeline(
        question=request.question,
        document_id=str(request.document_id),
        tenant_id=str(tenant_id),
    )

    # Step 5: Save assistant's answer
    latency_ms = int((time.time() - start_time) * 1000)
    assistant_message = ChatMessage(
        id=uuid4(),
        session_id=session.id,
        role="assistant",
        content=rag_answer,
        retrieved_chunk_ids=chunk_ids,
        ragas_faithfulness=faithfulness_score,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )
    db.add(assistant_message)

    await db.commit()

    # Step 6: Return response
    return ChatResponse(
        session_id=session.id,
        message_id=assistant_message.id,
        answer=rag_answer,
        retrieved_chunk_ids=chunk_ids,
        ragas_faithfulness=faithfulness_score,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )


# ── Get Chat History ──────────────────────────────────────────────

@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the complete conversation history for a chat session.

    Returns all messages in chronological order.
    Used when the user reopens a previous chat session.
    """
    tenant_id = get_tenant_id(current_user)

    # Verify session belongs to this user and tenant
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.tenant_id == tenant_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundError("Chat session", str(session_id))

    # Get all messages in order
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return ChatHistoryResponse(
        session_id=session.id,
        document_id=session.document_id,
        messages=[ChatMessageSchema.model_validate(m) for m in messages],
    )                                                                                               