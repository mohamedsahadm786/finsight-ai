"""
Authentication service — all business logic for user auth.

This module handles:
- User registration (create tenant + first admin user)
- User login (verify credentials, issue tokens)
- Token refresh (issue new access token using refresh token)
- Logout (blacklist access token, revoke refresh token)
- Forgot password (generate reset token, send email)
- Reset password (validate token, update password)

Every function here is called by the auth API router.
No HTTP-specific logic here — just pure business logic.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.database.redis import get_redis
from backend.app.models.password_reset_token import PasswordResetToken
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.superadmin import SuperAdmin
from backend.app.models.tenant import Tenant
from backend.app.models.user import User


# ── Helper: Hash a token for safe storage ─────────────────────────

def _hash_token(token: str) -> str:
    """
    We never store raw tokens in the database. Instead, we store
    the SHA256 hash. When a user presents a token, we hash it again
    and compare against the stored hash. Same concept as passwords,
    but using SHA256 instead of bcrypt (faster, which is fine for
    single-use tokens).
    """
    return hashlib.sha256(token.encode()).hexdigest()


# ── Registration ──────────────────────────────────────────────────

async def register_user(
    email: str,
    password: str,
    full_name: str,
    tenant_name: str,
    db: AsyncSession,
) -> dict:
    """
    Register a brand new user AND create their company (tenant).

    Flow:
    1. Check if email already exists → 409 Conflict if yes
    2. Create a new tenant (company) with a URL-friendly slug
    3. Create the user as the tenant's first admin
    4. Issue access + refresh tokens
    5. Store the refresh token hash in PostgreSQL
    6. Return everything the frontend needs

    The first user who registers a company becomes its admin.
    Additional users are invited by the admin via the admin panel.
    """
    # Step 1: Check if email already taken
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictError(f"Email {email} is already registered")

    # Step 2: Create tenant (company)
    tenant_slug = tenant_name.lower().replace(" ", "-").replace(".", "")
    # Check if slug already taken
    result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
    existing_tenant = result.scalar_one_or_none()
    if existing_tenant:
        raise ConflictError(f"Company '{tenant_name}' is already registered")

    tenant = Tenant(
        id=uuid4(),
        name=tenant_name,
        slug=tenant_slug,
        status="active",
        plan_tier="free",
        monthly_token_limit=100000,  # Free tier limit
    )
    db.add(tenant)

    # Step 3: Create user as admin of this tenant
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role="admin",  # First user is always admin
        is_active=True,
    )
    db.add(user)

    # Flush to insert tenant and user into the database BEFORE
    # creating the refresh token (which has a foreign key to users)
    await db.flush()

    # Step 4: Issue tokens
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role,
    )
    refresh_token_str, refresh_jti, refresh_expires = create_refresh_token(
        user_id=str(user.id),
    )

    # Step 5: Store refresh token hash in database
    refresh_token_record = RefreshToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=_hash_token(refresh_jti),
        expires_at=refresh_expires,
    )
    db.add(refresh_token_record)

    # Commit everything in one transaction
    await db.commit()

    # Step 6: Return response data
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "access_token": access_token,
        "refresh_token": refresh_token_str,
    }


# ── Login ─────────────────────────────────────────────────────────

async def login_user(email: str, password: str, db: AsyncSession) -> dict:
    """
    Authenticate a user with email + password.

    Flow:
    1. Find user by email → 401 if not found
    2. Check if user is active → 401 if deactivated
    3. Check if tenant is active → 401 if suspended/deleted
    4. Verify password → 401 if wrong
    5. Issue new tokens
    6. Update last_login_at timestamp
    7. Store refresh token hash
    """
    # Step 1: Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationError("Invalid email or password")

    # Step 2: Check user is active
    if not user.is_active:
        raise AuthenticationError("Your account has been deactivated")

    # Step 3: Check tenant is active
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant or tenant.status != "active":
        raise AuthenticationError("Your company account is suspended or deleted")

    # Step 4: Verify password
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    # Step 5: Issue tokens
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
    refresh_token_str, refresh_jti, refresh_expires = create_refresh_token(
        user_id=str(user.id),
    )

    # Step 6: Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Step 7: Store refresh token hash
    refresh_token_record = RefreshToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=_hash_token(refresh_jti),
        expires_at=refresh_expires,
    )
    db.add(refresh_token_record)

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
    }


# ── Token Refresh ─────────────────────────────────────────────────

async def refresh_access_token(refresh_token: str, db: AsyncSession) -> dict:
    """
    Issue a new access token using a valid refresh token.

    Flow:
    1. Decode the refresh token JWT → get user_id and jti
    2. Hash the jti and look it up in the refresh_tokens table
    3. Check it hasn't been revoked
    4. Check it hasn't expired
    5. Look up the user to get current role and tenant_id
    6. Issue a new access token
    """
    # Step 1: Decode
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise AuthenticationError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload.get("sub")
    token_jti = payload.get("jti")

    if not user_id or not token_jti:
        raise AuthenticationError("Invalid refresh token")

    # Step 2: Find in database
    token_hash = _hash_token(token_jti)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise AuthenticationError("Refresh token not found")

    # Step 3: Check not revoked
    if token_record.revoked_at is not None:
        raise AuthenticationError("Refresh token has been revoked")

    # Step 4: Check not expired
    if token_record.expires_at < datetime.now(timezone.utc):
        raise AuthenticationError("Refresh token has expired")

    # Step 5: Look up user
    result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User not found or deactivated")

    # Step 6: Issue new access token
    access_token = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )

    return {"access_token": access_token}


# ── Logout ────────────────────────────────────────────────────────

async def logout_user(
    access_token_payload: dict,
    refresh_token: str | None,
    db: AsyncSession,
) -> None:
    """
    Invalidate the user's session.

    Flow:
    1. Blacklist the access token's JTI in Redis DB 3
       (so even if someone has the token, it won't work)
    2. If a refresh token was provided, revoke it in PostgreSQL
       (set revoked_at timestamp)
    """
    settings = get_settings()

    # Step 1: Blacklist access token in Redis
    jti = access_token_payload.get("jti")
    exp = access_token_payload.get("exp")

    if jti and exp:
        # Calculate how many seconds until the token expires
        # We only need to keep it in the blacklist until then
        now = datetime.now(timezone.utc)
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        remaining_seconds = int((exp_datetime - now).total_seconds())

        if remaining_seconds > 0:
            redis = await get_redis(db=3)  # DB 3 = JWT blacklist
            await redis.setex(
                f"blacklist:{jti}",
                remaining_seconds,
                "revoked",
            )
            await redis.aclose()

    # Step 2: Revoke refresh token in PostgreSQL
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            token_jti = payload.get("jti")
            if token_jti:
                token_hash = _hash_token(token_jti)
                result = await db.execute(
                    select(RefreshToken).where(
                        RefreshToken.token_hash == token_hash
                    )
                )
                token_record = result.scalar_one_or_none()
                if token_record and token_record.revoked_at is None:
                    token_record.revoked_at = datetime.now(timezone.utc)
                    await db.commit()
        except Exception:
            # If refresh token is already invalid, just ignore
            pass


# ── Forgot Password ───────────────────────────────────────────────

async def request_password_reset(email: str, db: AsyncSession) -> str | None:
    """
    Generate a password reset token and return it.

    In production, this token would be emailed to the user.
    For now, we return it so we can test the flow.

    Flow:
    1. Find user by email → return None silently if not found
       (we never reveal whether an email exists in our system — security best practice)
    2. Generate a cryptographically secure random token
    3. Store its SHA256 hash in the password_reset_tokens table with 15-min expiry
    4. Return the raw token (would be emailed in production)
    """
    # Step 1: Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Security: don't reveal whether email exists
        return None

    # Step 2: Generate secure random token
    raw_token = secrets.token_urlsafe(32)

    # Step 3: Store hash in database
    reset_record = PasswordResetToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(reset_record)
    await db.commit()

    # Step 4: Return raw token (email it in production)
    return raw_token


# ── Reset Password ────────────────────────────────────────────────

async def reset_password(token: str, new_password: str, db: AsyncSession) -> None:
    """
    Validate a password reset token and update the user's password.

    Flow:
    1. Hash the provided token and look it up in the database
    2. Check it hasn't been used already (single-use tokens)
    3. Check it hasn't expired (15-minute TTL)
    4. Update the user's password
    5. Mark the token as used
    6. Revoke ALL existing refresh tokens for this user
       (forces re-login on all devices after password change)
    """
    # Step 1: Find token
    token_hash = _hash_token(token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    )
    reset_record = result.scalar_one_or_none()

    if not reset_record:
        raise BadRequestError("Invalid or expired reset token")

    # Step 2: Check not used
    if reset_record.used_at is not None:
        raise BadRequestError("This reset token has already been used")

    # Step 3: Check not expired
    if reset_record.expires_at < datetime.now(timezone.utc):
        raise BadRequestError("Reset token has expired")

    # Step 4: Update password
    result = await db.execute(
        select(User).where(User.id == reset_record.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User")

    user.password_hash = hash_password(new_password)

    # Step 5: Mark token as used
    reset_record.used_at = datetime.now(timezone.utc)

    # Step 6: Revoke all refresh tokens for this user
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    active_tokens = result.scalars().all()
    for rt in active_tokens:
        rt.revoked_at = datetime.now(timezone.utc)

    await db.commit()


# ── Superadmin Login ──────────────────────────────────────────────

async def login_superadmin(email: str, password: str, db: AsyncSession) -> dict:
    """
    Separate login flow for platform superadmins.

    Superadmins are stored in a different table (superadmins)
    and get a different JWT with actor_type="superadmin".
    A superadmin trying to log in through the regular /auth/login
    endpoint will fail (they don't exist in the users table).
    """
    result = await db.execute(
        select(SuperAdmin).where(SuperAdmin.email == email)
    )
    sa = result.scalar_one_or_none()

    if not sa:
        raise AuthenticationError("Invalid email or password")

    if not verify_password(password, sa.password_hash):
        raise AuthenticationError("Invalid email or password")

    # Update last login
    sa.last_login_at = datetime.now(timezone.utc)  



    # Issue tokens with superadmin privileges
    access_token = create_access_token(
        user_id=str(sa.id),
        tenant_id=None,  # Superadmin is above all tenants
        role="superadmin",
        actor_type="superadmin",
    )
    refresh_token_str, refresh_jti, refresh_expires = create_refresh_token(
        user_id=str(sa.id),
    )

    # Store refresh token
    refresh_token_record = RefreshToken(
        id=uuid4(),
        user_id=sa.id,
        token_hash=_hash_token(refresh_jti),
        expires_at=refresh_expires,
    )
    db.add(refresh_token_record)

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
    }