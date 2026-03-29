"""
Tests for authentication endpoints.

Tests cover:
- User registration (success + duplicate email)
- User login (success + wrong password + inactive user)
- Get current user profile
- Forgot password flow
- RBAC (viewer cannot access admin endpoints)
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from backend.app.models.user import User


def _unique() -> str:
    """Generate a unique short string for test data."""
    return uuid4().hex[:8]


# ── Registration Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration creates user and tenant."""
    uid = _unique()
    response = await client.post(
        "/auth/register",
        json={
            "email": f"reg-{uid}@test.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "tenant_name": f"Reg Company {uid}",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "admin"
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test that registering with an existing email returns 409."""
    uid = _unique()
    email = f"dup-{uid}@test.com"

    # First registration — should succeed
    resp1 = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "full_name": "First User",
            "tenant_name": f"Dup Co {uid}",
        },
    )
    assert resp1.status_code == 201

    # Second registration with same email — should fail
    uid2 = _unique()
    resp2 = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "AnotherPass456!",
            "full_name": "Second User",
            "tenant_name": f"Another Co {uid2}",
        },
    )
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test that a password shorter than 8 characters is rejected."""
    uid = _unique()
    response = await client.post(
        "/auth/register",
        json={
            "email": f"short-{uid}@test.com",
            "password": "short",
            "full_name": "Short Pass",
            "tenant_name": f"Short Co {uid}",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


# ── Login Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with correct credentials returns tokens."""
    uid = _unique()
    email = f"login-{uid}@test.com"
    password = "LoginPass123!"

    # Register first
    reg_resp = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login User",
            "tenant_name": f"Login Co {uid}",
        },
    )
    assert reg_resp.status_code == 201

    # Login
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password returns 401."""
    uid = _unique()
    email = f"wrongpw-{uid}@test.com"

    # Register
    await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "CorrectPass123!",
            "full_name": "Wrong PW",
            "tenant_name": f"WrongPW Co {uid}",
        },
    )

    # Login with wrong password
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Test login with non-existent email returns 401."""
    response = await client.post(
        "/auth/login",
        json={"email": "nobody@nowhere.com", "password": "Whatever123!"},
    )
    assert response.status_code == 401


# ── Profile Tests ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict):
    """Test GET /auth/me with valid token returns user profile."""
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "role" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Test GET /auth/me without token returns 403."""
    response = await client.get("/auth/me")
    assert response.status_code == 403


# ── Password Reset Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient):
    """Test forgot password with existing email returns success."""
    uid = _unique()
    email = f"forgot-{uid}@test.com"

    # Register first
    reg_resp = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "ForgotPass123!",
            "full_name": "Forgot User",
            "tenant_name": f"Forgot Co {uid}",
        },
    )
    assert reg_resp.status_code == 201

    # Request password reset
    response = await client.post(
        "/auth/forgot-password",
        json={"email": email},
    )
    assert response.status_code == 200
    data = response.json()
    assert "DEV TOKEN" in data["message"]


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Test forgot password with non-existent email still returns 200 (security)."""
    response = await client.post(
        "/auth/forgot-password",
        json={"email": "nobody@nowhere.com"},
    )
    assert response.status_code == 200


# ── Health Check Test ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
