"""
Pydantic schemas for job status polling.

After uploading a document, the frontend polls GET /jobs/{job_id}/status
every 5 seconds to check if processing is complete. These schemas
define what that polling endpoint returns.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    """
    Current status of a document processing job.

    The frontend uses this to:
    - Show which agent is currently running (current_agent)
    - Show a progress indicator based on status
    - Navigate to the report when status becomes "completed"
    """
    id: UUID
    document_id: UUID
    status: str        # queued / running / completed / failed / dead_letter
    current_agent: str | None = None  # e.g., "Document Parser", "Ratio Extractor"
    error_message: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}