"""
Pydantic schemas for tenant admin endpoints.

Tenant admins manage users within their own company.
They can invite new users, change roles, and deactivate accounts.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Invite User ───────────────────────────────────────────────────

class InviteUserRequest(BaseModel):
    """
    Admin invites a new user to their company.
    The user gets created with a temporary password.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(default="analyst", pattern="^(admin|analyst|viewer)$")
    temporary_password: str = Field(..., min_length=8, max_length=128)


class InviteUserResponse(BaseModel):
    """Confirmation of the newly created user."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


# ── Update User ───────────────────────────────────────────────────

class UpdateUserRoleRequest(BaseModel):
    """Change a user's role within the company."""
    role: str = Field(..., pattern="^(admin|analyst|viewer)$")


class DeactivateUserResponse(BaseModel):
    """Confirmation that a user was deactivated."""
    id: UUID
    email: str
    is_active: bool
    message: str


# ── User Listing ──────────────────────────────────────────────────

class UserListItem(BaseModel):
    """One user in the admin's user management table."""
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """List of all users in the tenant."""
    users: list[UserListItem]
    total_count: int