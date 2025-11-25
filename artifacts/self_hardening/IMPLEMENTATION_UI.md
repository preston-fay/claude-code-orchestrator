# UI Implementation Documentation

## Overview

This document details the **UI wiring** for the orchestrator runs API - TypeScript API client and React pages for managing and visualizing orchestrator runs.

**Status**: ✅ Complete
**Branch**: `selfhardening/api_alignment` (local)

---

## Files Created/Modified

### 1. rsg-ui/src/api/orchestrator.ts (NEW)

**Purpose**: TypeScript API client for orchestrator runs

**Features**:
- Axios-based HTTP client with auth headers (X-User-Id, X-User-Email)
- TypeScript interfaces matching backend DTOs
- 5 API functions mapping to backend endpoints
- Utility functions for formatting (cost, tokens, duration)

**API Functions**:
```typescript
createRun(request: CreateRunRequest): Promise<RunSummary>
advanceRun(runId: string, request?: AdvanceRunRequest): Promise<AdvanceRunResponse>
getRun(runId: string): Promise<RunDetail>
getRunArtifacts(runId: string): Promise<ArtifactsResponse>
getRunMetrics(runId: string): Promise<MetricsSummary>
```

**Utility Functions**:
- `formatCost(costUsd: number)` - USD currency formatting
- `formatTokens(tokens: number)` - K/M notation
- `formatDuration(seconds: number)` - Human-readable time
- `getPhaseDisplayName(phase: string)` - Friendly phase names
- `getPhaseStatusColor(status: string)` - Badge colors
- `calculateProgress(phases: PhaseInfo[])` - Completion percentage
- `isRunCompleted(run: RunDetail)` - Completion check
- `getArtifactTypeInfo(type: string)` - Icon/color mapping

### 2. rsg-ui/src/pages/OrchestratorRunsPage.tsx (NEW)

**Purpose**: List view of all orchestrator runs

**Features**:
- Create new run modal with profile selection
- Table view with run metadata (ID, profile, phase, status, created)
- Click row to navigate to detail page
- Empty state with call-to-action
- Error handling and loading states

**UI Components**:
- Page header with "New Run" button
- Create run modal (profile dropdown, project name, intake textarea)
- Runs table (clickable rows)
- Empty state

**Routes**: `/orchestrator/runs`

### 3. rsg-ui/src/pages/OrchestratorRunDetailPage.tsx (NEW)

**Purpose**: Detailed view of single orchestrator run

**Features**:
- Run summary (profile, phase, status, duration)
- "Advance to Next Phase" button
- Tabbed interface: Phases | Artifacts | Metrics
- Real-time data loading (runs, artifacts, metrics)

**Tabs**:

1. **Phases Tab**: Shows all phases with status, duration, artifacts count, agents
2. **Artifacts Tab**: Artifacts grouped by phase with icons, names, types, sizes
3. **Metrics Tab**:
   - Summary cards (total cost, tokens, governance score, hygiene score)
   - Phase metrics table (duration, tokens, cost, governance per phase)

**Routes**: `/orchestrator/runs/:runId`

### 4. rsg-ui/src/App.tsx (MODIFIED)

**Changes**:
1. Added imports:
   ```typescript
   import OrchestratorRunsPage from './pages/OrchestratorRunsPage';
   import OrchestratorRunDetailPage from './pages/OrchestratorRunDetailPage';
   ```

2. Added routes:
   ```typescript
   <Route path="/orchestrator/runs" element={<OrchestratorRunsPage />} />
   <Route path="/orchestrator/runs/:runId" element={<OrchestratorRunDetailPage />} />
   ```

---

## TypeScript Type Definitions

All types are defined in `rsg-ui/src/api/orchestrator.ts`:

```typescript
CreateRunRequest, RunSummary, PhaseInfo, RunDetail,
ArtifactSummary, ArtifactsResponse, PhaseMetrics, MetricsSummary,
AdvanceRunRequest, AdvanceRunResponse
```

Types mirror backend Pydantic models for end-to-end type safety.

---

## Usage

### Navigate to Runs List
```
http://localhost:5173/orchestrator/runs
```

### Create New Run
1. Click "New Run" button
2. Select profile from dropdown
3. (Optional) Enter project name and intake
4. Click "Create Run"
5. Redirected to run detail page

### View Run Details
```
http://localhost:5173/orchestrator/runs/{runId}
```

### Advance Run
1. On run detail page, click "Advance to Next Phase"
2. Current phase executes, run advances to next phase
3. Page refreshes with updated data

---

## Styling

Uses existing CSS classes from rsg-ui:
- `.page`, `.page-header`
- `.button-primary`, `.button-secondary`
- `.modal-overlay`, `.modal-content`
- `.phase-badge`, `.status-indicator`
- `.project-table`, `.clickable-row`

No new CSS required - pages integrate seamlessly with existing design.

---

## Future Enhancements

1. **Real-time Updates**: WebSocket connection for live phase progress
2. **Artifact Download**: Click artifact to download file
3. **Run Cancellation**: Cancel in-progress runs
4. **Run Cloning**: Clone existing run configuration
5. **Filtering/Search**: Filter runs by profile, status, date
6. **Pagination**: For large run lists
7. **Phase Logs**: View execution logs per phase
8. **Cost Alerts**: Notify when cost exceeds threshold

---

## Summary

**Files Created**:
- `rsg-ui/src/api/orchestrator.ts` (TypeScript API client)
- `rsg-ui/src/pages/OrchestratorRunsPage.tsx` (List view)
- `rsg-ui/src/pages/OrchestratorRunDetailPage.tsx` (Detail view)

**Files Modified**:
- `rsg-ui/src/App.tsx` (Added routes)

**Routes Added**:
- `/orchestrator/runs` → OrchestratorRunsPage
- `/orchestrator/runs/:runId` → OrchestratorRunDetailPage

**Status**: UI implementation complete ✅
**Ready For**: Manual testing, integration with backend
