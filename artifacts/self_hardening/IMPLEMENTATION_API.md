# API Implementation Documentation

## Overview

This document details the implementation of the **Orchestrator Runs API** - a 5-endpoint REST API surface for managing orchestrator run lifecycle, execution, and artifact tracking.

**Branch**: `selfhardening/api_alignment` (local)
**Status**: ✅ Complete
**Test Coverage**: Comprehensive (happy path + error cases)

---

## Architecture

### Layered Design

The implementation follows a clean 3-layer architecture:

```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI Routes)            │
│  orchestrator_v2/api/routes/runs.py    │
│  - HTTP request/response handling      │
│  - Request validation (Pydantic)       │
│  - Auth dependency injection           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Service Layer (Business Logic)        │
│  orchestrator_v2/services/             │
│    orchestrator_service.py             │
│  - Run lifecycle management            │
│  - Artifact tracking                   │
│  - Metrics calculation                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Engine Layer (Orchestrator Core)      │
│  orchestrator_v2/engine/engine.py      │
│  - Phase execution                     │
│  - Agent coordination                  │
│  - State management                    │
└─────────────────────────────────────────┘
```

### Dependency Injection

FastAPI's `Depends()` pattern is used for:
- **User Authentication**: `get_current_user()` extracts user from headers (`X-User-Id`, `X-User-Email`)
- **Service Instances**: `get_orchestrator_service()` provides singleton service instance

---

## Files Created/Modified

### 1. orchestrator_v2/api/dto/runs.py (NEW)
**Purpose**: Pydantic models for request/response validation

**DTOs Implemented**:
- `CreateRunRequest` - POST /runs request body
- `RunSummary` - Basic run information (create response)
- `RunDetail` - Comprehensive run details (get response)
- `PhaseInfo` - Phase status and metadata
- `ArtifactSummary` - Artifact metadata
- `ArtifactsResponse` - Artifacts grouped by phase
- `PhaseMetrics` - Per-phase performance metrics
- `MetricsSummary` - Comprehensive run metrics
- `AdvanceRunRequest` - Advance phase request
- `AdvanceRunResponse` - Advance phase response

**Key Design Decisions**:
- All DTOs use Pydantic `BaseModel` for automatic validation
- `Field(...)` with descriptions for auto-generated API docs
- Optional fields use `| None` type hints (Python 3.10+)
- Timestamps use `datetime` objects (auto-serialized to ISO8601)

### 2. orchestrator_v2/api/dto/__init__.py (NEW)
**Purpose**: Export all DTOs for easy importing

```python
from orchestrator_v2.api.dto.runs import (
    CreateRunRequest, RunSummary, RunDetail, ...
)
```

### 3. orchestrator_v2/services/orchestrator_service.py (NEW)
**Purpose**: Service layer implementing orchestrator business logic

**Class**: `OrchestratorService`

**Methods**:
1. `create_run()` - Create new orchestrator run
   - Generates UUID for run_id
   - Creates `ProjectState` with initial phase (PLANNING)
   - Creates workspace via `WorkspaceManager`
   - Persists state via `FileSystemProjectRepository`

2. `get_run()` - Get detailed run information
   - Loads state from repository
   - Builds `PhaseInfo` for all phases
   - Calculates total duration across phases
   - Determines run status (running/completed)

3. `advance_run()` - Advance run to next phase
   - Gets or creates `WorkflowEngine` for run
   - Executes current phase via engine
   - Advances to next phase in sequence
   - Persists updated state

4. `list_artifacts()` - List artifacts grouped by phase
   - Scans workspace `artifacts/` directory
   - Groups artifacts by phase subdirectory
   - Extracts metadata (size, created_at, type)
   - Returns `ArtifactsResponse` with counts

5. `get_metrics()` - Get comprehensive metrics
   - Calculates token usage per phase (from agent states)
   - Estimates cost (Sonnet 4.5 pricing: $0.003/1K input, $0.015/1K output)
   - Computes governance score based on errors
   - Returns performance, cost, and quality metrics

**Helper Methods**:
- `_calculate_duration()` - Duration between timestamps
- `_calculate_total_duration()` - Total run duration (earliest start → latest completion)
- `_get_next_phase()` - Phase transition logic (PLANNING → ARCHITECTURE → DATA → DEVELOPMENT → QA → DOCUMENTATION)
- `_determine_artifact_type()` - Artifact type classification (prd, architecture, code, test, etc.)

### 4. orchestrator_v2/services/__init__.py (NEW)
**Purpose**: Initialize services package

### 5. orchestrator_v2/api/routes/runs.py (NEW)
**Purpose**: FastAPI router with 5 endpoints for runs management

**Router Configuration**:
```python
router = APIRouter(prefix="/runs", tags=["runs"])
```

**Endpoints Implemented**:

#### Endpoint 1: POST /runs
**Purpose**: Create new orchestrator run

**Request**:
```json
{
  "profile": "analytics_forecast_app",
  "intake": "Build a demand forecasting app",
  "project_name": "Forecast Project Q4",
  "metadata": { "client": "Acme Corp" }
}
```

**Response** (201 Created):
```json
{
  "run_id": "abc123-...",
  "profile": "analytics_forecast_app",
  "project_name": "Forecast Project Q4",
  "current_phase": "planning",
  "status": "running",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Endpoint 2: POST /runs/{run_id}/next
**Purpose**: Advance run to next phase

**Request** (optional):
```json
{
  "skip_validation": false
}
```

**Response**:
```json
{
  "run_id": "abc123-...",
  "previous_phase": "planning",
  "current_phase": "architecture",
  "status": "running",
  "message": "Advanced from planning to architecture"
}
```

**Logic Flow**:
1. Get current run state (to capture previous phase)
2. Call `service.advance_run()` to execute phase and advance
3. Return before/after phase information

#### Endpoint 3: GET /runs/{run_id}
**Purpose**: Get detailed run information

**Response**:
```json
{
  "run_id": "abc123-...",
  "profile": "analytics_forecast_app",
  "intake": "Build a forecasting app",
  "project_name": "Test Project",
  "current_phase": "architecture",
  "status": "running",
  "phases": [
    {
      "phase": "planning",
      "status": "completed",
      "started_at": "2025-01-15T10:00:00Z",
      "completed_at": "2025-01-15T10:05:00Z",
      "duration_seconds": 300.0,
      "agent_ids": ["planner"],
      "artifacts_count": 3
    }
  ],
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:10:00Z",
  "total_duration_seconds": 600.0,
  "metadata": { "intake": "..." }
}
```

#### Endpoint 4: GET /runs/{run_id}/artifacts
**Purpose**: List artifacts grouped by phase

**Response**:
```json
{
  "run_id": "abc123-...",
  "total_count": 5,
  "artifacts_by_phase": {
    "planning": [
      {
        "artifact_id": "planning_PRD.md",
        "phase": "planning",
        "path": "/workspace/artifacts/planning/PRD.md",
        "name": "PRD.md",
        "description": "PRD artifact for planning",
        "artifact_type": "prd",
        "size_bytes": 1024,
        "created_at": "2025-01-15T10:05:00Z"
      }
    ]
  }
}
```

**Artifact Discovery**:
- Scans `{workspace_path}/artifacts/{phase}/` directories
- Ignores files starting with `_` (internal)
- Determines artifact type from filename/extension
- Extracts file metadata (size, timestamps)

#### Endpoint 5: GET /runs/{run_id}/metrics
**Purpose**: Get comprehensive performance and governance metrics

**Response**:
```json
{
  "run_id": "abc123-...",
  "total_duration_seconds": 3600.0,
  "total_token_usage": {
    "input": 10000,
    "output": 5000
  },
  "total_cost_usd": 0.45,
  "phases_metrics": [
    {
      "phase": "planning",
      "duration_seconds": 300.0,
      "token_usage": { "input": 2000, "output": 1000 },
      "cost_usd": 0.09,
      "agents_executed": ["planner"],
      "artifacts_generated": 3,
      "governance_passed": true,
      "governance_warnings": []
    }
  ],
  "governance_score": 1.0,
  "hygiene_score": 0.95,
  "artifacts_total": 12,
  "errors_count": 0
}
```

**Metrics Calculation**:
- Token usage aggregated from agent states (per phase)
- Cost estimated using Sonnet 4.5 pricing
- Governance score: 1.0 if no errors, 0.8 if errors present
- Hygiene score: TODO (future: workspace analysis)

### 6. orchestrator_v2/api/routes/__init__.py (NEW)
**Purpose**: Initialize routes package

### 7. orchestrator_v2/api/server.py (MODIFIED)
**Purpose**: Integrate runs router into main FastAPI app

**Changes**:
1. Import runs router:
   ```python
   from orchestrator_v2.api.routes import runs
   ```

2. Include router (after CORS middleware):
   ```python
   app.include_router(runs.router)
   ```

**Result**: All 5 endpoints now available at:
- `POST /runs`
- `POST /runs/{run_id}/next`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/artifacts`
- `GET /runs/{run_id}/metrics`

### 8. tests/test_runs_api.py (NEW)
**Purpose**: Comprehensive API tests using FastAPI TestClient

**Test Structure**:
- Uses `pytest` framework
- Organized by endpoint using test classes
- Mocks service layer to isolate API testing
- Tests both happy path and error cases

**Test Classes**:

1. `TestCreateRun` - POST /runs
   - ✅ Create run with valid request
   - ✅ Fail without authentication headers
   - ✅ Create with minimal fields
   - ✅ Create with metadata

2. `TestAdvanceRun` - POST /runs/{run_id}/next
   - ✅ Advance to next phase
   - ✅ 404 for non-existent run
   - ✅ Advance with skip_validation flag

3. `TestGetRun` - GET /runs/{run_id}
   - ✅ Get detailed run information
   - ✅ 404 for non-existent run
   - ✅ Get completed run with all phases

4. `TestGetRunArtifacts` - GET /runs/{run_id}/artifacts
   - ✅ Get artifacts grouped by phase
   - ✅ Get empty artifacts for new run
   - ✅ 404 for non-existent run

5. `TestGetRunMetrics` - GET /runs/{run_id}/metrics
   - ✅ Get comprehensive metrics
   - ✅ Get metrics with errors
   - ✅ 404 for non-existent run

6. `TestFullWorkflow` - Integration
   - ✅ Complete workflow: create → get → advance → artifacts → metrics

**Fixtures**:
- `temp_workspace` - Temporary workspace with sample artifacts
- `mock_user` - User profile for auth testing
- `sample_project_state` - ProjectState for service mocking
- `client` - FastAPI TestClient
- `auth_headers()` - Helper for authentication headers

**Coverage**:
- All 5 endpoints covered
- Happy path scenarios
- Error cases (404, 401, 500)
- Edge cases (empty artifacts, completed runs)
- Full workflow integration

**Running Tests**:
```bash
pytest tests/test_runs_api.py -v
```

---

## Authentication

### Header-Based Auth
The API requires two headers for all authenticated endpoints:

```http
X-User-Id: test-user-123
X-User-Email: test@example.com
```

**Implementation** (`orchestrator_v2/api/routes/runs.py:31-53`):
```python
async def get_current_user(
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_email: Annotated[str | None, Header()] = None,
) -> UserProfile:
    if not x_user_id or not x_user_email:
        raise HTTPException(status_code=401, detail="Missing auth headers")

    user_repo = FileSystemUserRepository()
    try:
        user = await user_repo.get_user(x_user_id)
    except KeyError:
        # Create default user if not exists
        user = UserProfile(
            user_id=x_user_id,
            email=x_user_email,
            name=x_user_email.split("@")[0],
        )

    return user
```

**Endpoints Requiring Auth**:
- ✅ POST /runs (create run)
- ✅ POST /runs/{run_id}/next (advance run)
- ❌ GET /runs/{run_id} (public read)
- ❌ GET /runs/{run_id}/artifacts (public read)
- ❌ GET /runs/{run_id}/metrics (public read)

**Future Enhancement**: OAuth2/JWT token-based auth for production deployment.

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/POST operations |
| 201 | Created | Successful run creation |
| 400 | Bad Request | Invalid request data (Pydantic validation) |
| 401 | Unauthorized | Missing authentication headers |
| 404 | Not Found | Run ID not found |
| 422 | Unprocessable Entity | Pydantic validation errors |
| 500 | Internal Server Error | Unexpected server errors |

### Error Response Format

All errors return JSON:
```json
{
  "detail": "Run not found: nonexistent-run"
}
```

### Error Handling in Routes

Example from `runs.py:174-178`:
```python
try:
    # ... endpoint logic
except KeyError:
    raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
except Exception as e:
    logger.error(f"Failed to advance run {run_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to advance run: {str(e)}")
```

---

## State Management

### ProjectState Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  1. CREATE RUN (POST /runs)                             │
│  - Generate UUID (run_id)                               │
│  - Create ProjectState with PLANNING phase              │
│  - Create workspace directory                           │
│  - Persist state via FileSystemProjectRepository        │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  2. ADVANCE RUN (POST /runs/{run_id}/next)              │
│  - Load state from repository                           │
│  - Get/create WorkflowEngine for run                    │
│  - Execute current phase (e.g., PLANNING)               │
│  - Generate artifacts in workspace/artifacts/{phase}/   │
│  - Update phase state (completed_at, artifacts)         │
│  - Advance to next phase (PLANNING → ARCHITECTURE)      │
│  - Persist updated state                                │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  3. QUERY RUN (GET /runs/{run_id})                      │
│  - Load state from repository                           │
│  - Build RunDetail DTO with all phases                  │
│  - Calculate total duration                             │
│  - Determine status (running/completed)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  4. GET ARTIFACTS (GET /runs/{run_id}/artifacts)        │
│  - Load state to get workspace_path                     │
│  - Scan {workspace_path}/artifacts/*/ directories       │
│  - Group artifacts by phase                             │
│  - Extract metadata (size, timestamps, type)            │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  5. GET METRICS (GET /runs/{run_id}/metrics)            │
│  - Load state with all phase states                     │
│  - Aggregate token usage from agent states              │
│  - Calculate cost estimates                             │
│  - Compute governance/hygiene scores                    │
└─────────────────────────────────────────────────────────┘
```

### Phase Transition Logic

Defined in `orchestrator_service.py:374-392`:

```python
def _get_next_phase(self, current_phase: PhaseType) -> PhaseType | None:
    phase_order = [
        PhaseType.PLANNING,
        PhaseType.ARCHITECTURE,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ]

    current_index = phase_order.index(current_phase)
    if current_index < len(phase_order) - 1:
        return phase_order[current_index + 1]
    return None
```

**Transition Rules**:
- Linear progression through 6 phases
- Cannot skip phases
- DOCUMENTATION is final phase (returns `None` for next)

---

## Workspace Structure

When a run is created, a workspace is generated:

```
/workspaces/{run_id}/
├── artifacts/
│   ├── planning/
│   │   ├── PRD.md
│   │   └── requirements.txt
│   ├── architecture/
│   │   ├── architecture.md
│   │   └── system_design.md
│   ├── data/
│   │   └── data_pipeline.py
│   ├── development/
│   │   └── src/
│   ├── qa/
│   │   └── test_results.json
│   └── documentation/
│       └── README.md
└── state.json
```

**Artifact Discovery**:
- `list_artifacts()` scans `artifacts/` subdirectories
- Each phase has its own subdirectory
- Files starting with `_` are ignored (internal)

---

## API Documentation

### OpenAPI/Swagger
FastAPI automatically generates interactive API docs:

**Swagger UI**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`
**OpenAPI JSON**: `http://localhost:8000/openapi.json`

**Features**:
- Interactive "Try it out" for each endpoint
- Request/response schemas from Pydantic models
- Example requests with descriptions
- Authentication headers configurable per request

### Pydantic Schema Generation
All DTOs include descriptions for auto-generated docs:

```python
class CreateRunRequest(BaseModel):
    profile: str = Field(..., description="Profile name (e.g., 'analytics_forecast_app')")
    intake: str | None = Field(None, description="Optional intake text or requirements")
    project_name: str | None = Field(None, description="Optional project name")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
```

**Result**: Rich, self-documenting API with examples.

---

## Testing Strategy

### Test Isolation via Mocking

All tests mock the service layer to isolate API testing:

```python
@patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.create_run")
def test_create_run_success(self, mock_create, client, mock_user):
    mock_create.return_value = RunSummary(...)

    response = client.post("/runs", json={...}, headers=auth_headers(mock_user))

    assert response.status_code == 201
    assert response.json()["run_id"] == "run-abc123"
```

**Why Mock Service Layer**:
- Faster tests (no database/filesystem I/O)
- Deterministic (no timing issues)
- Isolated (API layer only)
- Flexible (easy to test error conditions)

### Test Coverage

**Endpoint Coverage**:
- ✅ POST /runs - 4 tests
- ✅ POST /runs/{run_id}/next - 3 tests
- ✅ GET /runs/{run_id} - 3 tests
- ✅ GET /runs/{run_id}/artifacts - 3 tests
- ✅ GET /runs/{run_id}/metrics - 3 tests
- ✅ Full workflow - 1 integration test

**Total**: 17 tests covering all endpoints, happy/error paths, and integration.

### Running Tests

```bash
# Run all API tests
pytest tests/test_runs_api.py -v

# Run specific test class
pytest tests/test_runs_api.py::TestCreateRun -v

# Run with coverage
pytest tests/test_runs_api.py --cov=orchestrator_v2.api.routes.runs --cov-report=html
```

---

## Future Enhancements

### Planned Improvements

1. **Pagination** for large result sets
   - GET /runs (list all runs with pagination)
   - GET /runs/{run_id}/artifacts?page=1&limit=20

2. **Filtering and Search**
   - GET /runs?profile=analytics_forecast_app
   - GET /runs?status=running
   - GET /runs?created_after=2025-01-01

3. **WebSocket Support** for real-time updates
   - ws://localhost:8000/runs/{run_id}/stream
   - Stream phase transitions, artifact creation, logs

4. **Run Cancellation**
   - POST /runs/{run_id}/cancel

5. **Run Cloning**
   - POST /runs/{run_id}/clone

6. **Artifact Download**
   - GET /runs/{run_id}/artifacts/{artifact_id}/download

7. **Enhanced Metrics**
   - Per-agent token usage breakdown
   - Cost projections for remaining phases
   - Estimated time to completion

8. **Governance Integration**
   - Real-time governance validation during phases
   - Governance rule violations in metrics
   - Blocking vs. non-blocking governance checks

9. **Authentication Improvements**
   - OAuth2/JWT token-based auth
   - API key support
   - Role-based access control (RBAC)

10. **Rate Limiting**
    - Prevent abuse of create/advance endpoints
    - Per-user quotas

---

## Deployment Considerations

### Production Readiness Checklist

- [ ] **Authentication**: Replace header-based auth with OAuth2/JWT
- [ ] **Authorization**: Implement RBAC (users can only access their runs)
- [ ] **Rate Limiting**: Add rate limits to prevent abuse
- [ ] **Database**: Replace FileSystemProjectRepository with PostgreSQL
- [ ] **Caching**: Add Redis for frequently accessed runs
- [ ] **Monitoring**: Instrument with OpenTelemetry/Prometheus
- [ ] **Logging**: Structured logging with trace IDs
- [ ] **Error Tracking**: Integrate Sentry for error reporting
- [ ] **API Versioning**: Add /v1/ prefix for future versioning
- [ ] **CORS**: Configure allowed origins for production
- [ ] **HTTPS**: Enforce TLS in production
- [ ] **Health Checks**: Add /health and /ready endpoints
- [ ] **Documentation**: Host API docs separately (not /docs in prod)

### Environment Configuration

```bash
# .env
ORCHESTRATOR_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/orchestrator
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
SENTRY_DSN=https://...
ALLOWED_ORIGINS=https://app.example.com
```

---

## Summary

### What Was Implemented

✅ **5 REST API Endpoints**:
1. POST /runs - Create orchestrator run
2. POST /runs/{run_id}/next - Advance to next phase
3. GET /runs/{run_id} - Get run status and phases
4. GET /runs/{run_id}/artifacts - List artifacts by phase
5. GET /runs/{run_id}/metrics - Get governance, hygiene, and metrics

✅ **Service Layer** (`OrchestratorService`):
- Run lifecycle management (create, advance, query)
- Artifact tracking and discovery
- Metrics calculation (tokens, cost, governance)

✅ **DTOs** (Pydantic models):
- Request/response validation
- Auto-generated API documentation
- Type safety

✅ **Comprehensive Tests**:
- 17 tests covering all endpoints
- Happy path and error cases
- Integration workflow test

✅ **Documentation**:
- This implementation guide
- Auto-generated OpenAPI/Swagger docs
- Inline docstrings with examples

### Files Created

**New Files**:
- `orchestrator_v2/api/dto/runs.py` (DTOs)
- `orchestrator_v2/api/dto/__init__.py`
- `orchestrator_v2/services/orchestrator_service.py` (Service layer)
- `orchestrator_v2/services/__init__.py`
- `orchestrator_v2/api/routes/runs.py` (API routes)
- `orchestrator_v2/api/routes/__init__.py`
- `tests/test_runs_api.py` (Tests)
- `artifacts/self_hardening/IMPLEMENTATION_API.md` (This doc)

**Modified Files**:
- `orchestrator_v2/api/server.py` (Added runs router)

### Next Steps

**Remaining Tasks** (from user instructions):
- [ ] Implement UI API client in `rsg-ui/src/api/orchestrator.ts`
- [ ] Create `OrchestratorRunsPage.tsx` (list view)
- [ ] Create `OrchestratorRunDetailPage.tsx` (detail view)
- [ ] Add routes to rsg-ui routing
- [ ] Document UI implementation in `IMPLEMENTATION_UI.md`
- [ ] Create final `IMPLEMENTATION.md` summary

**Ready For**:
- UI integration (TypeScript client, React pages)
- Manual testing via Swagger UI
- Integration with existing orchestrator engine

---

**Status**: API Implementation Complete ✅
**Branch**: selfhardening/api_alignment (local)
**Test Results**: All tests passing
**Next Phase**: UI Implementation
