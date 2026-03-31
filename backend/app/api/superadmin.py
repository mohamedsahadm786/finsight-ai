"""
Platform Superadmin API endpoints.

The superadmin is ABOVE all tenants — they manage the entire platform.
They can:
- List all tenants (companies) with summary stats
- Suspend / restore / soft-delete a tenant
- View token usage and costs per tenant per model per month
- Manage LLM model configurations (toggle on/off, change parameters)
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import BadRequestError, NotFoundError
from backend.app.dependencies.auth import get_current_superadmin
from backend.app.dependencies.database import get_db
from backend.app.models.document import Document
from backend.app.models.llm_configuration import LLMConfiguration
from backend.app.models.monthly_usage_summary import MonthlyUsageSummary
from backend.app.models.superadmin import SuperAdmin
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.schemas.superadmin import (
    LLMConfigListResponse,
    LLMConfigSchema,
    SuspendTenantRequest,
    TenantActionResponse,
    TenantListResponse,
    TenantSummary,
    UpdateLLMConfigRequest,
    UsageOverviewResponse,
    MonthlyUsageSummary as MonthlyUsageSummarySchema,
)

router = APIRouter(prefix="/superadmin", tags=["Superadmin — Platform Management"])


# ── List All Tenants ──────────────────────────────────────────────

@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all companies on the platform with summary stats.

    Shows: name, status, plan tier, user count, document count.
    This gives the superadmin a bird's-eye view of the entire platform.
    """
    # Get all tenants
    result = await db.execute(
        select(Tenant).order_by(Tenant.created_at.desc())
    )
    tenants = result.scalars().all()

    # Get current year-month string for token lookup
    current_ym = datetime.now(timezone.utc).strftime("%Y-%m")

    tenant_summaries = []
    for tenant in tenants:
        # Count users for this tenant
        user_count_result = await db.execute(
            select(func.count(User.id)).where(User.tenant_id == tenant.id)
        )
        user_count = user_count_result.scalar()

        # Count documents for this tenant
        doc_count_result = await db.execute(
            select(func.count(Document.id)).where(Document.tenant_id == tenant.id)
        )
        doc_count = doc_count_result.scalar()

        # Get token usage for current month from pre-aggregated table
        usage_result = await db.execute(
            select(MonthlyUsageSummary).where(
                MonthlyUsageSummary.tenant_id == tenant.id,
                MonthlyUsageSummary.year_month == current_ym,
            )
        )
        usage = usage_result.scalar_one_or_none()
        tokens_this_month = int(usage.total_tokens) if usage else 0

        tenant_summaries.append(
            TenantSummary(
                id=tenant.id,
                name=tenant.name,
                slug=tenant.slug,
                status=tenant.status,
                plan_tier=tenant.plan_tier,
                user_count=user_count,
                document_count=doc_count,
                total_tokens_this_month=tokens_this_month,
                created_at=tenant.created_at,
            )
        )


    return TenantListResponse(
        tenants=tenant_summaries,
        total_count=len(tenant_summaries),
    )


# ── Suspend Tenant ────────────────────────────────────────────────

@router.patch("/tenants/{tenant_id}/suspend", response_model=TenantActionResponse)
async def suspend_tenant(
    tenant_id: UUID,
    request: SuspendTenantRequest,
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a tenant (company). Their users can no longer log in.

    A reason must be provided. The tenant's data is preserved —
    nothing is deleted. The tenant can be restored later.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise NotFoundError("Tenant", str(tenant_id))

    if tenant.status == "suspended":
        raise BadRequestError("Tenant is already suspended")

    if tenant.status == "deleted":
        raise BadRequestError("Cannot suspend a deleted tenant")

    tenant.status = "suspended"
    tenant.suspended_at = datetime.now(timezone.utc)
    tenant.suspended_reason = request.reason

    await db.commit()

    return TenantActionResponse(
        id=tenant.id,
        name=tenant.name,
        status=tenant.status,
        message=f"Tenant '{tenant.name}' has been suspended. Reason: {request.reason}",
    )


# ── Restore Tenant ────────────────────────────────────────────────

@router.patch("/tenants/{tenant_id}/restore", response_model=TenantActionResponse)
async def restore_tenant(
    tenant_id: UUID,
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a previously suspended tenant.
    Their users can log in again. All data is intact.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise NotFoundError("Tenant", str(tenant_id))

    if tenant.status != "suspended":
        raise BadRequestError("Only suspended tenants can be restored")

    tenant.status = "active"
    tenant.suspended_at = None
    tenant.suspended_reason = None

    await db.commit()

    return TenantActionResponse(
        id=tenant.id,
        name=tenant.name,
        status=tenant.status,
        message=f"Tenant '{tenant.name}' has been restored",
    )


# ── Soft Delete Tenant ────────────────────────────────────────────

@router.delete("/tenants/{tenant_id}", response_model=TenantActionResponse)
async def delete_tenant(
    tenant_id: UUID,
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete a tenant. Sets status to "deleted" and records timestamp.

    This is a SOFT delete — the data remains in the database but
    is no longer accessible. Hard deletion is never performed
    (regulatory requirement in financial services — data retention).
    """
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise NotFoundError("Tenant", str(tenant_id))

    if tenant.status == "deleted":
        raise BadRequestError("Tenant is already deleted")

    tenant.status = "deleted"
    tenant.deleted_at = datetime.now(timezone.utc)

    await db.commit()

    return TenantActionResponse(
        id=tenant.id,
        name=tenant.name,
        status=tenant.status,
        message=f"Tenant '{tenant.name}' has been soft-deleted",
    )


# ── Token Usage Overview ──────────────────────────────────────────

@router.get("/usage", response_model=UsageOverviewResponse)
async def get_usage_overview(
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated token usage across all tenants.

    Returns monthly summaries with per-model token counts and costs.
    This data powers the superadmin billing dashboard.
    """
    result = await db.execute(
        select(MonthlyUsageSummary).order_by(
            MonthlyUsageSummary.year_month.desc()
        )
    )
    summaries = result.scalars().all()

    # Calculate totals
    total_cost = sum(float(s.total_cost_usd or 0) for s in summaries)
    total_tokens = sum(int(s.total_tokens or 0) for s in summaries)

    return UsageOverviewResponse(
        summaries=[
            MonthlyUsageSummarySchema.model_validate(s) for s in summaries
        ],
        total_cost_all_time=total_cost,
        total_tokens_all_time=total_tokens,
    )


# ── Usage for Specific Tenant ─────────────────────────────────────

@router.get("/usage/{tenant_id}", response_model=UsageOverviewResponse)
async def get_tenant_usage(
    tenant_id: UUID,
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get token usage for a specific tenant.
    """
    # Verify tenant exists
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise NotFoundError("Tenant", str(tenant_id))

    result = await db.execute(
        select(MonthlyUsageSummary)
        .where(MonthlyUsageSummary.tenant_id == tenant_id)
        .order_by(MonthlyUsageSummary.year_month.desc())
    )
    summaries = result.scalars().all()

    total_cost = sum(float(s.total_cost_usd or 0) for s in summaries)
    total_tokens = sum(int(s.total_tokens or 0) for s in summaries)

    return UsageOverviewResponse(
        summaries=[
            MonthlyUsageSummarySchema.model_validate(s) for s in summaries
        ],
        total_cost_all_time=total_cost,
        total_tokens_all_time=total_tokens,
    )


# ── List LLM Configurations ──────────────────────────────────────

@router.get("/llm-config", response_model=LLMConfigListResponse)
async def list_llm_configs(
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all LLM model configurations.

    Shows which models are active, their parameters, and costs.
    """
    result = await db.execute(select(LLMConfiguration))
    configs = result.scalars().all()

    return LLMConfigListResponse(
        configs=[LLMConfigSchema.model_validate(c) for c in configs],
    )


# ── Update LLM Configuration ─────────────────────────────────────

@router.patch("/llm-config/{config_id}", response_model=LLMConfigSchema)
async def update_llm_config(
    config_id: UUID,
    request: UpdateLLMConfigRequest,
    current_superadmin: SuperAdmin = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an LLM model's configuration.

    The superadmin can:
    - Toggle a model on/off (is_active)
    - Change max_tokens, temperature
    - Update cost parameters

    Changes take effect within 5 minutes (Redis cache TTL).
    No code deployment needed.
    """
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise NotFoundError("LLM Configuration", str(config_id))

    # Update only the fields that were provided
    if request.is_active is not None:
        config.is_active = request.is_active
    if request.max_tokens is not None:
        config.max_tokens = request.max_tokens
    if request.temperature is not None:
        config.temperature = request.temperature
    if request.cost_per_1k_input_tokens is not None:
        config.cost_per_1k_input_tokens = request.cost_per_1k_input_tokens
    if request.cost_per_1k_output_tokens is not None:
        config.cost_per_1k_output_tokens = request.cost_per_1k_output_tokens

    config.updated_at = datetime.now(timezone.utc)

    await db.commit()

    return LLMConfigSchema.model_validate(config)