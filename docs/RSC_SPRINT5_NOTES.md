# RSC Sprint 5 - App Builder V2 Release Notes

## Overview

Sprint 5 delivers the App Builder V2 feature set, transforming RSC into a comprehensive orchestration platform for building real applications. This sprint focuses on making the platform usable for end-to-end app development workflows.

## New Features

### 1. App Builder Service

**Backend Endpoints:**
- `POST /app-builder/{project_id}/plan` - Generate PRD, architecture, user flows
- `POST /app-builder/{project_id}/scaffold` - Generate app structure and starter code
- `GET /app-builder/{project_id}/status` - Get build status
- `GET /app-builder/{project_id}/artifacts` - List build artifacts

**Console Commands:**
- `/app-plan` - Plan an app build (requires `app_build` capability)
- `/app-scaffold` - Generate scaffold files

**Generated Artifacts:**
- `app_prd.md` - Product requirements document
- `app_architecture.md` - System architecture and design
- `app_user_flows.md` - User journeys and screens
- `app_structure.json` - Directory structure
- `app_scaffold_instructions.md` - Setup guide
- Component files (AppShell.tsx, HomePage.tsx, main.py, etc.)

### 2. Feature Engine

**Backend Endpoints:**
- `POST /projects/{project_id}/features` - Create a feature
- `GET /projects/{project_id}/features` - List all features
- `GET /projects/{project_id}/features/{feature_id}` - Get feature details
- `POST /projects/{project_id}/features/{feature_id}/plan` - Generate spec and design
- `POST /projects/{project_id}/features/{feature_id}/build` - Generate code and tests
- `GET /projects/{project_id}/features/{feature_id}/artifacts` - List feature artifacts

**Console Commands:**
- `/new-feature "Title" [description]` - Create a feature request
- `/list-features` - List all project features
- `/plan-feature <feature-id>` - Generate feature spec and design
- `/build-feature <feature-id>` - Generate code and test stubs

**Feature Workflow:**
1. SUBMITTED → Created via UI or console
2. PLANNED → Spec and design generated
3. BUILDING → Code generation in progress
4. COMPLETED → All artifacts generated
5. FAILED → Error occurred

**Generated Artifacts per Feature:**
- `feature_spec.md` - Requirements and acceptance criteria
- `feature_design.md` - Technical design approach
- `implementation_guide.md` - Step-by-step instructions
- Code snippets and test stubs

### 3. Frontend Updates

**New Pages:**
- `/projects/:projectId/app-build` - App Build management page
- `/projects/:projectId/features` - Feature management page

**Navigation:**
- Added "App Build" button on project detail (for projects with `app_build` capability)
- Added "Features" button on all projects

**App Build Page Features:**
- Build status display (not started, planning, scaffolding, completed, failed)
- Plan and Scaffold action buttons
- Artifact listing with viewer modal
- External repo/app URL links
- Console command tips

**Features Page:**
- Create feature form (title, description)
- Features table with status, priority, actions
- Plan and Build buttons per feature
- Artifact count badges

## Technical Implementation

### New Modules

```
orchestrator_v2/
├── app_builder/
│   ├── __init__.py
│   ├── models.py      # AppBuildState, AppBuildStatus
│   └── service.py     # plan_app_build, run_app_scaffold
└── feature_engine/
    ├── __init__.py
    ├── models.py      # FeatureRequest, FeatureStatus
    ├── repository.py  # File-based storage
    └── service.py     # create, plan, build features
```

### State Management

**ProjectState Extensions:**
- Added `app_build: AppBuildState | None` field

**Feature Storage:**
- Features stored in `~/.orchestrator/projects/{project_id}/features/{feature_id}.json`

### LLM Integration

All artifact generation uses:
- Model: `claude-sonnet-4-5-20250929` (configurable via user settings)
- Structured JSON prompts with detailed requirements
- JSON parsing from LLM responses

## Usage Guide

### Creating a Web App Project

1. Create a new project with the `web_app` template
2. Navigate to Project → App Build
3. Click "Plan App Build" to generate PRD and architecture
4. Click "Run Scaffolding" to generate starter code
5. Review generated artifacts

### Managing Features

1. Navigate to Project → Features
2. Fill in feature title and description
3. Click "Create Feature"
4. Use "Plan" to generate spec and design
5. Use "Build" to generate code

### Console Workflow

```bash
# Plan app build
/app-plan

# Generate scaffold
/app-scaffold

# Create and build a feature
/new-feature "User Authentication" Implement login and registration
/plan-feature F-001
/build-feature F-001

# List features
/list-features
```

## API Changes Summary

### New Endpoints
- 4 App Builder endpoints
- 6 Feature Engine endpoints

### Updated Endpoints
- `/projects/{project_id}/chat` - Added app builder and feature commands to /help

### New Console Commands
- `/app-plan`
- `/app-scaffold`
- `/new-feature`
- `/list-features`
- `/plan-feature`
- `/build-feature`

## Configuration

No additional configuration required. App Builder and Feature Engine use existing:
- User LLM provider settings
- Project workspace paths
- Artifact storage locations

## Breaking Changes

None. All changes are additive.

## Known Limitations

1. **No External Repo Operations**: Scaffold generates artifacts only, doesn't clone/push to repos
2. **Feature Dependencies**: Feature dependency tracking is defined but not enforced
3. **Single Target Stack**: Currently defaults to React + FastAPI

## Future Improvements

- Git integration for applying scaffold to real repos
- Feature dependency visualization
- Multi-stack support (Next.js, Vue, Django)
- Real-time build progress streaming
- Feature branching integration

## Testing

To verify the implementation:

1. Start the API server:
   ```bash
   cd orchestrator_v2
   python -m uvicorn api.server:app --reload
   ```

2. Start the frontend:
   ```bash
   cd rsg-ui
   npm run dev
   ```

3. Create a project with `web_app` template
4. Test App Build flow
5. Test Feature creation and build flow

## Files Changed

### Backend
- `orchestrator_v2/app_builder/*` (new)
- `orchestrator_v2/feature_engine/*` (new)
- `orchestrator_v2/api/server.py` (endpoints + commands)
- `orchestrator_v2/engine/state_models.py` (app_build field)

### Frontend
- `rsg-ui/src/pages/ProjectAppBuildPage.tsx` (new)
- `rsg-ui/src/pages/ProjectFeaturesPage.tsx` (new)
- `rsg-ui/src/pages/ProjectDetailPage.tsx` (navigation)
- `rsg-ui/src/api/client.ts` (API functions)
- `rsg-ui/src/api/types.ts` (types)
- `rsg-ui/src/App.tsx` (routes)

### Documentation
- `docs/RSC_SPRINT5_NOTES.md` (this file)
