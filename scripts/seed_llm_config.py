"""
Seeds the llm_configurations table with default model configurations.

Run this ONCE after the database is set up:
    python scripts/seed_llm_config.py

On EC2:
    docker exec finsight-api python scripts/seed_llm_config.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.app.config import get_settings
from backend.app.models.llm_configuration import LLMConfiguration


# Default configurations for all 5 models used in the pipeline
DEFAULT_CONFIGS = [
    {
        "model_name": "llama",
        "is_active": True,
        "model_path": "models/llama-finance-adapter",
        "max_tokens": 512,
        "temperature": 0.1,
        "cost_per_1k_input_tokens": 0.0,   # Self-hosted — no cost
        "cost_per_1k_output_tokens": 0.0,
    },
    {
        "model_name": "finbert_sentiment",
        "is_active": True,
        "model_path": "models/finbert-sentiment",
        "max_tokens": 512,
        "temperature": 0.0,
        "cost_per_1k_input_tokens": 0.0,
        "cost_per_1k_output_tokens": 0.0,
    },
    {
        "model_name": "finbert_breach",
        "is_active": True,
        "model_path": "models/finbert-breach",
        "max_tokens": 512,
        "temperature": 0.0,
        "cost_per_1k_input_tokens": 0.0,
        "cost_per_1k_output_tokens": 0.0,
    },
    {
        "model_name": "gpt4",
        "is_active": True,
        "model_path": None,   # Hosted by OpenAI
        "max_tokens": 1000,
        "temperature": 0.3,
        "cost_per_1k_input_tokens": 0.03,
        "cost_per_1k_output_tokens": 0.06,
    },
    {
        "model_name": "gpt35",
        "is_active": True,
        "model_path": None,
        "max_tokens": 500,
        "temperature": 0.7,
        "cost_per_1k_input_tokens": 0.0005,
        "cost_per_1k_output_tokens": 0.0015,
    },
]


async def seed_llm_config():
    settings = get_settings()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        inserted = 0
        skipped = 0

        for config_data in DEFAULT_CONFIGS:
            # Check if this model already has a config row
            result = await db.execute(
                select(LLMConfiguration).where(
                    LLMConfiguration.model_name == config_data["model_name"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ↷ Skipping '{config_data['model_name']}' — already exists")
                skipped += 1
                continue

            config = LLMConfiguration(
                id=uuid4(),
                model_name=config_data["model_name"],
                is_active=config_data["is_active"],
                model_path=config_data["model_path"],
                max_tokens=config_data["max_tokens"],
                temperature=config_data["temperature"],
                cost_per_1k_input_tokens=config_data["cost_per_1k_input_tokens"],
                cost_per_1k_output_tokens=config_data["cost_per_1k_output_tokens"],
                updated_at=datetime.now(timezone.utc),
            )
            db.add(config)
            inserted += 1
            print(f"  ✓ Inserted config for '{config_data['model_name']}'")

        await db.commit()
        print()
        print(f"Done. Inserted: {inserted}, Skipped: {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_llm_config())