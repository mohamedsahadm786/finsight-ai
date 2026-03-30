"""
Agent 1 — Document Parser and Indexer.

Downloads the PDF from MinIO, extracts text with PyMuPDF, splits into
sentence-aware chunks with SpacyTextSplitter, generates dense + sparse
vectors, stores in Qdrant, and creates document_chunks rows in PostgreSQL.

Dense embeddings: Mocked locally (returns random 768-dim vectors).
                  Real BAAI/bge-base-financial model loads only on EC2.
Sparse vectors:   fastembed BM25 — lightweight, runs locally for real.
"""

import logging
import time
import uuid
from typing import Any

import fitz  # PyMuPDF
import numpy as np
from langchain.text_splitter import SpacyTextSplitter
from qdrant_client.http.models import PointStruct, SparseVector

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.services.storage_service import download_file
from backend.app.services.qdrant_service import get_qdrant_client, ensure_tenant_collection

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Text splitter — initialized once, reused across calls
# ---------------------------------------------------------------------------
# SpacyTextSplitter uses spaCy's sentence boundary detection so chunks
# never break mid-sentence. Financial docs have abbreviations like "Co.",
# "Ltd.", "Dec." that naive splitters mishandle.
# chunk_size=512 tokens, chunk_overlap=50 tokens
# ---------------------------------------------------------------------------
try:
    text_splitter = SpacyTextSplitter(
        pipeline="en_core_web_sm",
        chunk_size=512,
        chunk_overlap=50,
    )
except Exception as e:
    logger.warning(f"SpacyTextSplitter init failed: {e}. Will use fallback splitting.")
    text_splitter = None


# ---------------------------------------------------------------------------
# Sparse embedding model (fastembed BM25) — lightweight, runs locally
# ---------------------------------------------------------------------------
_sparse_model = None


def _get_sparse_model():
    """Lazy-load the fastembed sparse model on first use."""
    global _sparse_model
    if _sparse_model is None:
        try:
            from fastembed import SparseTextEmbedding
            _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        except Exception as e:
            logger.error(f"Failed to load sparse embedding model: {e}")
            _sparse_model = "FAILED"
    return _sparse_model


# ---------------------------------------------------------------------------
# Dense embedding — MOCKED locally, real on EC2
# ---------------------------------------------------------------------------
def _generate_dense_embedding(text: str) -> list[float]:
    """
    Generate a 768-dimensional dense embedding for a text chunk.

    Locally (USE_REAL_LLAMA=false): returns a deterministic pseudo-random
    vector based on the text length. This is enough for Qdrant to store
    and retrieve — the vectors won't be semantically meaningful but the
    pipeline works end-to-end.

    On EC2 (USE_REAL_LLAMA=true): loads BAAI/bge-base-financial via
    sentence-transformers and generates real semantic embeddings.
    """
    if settings.USE_REAL_LLAMA:
        # Real embedding — only runs on EC2 with enough RAM
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-base-financial-matryoshka")
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Real dense embedding failed: {e}. Falling back to mock.")

    # Mock embedding — deterministic based on text length so same text = same vector
    rng = np.random.RandomState(seed=len(text) % 10000)
    vec = rng.randn(768).astype(np.float32)
    # Normalize to unit length (cosine similarity expects this)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _generate_sparse_embedding(text: str) -> dict[str, Any]:
    """
    Generate a sparse BM25 vector for a text chunk using fastembed.

    Returns a dict with 'indices' and 'values' keys for Qdrant's SparseVector.
    If the sparse model fails to load, returns a minimal fallback.
    """
    model = _get_sparse_model()
    if model == "FAILED" or model is None:
        # Fallback: return a minimal sparse vector so Qdrant doesn't reject the point
        return {"indices": [0], "values": [0.1]}

    try:
        # fastembed returns a generator, we need the first result
        results = list(model.embed([text]))
        if results and len(results) > 0:
            sparse_emb = results[0]
            return {
                "indices": sparse_emb.indices.tolist(),
                "values": sparse_emb.values.tolist(),
            }
    except Exception as e:
        logger.error(f"Sparse embedding failed: {e}")

    return {"indices": [0], "values": [0.1]}


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------
def _extract_text_from_pdf(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """
    Extract text from every page of a PDF using PyMuPDF.

    Returns a list of dicts, one per page:
    [{"page_number": 1, "text": "...", "has_table": False}, ...]

    has_table is a heuristic: True if the page contains table-like structures
    (detected by PyMuPDF's find_tables method).
    """
    pages = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")

        # Table detection heuristic
        has_table = False
        try:
            tables = page.find_tables()
            if tables and len(tables.tables) > 0:
                has_table = True
        except Exception:
            pass

        if text.strip():
            pages.append({
                "page_number": page_num + 1,  # 1-indexed for human display
                "text": text.strip(),
                "has_table": has_table,
            })

    doc.close()
    return pages


# ---------------------------------------------------------------------------
# Text chunking with page tracking
# ---------------------------------------------------------------------------
def _chunk_text_with_metadata(
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Split extracted page texts into sentence-aware chunks.

    Each chunk gets metadata: page_number, section (placeholder), has_table, token_count.
    Uses SpacyTextSplitter for sentence-aware splitting. Falls back to simple
    character-based splitting if spaCy is not available.
    """
    # Combine all page texts with page markers for tracking
    all_chunks = []

    for page_info in pages:
        page_text = page_info["text"]
        page_number = page_info["page_number"]
        has_table = page_info["has_table"]

        if not page_text.strip():
            continue

        # Split this page's text into chunks
        if text_splitter is not None:
            try:
                chunk_texts = text_splitter.split_text(page_text)
            except Exception as e:
                logger.warning(f"SpacyTextSplitter failed on page {page_number}: {e}")
                # Fallback: split by ~2000 chars (rough approximation of 512 tokens)
                chunk_texts = [
                    page_text[i:i + 2000]
                    for i in range(0, len(page_text), 1800)
                ]
        else:
            # No spaCy available — simple character split
            chunk_texts = [
                page_text[i:i + 2000]
                for i in range(0, len(page_text), 1800)
            ]

        for chunk_text in chunk_texts:
            if not chunk_text.strip():
                continue
            # Approximate token count (1 token ≈ 4 characters for English)
            token_count = len(chunk_text) // 4
            all_chunks.append({
                "text": chunk_text.strip(),
                "page_number": page_number,
                "section": "General",  # Section detection is a future enhancement
                "has_table": has_table,
                "token_count": token_count,
            })

    return all_chunks


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_1_parser(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 1 — Document Parser and Indexer.

    Reads from state: document_id, tenant_id, job_id
    Writes to state: chunks, chunk_metadata, chunk_ids
    Side effects: Qdrant points created, document_chunks rows created in PostgreSQL
    """
    document_id = state["document_id"]
    tenant_id = state["tenant_id"]
    job_id = state["job_id"]

    start_time = time.time()

    db = SyncSessionLocal()
    try:
        # --- Update job status ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_agent = "Document Parser"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 1: Starting document parsing...")

        # --- Step 1: Get the document's MinIO key ---
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            error_msg = f"Document {document_id} not found in database"
            logger.error(f"[Job {job_id}] {error_msg}")
            return {**state, "errors": state.get("errors", []) + [error_msg]}

        minio_key = doc.minio_object_key
        logger.info(f"[Job {job_id}] Downloading PDF from MinIO: {minio_key}")

        # --- Step 2: Download PDF from MinIO ---
        try:
            pdf_bytes = download_file(minio_key)
        except Exception as e:
            error_msg = f"Failed to download PDF from MinIO: {e}"
            logger.error(f"[Job {job_id}] {error_msg}")
            return {**state, "errors": state.get("errors", []) + [error_msg]}

        # --- Step 3: Extract text from PDF ---
        logger.info(f"[Job {job_id}] Extracting text from PDF...")
        pages = _extract_text_from_pdf(pdf_bytes)

        if not pages:
            error_msg = "No text could be extracted from the PDF"
            logger.error(f"[Job {job_id}] {error_msg}")
            return {**state, "errors": state.get("errors", []) + [error_msg]}

        # Update page count in document record
        doc.page_count = len(pages)
        db.commit()
        logger.info(f"[Job {job_id}] Extracted text from {len(pages)} pages")

        # --- Step 4: Split into chunks ---
        logger.info(f"[Job {job_id}] Splitting text into chunks...")
        chunk_data = _chunk_text_with_metadata(pages)
        logger.info(f"[Job {job_id}] Created {len(chunk_data)} chunks")

        if not chunk_data:
            error_msg = "No chunks created from extracted text"
            logger.error(f"[Job {job_id}] {error_msg}")
            return {**state, "errors": state.get("errors", []) + [error_msg]}

        # --- Step 5: Ensure Qdrant collection exists ---
        ensure_tenant_collection(tenant_id)
        collection_name = f"tenant_{tenant_id}"
        qdrant_client = get_qdrant_client()

        # --- Step 6: Generate embeddings and store in Qdrant + PostgreSQL ---
        logger.info(f"[Job {job_id}] Generating embeddings and indexing {len(chunk_data)} chunks...")

        chunk_texts = []
        chunk_metadata_list = []
        chunk_id_list = []
        qdrant_points = []

        for idx, chunk_info in enumerate(chunk_data):
            chunk_id = str(uuid.uuid4())
            chunk_text = chunk_info["text"]

            # Generate dense embedding (mocked locally)
            dense_vector = _generate_dense_embedding(chunk_text)

            # Generate sparse BM25 embedding (real, runs locally)
            sparse_data = _generate_sparse_embedding(chunk_text)

            # Build Qdrant point
            point = PointStruct(
                id=chunk_id,
                vector={
                    "dense": dense_vector,
                    "sparse": SparseVector(
                        indices=sparse_data["indices"],
                        values=sparse_data["values"],
                    ),
                },
                payload={
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                    "chunk_index": idx,
                    "page_number": chunk_info["page_number"],
                    "section": chunk_info["section"],
                    "has_table": chunk_info["has_table"],
                    "text": chunk_text,
                },
            )
            qdrant_points.append(point)

            # Create PostgreSQL document_chunk record
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=idx,
                page_number=chunk_info["page_number"],
                section=chunk_info["section"],
                has_table=chunk_info["has_table"],
                token_count=chunk_info["token_count"],
            )
            db.add(db_chunk)

            # Track for state output
            chunk_texts.append(chunk_text)
            chunk_metadata_list.append({
                "page_number": chunk_info["page_number"],
                "section": chunk_info["section"],
                "has_table": chunk_info["has_table"],
                "token_count": chunk_info["token_count"],
            })
            chunk_id_list.append(chunk_id)

        # --- Batch upsert to Qdrant ---
        # Qdrant recommends batches of 100 points maximum
        batch_size = 100
        for i in range(0, len(qdrant_points), batch_size):
            batch = qdrant_points[i:i + batch_size]
            qdrant_client.upsert(
                collection_name=collection_name,
                points=batch,
            )

        # --- Commit PostgreSQL document_chunks ---
        db.commit()

        # --- Update document's qdrant_collection_id ---
        doc.qdrant_collection_id = collection_name
        db.commit()

        logger.info(
            f"[Job {job_id}] Agent 1 complete: {len(chunk_data)} chunks indexed "
            f"in Qdrant collection '{collection_name}' and PostgreSQL"
        )

        return {
            **state,
            "chunks": chunk_texts,
            "chunk_metadata": chunk_metadata_list,
            "chunk_ids": chunk_id_list,
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 1 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()
        duration = time.time() - start_time
        from backend.app.core.metrics import agent_duration
        agent_duration.labels(agent="parser").observe(duration)