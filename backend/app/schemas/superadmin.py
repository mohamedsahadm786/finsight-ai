"""
Pydantic schemas for platform superadmin endpoints.

The superadmin sees ALL tenants across the entire platform.
They can suspend/restore companies, view token usage and costs,
and manage LLM model configurations.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Tenant Management ─────────────────────────────────────────────

class TenantSummary(BaseModel):
    """One tenant (company) in the superadmin's overview list."""
    id: UUID
    name: str
    slug: str
    status: str  # active / suspended / deleted
    plan_tier: str  # free / pro / enterprise
    user_count: int = 0
    document_count: int = 0
    total_tokens_this_month: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    """List of all tenants on the platform."""
    tenants: list[TenantSummary]
    total_count: int


class SuspendTenantRequest(BaseModel):
    """Reason for suspending a tenant."""
    reason: str = Field(..., min_length=5, max_length=500)


class TenantActionResponse(BaseModel):
    """Confirmation of tenant status change."""
    id: UUID
    name: str
    status: str
    message: str


# ── Token Usage and Billing ───────────────────────────────────────

class MonthlyUsageSummary(BaseModel):
    """Pre-aggregated monthly token usage for one tenant."""
    tenant_id: UUID
    tenant_name: str = ""
    year_month: str  # e.g., "2025-03"
    total_tokens: int
    llama_tokens: int
    finbert_tokens: int
    gpt4_tokens: int
    gpt35_tokens: int
    total_cost_usd: float
    documents_processed: int

    model_config = {"from_attributes": True}


class UsageOverviewResponse(BaseModel):
    """Aggregated usage across all tenants or for a specific tenant."""
    summaries: list[MonthlyUsageSummary]
    total_cost_all_time: float = 0.0
    total_tokens_all_time: int = 0


# ── LLM Configuration Management ─────────────────────────────────

class LLMConfigSchema(BaseModel):
    """Current configuration for one LLM model."""
    model_config = {"from_attributes": True, "protected_namespaces": ()}
    id: UUID
    model_name: str
    is_active: bool
    model_path: str | None = None
    max_tokens: int
    temperature: float
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    updated_at: datetime

    


class LLMConfigListResponse(BaseModel):
    """All LLM configurations."""
    configs: list[LLMConfigSchema]


class UpdateLLMConfigRequest(BaseModel):
    """Update model parameters or toggle active status."""
    is_active: bool | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    cost_per_1k_input_tokens: float | None = None
    cost_per_1k_output_tokens: float | None = None