# Phase 2 Backend Implementation: GET /runs Endpoint

## Summary

Implemented the `GET /runs` endpoint to list all orchestrator runs with filtering and pagination support. This addresses the "no list of runs" UX gap identified in Phase 2 discovery.

## Changes Made

### 1. API DTO (`orchestrator_v2/api/dto/runs.py`)

**Added `ListRunsResponse` model:**
```python
class ListRunsResponse(BaseModel):
    """Response for list runs endpoint."""
    runs: list[RunSummary] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
```

### 2. Orchestrator Service (`orchestrator_v2/services/orchestrator_service.py`)

**Added `list_runs()` method:**
- Returns tuple of `(list[RunSummary], total_count)`
- Loads all project states from `FileSystemProjectRepository`
- Calculates run status (running/completed/failed) by examining phase states
- Applies optional filters:
  - `status`: Filter by run status
  - `profile`: Filter by profile/template name
- Sorts results by `created_at` descending (newest first)
- Applies pagination via `limit` and `offset`
- Handles corrupted state files gracefully (logs warning, skips run)

### 3. API Routes (`orchestrator_v2/api/routes/runs.py`)

**Added `GET /runs` endpoint:**
- Path: `/runs`
- Query Parameters:
  - `status` (optional): Filter by status ("running", "completed", "failed")
  - `profile` (optional): Filter by profile name
  - `limit` (optional, default=50): Max runs to return
  - `offset` (optional, default=0): Number of runs to skip
- Returns `ListRunsResponse` with:
  - `runs`: Array of RunSummary objects
  - `total`: Total count before pagination
  - `limit`: Applied limit value
  - `offset`: Applied offset value

### 4. Tests (`tests/test_runs_api.py`)

**Added `TestListRuns` class with 6 comprehensive tests:**
1. `test_list_runs_empty` - Empty list when no runs exist
2. `test_list_runs_multiple` - List multiple runs correctly
3. `test_list_runs_filter_by_status` - Status filtering works
4. `test_list_runs_filter_by_profile` - Profile filtering works
5. `test_list_runs_pagination` - Pagination with limit/offset works
6. `test_list_runs_combined_filters` - Combined filters work together

All tests use mocking pattern consistent with existing tests.

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string (optional) | None | Filter by run status: "running", "completed", "failed" |
| `profile` | string (optional) | None | Filter by profile name (e.g., "analytics_forecast_app") |
| `limit` | integer (optional) | 50 | Maximum number of runs to return |
| `offset` | integer (optional) | 0 | Number of runs to skip for pagination |

## Response Shape

```json
{
  "runs": [
    {
      "run_id": "abc123",
      "profile": "analytics_forecast_app",
      "project_name": "Forecast Project",
      "current_phase": "development",
      "status": "running",
      "created_at": "2025-11-26T12:00:00Z",
      "updated_at": "2025-11-26T14:30:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

## Example Usage

### List all runs
```bash
GET /runs
```

### Filter by status
```bash
GET /runs?status=completed
```

### Filter by profile
```bash
GET /runs?profile=analytics_forecast_app
```

### Pagination
```bash
GET /runs?limit=10&offset=20
```

### Combined filters
```bash
GET /runs?status=running&profile=analytics_forecast_app&limit=10&offset=0
```

## Files Modified

1. `orchestrator_v2/api/dto/runs.py` - Added `ListRunsResponse`
2. `orchestrator_v2/api/routes/runs.py` - Added `GET /runs` endpoint
3. `orchestrator_v2/services/orchestrator_service.py` - Added `list_runs()` method
4. `tests/test_runs_api.py` - Added 6 tests for list functionality

## Validation

Run tests:
```bash
pytest tests/test_runs_api.py::TestListRuns -v
```

Run all runs API tests:
```bash
pytest tests/test_runs_api.py -v
```

## Notes

- **Status Calculation**: Status is derived from phase states, not stored separately
  - "running" - Default state
  - "completed" - Documentation phase completed
  - "failed" - Any phase has failed status

- **Graceful Degradation**: Corrupted state files are skipped with a warning log

- **Sort Order**: Runs are always sorted by `created_at` descending (newest first)

- **Performance**: Currently loads all runs into memory. For large deployments (>1000 runs), consider:
  - Repository-level pagination
  - Index/metadata cache
  - Background indexing process

## Part of Self-Hardening Orchestrator

This implementation is Phase 2A (backend) of the self_hardening_orchestrator run. It directly addresses the UX gap: "Users have no way to see list of their runs" identified in PHASE2_DISCOVERY.md.

Next Phase 2B will implement the UI components to consume this endpoint.
