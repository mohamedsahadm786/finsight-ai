"""
Pytest configuration and fixtures for FinSight AI tests.

This file provides:
- An async test client (httpx) that talks to the FastAPI app
- Helper fixtures for creating test users, tenants, and tokens
"""

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import get_settings
from backend.app.core.security import create_access_token, hash_password
from backend.app.database.session import Base, get_db
from backend.app.main import app
from backend.app.models.tenant import Tenant
from backend.app.models.user import User


# ── Settings ──────────────────────────────────────────────────────
settings = get_settings()

# ── Shared engine for all tests ───────────────────────────────────
test_engine = create_async_engine(settings.DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ── Event Loop ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Test Database Session ─────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session():
    """
    Provide a database session for each test.
    Does NOT use a wrapping transaction — allows commits to work
    naturally inside API endpoints.
    """
    async with TestSessionFactory() as session:
        yield session


# ── Test Client ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """
    Provide an httpx AsyncClient that talks to the FastAPI app.
    Each endpoint call gets its own fresh database session
    (just like in production).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Helper Fixtures ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant (company) for use in tests."""
    tenant = Tenant(
        id=uuid4(),
        name="Test Company",
        slug=f"test-company-{uuid4().hex[:8]}",
        status="active",
        plan_tier="free",
        monthly_token_limit=100000,
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user (admin role) for use in tests."""
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email=f"testuser-{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("TestPassword123!"),
        full_name="Test User",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_viewer(db_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test viewer user (viewer role) for RBAC tests."""
    user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email=f"viewer-{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("ViewerPass123!"),
        full_name="Test Viewer",
        role="viewer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create Authorization headers with a valid access token."""
    token = create_access_token(
        user_id=str(test_user.id),
        tenant_id=str(test_user.tenant_id),
        role=test_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def viewer_headers(test_viewer: User) -> dict:
    """Create Authorization headers for a viewer user (RBAC tests)."""
    token = create_access_token(
        user_id=str(test_viewer.id),
        tenant_id=str(test_viewer.tenant_id),
        role=test_viewer.role,
    )
    return {"Authorization": f"Bearer {token}"}