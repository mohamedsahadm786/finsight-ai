"""
Pydantic schemas for document upload and listing endpoints.

Documents are PDFs uploaded by analysts. Each document goes through
the 6-agent LangGraph pipeline to produce a credit risk report.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Upload ────────────────────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    """
    Returned immediately after uploading a PDF.
    The frontend uses job_id to poll for processing status.
    Note: The actual file is sent as multipart form data,
    not as a JSON body — so there's no upload REQUEST schema.
    """
    document_id: UUID
    job_id: UUID
    filename: str
    status: str  # Always "queued" right after upload
    message: str = "Document uploaded successfully. Processing started."


# ── Document Listing ──────────────────────────────────────────────

class DocumentSummary(BaseModel):
    """One document in the list view — minimal info for the table/cards."""
    id: UUID
    original_filename: str
    document_type: str
    status: str
    file_size_bytes: int
    page_count: int | None = None
    uploaded_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents for the current tenant."""
    documents: list[DocumentSummary]
    total_count: int
    page: int
    page_size: int


# ── Single Document Detail ────────────────────────────────────────

class DocumentDetail(BaseModel):
    """Full document info — shown when clicking on a specific document."""
    id: UUID
    original_filename: str
    document_type: str
    status: str
    file_size_bytes: int
    page_count: int | None = None
    uploaded_by: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}