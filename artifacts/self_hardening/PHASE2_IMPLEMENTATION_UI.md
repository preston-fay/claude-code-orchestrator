# Phase 2B: Orchestrator Runs List UI - Implementation Artifact

**Branch:** `selfhardening/phase2_ui_runs_experience`
**Date:** 2025-11-26
**Phase:** Self-Hardening Phase 2B - UI Implementation

---

## Summary

Implemented the **Orchestrator Runs List UI** that connects to the Phase 2A backend (PR #8: `GET /runs` endpoint). This provides users with a production-grade interface to:

- View all orchestrator runs with filtering and pagination
- Filter runs by **status** (all/running/completed/failed) and **profile** (text search)
- Navigate between pages with **offset-based pagination** (20 runs per page)
- Click through to run detail pages
- Create new runs via modal (existing functionality preserved)

---

## Files Modified

### 1. `rsg-ui/src/api/orchestrator.ts`

**Changes:**
- Added type definitions:
  - `ListRunsParams` - Query parameters for filtering (status, profile, limit, offset)
  - `ListRunsResponse` - Response shape (runs array, total, limit, offset)
- Implemented `listRuns()` function:
  - Builds query parameters dynamically based on provided filters
  - Calls `GET /runs` endpoint with query string
  - Returns paginated list of runs with metadata

**Code snippet:**
```typescript
export interface ListRunsParams {
  status?: string;
  profile?: string;
  limit?: number;
  offset?: number;
}

export interface ListRunsResponse {
  runs: RunSummary[];
  total: number;
  limit: number;
  offset: number;
}

export async function listRuns(params: ListRunsParams = {}): Promise<ListRunsResponse> {
  const queryParams = new URLSearchParams();

  if (params.status) queryParams.append('status', params.status);
  if (params.profile) queryParams.append('profile', params.profile);
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());

  const queryString = queryParams.toString();
  const url = queryString ? `/runs?${queryString}` : '/runs';

  const response = await axiosInstance.get<ListRunsResponse>(url);
  return response.data;
}
```

---

### 2. `rsg-ui/src/pages/OrchestratorRunsPage.tsx`

**Changes:**
- Completely rewrote component with Phase 2B functionality
- Added state management:
  - **Runs list state**: `runs`, `loading`, `error`
  - **Filter state**: `statusFilter` (dropdown), `profileFilter` (text input)
  - **Pagination state**: `limit` (20), `offset`, `total`
  - **Create modal state**: `showCreateModal`, `newRun`, `creating`
- Implemented reactive data loading:
  - `useEffect` hook triggers `loadRuns()` when filters or pagination change
  - Resets to page 1 when filters change (better UX)
- Built UI components:
  - **Filters bar**: Status dropdown + Profile text input + Reset button
  - **Runs table**: Displays run_id (truncated), profile, project_name, current_phase, status, created_at
  - **Pagination controls**: Previous/Next buttons with page info ("Page X of Y (Z total runs)")
  - **Empty states**: Different messages for "no runs" vs "no filter matches"
  - **Create modal**: Preserved existing functionality for creating new runs

**Key features:**
- **Clickable rows**: Click any row to navigate to detail page (`/orchestrator/runs/${run.run_id}`)
- **Status badges**: Color-coded status indicators (running/completed/failed)
- **Phase badges**: Human-readable phase names (Planning, Architecture, Data Engineering, etc.)
- **Responsive error handling**: Error banner with dismiss button
- **Loading states**: Shows "Loading runs..." spinner during fetch

---

## UX Behavior

### How to Use the Runs List Page

1. **Navigate to `/orchestrator/runs`**
   - Click "Orchestrator Runs" in the navigation menu
   - Page loads with first 20 runs (or empty state if no runs exist)

2. **Filter by Status**
   - Use status dropdown to select:
     - **All** - Shows all runs regardless of status
     - **Running** - Only shows in-progress runs
     - **Completed** - Only shows successfully completed runs
     - **Failed** - Only shows failed runs
   - Page automatically resets to page 1 when filter changes

3. **Filter by Profile**
   - Type profile name in text input (e.g., "analytics_forecast_app")
   - Filters runs matching the profile name
   - Page automatically resets to page 1 when filter changes

4. **Reset Filters**
   - Click "Reset Filters" button to clear all filters
   - Returns to viewing all runs, page 1

5. **Paginate Through Results**
   - Click **"Previous"** to go to previous page (disabled on page 1)
   - Click **"Next"** to go to next page (disabled on last page)
   - View pagination info: "Page X of Y (Z total runs)"
   - Each page shows 20 runs

6. **Navigate to Run Detail**
   - Click any row in the table
   - Navigates to `/orchestrator/runs/{run_id}` detail page
   - Detail page shows full run information, phases, artifacts, metrics

7. **Create New Run**
   - Click "New Run" button in page header
   - Modal opens with form fields:
     - **Profile** (required): Select from dropdown (analytics_forecast_app, ml_classification, etc.)
     - **Project Name** (optional): Text input for project title
     - **Intake** (optional): Textarea for project requirements
   - Click "Create Run" to submit
   - On success, navigates to newly created run's detail page

8. **Observe "Advance Phase" Behavior**
   - From detail page, user can advance run to next phase
   - After advancing, navigate back to runs list
   - List reflects updated `current_phase` and `status` for that run
   - No WebSocket - user must manually refresh or re-navigate to see updates

---

## Known Limitations and TODOs

### 1. No Real-Time Updates (WebSocket)
**Current Behavior:** Runs list does NOT auto-refresh when run status changes.
**Workaround:** User must manually refresh page or re-navigate to `/orchestrator/runs` to see updates.
**Future Enhancement:** Add WebSocket or polling to update run status in real-time.

### 2. No Sorting Controls
**Current Behavior:** Runs are returned in backend default order (typically newest first).
**Future Enhancement:** Add sortable columns (e.g., click "Created" column to toggle asc/desc).

### 3. No Bulk Actions
**Current Behavior:** Cannot select multiple runs for bulk operations (e.g., delete, cancel).
**Future Enhancement:** Add checkboxes and bulk action toolbar.

### 4. Profile Filter is Exact Match (Case-Sensitive)
**Current Behavior:** Profile filter sends exact text to backend, which may do case-sensitive matching.
**Future Enhancement:** Add case-insensitive search or autocomplete dropdown with known profiles.

### 5. No Search by Run ID
**Current Behavior:** Cannot search for specific run by run_id.
**Future Enhancement:** Add run_id search field to quickly find specific run.

### 6. No Date Range Filtering
**Current Behavior:** Cannot filter runs by creation date range.
**Future Enhancement:** Add date picker for filtering by created_at range.

---

## Testing Commands

### Backend Tests (Verify No Regression)
```bash
# Ensure backend tests still pass with new UI
cd /Users/pfay01/Projects/claude-code-orchestrator
.venv/bin/pytest tests/test_runs_api.py -v
```

**Expected Result:** All tests pass (especially `test_list_runs_*` tests).

---

### Frontend Build (Verify No TypeScript Errors)
```bash
# Install dependencies (if not already done)
cd /Users/pfay01/Projects/claude-code-orchestrator/rsg-ui
npm install

# Build production bundle
npm run build
```

**Expected Result:** Build succeeds with no TypeScript errors or warnings.

---

### Manual Testing (Optional - Local Development)
```bash
# Terminal 1: Start backend API
cd /Users/pfay01/Projects/claude-code-orchestrator
.venv/bin/python scripts/dev/run_api_server.py

# Terminal 2: Start frontend dev server
cd /Users/pfay01/Projects/claude-code-orchestrator/rsg-ui
npm run dev

# Open browser to http://localhost:5173/orchestrator/runs
# Test:
# 1. Page loads with runs list (or empty state)
# 2. Filter by status (running/completed/failed)
# 3. Filter by profile (e.g., "analytics_forecast_app")
# 4. Click "Reset Filters"
# 5. Click "Previous" / "Next" pagination buttons
# 6. Click row to navigate to detail page
# 7. Click "New Run" to open modal, create run
```

---

## Backend Dependencies

This UI implementation depends on **Phase 2A backend** (PR #8: `selfhardening/phase2_backend_runs_list`):

- **Endpoint:** `GET /runs`
- **Query Parameters:** `status`, `profile`, `limit`, `offset`
- **Response:**
  ```json
  {
    "runs": [
      {
        "run_id": "uuid",
        "profile": "analytics_forecast_app",
        "project_name": "My Project",
        "current_phase": "planning",
        "status": "running",
        "created_at": "2025-11-26T10:00:00Z",
        "updated_at": "2025-11-26T10:05:00Z"
      }
    ],
    "total": 42,
    "limit": 20,
    "offset": 0
  }
  ```

**Merge Order:** Phase 2A backend (PR #8) should be merged BEFORE this UI PR to ensure endpoint availability.

---

## Acceptance Criteria

- [x] `/orchestrator/runs` page displays list of runs with pagination
- [x] Status filter dropdown (all/running/completed/failed) works correctly
- [x] Profile filter text input works correctly
- [x] Pagination controls (Previous/Next) work correctly
- [x] Clicking row navigates to run detail page
- [x] "New Run" modal still works (existing functionality preserved)
- [x] Empty states display appropriate messages
- [x] Error states display error banner with dismiss button
- [x] Loading states display spinner during fetch
- [x] TypeScript builds without errors
- [x] Backend tests still pass (no regression)

---

## Screenshots / Visual Reference

**Runs List with Data:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Orchestrator Runs                                      [New Run]        │
├─────────────────────────────────────────────────────────────────────────┤
│ Status: [All ▼]  Profile: [________________]  [Reset Filters]          │
├─────────────────────────────────────────────────────────────────────────┤
│ Run ID    │ Profile           │ Project Name │ Phase      │ Status      │
├─────────────────────────────────────────────────────────────────────────┤
│ 1b8f6ebe..│ analytics_for...  │ Q4 Forecast  │ Planning   │ running     │
│ a3c4d2f1..│ ml_classification │ Churn Model  │ QA         │ completed   │
│ ...                                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ [← Previous]    Page 1 of 3 (42 total runs)            [Next →]        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Empty State (No Runs):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Orchestrator Runs                                      [New Run]        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         No runs found.                                   │
│          Create your first orchestrator run to get started.              │
│                                                                          │
│                        [Create Run]                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

After merging this PR:

1. **Phase 3: Real-Time Updates**
   - Add WebSocket or polling to auto-refresh run status
   - Add "Live" badge indicator for running runs

2. **Phase 4: Advanced Filtering**
   - Add run_id search
   - Add date range filtering
   - Add sortable columns
   - Add profile autocomplete

3. **Phase 5: Bulk Actions**
   - Add row checkboxes
   - Add bulk cancel/delete/retry actions
   - Add bulk export to CSV

4. **Phase 6: Performance Optimization**
   - Add virtual scrolling for large run lists
   - Add client-side caching with React Query
   - Add optimistic updates for phase advancement

---

## Artifact Metadata

- **Artifact Type:** Implementation Documentation
- **Related PRs:**
  - Phase 2A Backend: PR #8 (`selfhardening/phase2_backend_runs_list`)
  - Phase 2B UI: This PR (`selfhardening/phase2_ui_runs_experience`)
- **Test Coverage:** Backend tests in `tests/test_runs_api.py`
- **Documentation Status:** Complete
- **Production Ready:** Yes (pending PR #8 merge)
