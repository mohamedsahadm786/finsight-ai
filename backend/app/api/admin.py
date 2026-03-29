"""
Tenant Admin API endpoints.

These endpoints are for company administrators to manage their own users.
A tenant admin can:
- List all users in their company
- Invite (create) a new user
- Change a user's role
- Deactivate a user

All operations are strictly scoped to the admin's own tenant.
An admin from ADCB Bank can NEVER see or manage users from Emirates NBD.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from backend.app.core.security import hash_password
from backend.app.dependencies.auth import require_role
from backend.app.dependencies.database import get_db
from backend.app.middleware.tenant import get_tenant_id
from backend.app.models.user import User
from backend.app.schemas.admin import (
    DeactivateUserResponse,
    InviteUserRequest,
    InviteUserResponse,
    UpdateUserRoleRequest,
    UserListItem,
    UserListResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin — User Management"])


# ── List Users ────────────────────────────────────────────────────

@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users in the admin's company.

    Only admin role can access this endpoint.
    Results include active AND deactivated users.
    """
    tenant_id = get_tenant_id(current_user)

    # Count total
    count_result = await db.execute(
        select(func.count(User.id)).where(User.tenant_id == tenant_id)
    )
    total_count = count_result.scalar()

    # Fetch all users
    result = await db.execute(
        select(User)
        .where(User.tenant_id == tenant_id)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return UserListResponse(
        users=[UserListItem.model_validate(u) for u in users],
        total_count=total_count,
    )


# ── Invite (Create) User ─────────────────────────────────────────

@router.post("/users/invite", response_model=InviteUserResponse, status_code=201)
async def invite_user(
    request: InviteUserRequest,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite (create) a new user in the admin's company.

    The admin provides:
    - email: must be unique within the company
    - full_name: the user's display name
    - role: admin, analyst, or viewer
    - temporary_password: the user's initial password

    In production, the user would receive an email with
    their temporary credentials. For now, the admin sets
    the password directly.
    """
    tenant_id = get_tenant_id(current_user)

    # Check if email already exists in this tenant
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.tenant_id == tenant_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ConflictError(f"Email {request.email} already exists in your company")

    # Also check if email exists in ANY tenant (global uniqueness)
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_global = result.scalar_one_or_none()
    if existing_global:
        raise ConflictError(f"Email {request.email} is already registered")

    # Create the user
    new_user = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email=request.email,
        password_hash=hash_password(request.temporary_password),
        full_name=request.full_name,
        role=request.role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()

    return InviteUserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )


# ── Update User Role ─────────────────────────────────────────────

@router.patch("/users/{user_id}/role", response_model=UserListItem)
async def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Change a user's role within the company.

    Admins cannot change their own role (prevents accidentally
    removing the last admin from a company).
    """
    tenant_id = get_tenant_id(current_user)

    # Cannot change own role
    if user_id == current_user.id:
        raise BadRequestError("You cannot change your own role")

    # Find the user (must be in same tenant)
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", str(user_id))

    user.role = request.role
    await db.commit()

    return UserListItem.model_validate(user)


# ── Deactivate User ──────────────────────────────────────────────

@router.patch("/users/{user_id}/deactivate", response_model=DeactivateUserResponse)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a user account.

    Deactivated users cannot log in. Their data is preserved.
    Admins cannot deactivate themselves.
    """
    tenant_id = get_tenant_id(current_user)

    # Cannot deactivate yourself
    if user_id == current_user.id:
        raise BadRequestError("You cannot deactivate your own account")

    # Find the user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", str(user_id))

    if not user.is_active:
        raise BadRequestError("User is already deactivated")

    user.is_active = False
    await db.commit()

    return DeactivateUserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        message=f"User {user.email} has been deactivated",
    )


# ── Reactivate User ──────────────────────────────────────────────

@router.patch("/users/{user_id}/reactivate", response_model=UserListItem)
async def reactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
):
    """
    Reactivate a previously deactivated user account.
    """
    tenant_id = get_tenant_id(current_user)

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", str(user_id))

    if user.is_active:
        raise BadRequestError("User is already active")

    user.is_active = True
    await db.commit()

    return UserListItem.model_validate(user)