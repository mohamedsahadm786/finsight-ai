"""
Centralized LLM Registry Service.

All LLM calls in all agents go through this registry. It provides:
1. Model configuration lookup from the llm_configurations database table
2. Redis caching of configurations (5-minute TTL)
3. Automatic token usage logging to token_usage_events table
4. Clean mock/real switching based on USE_REAL_LLAMA env var

No agent directly instantiates a model — they call registry methods.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import redis as redis_lib

from backend.app.config import get_settings
from backend.app.database.session import SyncSessionLocal
from backend.app.models.llm_configuration import LLMConfiguration
from backend.app.models.token_usage_event import TokenUsageEvent

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMRegistry:
    """
    Centralized registry for all LLM model configurations and usage tracking.

    Usage:
        registry = LLMRegistry()
        config = registry.get_model_config("llama")
        registry.log_usage(tenant_id, document_id, job_id, "llama", "extraction", 500, 200)
    """

    def __init__(self):
        self._config_cache: dict[str, Any] = {}
        self._redis: Optional[redis_lib.Redis] = None

    def _get_redis(self) -> redis_lib.Redis:
        """Get Redis connection for config caching (DB 2)."""
        if self._redis is None:
            self._redis = redis_lib.Redis.from_url(
                settings.redis_url(db=2), decode_responses=True
            )
        return self._redis

    def get_model_config(self, model_name: str) -> Optional[dict[str, Any]]:
        """
        Get configuration for a specific model.

        Checks Redis cache first (5-minute TTL), then falls back to PostgreSQL.
        Returns dict with: model_name, is_active, model_path, max_tokens,
        temperature, cost_per_1k_input_tokens, cost_per_1k_output_tokens.
        Returns None if model not found or not active.
        """
        cache_key = f"llm_config:{model_name}"

        # Check Redis cache first
        try:
            r = self._get_redis()
            cached = r.get(cache_key)
            if cached:
                config = json.loads(cached)
                if config.get("is_active", False):
                    return config
                return None
        except Exception as e:
            logger.warning(f"Redis cache lookup failed: {e}")

        # Fall back to PostgreSQL
        db = SyncSessionLocal()
        try:
            config_row = (
                db.query(LLMConfiguration)
                .filter(LLMConfiguration.model_name == model_name)
                .first()
            )

            if not config_row:
                return None

            config = {
                "model_name": config_row.model_name,
                "is_active": config_row.is_active,
                "model_path": config_row.model_path,
                "max_tokens": config_row.max_tokens,
                "temperature": float(config_row.temperature) if config_row.temperature else 0.1,
                "cost_per_1k_input_tokens": (
                    float(config_row.cost_per_1k_input_tokens)
                    if config_row.cost_per_1k_input_tokens
                    else 0.0
                ),
                "cost_per_1k_output_tokens": (
                    float(config_row.cost_per_1k_output_tokens)
                    if config_row.cost_per_1k_output_tokens
                    else 0.0
                ),
            }

            # Cache in Redis for 5 minutes
            try:
                r = self._get_redis()
                r.set(cache_key, json.dumps(config), ex=300)
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

            if config.get("is_active", False):
                return config
            return None

        except Exception as e:
            logger.error(f"Failed to load LLM config from DB: {e}")
            return None
        finally:
            db.close()

    def log_usage(
        self,
        tenant_id: str,
        document_id: Optional[str],
        job_id: Optional[str],
        model_name: str,
        usage_type: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Log token usage to the token_usage_events table.

        Args:
            tenant_id: UUID string of the tenant
            document_id: UUID string of the document (optional)
            job_id: UUID string of the job (optional)
            model_name: One of: llama, finbert_sentiment, finbert_breach, gpt4, gpt35
            usage_type: One of: extraction, sentiment, breach, report_writing, hyde, chat
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
        """
        db = SyncSessionLocal()
        try:
            # Calculate cost
            config = self.get_model_config(model_name)
            cost_usd = 0.0
            if config:
                cost_input = (input_tokens / 1000) * config.get("cost_per_1k_input_tokens", 0.0)
                cost_output = (output_tokens / 1000) * config.get("cost_per_1k_output_tokens", 0.0)
                cost_usd = cost_input + cost_output

            usage = TokenUsageEvent(
                tenant_id=tenant_id,
                document_id=document_id,
                job_id=job_id,
                model_name=model_name,
                usage_type=usage_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost_usd, 6),
            )
            db.add(usage)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log token usage: {e}")
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Module-level singleton — all agents share one registry instance
# ---------------------------------------------------------------------------
llm_registry = LLMRegistry()