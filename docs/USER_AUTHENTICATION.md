# User Authentication & BYOK Guide

This guide explains how user authentication, API key management, and entitlements work in the Claude Code Orchestrator.

---

## Overview

The orchestrator uses a **BYOK (Bring Your Own Key)** model where each user provides their own LLM API key. This enables:

- Per-user billing attribution
- Individual token tracking
- Model entitlements per agent role
- Project-level access control
- Future migration to enterprise SSO

---

## Authentication Modes

### 1. Development Mode (Headers)

For local development and testing, use header-based authentication:

```bash
curl -X GET http://localhost:8000/me \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com" \
  -H "X-User-Name: John Doe"
```

**Required Headers:**
- `X-User-Id`: Unique user identifier
- `X-User-Email`: User email address

**Optional Headers:**
- `X-User-Name`: Display name

### 2. Production Mode (SSO/OIDC)

For production, use Bearer tokens from your identity provider:

```bash
curl -X GET https://api.example.com/me \
  -H "Authorization: Bearer <ID_TOKEN>"
```

The orchestrator extracts user info from the JWT token claims:
- `sub` or `user_id`: User identifier
- `email`: User email
- `name`: Display name

---

## Setting Up BYOK

### 1. Authenticate and Get Your Profile

```bash
# Dev mode
curl http://localhost:8000/me \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"
```

On first request, a user profile is automatically created.

### 2. Set Your LLM API Key

```bash
curl -X POST http://localhost:8000/users/user123/key \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-ant-api03-xxxxx",
    "provider": "anthropic"
  }'
```

**Supported Providers:**
- `anthropic` - Claude API
- `openai` - OpenAI API (future)

### 3. Verify Your Key is Set

```bash
curl http://localhost:8000/me \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"
```

Response will show masked key: `"llm_api_key": "***xxxx"`

---

## Model Entitlements

Admins can configure which models each user can use per agent role:

```bash
# Admin sets entitlements for a user
curl -X POST http://localhost:8000/users/user123/entitlements \
  -H "X-User-Id: admin" \
  -H "X-User-Email: admin@example.com" \
  -H "Content-Type: application/json" \
  -d '{
    "architect": ["claude-3-opus-20240229", "claude-sonnet-4-20250514"],
    "developer": ["claude-sonnet-4-20250514"],
    "qa": ["claude-sonnet-4-20250514", "claude-3-haiku-20240307"]
  }'
```

When an agent runs:
1. Check user's entitlements for that agent role
2. Select model from allowed list
3. If no entitlements set, use user's `default_model`

---

## Project Access Control

### Grant Access

```bash
curl -X POST http://localhost:8000/users/user123/projects/proj-abc123/grant \
  -H "X-User-Id: admin" \
  -H "X-User-Email: admin@example.com"
```

### Revoke Access

```bash
curl -X DELETE http://localhost:8000/users/user123/projects/proj-abc123/revoke \
  -H "X-User-Id: admin" \
  -H "X-User-Email: admin@example.com"
```

### Access Rules

| Role | Access |
|------|--------|
| Admin | All projects |
| Developer | Granted projects only |
| Viewer | Granted projects (read-only) |

---

## Token Usage Tracking

Every LLM request is tracked with:

- `user_id` - Who made the request
- `project_id` - Which project
- `agent_role` - Which agent (architect, developer, etc.)
- `model` - Which model was used
- `input_tokens` - Tokens in prompt
- `output_tokens` - Tokens in response
- `cost_usd` - Estimated cost

### View Your Usage

```bash
curl http://localhost:8000/me \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"
```

Response includes:
```json
{
  "token_usage": {
    "total_input_tokens": 50000,
    "total_output_tokens": 25000,
    "total_requests": 100,
    "last_reset": "2024-01-01T00:00:00Z"
  }
}
```

---

## How the Orchestrator Chooses Models

When an agent executes:

1. **Check entitlements**: Look up user's allowed models for this agent role
2. **Select model**: Pick first available model from entitlements
3. **Fall back**: If no entitlements, use user's `default_model`
4. **Get API key**: Use user's BYOK key for the request
5. **Track usage**: Record tokens against user + project

### Example Flow

```
User calls: POST /rsg/{project_id}/ready/start

1. Auth middleware extracts user from headers/token
2. Check user has project access
3. Start Ready stage (PLANNING + ARCHITECTURE)
4. For each agent:
   a. Get user's entitlements for "architect"
   b. Select allowed model (e.g., claude-3-opus)
   c. Make API call with user's BYOK key
   d. Track token usage
5. Return results
```

---

## API Reference

### User Profile Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/me` | Get current user profile | User |
| GET | `/users` | List all users | Admin |
| GET | `/users/{id}` | Get user by ID | Self/Admin |
| POST | `/users/{id}/key` | Set BYOK API key | Self/Admin |
| POST | `/users/{id}/entitlements` | Set model entitlements | Admin |
| POST | `/users/{id}/projects/{pid}/grant` | Grant project access | Admin |
| DELETE | `/users/{id}/projects/{pid}/revoke` | Revoke project access | Admin |

### UserProfile Schema

```json
{
  "user_id": "string",
  "email": "string",
  "name": "string | null",
  "role": "admin | developer | viewer",
  "llm_api_key": "string | null (masked)",
  "llm_provider": "anthropic | openai",
  "default_model": "claude-sonnet-4-20250514",
  "model_entitlements": {
    "agent_role": ["model1", "model2"]
  },
  "token_limits": {
    "daily_input": 100000
  },
  "token_usage": {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_requests": 0
  },
  "projects": ["proj-123", "proj-456"],
  "created_at": "datetime",
  "last_login": "datetime"
}
```

---

## Security Considerations

### API Key Storage

- Keys stored in user profile files: `~/.orchestrator/users/{id}.json`
- In production, encrypt at rest using AWS KMS or similar
- Never logged or returned in full (always masked)

### Authentication Best Practices

1. **Development**: Use unique X-User-Id per developer
2. **Staging**: Use test accounts with limited keys
3. **Production**: Always use SSO/OIDC tokens

### Token Verification (Production)

Replace the stub verifier with proper JWKS validation:

```python
# In auth/dependencies.py
from authlib.jose import jwt
from authlib.jose.errors import JoseError

async def verify_token(token: str) -> dict:
    # Fetch JWKS from your identity provider
    jwks = await fetch_jwks("https://your-idp/.well-known/jwks.json")

    try:
        claims = jwt.decode(token, jwks)
        claims.validate()
        return claims
    except JoseError as e:
        raise HTTPException(401, f"Invalid token: {e}")
```

---

## Future: Enterprise Pool Keys

When ready to migrate from BYOK to enterprise-managed keys:

1. Add `enterprise_key_pool` to configuration
2. Modify agent executor to check for enterprise key first
3. Fall back to BYOK if enterprise key not available
4. Update billing attribution to department/cost-center

The current architecture supports this transition with minimal changes.

---

## Troubleshooting

### 401 Unauthorized

**Cause**: Missing authentication headers/token

**Fix**: Include X-User-Id and X-User-Email headers (dev) or Authorization header (prod)

### 403 Forbidden

**Cause**: Insufficient permissions

**Fix**:
- Check user role (admin required for some endpoints)
- Verify project access has been granted

### LLM API Errors

**Cause**: Invalid or missing BYOK key

**Fix**:
1. Check key is set: `GET /me`
2. Update key: `POST /users/{id}/key`
3. Verify key is valid with provider

### No Model Entitlements

**Cause**: User not entitled to any models for agent role

**Fix**: Admin sets entitlements or user sets default_model

---

## Related Documentation

- [ORCHESTRATOR_QUICK_REFERENCE.md](../ORCHESTRATOR_QUICK_REFERENCE.md) - Quick reference
- [DEPLOYMENT_APP_RUNNER.md](../DEPLOYMENT_APP_RUNNER.md) - Deployment guide
- [orchestrator-v2-architecture.md](orchestrator-v2-architecture.md) - Architecture overview
