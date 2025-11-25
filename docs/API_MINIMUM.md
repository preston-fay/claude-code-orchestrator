# Orchestrator Runs API Reference

**Version:** 1.0
**Base URL:** `https://api.your-domain.com` (or `http://localhost:8000` for local development)
**Endpoint Prefix:** `/runs`

## Overview

The Orchestrator Runs API provides programmatic access to the Claude Code Orchestrator's workflow execution system. It enables you to create, manage, and monitor multi-phase orchestrator runs through RESTful endpoints.

### Key Features

- **Run Management**: Create and track orchestrator workflow runs
- **Phase Execution**: Advance through workflow phases (Planning → Architecture → Data → Development → QA → Documentation)
- **Artifact Tracking**: List and access artifacts generated during each phase
- **Metrics & Governance**: Monitor token usage, costs, and governance compliance
- **User Context**: Per-user run isolation with authentication headers

### Use Cases

- **Interactive Dashboards**: Build UIs for monitoring orchestrator workflows
- **CI/CD Integration**: Trigger orchestrator runs from deployment pipelines
- **Analytics**: Track performance, costs, and quality metrics across projects
- **Automation**: Script multi-run workflows with custom profiles

---

## Authentication

All endpoints require user authentication via HTTP headers:

**Required Headers:**
```http
X-User-Id: user123
X-User-Email: user@example.com
```

**Error Response (401):**
```json
{
  "detail": "Missing user authentication headers (X-User-Id, X-User-Email)"
}
```

---

## Endpoints

### 1. Create Orchestrator Run

**POST** `/runs`

Creates a new orchestrator run with the specified profile and optional intake requirements.

#### Request Body

```json
{
  "profile": "analytics_forecast_app",
  "intake": "Build a demand forecasting app with Prophet",
  "project_name": "Forecast Project Q4",
  "metadata": {
    "client": "acme-corp",
    "priority": "high"
  }
}
```

**Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile` | `string` | ✅ | Profile name (e.g., `analytics_forecast_app`, `data_pipeline`, `ml_model`) |
| `intake` | `string` | ❌ | Optional intake text or requirements |
| `project_name` | `string` | ❌ | Optional project name |
| `metadata` | `object` | ❌ | Additional metadata (key-value pairs) |

#### Response (201 Created)

```json
{
  "run_id": "abc123",
  "profile": "analytics_forecast_app",
  "project_name": "Forecast Project Q4",
  "current_phase": "planning",
  "status": "running",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Response Schema:** `RunSummary`
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Unique run identifier |
| `profile` | `string` | Profile name used |
| `project_name` | `string \| null` | Project name (if provided) |
| `current_phase` | `string` | Current phase (`planning`, `architecture`, `data`, `development`, `qa`, `documentation`) |
| `status` | `string` | Run status (`running`, `completed`, `failed`, `paused`) |
| `created_at` | `datetime` | ISO 8601 timestamp of creation |
| `updated_at` | `datetime` | ISO 8601 timestamp of last update |

#### Error Responses

- **401 Unauthorized**: Missing authentication headers
- **500 Internal Server Error**: Run creation failed

---

### 2. Get Run Details

**GET** `/runs/{run_id}`

Returns comprehensive information about a run, including all phases, status, and metadata.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | `string` | Run identifier (e.g., `abc123`) |

#### Response (200 OK)

```json
{
  "run_id": "abc123",
  "profile": "analytics_forecast_app",
  "intake": "Build a demand forecasting app with Prophet",
  "project_name": "Forecast Project Q4",
  "current_phase": "architecture",
  "status": "running",
  "phases": [
    {
      "phase": "planning",
      "status": "completed",
      "started_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:45:00Z",
      "duration_seconds": 900.0,
      "agent_ids": ["planning-agent-001"],
      "artifacts_count": 3
    },
    {
      "phase": "architecture",
      "status": "in_progress",
      "started_at": "2025-01-15T10:45:00Z",
      "completed_at": null,
      "duration_seconds": null,
      "agent_ids": ["architect-agent-002"],
      "artifacts_count": 1
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:50:00Z",
  "completed_at": null,
  "total_duration_seconds": 1200.0,
  "metadata": {
    "client": "acme-corp",
    "priority": "high"
  }
}
```

**Response Schema:** `RunDetail`
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Unique run identifier |
| `profile` | `string` | Profile name |
| `intake` | `string \| null` | Intake requirements |
| `project_name` | `string \| null` | Project name |
| `current_phase` | `string` | Current phase |
| `status` | `string` | Run status |
| `phases` | `PhaseInfo[]` | Array of phase information |
| `created_at` | `datetime` | ISO 8601 creation timestamp |
| `updated_at` | `datetime` | ISO 8601 last update timestamp |
| `completed_at` | `datetime \| null` | ISO 8601 completion timestamp (null if in progress) |
| `total_duration_seconds` | `float \| null` | Total duration in seconds |
| `metadata` | `object` | Additional metadata |

**PhaseInfo Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `phase` | `string` | Phase name |
| `status` | `string` | `pending`, `in_progress`, `completed`, `failed` |
| `started_at` | `datetime \| null` | ISO 8601 start timestamp |
| `completed_at` | `datetime \| null` | ISO 8601 completion timestamp |
| `duration_seconds` | `float \| null` | Duration in seconds |
| `agent_ids` | `string[]` | List of agent IDs executed |
| `artifacts_count` | `int` | Number of artifacts generated |

#### Error Responses

- **404 Not Found**: Run not found
- **500 Internal Server Error**: Failed to fetch run details

---

### 3. Advance Run to Next Phase

**POST** `/runs/{run_id}/next`

Executes the current phase and advances the run to the next phase in the workflow.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | `string` | Run identifier (e.g., `abc123`) |

#### Request Body (Optional)

```json
{
  "skip_validation": false
}
```

**Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skip_validation` | `boolean` | ❌ | Skip governance validation (default: `false`) |

#### Response (200 OK)

```json
{
  "run_id": "abc123",
  "previous_phase": "planning",
  "current_phase": "architecture",
  "status": "running",
  "message": "Advanced from planning to architecture"
}
```

**Response Schema:** `AdvanceRunResponse`
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Run identifier |
| `previous_phase` | `string` | Previous phase name |
| `current_phase` | `string` | Current phase name |
| `status` | `string` | Current run status |
| `message` | `string` | Human-readable status message |

#### Error Responses

- **404 Not Found**: Run not found
- **500 Internal Server Error**: Failed to advance run

---

### 4. List Run Artifacts

**GET** `/runs/{run_id}/artifacts`

Returns all artifacts generated during the run, grouped by phase.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | `string` | Run identifier (e.g., `abc123`) |

#### Response (200 OK)

```json
{
  "run_id": "abc123",
  "artifacts_by_phase": {
    "planning": [
      {
        "artifact_id": "planning_PRD.md",
        "phase": "planning",
        "path": "/workspace/abc123/artifacts/planning/PRD.md",
        "name": "PRD.md",
        "description": "Product Requirements Document",
        "artifact_type": "prd",
        "size_bytes": 4096,
        "created_at": "2025-01-15T10:40:00Z"
      },
      {
        "artifact_id": "planning_intake.yaml",
        "phase": "planning",
        "path": "/workspace/abc123/artifacts/planning/intake.yaml",
        "name": "intake.yaml",
        "description": "Intake specification",
        "artifact_type": "intake",
        "size_bytes": 1024,
        "created_at": "2025-01-15T10:35:00Z"
      }
    ],
    "architecture": [
      {
        "artifact_id": "architecture_system_design.md",
        "phase": "architecture",
        "path": "/workspace/abc123/artifacts/architecture/system_design.md",
        "name": "system_design.md",
        "description": "System architecture design",
        "artifact_type": "architecture",
        "size_bytes": 8192,
        "created_at": "2025-01-15T10:55:00Z"
      }
    ]
  },
  "total_count": 3
}
```

**Response Schema:** `ArtifactsResponse`
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Run identifier |
| `artifacts_by_phase` | `object` | Artifacts grouped by phase name |
| `total_count` | `int` | Total number of artifacts |

**ArtifactSummary Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | `string` | Unique artifact identifier |
| `phase` | `string` | Phase that generated this artifact |
| `path` | `string` | Full file path to artifact |
| `name` | `string` | Artifact filename |
| `description` | `string \| null` | Human-readable description |
| `artifact_type` | `string` | Type (`prd`, `architecture`, `code`, `test`, `documentation`, etc.) |
| `size_bytes` | `int` | File size in bytes |
| `created_at` | `datetime` | ISO 8601 creation timestamp |

#### Error Responses

- **404 Not Found**: Run not found
- **500 Internal Server Error**: Failed to fetch artifacts

---

### 5. Get Run Metrics

**GET** `/runs/{run_id}/metrics`

Returns comprehensive metrics including performance, governance, token usage, and costs.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | `string` | Run identifier (e.g., `abc123`) |

#### Response (200 OK)

```json
{
  "run_id": "abc123",
  "total_duration_seconds": 3600.0,
  "total_token_usage": {
    "input": 10000,
    "output": 5000
  },
  "total_cost_usd": 0.45,
  "phases_metrics": [
    {
      "phase": "planning",
      "duration_seconds": 900.0,
      "token_usage": {
        "input": 2000,
        "output": 1000
      },
      "cost_usd": 0.09,
      "agents_executed": ["planning-agent-001"],
      "artifacts_generated": 3,
      "governance_passed": true,
      "governance_warnings": []
    },
    {
      "phase": "architecture",
      "duration_seconds": 1200.0,
      "token_usage": {
        "input": 3000,
        "output": 1500
      },
      "cost_usd": 0.14,
      "agents_executed": ["architect-agent-002"],
      "artifacts_generated": 2,
      "governance_passed": true,
      "governance_warnings": ["Minor code style issues detected"]
    }
  ],
  "governance_score": 0.95,
  "hygiene_score": 0.92,
  "artifacts_total": 5,
  "errors_count": 0
}
```

**Response Schema:** `MetricsSummary`
| Field | Type | Description |
|-------|------|-------------|
| `run_id` | `string` | Run identifier |
| `total_duration_seconds` | `float` | Total run duration in seconds |
| `total_token_usage` | `object` | Total tokens (`input`, `output`) |
| `total_cost_usd` | `float` | Total cost in USD |
| `phases_metrics` | `PhaseMetrics[]` | Per-phase metrics |
| `governance_score` | `float` | Governance compliance score (0.0 to 1.0) |
| `hygiene_score` | `float` | Code hygiene score (0.0 to 1.0) |
| `artifacts_total` | `int` | Total number of artifacts |
| `errors_count` | `int` | Total number of errors encountered |

**PhaseMetrics Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `phase` | `string` | Phase name |
| `duration_seconds` | `float` | Phase duration in seconds |
| `token_usage` | `object` | Tokens used (`input`, `output`) |
| `cost_usd` | `float` | Phase cost in USD |
| `agents_executed` | `string[]` | List of agent IDs executed |
| `artifacts_generated` | `int` | Number of artifacts generated |
| `governance_passed` | `boolean` | Whether governance checks passed |
| `governance_warnings` | `string[]` | List of governance warnings |

#### Error Responses

- **404 Not Found**: Run not found
- **500 Internal Server Error**: Failed to fetch metrics

---

## Error Handling

All endpoints return standard HTTP status codes:

### Success Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully

### Client Error Codes
- **400 Bad Request**: Invalid request body or parameters
- **401 Unauthorized**: Missing or invalid authentication headers
- **404 Not Found**: Requested resource not found

### Server Error Codes
- **500 Internal Server Error**: Server-side error occurred

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Example:**
```json
{
  "detail": "Run not found: abc123"
}
```

---

## Rate Limiting

Currently, no rate limiting is enforced. Future versions may implement:
- **Per-user limits**: 100 requests per minute
- **Burst allowance**: 20 requests per second

Rate limit headers (planned):
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642262400
```

---

## Interactive API Documentation

When running the API server, interactive documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to:
- Explore all endpoints interactively
- Test API calls directly from the browser
- View request/response schemas in detail
- Download OpenAPI specification (JSON/YAML)

---

## Examples

### Example 1: Create and Monitor a Run

```bash
# 1. Create a new run
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com" \
  -d '{
    "profile": "analytics_forecast_app",
    "intake": "Build a demand forecasting app",
    "project_name": "Q4 Forecast Project"
  }'

# Response:
# {
#   "run_id": "abc123",
#   "profile": "analytics_forecast_app",
#   "current_phase": "planning",
#   "status": "running",
#   ...
# }

# 2. Get run details
curl http://localhost:8000/runs/abc123 \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"

# 3. Advance to next phase
curl -X POST http://localhost:8000/runs/abc123/next \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com" \
  -d '{"skip_validation": false}'

# 4. List artifacts
curl http://localhost:8000/runs/abc123/artifacts \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"

# 5. Get metrics
curl http://localhost:8000/runs/abc123/metrics \
  -H "X-User-Id: user123" \
  -H "X-User-Email: user@example.com"
```

### Example 2: Python Client

```python
import requests

BASE_URL = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "user123",
    "X-User-Email": "user@example.com"
}

# Create run
response = requests.post(
    f"{BASE_URL}/runs",
    headers=HEADERS,
    json={
        "profile": "analytics_forecast_app",
        "intake": "Build demand forecasting app",
        "project_name": "Q4 Forecast"
    }
)
run = response.json()
run_id = run["run_id"]

print(f"Created run: {run_id}")

# Get run details
response = requests.get(f"{BASE_URL}/runs/{run_id}", headers=HEADERS)
details = response.json()
print(f"Current phase: {details['current_phase']}")

# Advance run
response = requests.post(
    f"{BASE_URL}/runs/{run_id}/next",
    headers=HEADERS,
    json={"skip_validation": False}
)
advance = response.json()
print(f"Advanced to: {advance['current_phase']}")

# Get artifacts
response = requests.get(f"{BASE_URL}/runs/{run_id}/artifacts", headers=HEADERS)
artifacts = response.json()
print(f"Total artifacts: {artifacts['total_count']}")

# Get metrics
response = requests.get(f"{BASE_URL}/runs/{run_id}/metrics", headers=HEADERS)
metrics = response.json()
print(f"Total cost: ${metrics['total_cost_usd']:.2f}")
print(f"Governance score: {metrics['governance_score']:.2%}")
```

### Example 3: TypeScript/JavaScript Client

```typescript
const BASE_URL = "http://localhost:8000";
const headers = {
  "X-User-Id": "user123",
  "X-User-Email": "user@example.com",
  "Content-Type": "application/json"
};

// Create run
const createResponse = await fetch(`${BASE_URL}/runs`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    profile: "analytics_forecast_app",
    intake: "Build demand forecasting app",
    project_name: "Q4 Forecast"
  })
});
const run = await createResponse.json();
const runId = run.run_id;

console.log(`Created run: ${runId}`);

// Get run details
const detailsResponse = await fetch(`${BASE_URL}/runs/${runId}`, { headers });
const details = await detailsResponse.json();
console.log(`Current phase: ${details.current_phase}`);

// Advance run
const advanceResponse = await fetch(`${BASE_URL}/runs/${runId}/next`, {
  method: "POST",
  headers,
  body: JSON.stringify({ skip_validation: false })
});
const advance = await advanceResponse.json();
console.log(`Advanced to: ${advance.current_phase}`);

// Get metrics
const metricsResponse = await fetch(`${BASE_URL}/runs/${runId}/metrics`, { headers });
const metrics = await metricsResponse.json();
console.log(`Total cost: $${metrics.total_cost_usd.toFixed(2)}`);
console.log(`Governance score: ${(metrics.governance_score * 100).toFixed(0)}%`);
```

---

## Workflow Phases

The orchestrator executes runs through the following phases in order:

1. **planning** - Requirements analysis and project planning
2. **architecture** - System design and architectural decisions
3. **data** - Data engineering, ETL, and model training (optional)
4. **development** - Feature implementation and coding
5. **qa** - Testing, validation, and quality assurance
6. **documentation** - Documentation generation and README updates

Each phase must complete before advancing to the next. Use `POST /runs/{run_id}/next` to advance through phases.

---

## Best Practices

### 1. Poll for Status Updates

```typescript
async function waitForPhaseCompletion(runId: string, maxWaitSeconds: number = 300) {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitSeconds * 1000) {
    const response = await fetch(`${BASE_URL}/runs/${runId}`, { headers });
    const details = await response.json();

    const currentPhaseInfo = details.phases.find(
      (p: any) => p.phase === details.current_phase
    );

    if (currentPhaseInfo?.status === "completed") {
      return details;
    }

    if (currentPhaseInfo?.status === "failed") {
      throw new Error(`Phase ${details.current_phase} failed`);
    }

    await new Promise(resolve => setTimeout(resolve, 5000)); // Poll every 5 seconds
  }

  throw new Error("Timeout waiting for phase completion");
}
```

### 2. Handle Errors Gracefully

```python
def create_run_with_retry(profile: str, intake: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{BASE_URL}/runs",
                headers=HEADERS,
                json={"profile": profile, "intake": intake}
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 3. Monitor Costs

```python
def check_cost_threshold(run_id: str, max_cost_usd: float = 1.0):
    response = requests.get(f"{BASE_URL}/runs/{run_id}/metrics", headers=HEADERS)
    metrics = response.json()

    if metrics["total_cost_usd"] > max_cost_usd:
        print(f"⚠️  Cost threshold exceeded: ${metrics['total_cost_usd']:.2f} > ${max_cost_usd}")
        return False

    return True
```

### 4. Validate Governance

```python
def ensure_governance_passing(run_id: str):
    response = requests.get(f"{BASE_URL}/runs/{run_id}/metrics", headers=HEADERS)
    metrics = response.json()

    if metrics["governance_score"] < 0.8:
        warnings = []
        for phase in metrics["phases_metrics"]:
            if phase["governance_warnings"]:
                warnings.extend(phase["governance_warnings"])

        print(f"⚠️  Governance score low: {metrics['governance_score']:.2%}")
        print("Warnings:", warnings)
        return False

    return True
```

---

## Changelog

### Version 1.0 (2025-01-15)
- Initial release
- 5 core endpoints: create, get, advance, artifacts, metrics
- User authentication via headers
- Phase-based workflow execution
- Comprehensive metrics and governance tracking

---

## Support

For issues, feature requests, or questions:
- **GitHub Issues**: [claude-code-orchestrator/issues](https://github.com/preston-fay/claude-code-orchestrator/issues)
- **Documentation**: [docs/](../docs/)
- **Implementation Details**: [artifacts/self_hardening/IMPLEMENTATION_API.md](../artifacts/self_hardening/IMPLEMENTATION_API.md)
