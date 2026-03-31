"""
Nightly aggregation script — reads token_usage_events and writes
pre-aggregated monthly totals into monthly_usage_summaries.

Run manually:
    python scripts/aggregate_monthly_usage.py

On EC2 this runs nightly via Celery Beat (configured in Phase 14).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.app.config import get_settings
from backend.app.models.token_usage_event import TokenUsageEvent
from backend.app.models.monthly_usage_summary import MonthlyUsageSummary
from backend.app.models.tenant import Tenant


async def aggregate_monthly_usage():
    settings = get_settings()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        print("Starting monthly usage aggregation...")

        # Get all tenants
        result = await db.execute(select(Tenant))
        tenants = result.scalars().all()
        print(f"Found {len(tenants)} tenants to process")

        for tenant in tenants:
            # Get all usage events for this tenant
            result = await db.execute(
                select(TokenUsageEvent).where(
                    TokenUsageEvent.tenant_id == tenant.id
                )
            )
            events = result.scalars().all()

            if not events:
                continue

            # Group events by year_month
            monthly_data: dict = {}

            for event in events:
                # Extract year-month string from created_at
                ym = event.created_at.strftime("%Y-%m")

                if ym not in monthly_data:
                    monthly_data[ym] = {
                        "total_tokens": 0,
                        "llama_tokens": 0,
                        "finbert_tokens": 0,
                        "gpt4_tokens": 0,
                        "gpt35_tokens": 0,
                        "total_cost_usd": 0.0,
                        "documents_processed": set(),
                    }

                total_tokens = (event.input_tokens or 0) + (event.output_tokens or 0)
                monthly_data[ym]["total_tokens"] += total_tokens
                monthly_data[ym]["total_cost_usd"] += float(event.cost_usd or 0)

                # Attribute tokens to the right model bucket
                model = str(event.model_name)
                if "llama" in model:
                    monthly_data[ym]["llama_tokens"] += total_tokens
                elif "finbert" in model:
                    monthly_data[ym]["finbert_tokens"] += total_tokens
                elif model == "gpt4":
                    monthly_data[ym]["gpt4_tokens"] += total_tokens
                elif model == "gpt35":
                    monthly_data[ym]["gpt35_tokens"] += total_tokens

                # Track unique documents processed
                if event.document_id:
                    monthly_data[ym]["documents_processed"].add(
                        str(event.document_id)
                    )

            # Upsert monthly summaries for this tenant
            for ym, data in monthly_data.items():
                # Check if row already exists
                result = await db.execute(
                    select(MonthlyUsageSummary).where(
                        MonthlyUsageSummary.tenant_id == tenant.id,
                        MonthlyUsageSummary.year_month == ym,
                    )
                )
                existing = result.scalar_one_or_none()

                doc_count = len(data["documents_processed"])

                if existing:
                    # Update existing row
                    existing.total_tokens = data["total_tokens"]
                    existing.llama_tokens = data["llama_tokens"]
                    existing.finbert_tokens = data["finbert_tokens"]
                    existing.gpt4_tokens = data["gpt4_tokens"]
                    existing.gpt35_tokens = data["gpt35_tokens"]
                    existing.total_cost_usd = data["total_cost_usd"]
                    existing.documents_processed = doc_count
                    existing.updated_at = datetime.now(timezone.utc)
                    print(f"  ↷ Updated {tenant.name} / {ym}")
                else:
                    # Insert new row
                    summary = MonthlyUsageSummary(
                        id=uuid4(),
                        tenant_id=tenant.id,
                        year_month=ym,
                        total_tokens=data["total_tokens"],
                        llama_tokens=data["llama_tokens"],
                        finbert_tokens=data["finbert_tokens"],
                        gpt4_tokens=data["gpt4_tokens"],
                        gpt35_tokens=data["gpt35_tokens"],
                        total_cost_usd=data["total_cost_usd"],
                        documents_processed=doc_count,
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(summary)
                    print(f"  ✓ Inserted {tenant.name} / {ym}")

        await db.commit()
        print()
        print("✓ Aggregation complete.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(aggregate_monthly_usage())