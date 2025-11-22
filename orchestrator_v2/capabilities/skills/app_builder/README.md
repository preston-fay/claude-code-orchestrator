# App Builder Skills

Skills for agent-driven application scaffolding and development in RSC Orchestrator.

## Overview

The App Builder skills enable automated generation of React frontends and FastAPI backends through the orchestrator's agent system. These skills are used during the SCAFFOLDING and DEVELOPMENT phases of the APP_BUILD workflow.

## Skills

### ReactAppScaffolder

Generates a complete React + Vite project with Kearney Design System styling.

**Input:**
- `repo_path`: Local workspace path for the app
- `app_name`: Name of the application
- `style`: Style theme (`kearney` | `minimal`)
- `include_routing`: Whether to set up React Router
- `include_api_client`: Whether to create Axios API client
- `api_base_url`: Base URL for API calls
- `initial_pages`: List of initial pages to create

**Output:**
- Project structure with src/, public/, config files
- KDS stylesheet with purple accent colors
- Initial page components
- Axios API client (if requested)

### ReactFeatureGenerator

Adds new pages and features to existing React applications.

**Input:**
- `repo_path`: Local workspace path for the app
- `feature_description`: Natural language description of the feature
- `target_route`: Optional route path (e.g., "/map")
- `component_name`: Optional component name (auto-derived if not provided)
- `include_tests`: Whether to generate test files
- `include_state`: Whether to add local state management

**Output:**
- New page component
- Associated helper components
- Updated App.tsx routing
- Test files (if requested)

### FastAPIScaffolder

Generates FastAPI routers, endpoints, and Pydantic models.

**Input:**
- `repo_path`: Local workspace path for the app
- `endpoint_name`: Name for the endpoint (e.g., "territories")
- `resource_model`: Dict of field names to types
- `summary`: Description of the endpoint
- `methods`: HTTP methods to generate (GET, POST, PUT, DELETE)
- `include_tests`: Whether to generate test files

**Output:**
- Pydantic models (Base, Create, Update, Response)
- FastAPI router with endpoints
- Test files (if requested)
- Updated main.py with router registration

## Usage

### From Agent Code

```python
from orchestrator_v2.capabilities.skills.app_builder import (
    ReactAppScaffolder,
    AppScaffoldInput,
)

scaffolder = ReactAppScaffolder()
result = scaffolder.execute(AppScaffoldInput(
    repo_path="/path/to/app",
    app_name="Territory Optimizer",
    style="kearney",
    initial_pages=["Home", "Map", "Scenarios"],
))

if result.success:
    print(f"Created {len(result.files_created)} files")
    print(result.structure_summary)
```

### From API

```bash
# Plan an app build
curl -X POST http://localhost:8000/app-builder/{project_id}/plan \
  -H "Content-Type: application/json" \
  -d '{"description": "Build Territory Optimizer with map view and scenario management"}'

# Run the build
curl -X POST http://localhost:8000/app-builder/{project_id}/run
```

## Kearney Design System

All generated React apps follow the Kearney Design System:

- **Primary color**: #6B2D7B (Kearney Purple)
- **Secondary color**: #2C3E50 (Charcoal)
- **No red or green** in UI elements (per brand guidelines)
- **Typography**: Inter font family
- **Spacing**: Consistent spacing scale (xs, sm, md, lg, xl)

## Workflow Integration

These skills are invoked during the APP_BUILD workflow:

1. **PLANNING** - Architect agent creates PRD
2. **ARCHITECTURE** - Architect + Consensus create ADRs
3. **SCAFFOLDING** - Developer runs `react_app_scaffolder` or `fastapi_scaffolder`
4. **DEVELOPMENT** - Developer uses `react_feature_generator` for features
5. **QA** - QA agent runs tests
6. **DOCUMENTATION** - Documentarian creates README

## File Output

All files are written to the project's workspace:

```
~/.orchestrator/workspaces/{project_id}/app_repo/
├── src/
│   ├── pages/
│   ├── components/
│   ├── api/
│   └── styles/
├── api/
│   ├── routers/
│   └── models/
└── tests/
```
