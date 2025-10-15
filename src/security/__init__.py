"""
Security module for Kearney Data Platform.

Provides:
- Authentication (API keys, OIDC)
- Authorization (RBAC, tenant scoping)
- Rate limiting
- Signed URLs
- Audit logging
- Security headers
"""

from .schemas import Identity, ApiKey, Role, TenantContext, AuditEvent
from .context import get_identity, get_tenant_context, require_auth

__all__ = [
    "Identity",
    "ApiKey",
    "Role",
    "TenantContext",
    "AuditEvent",
    "get_identity",
    "get_tenant_context",
    "require_auth",
]
