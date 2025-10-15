"""
RBAC (Role-Based Access Control) and tenant scoping.

Provides:
- require_roles: Decorator to require specific roles
- require_scope: Decorator to require specific scopes
- require_tenant_access: Dependency to verify tenant access
"""

from fastapi import Depends, HTTPException
from typing import Annotated, List

from .schemas import Identity, TenantContext, RoleEnum, ScopeEnum
from .context import require_auth, get_tenant_context


def require_roles(*roles: RoleEnum):
    """
    Decorator to require specific roles.

    Usage:
        @app.get("/admin/users")
        async def list_users(identity: Annotated[Identity, Depends(require_roles(RoleEnum.ADMIN))]):
            ...

    Args:
        *roles: Required roles (any of)

    Returns:
        Dependency that enforces role requirement
    """
    async def check_roles(identity: Annotated[Identity, Depends(require_auth)]) -> Identity:
        if not identity.has_role(*roles):
            role_names = [role.value for role in roles]
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Requires one of roles: {', '.join(role_names)}",
                    "required_roles": role_names,
                    "user_roles": [role.value for role in identity.roles]
                }
            )
        return identity

    return check_roles


def require_scope(*scopes: ScopeEnum):
    """
    Decorator to require specific scopes.

    Usage:
        @app.post("/api/registry/models")
        async def create_model(identity: Annotated[Identity, Depends(require_scope(ScopeEnum.REGISTRY_WRITE))]):
            ...

    Args:
        *scopes: Required scopes (any of)

    Returns:
        Dependency that enforces scope requirement
    """
    async def check_scopes(identity: Annotated[Identity, Depends(require_auth)]) -> Identity:
        if not identity.has_scope(*scopes):
            scope_names = [scope.value for scope in scopes]
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Requires one of scopes: {', '.join(scope_names)}",
                    "required_scopes": scope_names,
                    "user_scopes": [scope.value for scope in identity.scopes]
                }
            )
        return identity

    return check_scopes


async def require_tenant_access(
    context: Annotated[TenantContext, Depends(get_tenant_context)]
) -> TenantContext:
    """
    Require tenant access (already checked in get_tenant_context).

    This is a pass-through dependency for clarity.

    Args:
        context: Tenant context

    Returns:
        TenantContext
    """
    return context


def require_roles_and_scopes(*roles: RoleEnum, scopes: List[ScopeEnum]):
    """
    Decorator to require both roles AND scopes.

    Usage:
        @app.post("/api/admin/theme")
        async def admin_theme(
            identity: Annotated[Identity, Depends(require_roles_and_scopes(
                RoleEnum.ADMIN,
                scopes=[ScopeEnum.THEME_WRITE]
            ))]
        ):
            ...

    Args:
        *roles: Required roles (any of)
        scopes: Required scopes (any of)

    Returns:
        Dependency that enforces role and scope requirements
    """
    async def check_roles_and_scopes(identity: Annotated[Identity, Depends(require_auth)]) -> Identity:
        # Check roles
        if not identity.has_role(*roles):
            role_names = [role.value for role in roles]
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Requires one of roles: {', '.join(role_names)}",
                    "required_roles": role_names,
                }
            )

        # Check scopes
        if not identity.has_scope(*scopes):
            scope_names = [scope.value for scope in scopes]
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Requires one of scopes: {', '.join(scope_names)}",
                    "required_scopes": scope_names,
                }
            )

        return identity

    return check_roles_and_scopes


def check_write_access(identity: Identity, tenant: str, scope: ScopeEnum) -> bool:
    """
    Check if identity has write access to resource in tenant.

    Args:
        identity: User identity
        tenant: Target tenant
        scope: Required scope

    Returns:
        True if access granted
    """
    # Check tenant access
    if not identity.has_tenant_access(tenant):
        return False

    # Check scope
    if not identity.has_scope(scope):
        return False

    return True


def check_read_access(identity: Identity, tenant: str, scope: ScopeEnum) -> bool:
    """
    Check if identity has read access to resource in tenant.

    Args:
        identity: User identity
        tenant: Target tenant
        scope: Required scope

    Returns:
        True if access granted
    """
    # Check tenant access
    if not identity.has_tenant_access(tenant):
        return False

    # Check scope
    if not identity.has_scope(scope):
        return False

    return True


class PermissionChecker:
    """
    Helper class for complex permission checks.
    """

    def __init__(self, identity: Identity):
        self.identity = identity

    def can_read(self, tenant: str, scope: ScopeEnum) -> bool:
        """Check if can read resource."""
        return check_read_access(self.identity, tenant, scope)

    def can_write(self, tenant: str, scope: ScopeEnum) -> bool:
        """Check if can write resource."""
        return check_write_access(self.identity, tenant, scope)

    def can_manage_security(self) -> bool:
        """Check if can manage security settings."""
        return (
            self.identity.has_role(RoleEnum.ADMIN) and
            self.identity.has_scope(ScopeEnum.SECURITY_MANAGE)
        )

    def can_access_admin(self) -> bool:
        """Check if can access admin interface."""
        return self.identity.has_role(RoleEnum.ADMIN, RoleEnum.EDITOR)

    def can_manage_tenant(self, tenant: str) -> bool:
        """Check if can manage tenant (admin or editor with access)."""
        if not self.identity.has_tenant_access(tenant):
            return False

        return self.identity.has_role(RoleEnum.ADMIN, RoleEnum.EDITOR)

    def get_accessible_tenants(self) -> List[str]:
        """Get list of accessible tenants."""
        if self.identity.has_role(RoleEnum.ADMIN) or "*" in self.identity.tenants:
            # Admin or wildcard access - return all tenants
            # In practice, would load from configs/security.yaml
            return ["*"]

        return self.identity.tenants
