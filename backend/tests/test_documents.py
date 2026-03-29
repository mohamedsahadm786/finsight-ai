"""
Tests for document and RBAC endpoints.

Tests cover:
- Document listing (authenticated)
- Document listing (unauthenticated — rejected)
- RBAC: viewer cannot upload documents
- RBAC: admin can list users
- RBAC: viewer cannot list users
"""

import pytest
from httpx import AsyncClient


# ── Document Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_documents_authenticated(client: AsyncClient, auth_headers: dict):
    """Test listing documents with valid token returns empty list."""
    response = await client.get("/documents/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["documents"] == []
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_list_documents_no_token(client: AsyncClient):
    """Test listing documents without token returns 403."""
    response = await client.get("/documents/")
    assert response.status_code == 403


# ── Report Tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_reports_authenticated(client: AsyncClient, auth_headers: dict):
    """Test listing reports with valid token returns empty list."""
    response = await client.get("/reports/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["reports"] == []
    assert data["total_count"] == 0


# ── RBAC Tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_viewer_cannot_upload(client: AsyncClient, viewer_headers: dict):
    """Test that a viewer role cannot upload documents (403)."""
    # Create a minimal fake PDF content
    files = {"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")}
    response = await client.post(
        "/documents/upload?document_type=other",
        headers=viewer_headers,
        files=files,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_list_users(client: AsyncClient, auth_headers: dict):
    """Test that an admin can list users in their company."""
    response = await client.get("/admin/users", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert data["total_count"] >= 1  # At least the admin user


@pytest.mark.asyncio
async def test_viewer_cannot_list_users(client: AsyncClient, viewer_headers: dict):
    """Test that a viewer cannot access admin user management (403)."""
    response = await client.get("/admin/users", headers=viewer_headers)
    assert response.status_code == 403