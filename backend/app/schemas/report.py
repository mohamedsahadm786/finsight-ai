"""
Pydantic schemas for credit risk report endpoints.

The report is the final output of the 6-agent pipeline. It combines
outputs from all agents into one comprehensive view that the frontend
renders with gauges, charts, and narrative text.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Sub-sections of the report ────────────────────────────────────

class ExtractedRatios(BaseModel):
    """Financial ratios extracted by Agent 2 (LLaMA)."""
    dscr: float | None = None
    leverage_ratio: float | None = None
    interest_coverage: float | None = None
    current_ratio: float | None = None
    net_profit_margin: float | None = None
    ratios_found_count: int = 0

    model_config = {"from_attributes": True}


class SentimentResult(BaseModel):
    """Sentiment analysis from Agent 3 (FinBERT)."""
    overall_sentiment: str  # positive / neutral / negative
    positive_count: int
    neutral_count: int
    negative_count: int
    confidence_score: float
    flagged_sentences: list | None = None  # Most negative sentences

    model_config = {"from_attributes": True}


class BreachResult(BaseModel):
    """Covenant breach detection from Agent 4 (FinBERT)."""
    breach_detected: bool
    breach_count: int
    breach_details: list | None = None  # Array of breach objects

    model_config = {"from_attributes": True}


class RiskScoreResult(BaseModel):
    """Credit risk score from Agent 5 (XGBoost + SHAP)."""
    risk_score: float          # 0.0 to 1.0
    risk_tier: str             # low / medium / high / distress
    ratios_used_count: int
    imputed_features: dict | None = None
    shap_values: dict | None = None  # {feature_name: shap_value}
    score_reliability: str     # high / partial / low

    model_config = {"from_attributes": True}


# ── Complete Report ───────────────────────────────────────────────

class ReportSummary(BaseModel):
    """One report in the list view — minimal info."""
    id: UUID
    document_id: UUID
    overall_risk_tier: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """Paginated list of reports for the current tenant."""
    reports: list[ReportSummary]
    total_count: int
    page: int
    page_size: int


class ReportDetail(BaseModel):
    """
    The FULL report — everything the frontend needs to render
    the complete risk analysis page with all charts and narratives.
    """
    id: UUID
    document_id: UUID
    tenant_id: UUID
    summary_text: str | None = None      # GPT-4 narrative
    overall_risk_tier: str
    key_findings: list | None = None     # Bullet points
    llm_tokens_used: int | None = None
    created_at: datetime

    # Agent outputs — joined from separate tables
    ratios: ExtractedRatios | None = None
    sentiment: SentimentResult | None = None
    breaches: BreachResult | None = None
    risk_score: RiskScoreResult | None = None

    model_config = {"from_attributes": True}