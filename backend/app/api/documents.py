"""
Document management API endpoints.

- POST /documents/upload   — Upload a PDF and start processing
- GET  /documents/         — List all documents for the current tenant
- GET  /documents/{id}     — Get a single document's details
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.dependencies.auth import require_role
from backend.app.dependencies.database import get_db
from backend.app.middleware.tenant import get_tenant_id
from backend.app.models.document import Document
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.user import User
from backend.tasks.document_tasks import process_document
from backend.app.schemas.document import (
    DocumentDetail,
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


# ── Upload Document ───────────────────────────────────────────────

@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(
        default="annual_report",
        pattern="^(annual_report|earnings_call|credit_agreement|other)$",
    ),
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF document for AI-powered credit risk analysis.

    Only admin and analyst roles can upload. Viewers cannot.

    Flow:
    1. Validate the file is a PDF and within size limits
    2. Upload the file to MinIO object storage
    3. Create a document record in PostgreSQL
    4. Create a processing job record (status: queued)
    5. Queue a Celery task for async processing (mocked for now)
    6. Return job_id immediately — frontend polls for status

    HTTP 202 (Accepted) means "I got your request and will process
    it in the background" — different from 200 (done) or 201 (created).
    """
    tenant_id = get_tenant_id(current_user)

    # Step 1: Validate file
    if not file.filename:
        raise BadRequestError("No file provided")

    if not file.filename.lower().endswith(".pdf"):
        raise BadRequestError("Only PDF files are accepted")

    # Read file content to check size
    file_content = await file.read()
    file_size = len(file_content)

    # 50MB limit
    max_size = 50 * 1024 * 1024
    if file_size > max_size:
        raise BadRequestError(f"File too large. Maximum size is 50MB, got {file_size / (1024*1024):.1f}MB")

    if file_size == 0:
        raise BadRequestError("File is empty")

    # Step 2: Upload to MinIO
    document_id = uuid4()
    minio_key = f"{str(tenant_id)}/{str(document_id)}/{file.filename}"

    try:
        from backend.app.services.storage_service import upload_file
        await file.seek(0)  # Reset file pointer after reading
        upload_file(file_content, minio_key)
    except Exception as e:
        raise BadRequestError(f"Failed to upload file: {str(e)}")

    # Step 3: Create document record
    document = Document(
        id=document_id,
        tenant_id=tenant_id,
        uploaded_by=current_user.id,
        original_filename=file.filename,
        minio_object_key=minio_key,
        file_size_bytes=file_size,
        document_type=document_type,
        status="uploaded",
    )
    db.add(document)

    # Step 4: Create processing job
    job_id = uuid4()
    job = ProcessingJob(
        id=job_id,
        document_id=document_id,
        tenant_id=tenant_id,
        status="queued",
    )
    db.add(job)

    await db.commit()

    # Step 5: Queue Celery task for async processing
    celery_task = process_document.delay(
        str(document_id), str(tenant_id), str(job_id)
    )

    return DocumentUploadResponse(
        document_id=document_id,
        job_id=job_id,
        filename=file.filename,
        status="queued",
        message="Document uploaded successfully. Processing started.",
    )


# ── List Documents ────────────────────────────────────────────────

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents for the current tenant.

    Paginated — default 20 per page, max 100.
    All roles can view documents (including viewers).
    Results are ordered by newest first.
    """
    tenant_id = get_tenant_id(current_user)

    # Count total documents for this tenant
    count_query = select(func.count(Document.id)).where(
        Document.tenant_id == tenant_id
    )
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    # Fetch paginated documents
    offset = (page - 1) * page_size
    query = (
        select(Document)
        .where(Document.tenant_id == tenant_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentSummary.model_validate(doc) for doc in documents],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


# ── Get Single Document ──────────────────────────────────────────

@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details for a specific document.

    The tenant_id filter ensures users can only see
    documents belonging to their own company.
    """
    tenant_id = get_tenant_id(current_user)

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise NotFoundError("Document", str(document_id))

    return DocumentDetail.model_validate(document)