"""
Pydantic schemas for authentication endpoints.

These define the exact JSON structure for:
- Registration requests and responses
- Login requests and responses
- Token refresh responses
- Password reset requests
- User profile responses
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Registration ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """
    What the frontend sends when a new user registers.
    Example JSON:
    {
        "email": "analyst@adcb.ae",
        "password": "SecurePass123!",
        "full_name": "Mohammed Al Hashmi",
        "tenant_name": "ADCB Bank"
    }
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    tenant_name: str = Field(..., min_length=2, max_length=100)


class RegisterResponse(BaseModel):
    """What we send back after successful registration."""
    id: UUID
    email: str
    full_name: str
    role: str
    tenant_id: UUID
    tenant_name: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Login ─────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    What the frontend sends when a user logs in.
    Example JSON:
    {
        "email": "analyst@adcb.ae",
        "password": "SecurePass123!"
    }
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    The JWT tokens returned after login or refresh.
    access_token goes in the Authorization header for every API call.
    refresh_token goes in an httpOnly cookie.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Token Refresh ─────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    """Frontend sends the refresh token to get a new access token."""
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Only a new access token — refresh token stays the same."""
    access_token: str
    token_type: str = "bearer"


# ── Password Reset ────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """User submits their email to receive a reset link."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """User submits the token from the email + their new password."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str


# ── User Profile ──────────────────────────────────────────────────

class UserProfile(BaseModel):
    """
    The current user's profile info, returned by GET /auth/me.
    Also used when listing users in the admin panel.
    """
    id: UUID
    email: str
    full_name: str
    role: str
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Superadmin Login ──────────────────────────────────────────────

class SuperadminLoginRequest(BaseModel):
    """Separate login for platform superadmins."""
    email: EmailStr
    password: str


class SuperadminTokenResponse(BaseModel):
    """Tokens for superadmin — same structure but role is always 'superadmin'."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
