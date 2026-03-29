"""
Multi-tenancy middleware and helpers.

In a multi-tenant SaaS platform, every company's data must be
completely isolated. A user from ADCB Bank must NEVER see data
from Emirates NBD, even accidentally.

This module provides helpers to extract the tenant_id from the
current user's JWT token, which is then used to filter every
database query.

Usage in endpoints:
    @router.get("/documents")
    async def list_docs(current_user: User = Depends(get_current_user)):
        tenant_id = current_user.tenant_id
        # Every query includes: .where(Document.tenant_id == tenant_id)
"""

from uuid import UUID

from backend.app.models.user import User


def get_tenant_id(current_user: User) -> UUID:
    """
    Extract the tenant_id from the authenticated user.

    This is a simple helper, but having it as a dedicated function
    makes the code more readable and makes it clear that tenant
    isolation is intentional, not accidental.

    Every database query for tenant-scoped data MUST use this:
        query.where(Model.tenant_id == get_tenant_id(current_user))
    """
    return current_user.tenant_id