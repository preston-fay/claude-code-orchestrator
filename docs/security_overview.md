# Security Overview

Complete security guide for the Kearney Data Platform.

## Quickstart (5 minutes)

```bash
# 1. Create an API key
orchestrator security apikey create \
  --tenant acme-corp \
  --roles editor \
  --ttl 90

# 2. Use the key
curl -H "X-API-Key: kdk_..." \
     -H "X-Tenant: acme-corp" \
     http://localhost:8000/api/registry/models

# 3. Check audit log
tail -f .claude/logs/audit.log
```

---

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization (RBAC)](#authorization-rbac)
3. [Tenant Model](#tenant-model)
4. [Rate Limiting](#rate-limiting)
5. [Signed URLs](#signed-urls)
6. [Security Headers](#security-headers)
7. [Audit Logging](#audit-logging)
8. [How-Tos](#how-tos)

---

## Authentication

The platform supports two authentication modes:

### 1. API Keys (Default)

**Format:** `kdk_<64-hex-characters>`

**Usage:**
```bash
curl -H "X-API-Key: kdk_a1b2c3..." http://localhost:8000/api/...
```

**Create API key:**
```bash
orchestrator security apikey create \
  --tenant acme-corp \
  --roles editor \
  --scopes registry:write,theme:write \
  --ttl 90 \
  --name "Production API Key"
```

**Key properties:**
- Hashed with bcrypt before storage
- TTL-based expiration (default: 90 days)
- Revocable at any time
- Scoped to specific tenants and roles

**List keys:**
```bash
orchestrator security apikey list
orchestrator security apikey list --tenant acme-corp
orchestrator security apikey list --all  # Include revoked/expired
```

**Revoke key:**
```bash
orchestrator security apikey revoke --id <key-id>
```

### 2. OIDC/OAuth2 (Optional)

**Enable OIDC:**

Set environment variables:
```bash
export OIDC_ISSUER="https://login.example.com"
export OIDC_AUDIENCE="kearney-platform"
export OIDC_JWKS_URL="https://login.example.com/.well-known/jwks.json"
```

Or configure in secrets (AWS SSM/Secrets Manager):
```bash
aws ssm put-parameter \
  --name /kearney-platform/prod/oidc_issuer \
  --value "https://login.example.com" \
  --type SecureString
```

**Usage:**
```bash
curl -H "Authorization: Bearer <jwt-token>" http://localhost:8000/api/...
```

**JWT Claims:**
- `sub`: User ID
- `roles`: Array of role strings
- `scope`: Space-separated scopes
- `tenants`: Array of tenant slugs
- `exp`, `nbf`, `aud`, `iss`: Standard validation

---

## Authorization (RBAC)

### Roles

| Role | Description | Default Scopes |
|------|-------------|----------------|
| **admin** | Full access to all resources and tenants | All scopes |
| **editor** | Read/write access to assigned tenants | registry:*, theme:*, dataset:*, artifact:read |
| **viewer** | Read-only access to assigned tenants | registry:read, theme:read, dataset:read, artifact:read |
| **service** | Machine-to-machine with specific scopes | None (assigned per service) |

### Scopes

| Scope | Description |
|-------|-------------|
| `registry:read` | Read model registry |
| `registry:write` | Write to model registry |
| `theme:read` | Read theme configurations |
| `theme:write` | Write theme configurations |
| `dataset:read` | Read datasets |
| `dataset:write` | Register datasets |
| `artifact:read` | Download artifacts |
| `artifact:write` | Upload artifacts |
| `admin:read` | View admin dashboard |
| `admin:write` | Modify admin settings |
| `security:manage` | Manage API keys and tenants |

### Route Protection

**Protect a route:**
```python
from fastapi import Depends
from src.security.context import require_auth
from src.security.rbac import require_scope
from src.security.schemas import Identity, ScopeEnum

@app.post("/api/registry/models")
async def create_model(
    identity: Identity = Depends(require_scope(ScopeEnum.REGISTRY_WRITE))
):
    # Identity has been verified with registry:write scope
    ...
```

**Require specific roles:**
```python
from src.security.rbac import require_roles
from src.security.schemas import RoleEnum

@app.get("/admin/users")
async def list_users(
    identity: Identity = Depends(require_roles(RoleEnum.ADMIN))
):
    # Only admins can access
    ...
```

**Check tenant access:**
```python
from src.security.context import get_tenant_context
from src.security.schemas import TenantContext

@app.post("/api/theme/apply")
async def apply_theme(
    context: TenantContext = Depends(get_tenant_context)
):
    # context.tenant and context.identity verified
    # context.check_access() already called
    ...
```

---

## Tenant Model

### Concept

Tenants provide multi-client isolation. Each API key is scoped to one or more tenants.

### Configuration

**File:** `configs/security.yaml`

```yaml
tenants:
  - slug: acme-corp
    name: "Acme Corporation"
    enabled: true

  - slug: globex
    name: "Globex Industries"
    enabled: true
```

### Management

**List tenants:**
```bash
orchestrator security tenant list
```

**Add tenant:**
```bash
orchestrator security tenant add \
  --slug new-corp \
  --name "New Corporation"
```

**Remove tenant:**
```bash
orchestrator security tenant remove --slug old-corp
```

### Wildcard Access

Admin keys can use `*` for all tenants:
```bash
orchestrator security apikey create \
  --tenant '*' \
  --roles admin
```

### Request Headers

Specify tenant in requests:
```bash
curl -H "X-Tenant: acme-corp" \
     -H "X-API-Key: kdk_..." \
     http://localhost:8000/api/...
```

If omitted, uses first tenant in API key's tenant list.

---

## Rate Limiting

### Default Limits

- **60 requests per minute** per user per route
- **Burst allowance:** 10 requests

### Configuration

**File:** `configs/security.yaml`

```yaml
rate_limits:
  enabled: true

  default:
    requests_per_minute: 60
    burst: 10

  routes:
    "/api/registry/models":
      requests_per_minute: 120
      burst: 20

    "/api/theme/apply":
      requests_per_minute: 30
      burst: 5
```

### Response Headers

When rate limited, response includes:

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705345200
Retry-After: 45
```

### Tuning

**Increase limits for specific route:**
```yaml
routes:
  "/api/high-throughput":
    requests_per_minute: 300
    burst: 50
```

**Disable rate limiting (not recommended):**
```yaml
rate_limits:
  enabled: false
```

---

## Signed URLs

### Purpose

Time-limited, tamper-proof URLs for artifact downloads.

### Generate Signed URL

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/sign" \
  -H "X-API-Key: kdk_..." \
  -H "X-Tenant: acme-corp" \
  -d "path=/api/artifacts/datasets/run_123/output.csv" \
  -d "ttl_minutes=15"
```

**Response:**
```json
{
  "signed_url": "/api/artifacts/datasets/run_123/output.csv?tenant=acme-corp&expires=1705345200&signature=abc123...",
  "expires_in_seconds": 900,
  "path": "/api/artifacts/datasets/run_123/output.csv",
  "tenant": "acme-corp"
}
```

**Via Python:**
```python
from src.security.signing import create_signed_artifact_url

signed_url = create_signed_artifact_url(
    artifact_path="datasets/run_123/output.csv",
    tenant="acme-corp",
    ttl_minutes=15,
    ip_address="192.168.1.100"  # Optional IP binding
)
```

### Use Signed URL

```bash
# Works before expiration
curl "$SIGNED_URL" -o output.csv

# Fails after expiration (15 minutes)
curl "$SIGNED_URL"
# {"error": "Signed URL has expired"}
```

### IP Binding

Bind signature to specific IP (optional):
```python
signed_url = create_signed_artifact_url(
    artifact_path="sensitive.csv",
    tenant="acme-corp",
    ttl_minutes=5,
    ip_address="203.0.113.42"  # Only this IP can use URL
)
```

### Configuration

**File:** `configs/security.yaml`

```yaml
signed_urls:
  enabled: true
  default_ttl_minutes: 15
  max_ttl_minutes: 1440  # 24 hours
```

**Signing secret:**
```bash
export SIGNED_URL_SECRET="your-secret-key-change-me"
```

---

## Security Headers

### Headers Set

All responses include:

- **Content-Security-Policy:** Restricts resource loading
- **Strict-Transport-Security:** Enforces HTTPS
- **X-Content-Type-Options:** Prevents MIME sniffing
- **X-Frame-Options:** Prevents clickjacking
- **Referrer-Policy:** Controls referrer information
- **Permissions-Policy:** Restricts browser features

### CSP Configuration

**File:** `configs/security.yaml`

```yaml
csp:
  default:
    default-src: "'self'"
    script-src:
      - "'self'"
      - "'unsafe-inline'"  # For HTMX
      - "https://cdn.jsdelivr.net"
    img-src:
      - "'self'"
      - "data:"
      - "https://api.mapbox.com"  # Tile servers
    connect-src:
      - "'self'"
      - "https://api.mapbox.com"
```

### Custom CSP for Admin

Admin routes use more permissive CSP for development tools:

```yaml
csp:
  admin:
    script-src:
      - "'self'"
      - "'unsafe-inline'"
      - "'unsafe-eval'"  # For SQL console
```

---

## Audit Logging

### Log Format

**File:** `.claude/logs/audit.log` (NDJSON)

**Fields:**
```json
{
  "ts": "2025-01-15T10:30:00.123Z",
  "actor": "user-123",
  "actor_type": "user",
  "tenant": "acme-corp",
  "action": "create",
  "resource": "theme",
  "resource_id": "theme-456",
  "result": "success",
  "result_details": null,
  "ip": "192.168.1.1",
  "trace_id": "a1b2c3d4"
}
```

### Events Logged

- **Authentication:** `login` (success/failure)
- **API Keys:** `create`, `revoke`
- **Themes:** `create`, `update`, `delete`
- **Registry:** `model_register`, `dataset_register`
- **Artifacts:** `download`, `signed_url_issue`
- **Access:** `access_denied`

### Query Audit Log

**Read recent events:**
```python
from src.security.audit import get_audit_logger

audit_logger = get_audit_logger()
recent = audit_logger.read_recent(limit=100)

for event in recent:
    print(f"{event['ts']}: {event['actor']} {event['action']} {event['resource']}")
```

**Export to CSV:**
```python
audit_logger.export_csv("audit_report.csv", days=30)
```

**Filter with jq:**
```bash
# All failed logins
jq 'select(.action=="login" and .result=="failure")' .claude/logs/audit.log

# Access denied events for tenant
jq 'select(.tenant=="acme-corp" and .result=="denied")' .claude/logs/audit.log

# Events by specific user
jq 'select(.actor=="user-123")' .claude/logs/audit.log
```

### Retention

**Configuration:**
```yaml
audit:
  enabled: true
  log_path: ".claude/logs/audit.log"
  retention_days: 90
```

**Rotate logs:**
```bash
# Archive old logs
gzip .claude/logs/audit.log
mv .claude/logs/audit.log.gz .claude/logs/archive/audit_$(date +%Y%m).log.gz
touch .claude/logs/audit.log
```

---

## How-Tos

### Enable OIDC in AWS Amplify

1. **Set environment variables** in Amplify console:
   ```
   OIDC_ISSUER=https://login.example.com
   OIDC_AUDIENCE=kearney-platform
   OIDC_JWKS_URL=https://login.example.com/.well-known/jwks.json
   ```

2. **Redeploy** application

3. **Verify** OIDC enabled:
   ```bash
   curl http://your-app.amplifyapp.com/api/config
   # Should show: {"oidc_enabled": true}
   ```

### Rotate API Keys

**Best practice:** Rotate keys every 90 days

```bash
# 1. Create new key
orchestrator security apikey create \
  --tenant acme-corp \
  --roles editor \
  --ttl 90 \
  --name "Production Key (2025-Q2)"

# 2. Update application with new key
export API_KEY="kdk_new_key..."

# 3. Test application
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/health

# 4. Revoke old key
orchestrator security apikey revoke --id <old-key-id>
```

### Protect a New Route

**Add route protection:**

```python
from fastapi import Depends
from src.security.context import require_auth
from src.security.rbac import require_scope
from src.security.schemas import Identity, ScopeEnum, TenantContext
from src.security.audit import get_audit_logger

@app.post("/api/my-resource")
async def create_resource(
    data: dict,
    identity: Identity = Depends(require_auth),
    context: TenantContext = Depends(get_tenant_context)
):
    # Check scope
    if not identity.has_scope(ScopeEnum.MY_RESOURCE_WRITE):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Create resource
    resource = create_my_resource(data, context.tenant)

    # Log audit event
    audit_logger = get_audit_logger()
    audit_logger.log(
        actor=identity,
        action="create",
        resource_type="my_resource",
        resource_id=resource.id,
        tenant=context.tenant,
        result="success"
    )

    return {"id": resource.id}
```

### Monitor Security Events

**Failed authentication attempts:**
```bash
jq 'select(.action=="login" and .result=="failure")' .claude/logs/audit.log | \
  jq -s 'group_by(.ip) | map({ip: .[0].ip, count: length}) | sort_by(.count) | reverse'
```

**Access denied by tenant:**
```bash
jq 'select(.result=="denied")' .claude/logs/audit.log | \
  jq -s 'group_by(.tenant) | map({tenant: .[0].tenant, count: length})'
```

**API key usage:**
```bash
jq 'select(.action=="login" and .result=="success" and .source=="api_key")' .claude/logs/audit.log | \
  jq -s 'length'
```

---

## Security Checklist

### Production Deployment

- [ ] Rotate default API keys
- [ ] Set `SIGNED_URL_SECRET` environment variable
- [ ] Enable HTTPS (Strict-Transport-Security header)
- [ ] Configure CSP for your domain
- [ ] Set up log rotation for audit logs
- [ ] Review rate limits for production traffic
- [ ] Test OIDC integration (if using)
- [ ] Document emergency access procedures
- [ ] Set up monitoring for failed auth attempts
- [ ] Configure backup for API key storage

### Regular Maintenance

- [ ] Rotate API keys every 90 days
- [ ] Review audit logs monthly
- [ ] Update tenant list as clients change
- [ ] Monitor rate limit violations
- [ ] Check for expired/revoked keys
- [ ] Test disaster recovery procedures

---

## Troubleshooting

### "Invalid API key" Error

**Check:**
1. Key format: `kdk_<64-hex>`
2. Key not revoked: `orchestrator security apikey list --all`
3. Key not expired: Check `expires_at`
4. Correct header: `X-API-Key: kdk_...`

### "Access denied" with Valid Key

**Check:**
1. Tenant access: Key must include tenant in `tenants` list
2. Scope: Key must have required scope (e.g., `registry:write`)
3. Role: Route may require specific role (e.g., `admin`)
4. Header: Ensure `X-Tenant` header matches

### Rate Limit Exceeded

**Solutions:**
1. Wait for reset: Check `Retry-After` header
2. Increase limits: Edit `configs/security.yaml`
3. Use burst allowance strategically
4. Distribute requests over time

### OIDC Not Working

**Check:**
1. Environment variables set: `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`
2. JWKS URL accessible: `curl $OIDC_JWKS_URL`
3. Token claims: Must include `sub`, `exp`, `aud`, `iss`
4. Custom claims: `roles`, `tenants`, `scope`

---

## References

- [Ops Overview](ops_overview.md) - Logging, tracing, metrics
- [Performance Strategy](perf_strategy.md) - Tuning and optimization
- [API Documentation](api_docs.md) - Full API reference

---

**Last Updated:** January 2025
**Version:** 1.0.0
