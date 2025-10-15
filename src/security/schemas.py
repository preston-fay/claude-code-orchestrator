"""
Security schemas for authentication and authorization.

Pydantic models for:
- Identity: User/service identity with roles and scopes
- ApiKey: API key metadata and validation
- Role: RBAC role definition
- TenantContext: Tenant isolation context
- AuditEvent: Audit trail event
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


class RoleEnum(str, Enum):
    """RBAC role types."""
    ADMIN = "admin"          # Full access, all tenants
    EDITOR = "editor"        # Read/write for assigned tenants
    VIEWER = "viewer"        # Read-only for assigned tenants
    SERVICE = "service"      # Machine-to-machine, specific scopes


class ScopeEnum(str, Enum):
    """Permission scopes."""
    # Registry
    REGISTRY_READ = "registry:read"
    REGISTRY_WRITE = "registry:write"

    # Theme
    THEME_READ = "theme:read"
    THEME_WRITE = "theme:write"

    # Datasets
    DATASET_READ = "dataset:read"
    DATASET_WRITE = "dataset:write"

    # Artifacts
    ARTIFACT_READ = "artifact:read"
    ARTIFACT_WRITE = "artifact:write"

    # Admin
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"

    # Security
    SECURITY_MANAGE = "security:manage"


class Identity(BaseModel):
    """
    User or service identity.

    Resolved from API key or OIDC token.
    """
    id: str = Field(..., description="Unique identity ID")
    type: str = Field(..., description="Identity type: user, service, admin")
    roles: List[RoleEnum] = Field(default_factory=list, description="Assigned roles")
    scopes: Set[ScopeEnum] = Field(default_factory=set, description="Granted scopes")
    tenants: List[str] = Field(default_factory=list, description="Accessible tenant slugs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Source info
    source: str = Field(..., description="Auth source: api_key, oidc")
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def has_role(self, *roles: RoleEnum) -> bool:
        """Check if identity has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_scope(self, *scopes: ScopeEnum) -> bool:
        """Check if identity has any of the specified scopes."""
        return any(scope in self.scopes for scope in scopes)

    def has_tenant_access(self, tenant: str) -> bool:
        """Check if identity has access to tenant."""
        # Admin has access to all tenants
        if RoleEnum.ADMIN in self.roles:
            return True
        # Wildcard tenant
        if "*" in self.tenants:
            return True
        # Specific tenant
        return tenant in self.tenants

    def is_expired(self) -> bool:
        """Check if identity is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class ApiKey(BaseModel):
    """
    API key metadata.

    Keys are hashed before storage.
    """
    id: str = Field(..., description="Unique key ID")
    key_hash: str = Field(..., description="Bcrypt hash of key")
    prefix: str = Field(..., description="Key prefix for identification (first 8 chars)")

    # Owner
    owner_id: str = Field(..., description="Owner identity ID")
    owner_type: str = Field(default="user", description="Owner type: user, service")

    # Authorization
    roles: List[RoleEnum] = Field(default_factory=list)
    scopes: Set[ScopeEnum] = Field(default_factory=set)
    tenants: List[str] = Field(default_factory=list, description="Tenant slugs or ['*'] for all")

    # Lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    # Metadata
    name: Optional[str] = Field(None, description="Human-readable key name")
    description: Optional[str] = None

    def is_active(self) -> bool:
        """Check if key is active (not revoked, not expired)."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.utcnow() > self.expires_at:
            return False
        return True

    def to_identity(self) -> Identity:
        """Convert API key to Identity."""
        return Identity(
            id=self.owner_id,
            type=self.owner_type,
            roles=self.roles,
            scopes=self.scopes,
            tenants=self.tenants,
            source="api_key",
            issued_at=self.created_at,
            expires_at=self.expires_at,
            metadata={"key_id": self.id, "key_name": self.name}
        )


class Role(BaseModel):
    """
    RBAC role definition.
    """
    name: RoleEnum
    description: str
    default_scopes: Set[ScopeEnum] = Field(default_factory=set)

    @classmethod
    def get_default_roles(cls) -> Dict[RoleEnum, "Role"]:
        """Get default role definitions."""
        return {
            RoleEnum.ADMIN: cls(
                name=RoleEnum.ADMIN,
                description="Full access to all resources and tenants",
                default_scopes={
                    ScopeEnum.REGISTRY_READ, ScopeEnum.REGISTRY_WRITE,
                    ScopeEnum.THEME_READ, ScopeEnum.THEME_WRITE,
                    ScopeEnum.DATASET_READ, ScopeEnum.DATASET_WRITE,
                    ScopeEnum.ARTIFACT_READ, ScopeEnum.ARTIFACT_WRITE,
                    ScopeEnum.ADMIN_READ, ScopeEnum.ADMIN_WRITE,
                    ScopeEnum.SECURITY_MANAGE,
                }
            ),
            RoleEnum.EDITOR: cls(
                name=RoleEnum.EDITOR,
                description="Read/write access to assigned tenants",
                default_scopes={
                    ScopeEnum.REGISTRY_READ, ScopeEnum.REGISTRY_WRITE,
                    ScopeEnum.THEME_READ, ScopeEnum.THEME_WRITE,
                    ScopeEnum.DATASET_READ, ScopeEnum.DATASET_WRITE,
                    ScopeEnum.ARTIFACT_READ,
                }
            ),
            RoleEnum.VIEWER: cls(
                name=RoleEnum.VIEWER,
                description="Read-only access to assigned tenants",
                default_scopes={
                    ScopeEnum.REGISTRY_READ,
                    ScopeEnum.THEME_READ,
                    ScopeEnum.DATASET_READ,
                    ScopeEnum.ARTIFACT_READ,
                }
            ),
            RoleEnum.SERVICE: cls(
                name=RoleEnum.SERVICE,
                description="Machine-to-machine with specific scopes",
                default_scopes=set()  # Scopes assigned per service
            ),
        }


class TenantContext(BaseModel):
    """
    Tenant isolation context.

    Attached to requests to enforce tenant boundaries.
    """
    tenant: str = Field(..., description="Tenant slug")
    identity: Identity = Field(..., description="Authenticated identity")

    def check_access(self) -> bool:
        """Verify identity has access to this tenant."""
        return self.identity.has_tenant_access(self.tenant)


class AuditEvent(BaseModel):
    """
    Audit trail event.

    Written to append-only log.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Actor
    actor_id: str = Field(..., description="Identity ID")
    actor_type: str = Field(..., description="user, service, admin")

    # Context
    tenant: Optional[str] = None

    # Action
    action: str = Field(..., description="Action performed: login, create, update, delete, access")
    resource_type: str = Field(..., description="Resource type: api_key, theme, model, dataset, artifact")
    resource_id: Optional[str] = None

    # Result
    result: str = Field(..., description="Result: success, failure, denied")
    result_details: Optional[str] = None

    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    trace_id: Optional[str] = None

    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_ndjson_line(self) -> str:
        """Convert to NDJSON line for audit log."""
        import json
        return json.dumps({
            "ts": self.timestamp.isoformat(),
            "actor": self.actor_id,
            "actor_type": self.actor_type,
            "tenant": self.tenant,
            "action": self.action,
            "resource": self.resource_type,
            "resource_id": self.resource_id,
            "result": self.result,
            "result_details": self.result_details,
            "ip": self.ip_address,
            "trace_id": self.trace_id,
            **self.metadata
        })


class SecurityConfig(BaseModel):
    """Security configuration."""

    # API keys
    api_key_min_length: int = 32
    api_key_default_ttl_days: int = 90

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

    # OIDC
    oidc_enabled: bool = False
    oidc_issuer: Optional[str] = None
    oidc_audience: Optional[str] = None
    oidc_jwks_url: Optional[str] = None

    # Signed URLs
    signed_url_default_ttl_minutes: int = 15
    signed_url_secret: Optional[str] = None

    # Audit
    audit_log_path: str = ".claude/logs/audit.log"
    audit_log_retention_days: int = 90
