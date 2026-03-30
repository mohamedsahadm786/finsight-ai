"""
Agent 6 — Report Writer.

Assembles the structured outputs of all previous agents (ratios, sentiment,
breach detection, risk score) and generates the final human-readable
credit risk report.

Locally (USE_REAL_LLAMA=false): Returns a mock report instantly.
On EC2 (USE_REAL_LLAMA=true): Makes one GPT-4 API call to generate
a professional credit analyst report narrative.
"""

import logging
import time
from typing import Any

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.report import Report

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Mock report generation — used locally
# ---------------------------------------------------------------------------
def _mock_generate_report(
    extracted_ratios: dict,
    sentiment_result: dict,
    breach_result: dict,
    risk_score: dict,
) -> dict[str, Any]:
    """
    Returns a hardcoded report instantly.
    Used when USE_REAL_LLAMA=false (local development).
    """
    risk_tier = risk_score.get("risk_tier", "medium")
    score_val = risk_score.get("risk_score", 0.5)

    return {
        "summary_text": (
            f"Based on the analysis of the uploaded financial document, the company presents "
            f"a {str(risk_tier).upper()} risk profile. "
            f"The Debt Service Coverage Ratio of {extracted_ratios.get('dscr', 'N/A')}x "
            f"{'is above the minimum covenant threshold but leaves limited headroom' if extracted_ratios.get('dscr') and extracted_ratios['dscr'] > 1.2 else 'requires attention'}. "
            f"The leverage ratio of {extracted_ratios.get('leverage_ratio', 'N/A')}x indicates "
            f"{'significant' if extracted_ratios.get('leverage_ratio', 0) > 4 else 'moderate'} debt burden. "
            f"{'One or more covenant breaches were detected. ' if breach_result.get('breach_detected') else 'No covenant breaches were detected. '}"
            f"Overall document sentiment is {sentiment_result.get('overall_sentiment', 'neutral')}. "
            f"XGBoost risk score: {score_val} ({str(risk_tier).upper()} tier). "
            f"Recommend {'enhanced monitoring and quarterly review' if risk_tier in ('high', 'distress') else 'standard periodic review'}."
        ),
        "key_findings": [
            f"DSCR: {extracted_ratios.get('dscr', 'N/A')}x",
            f"Leverage Ratio: {extracted_ratios.get('leverage_ratio', 'N/A')}x",
            f"Interest Coverage: {extracted_ratios.get('interest_coverage', 'N/A')}x",
            f"Current Ratio: {extracted_ratios.get('current_ratio', 'N/A')}x",
            f"Net Profit Margin: {extracted_ratios.get('net_profit_margin', 'N/A')}",
            f"Sentiment: {sentiment_result.get('overall_sentiment', 'N/A')}",
            f"Breaches detected: {breach_result.get('breach_count', 0)}",
            f"Risk Score: {score_val} ({str(risk_tier).upper()})",
        ],
        "overall_risk_tier": risk_tier or "medium",
        "llm_tokens_used": 0,
    }


# ---------------------------------------------------------------------------
# Real GPT-4 report generation — used on EC2 only
# ---------------------------------------------------------------------------
def _real_generate_report(
    extracted_ratios: dict,
    sentiment_result: dict,
    breach_result: dict,
    risk_score: dict,
) -> dict[str, Any]:
    """
    Uses OpenAI GPT-4 to generate a professional credit risk report.
    Only runs on EC2 where USE_REAL_LLAMA=true and OPENAI_API_KEY is set.
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Build structured context for GPT-4
        context = {
            "financial_ratios": extracted_ratios,
            "sentiment_analysis": {
                "overall": sentiment_result.get("overall_sentiment"),
                "positive_count": sentiment_result.get("positive_count"),
                "neutral_count": sentiment_result.get("neutral_count"),
                "negative_count": sentiment_result.get("negative_count"),
                "flagged_sentences": sentiment_result.get("flagged_sentences", []),
            },
            "covenant_breaches": {
                "detected": breach_result.get("breach_detected"),
                "count": breach_result.get("breach_count"),
                "details": breach_result.get("breach_details", []),
            },
            "risk_assessment": {
                "score": risk_score.get("risk_score"),
                "tier": risk_score.get("risk_tier"),
                "shap_values": risk_score.get("shap_values", {}),
                "reliability": risk_score.get("score_reliability"),
            },
        }

        import json
        context_json = json.dumps(context, indent=2, default=str)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior credit risk analyst at a major UAE bank. "
                        "Write a professional credit risk advisory report based on the "
                        "automated analysis results provided. Be specific, cite exact "
                        "numbers, and provide actionable recommendations. "
                        "Format: Start with an executive summary paragraph, then provide "
                        "key findings as bullet points."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Generate a credit risk report based on this analysis:\n\n{context_json}",
                },
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        report_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0

        # Split into summary and key findings
        lines = report_text.strip().split("\n")
        summary_lines = []
        findings = []
        in_findings = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("• ") or stripped.startswith("* "):
                in_findings = True
                findings.append(stripped.lstrip("-•* ").strip())
            elif not in_findings:
                summary_lines.append(stripped)

        summary_text = " ".join(summary_lines).strip()
        if not summary_text:
            summary_text = report_text[:500]

        if not findings:
            findings = [
                f"Risk Score: {risk_score.get('risk_score')} ({risk_score.get('risk_tier', 'N/A').upper()})",
                f"Breaches: {breach_result.get('breach_count', 0)} detected",
                f"Sentiment: {sentiment_result.get('overall_sentiment', 'N/A')}",
            ]

        return {
            "summary_text": summary_text,
            "key_findings": findings,
            "overall_risk_tier": risk_score.get("risk_tier", "medium"),
            "llm_tokens_used": tokens_used,
        }

    except Exception as e:
        logger.error(f"GPT-4 report generation failed: {e}. Falling back to mock.")
        return _mock_generate_report(extracted_ratios, sentiment_result, breach_result, risk_score)


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_6_report_writer(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 6 — Report Writer.

    Reads from state: extracted_ratios, sentiment_result, breach_result, risk_score,
                      document_id, tenant_id, job_id
    Writes to state: final_report
    Side effects: reports row created in PostgreSQL
    """
    document_id = state["document_id"]
    tenant_id = state["tenant_id"]
    job_id = state["job_id"]
    extracted_ratios = state.get("extracted_ratios", {})
    sentiment_result = state.get("sentiment_result", {})
    breach_result = state.get("breach_result", {})
    risk_score_data = state.get("risk_score", {})

    start_time = time.time()

    db = SyncSessionLocal()
    try:
        # --- Update job status ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_agent = "Report Writer"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 6: Starting report generation...")

        # --- Choose real or mock ---
        if settings.USE_REAL_LLAMA and settings.OPENAI_API_KEY:
            result = _real_generate_report(
                extracted_ratios, sentiment_result, breach_result, risk_score_data
            )
        else:
            result = _mock_generate_report(
                extracted_ratios, sentiment_result, breach_result, risk_score_data
            )

        # --- Save to PostgreSQL ---
        report = Report(
            document_id=document_id,
            job_id=job_id,
            tenant_id=tenant_id,
            summary_text=result["summary_text"],
            overall_risk_tier=result["overall_risk_tier"],
            key_findings=result["key_findings"],
            llm_tokens_used=result["llm_tokens_used"],
        )
        db.add(report)
        db.commit()

        logger.info(
            f"[Job {job_id}] Agent 6 complete: "
            f"tier={result['overall_risk_tier']}, "
            f"tokens_used={result['llm_tokens_used']}"
        )

        return {
            **state,
            "final_report": result,
        }

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 6 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()
        duration = time.time() - start_time
        from backend.app.core.metrics import agent_duration
        agent_duration.labels(agent="report_writer").observe(duration)