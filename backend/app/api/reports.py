"""
Report API endpoints.

- GET /reports/          — List all reports for the current tenant
- GET /reports/{id}      — Get full report with all agent outputs
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import NotFoundError
from backend.app.dependencies.auth import require_role
from backend.app.dependencies.database import get_db
from backend.app.middleware.tenant import get_tenant_id
from backend.app.models.breach_result import BreachResult
from backend.app.models.extracted_ratio import ExtractedRatio
from backend.app.models.report import Report
from backend.app.models.risk_score import RiskScore
from backend.app.models.sentiment_result import SentimentResult
from backend.app.models.user import User
from backend.app.schemas.report import (
    BreachResult as BreachResultSchema,
    ExtractedRatios,
    ReportDetail,
    ReportListResponse,
    ReportSummary,
    RiskScoreResult,
    SentimentResult as SentimentResultSchema,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


# ── List Reports ──────────────────────────────────────────────────

@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    List all completed reports for the current tenant.
    Paginated, ordered by newest first.
    All roles can view reports.
    """
    tenant_id = get_tenant_id(current_user)

    # Count total
    count_query = select(func.count(Report.id)).where(
        Report.tenant_id == tenant_id
    )
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    # Fetch paginated
    offset = (page - 1) * page_size
    query = (
        select(Report)
        .where(Report.tenant_id == tenant_id)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        reports=[ReportSummary.model_validate(r) for r in reports],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


# ── Get Full Report ───────────────────────────────────────────────

@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(require_role(["admin", "analyst", "viewer"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the complete report with ALL agent outputs.

    This is the most data-rich endpoint in the entire application.
    It joins data from 5 tables to build the full report view:
    - reports (GPT-4 narrative, key findings)
    - extracted_ratios (Agent 2 — LLaMA output)
    - sentiment_results (Agent 3 — FinBERT sentiment)
    - breach_results (Agent 4 — FinBERT breach)
    - risk_scores (Agent 5 — XGBoost + SHAP)

    The frontend uses this to render:
    - Risk gauge (semicircle)
    - Ratio cards
    - Sentiment bar chart
    - Breach alert cards
    - SHAP feature importance chart
    - GPT-4 narrative summary
    """
    tenant_id = get_tenant_id(current_user)

    # Get the report
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.tenant_id == tenant_id,
        )
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report", str(report_id))

    # Get associated agent outputs using document_id
    doc_id = report.document_id

    # Agent 2 output
    ratio_result = await db.execute(
        select(ExtractedRatio).where(ExtractedRatio.document_id == doc_id)
    )
    ratios = ratio_result.scalar_one_or_none()

    # Agent 3 output
    sentiment_result = await db.execute(
        select(SentimentResult).where(SentimentResult.document_id == doc_id)
    )
    sentiment = sentiment_result.scalar_one_or_none()

    # Agent 4 output
    breach_result = await db.execute(
        select(BreachResult).where(BreachResult.document_id == doc_id)
    )
    breach = breach_result.scalar_one_or_none()

    # Agent 5 output
    risk_result = await db.execute(
        select(RiskScore).where(RiskScore.document_id == doc_id)
    )
    risk = risk_result.scalar_one_or_none()

    # Build the complete response
    return ReportDetail(
        id=report.id,
        document_id=report.document_id,
        tenant_id=report.tenant_id,
        summary_text=report.summary_text,
        overall_risk_tier=report.overall_risk_tier,
        key_findings=report.key_findings,
        llm_tokens_used=report.llm_tokens_used,
        created_at=report.created_at,
        ratios=ExtractedRatios.model_validate(ratios) if ratios else None,
        sentiment=SentimentResultSchema.model_validate(sentiment) if sentiment else None,
        breaches=BreachResultSchema.model_validate(breach) if breach else None,
        risk_score=RiskScoreResult.model_validate(risk) if risk else None,
    )