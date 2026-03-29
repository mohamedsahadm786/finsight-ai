"""
Authentication API endpoints.

All auth-related HTTP endpoints:
- POST /auth/register     — Create new user + company
- POST /auth/login        — Log in with email + password
- POST /auth/logout       — Invalidate tokens
- POST /auth/refresh      — Get new access token
- GET  /auth/me           — Get current user profile
- POST /auth/forgot-password  — Request password reset email
- POST /auth/reset-password   — Reset password with token
- POST /auth/superadmin/login — Separate superadmin login
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.rate_limit import limiter
from backend.app.dependencies.auth import (
    get_current_user,
    get_token_payload,
)
from backend.app.dependencies.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SuperadminLoginRequest,
    SuperadminTokenResponse,
    TokenResponse,
    UserProfile,
)
from backend.app.services.auth_service import (
    login_superadmin,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    request_password_reset,
    reset_password,
)

# Create the router — all endpoints here will be prefixed with /auth
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ──────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and create their company.

    The first user automatically becomes the company admin.
    Returns JWT tokens so the user is immediately logged in.
    """
    result = await register_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        tenant_name=request.tenant_name,
        db=db,
    )
    return RegisterResponse(**result, token_type="bearer")


# ── Login ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Log in with email and password.

    Returns:
    - access_token (15-min TTL) — sent in Authorization header
    - refresh_token (7-day TTL) — stored in httpOnly cookie
    """
    result = await login_user(
        email=body.email,
        password=body.password,
        db=db,
    )
    return TokenResponse(**result, token_type="bearer")


# ── Logout ────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(
    token_payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = None,
):
    """
    Log out — blacklist the access token and revoke the refresh token.

    After this, the access token cannot be used even if someone has it.
    The user must log in again to get new tokens.
    """
    await logout_user(
        access_token_payload=token_payload,
        refresh_token=refresh_token,
        db=db,
    )
    return MessageResponse(message="Successfully logged out")


# ── Refresh Token ─────────────────────────────────────────────────

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Get a new access token using a valid refresh token.

    Call this when the access token expires (after 15 minutes).
    The frontend should call this automatically before the token expires.
    """
    result = await refresh_access_token(
        refresh_token=request.refresh_token,
        db=db,
    )
    return AccessTokenResponse(**result, token_type="bearer")


# ── Get Current User Profile ──────────────────────────────────────

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the currently logged-in user's profile.

    This endpoint proves the JWT token is valid and returns
    the user's information. The frontend calls this on page load
    to check if the user is still logged in.
    """
    return UserProfile.model_validate(current_user)


# ── Forgot Password ──────────────────────────────────────────────

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset token.

    In production, this sends an email with a reset link.
    For security, we always return the same message whether
    the email exists or not (prevents email enumeration attacks).
    """
    token = await request_password_reset(email=request.email, db=db)

    # In production, we would send an email here with the token.
    # For development/testing, the token is returned in the response
    # (remove this in production!)
    if token:
        return MessageResponse(
            message=f"Password reset link sent. DEV TOKEN: {token}"
        )

    # Same message even if email not found (security)
    return MessageResponse(message="If the email exists, a reset link has been sent")


# ── Reset Password ────────────────────────────────────────────────

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using the token from the forgot-password email.

    After this:
    - Password is updated
    - The reset token is marked as used (single-use)
    - All existing sessions are invalidated (must log in again)
    """
    await reset_password(
        token=request.token,
        new_password=request.new_password,
        db=db,
    )
    return MessageResponse(message="Password reset successfully. Please log in again.")


# ── Superadmin Login ──────────────────────────────────────────────

@router.post("/superadmin/login", response_model=SuperadminTokenResponse)
async def superadmin_login(
    request: SuperadminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Separate login endpoint for platform superadmins.

    Superadmins are stored in a separate table and get tokens
    with actor_type="superadmin". Regular users cannot use this
    endpoint, and superadmins cannot use the regular /auth/login.
    """
    result = await login_superadmin(
        email=request.email,
        password=request.password,
        db=db,
    )
    return SuperadminTokenResponse(**result, token_type="bearer")
