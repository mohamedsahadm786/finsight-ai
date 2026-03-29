"""
Authentication and authorization dependencies for FastAPI.

These are injected into endpoint functions using FastAPI's Depends() system.
They run BEFORE the endpoint code and either:
- Return the authenticated user (if valid)
- Raise HTTP 401 (if not authenticated)
- Raise HTTP 403 (if not authorized for the specific role)

Usage in an endpoint:
    @router.get("/documents")
    async def list_documents(current_user: User = Depends(get_current_user)):
        # current_user is guaranteed to be authenticated here
        ...

    @router.post("/documents/upload")
    async def upload(current_user: User = Depends(require_role(["admin", "analyst"]))):
        # current_user is guaranteed to have admin or analyst role
        ...
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import AuthenticationError, AuthorizationError
from backend.app.core.security import decode_token
from backend.app.database.redis import get_redis
from backend.app.database.session import get_db
from backend.app.models.superadmin import SuperAdmin
from backend.app.models.user import User


# ── Bearer Token Extraction ───────────────────────────────────────
# HTTPBearer automatically extracts the token from the
# "Authorization: Bearer <token>" header. If the header is missing
# or malformed, it returns 403 automatically.
security_scheme = HTTPBearer()


# ── Get Current User ──────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the JWT access token and return the authenticated user.

    This is the main security dependency. It:
    1. Extracts the Bearer token from the Authorization header
    2. Decodes and validates the JWT (checks signature, expiry)
    3. Checks Redis blacklist (was this token revoked by logout?)
    4. Loads the user from PostgreSQL
    5. Verifies the user is still active
    6. Returns the User object

    If ANY step fails → HTTP 401 Unauthorized.
    """
    token = credentials.credentials

    # Step 1: Decode the JWT
    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthenticationError("Invalid or expired token")

    # Step 2: Check if this token has been blacklisted (user logged out)
    jti = payload.get("jti")
    if jti:
        redis = await get_redis(db=3)  # DB 3 = JWT blacklist
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        await redis.aclose()
        if is_blacklisted:
            raise AuthenticationError("Token has been revoked")

    # Step 3: Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Check actor_type — superadmins use a different table
    actor_type = payload.get("actor_type", "user")
    if actor_type == "superadmin":
        raise AuthenticationError(
            "Superadmin tokens cannot be used on regular endpoints"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")

    # Step 4: Check user is still active
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


# ── Get Current Superadmin ────────────────────────────────────────

async def get_current_superadmin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> SuperAdmin:
    """
    Same as get_current_user but for superadmin endpoints.
    Only accepts tokens with actor_type="superadmin".
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthenticationError("Invalid or expired token")

    # Check blacklist
    jti = payload.get("jti")
    if jti:
        redis = await get_redis(db=3)
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        await redis.aclose()
        if is_blacklisted:
            raise AuthenticationError("Token has been revoked")

    # Must be superadmin
    actor_type = payload.get("actor_type", "user")
    if actor_type != "superadmin":
        raise AuthorizationError("Superadmin access required")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    result = await db.execute(
        select(SuperAdmin).where(SuperAdmin.id == user_id)
    )
    sa = result.scalar_one_or_none()

    if not sa:
        raise AuthenticationError("Superadmin not found")

    return sa


# ── Role-Based Access Control ─────────────────────────────────────

def require_role(allowed_roles: list[str]):
    """
    Factory function that creates a dependency requiring specific roles.

    Usage:
        @router.post("/upload")
        async def upload(user = Depends(require_role(["admin", "analyst"]))):
            ...

    This means: the user must be logged in AND have either
    the "admin" or "analyst" role. Viewers would get HTTP 403.
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"This action requires one of these roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


# ── Get Token Payload (for logout) ────────────────────────────────

async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    Decode the token and return its raw payload WITHOUT hitting the database.
    Used specifically for logout — we need the JTI to blacklist it,
    but we don't need to load the full user object.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        raise AuthenticationError("Invalid or expired token")