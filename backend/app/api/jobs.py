"""
Job status polling API endpoint.

After uploading a document, the frontend polls this endpoint
every 5 seconds to check processing progress:

    GET /jobs/{job_id}/status

The response tells the frontend:
- status: queued → running → completed (or failed/dead_letter)
- current_agent: which of the 6 agents is currently running
- error_message: what went wrong (if failed)
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundError
from backend.app.dependencies.auth import get_current_user
from backend.app.dependencies.database import get_db
from backend.app.middleware.tenant import get_tenant_id
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.user import User
from backend.app.schemas.job import JobStatusResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current status of a document processing job.

    The frontend uses this to:
    1. Show a progress indicator (queued → running → completed)
    2. Display which agent is currently running (e.g., "Ratio Extractor")
    3. Navigate to the report page when status becomes "completed"
    4. Show an error message if status is "failed" or "dead_letter"

    Tenant isolation: users can only see jobs from their own company.
    """
    tenant_id = get_tenant_id(current_user)

    result = await db.execute(
        select(ProcessingJob).where(
            ProcessingJob.id == job_id,
            ProcessingJob.tenant_id == tenant_id,
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise NotFoundError("Job", str(job_id))

    return JobStatusResponse.model_validate(job)