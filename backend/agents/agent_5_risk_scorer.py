"""
Agent 5 — Risk Scorer.

Takes the extracted financial ratios from Agent 2, runs them through the
trained XGBoost credit risk model, and produces a risk score with full
SHAP explainability.

This agent runs the REAL model even locally — XGBoost is lightweight
and does not require GPU or heavy RAM.

Tier thresholds:
  0.00 - 0.30 = low
  0.30 - 0.55 = medium
  0.55 - 0.75 = high
  0.75 - 1.00 = distress
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.risk_score import RiskScore

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Model file paths
# ---------------------------------------------------------------------------
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "credit_risk_model.pkl"
MEDIANS_PATH = MODEL_DIR / "medians.json"
THRESHOLDS_PATH = MODEL_DIR / "tier_thresholds.json"

# The 5 features in the exact order the XGBoost model expects
FEATURE_ORDER = ["dscr", "leverage_ratio", "interest_coverage", "current_ratio", "net_profit_margin"]


# ---------------------------------------------------------------------------
# Load model artifacts (lazy, cached)
# ---------------------------------------------------------------------------
_model_cache = {}


def _load_model():
    """Load the XGBoost model from disk (cached after first load)."""
    if "model" not in _model_cache:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"XGBoost model not found at {MODEL_PATH}")
        _model_cache["model"] = joblib.load(MODEL_PATH)
    return _model_cache["model"]


def _load_medians() -> dict[str, float]:
    """Load training medians for missing value imputation."""
    if "medians" not in _model_cache:
        if not MEDIANS_PATH.exists():
            raise FileNotFoundError(f"Medians file not found at {MEDIANS_PATH}")
        with open(MEDIANS_PATH, "r") as f:
            _model_cache["medians"] = json.load(f)
    return _model_cache["medians"]


def _load_thresholds() -> dict[str, float]:
    """Load risk tier thresholds."""
    if "thresholds" not in _model_cache:
        if not THRESHOLDS_PATH.exists():
            raise FileNotFoundError(f"Thresholds file not found at {THRESHOLDS_PATH}")
        with open(THRESHOLDS_PATH, "r") as f:
            _model_cache["thresholds"] = json.load(f)
    return _model_cache["thresholds"]


def _score_to_tier(score: float, thresholds: dict[str, float]) -> str:
    """Convert a probability score to a risk tier label."""
    if score < thresholds.get("low", 0.30):
        return "low"
    elif score < thresholds.get("medium", 0.55):
        return "medium"
    elif score < thresholds.get("high", 0.75):
        return "high"
    else:
        return "distress"


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------
def agent_5_risk_scorer(state: dict[str, Any]) -> dict[str, Any]:
    """
    Agent 5 — Risk Scorer.

    Reads from state: extracted_ratios, ratios_found_count, document_id, job_id
    Writes to state: risk_score
    Side effects: risk_scores row created in PostgreSQL
    """
    document_id = state["document_id"]
    job_id = state["job_id"]
    extracted_ratios = state.get("extracted_ratios", {})
    ratios_found_count = state.get("ratios_found_count", 0)

    start_time = time.time()

    db = SyncSessionLocal()
    try:
        # --- Update job status ---
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_agent = "Risk Scorer"
            db.commit()

        logger.info(f"[Job {job_id}] Agent 5: Starting risk scoring...")

        # --- Check if we have enough ratios ---
        if ratios_found_count < 2:
            logger.warning(
                f"[Job {job_id}] Only {ratios_found_count} ratios found. "
                f"Insufficient for reliable scoring."
            )
            risk_result = {
                "risk_score": None,
                "risk_tier": None,
                "ratios_used_count": ratios_found_count,
                "imputed_features": {},
                "shap_values": {},
                "score_reliability": "low",
            }

            # Still save to DB
            risk_db = RiskScore(
                document_id=document_id,
                job_id=job_id,
                risk_score=0.5,  # Default neutral score
                risk_tier="medium",
                ratios_used_count=ratios_found_count,
                imputed_features={},
                shap_values={},
                score_reliability="low",
            )
            db.add(risk_db)
            db.commit()

            return {**state, "risk_score": risk_result}

        # --- Load model artifacts ---
        model = _load_model()
        medians = _load_medians()
        thresholds = _load_thresholds()

        # --- Build feature vector with imputation ---
        feature_values = []
        imputed_features = {}

        for feature_name in FEATURE_ORDER:
            value = extracted_ratios.get(feature_name)
            if value is not None:
                feature_values.append(float(value))
            else:
                # Impute with training median
                median_val = medians.get(feature_name, 0.0)
                feature_values.append(float(median_val))
                imputed_features[feature_name] = float(median_val)
                logger.info(
                    f"[Job {job_id}] Imputed {feature_name} with median: {median_val}"
                )

        # --- Run XGBoost prediction ---
        X = np.array([feature_values])
        probability = float(model.predict_proba(X)[0][1])  # Probability of default (class 1)
        risk_tier = _score_to_tier(probability, thresholds)

        ratios_used = len(FEATURE_ORDER) - len(imputed_features)

        # Determine reliability based on imputation
        if len(imputed_features) == 0:
            reliability = "high"
        elif len(imputed_features) <= 2:
            reliability = "partial"
        else:
            reliability = "low"

        # --- Compute SHAP values ---
        shap_values_dict = {}
        try:
            import shap
            explainer = shap.TreeExplainer(model)
            shap_result = explainer.shap_values(X)
            # shap_result is either a list (binary) or array
            if isinstance(shap_result, list):
                shap_array = shap_result[1][0]  # Class 1 (default) SHAP values
            else:
                shap_array = shap_result[0]

            for i, feature_name in enumerate(FEATURE_ORDER):
                shap_values_dict[feature_name] = round(float(shap_array[i]), 6)
        except Exception as e:
            logger.warning(f"[Job {job_id}] SHAP computation failed: {e}")
            # Provide zero SHAP values as fallback
            for feature_name in FEATURE_ORDER:
                shap_values_dict[feature_name] = 0.0

        risk_result = {
            "risk_score": round(probability, 6),
            "risk_tier": risk_tier,
            "ratios_used_count": ratios_used,
            "imputed_features": imputed_features,
            "shap_values": shap_values_dict,
            "score_reliability": reliability,
        }

        # --- Save to PostgreSQL ---
        risk_db = RiskScore(
            document_id=document_id,
            job_id=job_id,
            risk_score=round(probability, 6),
            risk_tier=risk_tier,
            ratios_used_count=ratios_used,
            imputed_features=imputed_features,
            shap_values=shap_values_dict,
            score_reliability=reliability,
        )
        db.add(risk_db)
        db.commit()

        # Record risk tier in Prometheus
        try:
            from backend.app.core.metrics import risk_tier_total
            risk_tier_total.labels(tier=risk_tier).inc()
        except Exception:
            pass

        logger.info(
            f"[Job {job_id}] Agent 5 complete: "
            f"score={round(probability, 4)}, tier={risk_tier}, "
            f"reliability={reliability}, imputed={list(imputed_features.keys())}"
        )

        return {**state, "risk_score": risk_result}

    except Exception as e:
        db.rollback()
        error_msg = f"Agent 5 failed: {e}"
        logger.error(f"[Job {job_id}] {error_msg}")
        return {**state, "errors": state.get("errors", []) + [error_msg]}

    finally:
        db.close()
        duration = time.time() - start_time
        from backend.app.core.metrics import agent_duration
        agent_duration.labels(agent="risk_scorer").observe(duration)