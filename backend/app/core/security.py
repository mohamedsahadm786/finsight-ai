"""
Security utilities for password hashing and JWT token management.

This module provides:
- Password hashing using bcrypt (one-way encryption)
- JWT access token creation (short-lived, 15 minutes)
- JWT refresh token creation (long-lived, 7 days)
- Token decoding and verification
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.app.config import get_settings

# ── Password Hashing ──────────────────────────────────────────────
# CryptContext handles all the complexity of bcrypt hashing.
# "schemes=bcrypt" means we use the bcrypt algorithm.
# "deprecated=auto" means if we ever switch algorithms, old hashes
# still verify correctly.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Takes a plain text password like "mypassword123" and returns
    a bcrypt hash like "$2b$12$LJ3m4ys..." that is safe to store
    in the database. This is ONE-WAY — you cannot get the original
    password back from the hash.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain text password against a stored hash.
    Returns True if they match, False otherwise.
    Used during login to check if the user typed the right password.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Token Creation ────────────────────────────────────────────



def create_access_token(
    user_id: str,
    tenant_id: str | None = None,
    role: str = "analyst",
    actor_type: str = "user",
) -> str:
    """
    Creates a short-lived JWT access token (15 minutes by default).

    The token contains:
    - sub: the user's UUID (who this token belongs to)
    - tenant_id: which company they belong to (for multi-tenancy)
    - role: what they can do (admin/analyst/viewer)
    - actor_type: "user" or "superadmin"
    - jti: a unique ID for THIS specific token (used for blacklisting on logout)
    - exp: when this token expires

    This token is sent with every API request in the Authorization header.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "role": role,
        "actor_type": actor_type,
        "jti": str(uuid4()),  # Unique token ID — for blacklisting
        "iat": now,            # Issued at
        "exp": expire,         # Expires at
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def create_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    """
    Creates a long-lived refresh token (7 days by default).

    Returns a tuple of:
    - token: the actual JWT string to send to the user
    - token_jti: the unique ID of this token (we store its SHA256 hash in DB)
    - expires_at: when this token expires (stored in DB for cleanup)

    The refresh token is stored in an httpOnly cookie on the frontend.
    When the access token expires, the frontend uses this to get a new one
    WITHOUT the user having to log in again.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_jti = str(uuid4())

    payload = {
        "sub": str(user_id),
        "jti": token_jti,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, token_jti, expire


# ── JWT Token Verification ────────────────────────────────────────

def decode_token(token: str) -> dict:
    """
    Decodes a JWT token and returns the payload (the data inside it).

    If the token is expired, tampered with, or invalid in any way,
    this raises a JWTError which the calling code must handle.

    The calling code (in auth dependencies) will also check the Redis
    blacklist to see if this token was revoked by a logout.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise JWTError("Token is invalid or expired")