"""
Comprehensive security test suite for Kearney Data Platform.

Tests:
- API key management (create, list, revoke, TTL)
- RBAC and tenant scoping
- Rate limiting
- Signed URLs
- Audit logging
"""

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path

from src.security.keys import ApiKeyManager, get_key_manager
from src.security.schemas import RoleEnum, ScopeEnum, Identity, TenantContext
from src.security.rbac import check_write_access, check_read_access
from src.security.ratelimit import RateLimiter, is_rate_limited
from src.security.signing import sign_url, verify_signature, create_signed_artifact_url
from src.security.audit import AuditLogger


# Fixtures

@pytest.fixture
def temp_key_storage(tmp_path):
    """Temporary API key storage."""
    storage_path = tmp_path / "api_keys.ndjson"
    return ApiKeyManager(storage_path=str(storage_path))


@pytest.fixture
def temp_audit_log(tmp_path):
    """Temporary audit log."""
    log_path = tmp_path / "audit.log"
    return AuditLogger(log_path=str(log_path))


@pytest.fixture
def test_identity():
    """Test identity with editor role."""
    return Identity(
        id="test-user",
        type="user",
        roles=[RoleEnum.EDITOR],
        scopes={ScopeEnum.REGISTRY_WRITE, ScopeEnum.THEME_READ},
        tenants=["acme-corp"],
        source="test"
    )


# API Key Tests

class TestAPIKeys:
    """Test API key management."""

    def test_create_api_key(self, temp_key_storage):
        """Should create API key with roles and scopes."""
        api_key, plain_key = temp_key_storage.create(
            owner_id="test-user",
            roles=[RoleEnum.EDITOR],
            tenants=["acme-corp"],
            ttl_days=90
        )

        assert api_key.id is not None
        assert plain_key.startswith("kdk_")
        assert len(plain_key) > 32
        assert RoleEnum.EDITOR in api_key.roles
        assert "acme-corp" in api_key.tenants

    def test_list_api_keys(self, temp_key_storage):
        """Should list API keys with filtering."""
        # Create multiple keys
        temp_key_storage.create("user1", [RoleEnum.VIEWER], ["tenant1"])
        temp_key_storage.create("user2", [RoleEnum.EDITOR], ["tenant2"])

        # List all
        all_keys = temp_key_storage.list()
        assert len(all_keys) == 2

        # Filter by tenant
        tenant1_keys = temp_key_storage.list(tenant="tenant1")
        assert len(tenant1_keys) == 1

    def test_revoke_api_key(self, temp_key_storage):
        """Should revoke API key."""
        api_key, _ = temp_key_storage.create("user", [RoleEnum.VIEWER], ["tenant"])

        # Revoke
        success = temp_key_storage.revoke(api_key.id)
        assert success

        # Verify revoked
        revoked_key = temp_key_storage.get_by_id(api_key.id)
        assert not revoked_key.is_active()

    def test_api_key_ttl_expiry(self, temp_key_storage):
        """Should respect TTL expiration."""
        # Create key with 0 day TTL (immediately expired)
        api_key, _ = temp_key_storage.create(
            "user", [RoleEnum.VIEWER], ["tenant"], ttl_days=0
        )

        # Should be expired
        assert not api_key.is_active()

    def test_authenticate_with_key(self, temp_key_storage):
        """Should authenticate with valid API key."""
        api_key, plain_key = temp_key_storage.create("user", [RoleEnum.VIEWER], ["tenant"])

        # Authenticate
        authenticated = temp_key_storage.authenticate(plain_key)
        assert authenticated is not None
        assert authenticated.id == api_key.id

    def test_authenticate_invalid_key(self, temp_key_storage):
        """Should reject invalid API key."""
        authenticated = temp_key_storage.authenticate("kdk_invalid")
        assert authenticated is None


# RBAC Tests

class TestRBAC:
    """Test role-based access control."""

    def test_admin_has_all_access(self):
        """Admin should have access to all tenants."""
        admin = Identity(
            id="admin", type="admin", roles=[RoleEnum.ADMIN],
            scopes={ScopeEnum.REGISTRY_WRITE}, tenants=["*"], source="test"
        )

        assert admin.has_tenant_access("any-tenant")
        assert admin.has_tenant_access("another-tenant")

    def test_editor_tenant_scoping(self):
        """Editor should only access assigned tenants."""
        editor = Identity(
            id="editor", type="user", roles=[RoleEnum.EDITOR],
            scopes={ScopeEnum.REGISTRY_WRITE}, tenants=["acme-corp"], source="test"
        )

        assert editor.has_tenant_access("acme-corp")
        assert not editor.has_tenant_access("other-corp")

    def test_check_write_access(self):
        """Should check write access with scope."""
        identity = Identity(
            id="user", type="user", roles=[RoleEnum.EDITOR],
            scopes={ScopeEnum.THEME_WRITE}, tenants=["acme-corp"], source="test"
        )

        # Has write access
        assert check_write_access(identity, "acme-corp", ScopeEnum.THEME_WRITE)

        # No write access (wrong scope)
        assert not check_write_access(identity, "acme-corp", ScopeEnum.REGISTRY_WRITE)

        # No access (wrong tenant)
        assert not check_write_access(identity, "other-corp", ScopeEnum.THEME_WRITE)

    def test_viewer_read_only(self):
        """Viewer should have read-only access."""
        viewer = Identity(
            id="viewer", type="user", roles=[RoleEnum.VIEWER],
            scopes={ScopeEnum.THEME_READ}, tenants=["acme-corp"], source="test"
        )

        # Has read access
        assert check_read_access(viewer, "acme-corp", ScopeEnum.THEME_READ)

        # No write access
        assert not viewer.has_scope(ScopeEnum.THEME_WRITE)


# Rate Limiting Tests

class TestRateLimiting:
    """Test rate limiting."""

    def test_rate_limit_enforcement(self, test_identity):
        """Should enforce rate limits."""
        limiter = RateLimiter(default_requests_per_minute=5, default_burst=2)

        # First requests should succeed
        for _ in range(2):
            allowed, remaining, reset_in = limiter.check_rate_limit(
                test_identity, "acme-corp", "/api/test"
            )
            assert allowed
            assert remaining >= 0

        # Next request should be rate limited
        allowed, remaining, reset_in = limiter.check_rate_limit(
            test_identity, "acme-corp", "/api/test"
        )
        assert not allowed
        assert reset_in > 0

    def test_rate_limit_refill(self, test_identity):
        """Should refill tokens over time."""
        limiter = RateLimiter(default_requests_per_minute=60, default_burst=2)

        # Exhaust burst
        limiter.check_rate_limit(test_identity, "acme-corp", "/api/test")
        limiter.check_rate_limit(test_identity, "acme-corp", "/api/test")

        # Should be limited
        allowed, _, _ = limiter.check_rate_limit(test_identity, "acme-corp", "/api/test")
        assert not allowed

        # Wait for refill (1 token per second at 60 req/min)
        time.sleep(1.1)

        # Should have refilled
        allowed, _, _ = limiter.check_rate_limit(test_identity, "acme-corp", "/api/test")
        assert allowed

    def test_rate_limit_per_tenant(self, test_identity):
        """Should enforce separate limits per tenant."""
        limiter = RateLimiter(default_requests_per_minute=5, default_burst=2)

        # Exhaust tenant1
        limiter.check_rate_limit(test_identity, "tenant1", "/api/test")
        limiter.check_rate_limit(test_identity, "tenant1", "/api/test")
        allowed, _, _ = limiter.check_rate_limit(test_identity, "tenant1", "/api/test")
        assert not allowed

        # tenant2 should still have capacity
        allowed, _, _ = limiter.check_rate_limit(test_identity, "tenant2", "/api/test")
        assert allowed


# Signed URL Tests

class TestSignedURLs:
    """Test signed URL generation and verification."""

    def test_sign_and_verify_url(self):
        """Should sign and verify URL."""
        path = "/api/artifacts/run_123/output.csv"
        tenant = "acme-corp"
        ttl = 900  # 15 minutes

        signed_url = sign_url(path, tenant, ttl)

        # Extract components
        assert "expires=" in signed_url
        assert "signature=" in signed_url
        assert "tenant=" in signed_url

    def test_expired_url_rejected(self):
        """Should reject expired URLs."""
        path = "/api/artifacts/test.csv"
        tenant = "acme-corp"
        expires = int(time.time()) - 100  # Expired 100 seconds ago
        signature = "dummy"

        is_valid, error = verify_signature(path, tenant, expires, signature)
        assert not is_valid
        assert "expired" in error.lower()

    def test_invalid_signature_rejected(self):
        """Should reject invalid signatures."""
        path = "/api/artifacts/test.csv"
        tenant = "acme-corp"
        expires = int(time.time()) + 900
        signature = "invalid_signature"

        is_valid, error = verify_signature(path, tenant, expires, signature)
        assert not is_valid
        assert "invalid" in error.lower()

    def test_create_signed_artifact_url(self):
        """Should create complete signed artifact URL."""
        signed_url = create_signed_artifact_url(
            "datasets/run_123/output.csv",
            "acme-corp",
            ttl_minutes=15
        )

        assert "/api/artifacts/" in signed_url
        assert "signature=" in signed_url
        assert "expires=" in signed_url


# Audit Logging Tests

class TestAuditLogging:
    """Test audit logging."""

    def test_log_audit_event(self, temp_audit_log, test_identity):
        """Should log audit event."""
        temp_audit_log.log(
            actor=test_identity,
            action="create",
            resource_type="theme",
            result="success",
            tenant="acme-corp",
            resource_id="theme-123"
        )

        # Read log
        assert temp_audit_log.log_path.exists()
        content = temp_audit_log.log_path.read_text()
        assert "test-user" in content
        assert "create" in content
        assert "theme" in content

    def test_log_auth_success(self, temp_audit_log, test_identity):
        """Should log successful authentication."""
        temp_audit_log.log_auth_success(
            identity=test_identity,
            ip_address="192.168.1.1"
        )

        content = temp_audit_log.log_path.read_text()
        assert "login" in content
        assert "success" in content

    def test_log_access_denied(self, temp_audit_log, test_identity):
        """Should log access denied events."""
        temp_audit_log.log_access_denied(
            identity=test_identity,
            resource_type="theme",
            resource_id="theme-456",
            tenant="other-corp",
            reason="insufficient_permissions"
        )

        content = temp_audit_log.log_path.read_text()
        assert "denied" in content
        assert "insufficient_permissions" in content

    def test_read_recent_events(self, temp_audit_log, test_identity):
        """Should read recent audit events."""
        # Log multiple events
        for i in range(5):
            temp_audit_log.log(
                actor=test_identity,
                action="create",
                resource_type="test",
                result="success",
                resource_id=f"test-{i}"
            )

        # Read recent
        recent = temp_audit_log.read_recent(limit=3)
        assert len(recent) == 3

    def test_export_csv(self, temp_audit_log, test_identity, tmp_path):
        """Should export audit log to CSV."""
        # Log event
        temp_audit_log.log(
            actor=test_identity,
            action="create",
            resource_type="theme",
            result="success"
        )

        # Export
        csv_path = tmp_path / "audit.csv"
        temp_audit_log.export_csv(str(csv_path))

        # Verify CSV exists and has content
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "timestamp" in content
        assert "actor" in content


# Integration Tests

class TestSecurityIntegration:
    """Integration tests for security components."""

    def test_full_auth_flow(self, temp_key_storage):
        """Test complete authentication flow."""
        # Create API key
        api_key, plain_key = temp_key_storage.create(
            "user", [RoleEnum.EDITOR], ["acme-corp"],
            scopes=[ScopeEnum.REGISTRY_WRITE]
        )

        # Authenticate
        authenticated = temp_key_storage.authenticate(plain_key)
        assert authenticated is not None

        # Convert to identity
        identity = authenticated.to_identity()
        assert identity.has_role(RoleEnum.EDITOR)
        assert identity.has_scope(ScopeEnum.REGISTRY_WRITE)
        assert identity.has_tenant_access("acme-corp")

        # Check access
        assert check_write_access(identity, "acme-corp", ScopeEnum.REGISTRY_WRITE)

    def test_tenant_context_access_check(self, test_identity):
        """Test tenant context access verification."""
        # Valid tenant
        context = TenantContext(tenant="acme-corp", identity=test_identity)
        assert context.check_access()

        # Invalid tenant
        context = TenantContext(tenant="other-corp", identity=test_identity)
        assert not context.check_access()
