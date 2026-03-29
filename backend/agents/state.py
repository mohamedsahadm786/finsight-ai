"""
LangGraph Pipeline State Schema.

This module defines the shared state object that flows through all 6 agents
in the LangGraph pipeline. Each agent reads what it needs from the state
and writes its results back into the state.

The state is a TypedDict (not Pydantic) because LangGraph requires TypedDict
for its state management system.
"""

from typing import TypedDict, Any


class PipelineState(TypedDict, total=False):
    """
    Shared state that flows through the entire LangGraph pipeline.

    Fields:
        document_id: UUID string of the document being processed
        tenant_id: UUID string of the tenant who owns the document
        job_id: UUID string of the processing job tracking this run

        chunks: List of chunk text strings extracted by Agent 1
        chunk_metadata: List of dicts with page_number, section, has_table, token_count per chunk
        chunk_ids: List of UUID strings for document_chunks rows (match Qdrant point IDs)

        extracted_ratios: Dict of ratio_name → value from Agent 2
        ratios_found_count: How many of the 5 target ratios were found (0-5)
        raw_extraction: Full raw LLaMA output for debugging

        sentiment_result: Dict with overall_sentiment, counts, confidence, flagged_sentences
        breach_result: Dict with breach_detected, breach_count, breach_details

        risk_score: Dict with score, tier, shap_values, reliability, imputed_features
        final_report: Dict with summary_text, key_findings, overall_risk_tier, tokens_used

        errors: List of error messages from any agent that failed
    """

    # --- Input (set before graph.invoke) ---
    document_id: str
    tenant_id: str
    job_id: str

    # --- Agent 1 outputs ---
    chunks: list[str]
    chunk_metadata: list[dict[str, Any]]
    chunk_ids: list[str]

    # --- Agent 2 outputs ---
    extracted_ratios: dict[str, Any]
    ratios_found_count: int
    raw_extraction: dict[str, Any]

    # --- Agent 3 output ---
    sentiment_result: dict[str, Any]

    # --- Agent 4 output ---
    breach_result: dict[str, Any]

    # --- Agent 5 output ---
    risk_score: dict[str, Any]

    # --- Agent 6 output ---
    final_report: dict[str, Any]

    # --- Error tracking ---
    errors: list[str]