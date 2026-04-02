"""
One-time script to create the platform superadmin account.

Run this ONCE after the database is set up:
    python scripts/create_superadmin.py

On EC2, run it inside the container:
    docker exec finsight-api python scripts/create_superadmin.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.app.config import get_settings
from backend.app.core.security import hash_password
from backend.app.models.superadmin import SuperAdmin


SUPERADMIN_EMAIL = "mohamedsahadm786@gmail.com"
SUPERADMIN_PASSWORD = "Sahad@123"


async def create_superadmin():
    settings = get_settings()

    # Connect to database
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # Check if superadmin already exists
        result = await db.execute(
            select(SuperAdmin).where(SuperAdmin.email == SUPERADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ Superadmin already exists: {SUPERADMIN_EMAIL}")
            await engine.dispose()
            return

        # Create superadmin
        sa = SuperAdmin(
            id=uuid4(),
            email=SUPERADMIN_EMAIL,
            password_hash=hash_password(SUPERADMIN_PASSWORD),
        )
        db.add(sa)
        await db.commit()

        print("✓ Superadmin created successfully!")
        print(f"  Email:    {SUPERADMIN_EMAIL}")
        print(f"  Password: {SUPERADMIN_PASSWORD}")
        print()
        print("  ⚠️  Change this password immediately in production!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_superadmin())