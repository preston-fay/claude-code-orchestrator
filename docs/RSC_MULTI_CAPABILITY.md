# RSC Multi-Capability Projects

This document describes the multi-capability feature for Ready-Set-Code (RSC) projects, which allows projects to have multiple attached capabilities that determine their workflow phases.

## Overview

RSC projects can now have one or more **capabilities** attached to them. Each capability represents a type of work (e.g., data pipeline, analytics, ML, app build) and maps to specific workflow phases. This enables:

- Projects that combine multiple types of work (e.g., data pipeline + ML + app build)
- Dynamic phase determination based on selected capabilities
- Clear visibility of project scope in the UI

## Available Capabilities

| Capability ID | Display Label | Description |
|--------------|---------------|-------------|
| `data_pipeline` | Data Pipeline | Data ingestion and basic transformation |
| `analytics_forecasting` | Analytics (Forecasting) | Time-series forecasting and prediction |
| `analytics_bi_dashboard` | Analytics (BI Dashboard) | Business intelligence dashboards |
| `ml_classification` | ML (Classification) | Machine learning classification models |
| `ml_regression` | ML (Regression) | Machine learning regression models |
| `optimization` | Optimization | Mathematical optimization problems |
| `app_build` | App Build / UI | Frontend application development |
| `service_api` | Service / API | Backend API development |
| `data_engineering` | Data Engineering | ETL pipelines and data infrastructure |

## Capability to Phases Mapping

Each capability participates in specific workflow phases:

| Capability | Planning | Architecture | Data | Development | QA | Documentation |
|------------|:--------:|:------------:|:----:|:-----------:|:--:|:-------------:|
| data_pipeline | ✓ | | ✓ | | | |
| analytics_forecasting | ✓ | | ✓ | ✓ | ✓ | ✓ |
| analytics_bi_dashboard | ✓ | | ✓ | ✓ | ✓ | ✓ |
| ml_classification | ✓ | | ✓ | ✓ | ✓ | ✓ |
| ml_regression | ✓ | | ✓ | ✓ | ✓ | ✓ |
| optimization | ✓ | | ✓ | ✓ | ✓ | ✓ |
| app_build | ✓ | ✓ | | ✓ | ✓ | ✓ |
| service_api | ✓ | ✓ | | ✓ | ✓ | ✓ |
| data_engineering | ✓ | | ✓ | ✓ | ✓ | ✓ |

When a project has multiple capabilities, the effective phases are the **union** of all capability phases, presented in canonical order.

## Templates and Default Capabilities

Each project template has default capabilities pre-configured:

| Template | Category | Default Capabilities |
|----------|----------|---------------------|
| Blank Project | general | (none - user selects) |
| App Build (React + API) | application | `app_build`, `service_api` |
| Analytics – Forecasting | analytics | `data_pipeline`, `analytics_forecasting` |
| Analytics – BI Dashboard | analytics | `data_pipeline`, `analytics_bi_dashboard`, `app_build` |
| ML – Classification | ml | `data_pipeline`, `ml_classification` |
| ML – Regression | ml | `data_pipeline`, `ml_regression` |
| Optimization – Resource Allocation | optimization | `data_pipeline`, `optimization` |
| Service / API Project | backend | `service_api` |
| Data Engineering Pipeline | data | `data_engineering` |

## Creating a Multi-Capability Project

### From the RSG UI

1. Click **New Project** button
2. Enter a project name
3. Select a template (which sets default capabilities)
4. Modify capabilities if needed:
   - Check/uncheck capability checkboxes
   - Templates allow override by default
5. Enter client name
6. Click **Create Project**

### Via API

```bash
# Create project with specific capabilities
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "My Multi-Cap Project",
    "client": "kearney-default",
    "template_id": "blank",
    "capabilities": ["data_pipeline", "ml_classification", "app_build"]
  }'
```

## API Endpoints

### GET /project-templates

Returns available templates with their default capabilities:

```json
[
  {
    "id": "analytics_forecasting",
    "name": "Analytics – Forecasting",
    "description": "Time-series forecasting with data pipeline",
    "project_type": "analytics_forecasting",
    "category": "analytics",
    "default_capabilities": ["data_pipeline", "analytics_forecasting"],
    "allow_capability_override": true
  }
]
```

### POST /projects

Create a project with capabilities:

Request:
```json
{
  "project_name": "My Project",
  "client": "kearney-default",
  "template_id": "blank",
  "capabilities": ["data_pipeline", "ml_classification"]
}
```

Response includes:
```json
{
  "project_id": "proj_abc123",
  "capabilities": ["data_pipeline", "ml_classification"],
  "phases": ["planning", "data", "development", "qa", "documentation"]
}
```

### GET /projects/{project_id}

Returns project with capabilities and effective phases:

```json
{
  "project_id": "proj_abc123",
  "project_name": "My Project",
  "project_type": "generic",
  "capabilities": ["data_pipeline", "ml_classification"],
  "phases": ["planning", "data", "development", "qa", "documentation"],
  "current_phase": "planning",
  "completed_phases": []
}
```

## How Phases Are Determined

1. When a project is created:
   - If `capabilities` provided in request, use those
   - Otherwise, use template's `default_capabilities`
   - If neither, use empty list

2. Effective phases are computed:
   - Union of all phases from all capabilities
   - Sorted in canonical order: planning → architecture → data → development → qa → documentation

3. If no capabilities or no valid capabilities:
   - Default 6-phase workflow is used

## Backward Compatibility

- Projects created before this feature will have `capabilities: []` and `phases: []`
- They will use the default 6-phase workflow
- No migration needed; defaults are applied at load time

## Integration with Planning

During the planning phase, agents receive:
- Project capabilities list
- Effective phases
- This context helps agents plan appropriately for multi-capability projects

## Demo Templates

Demo-specific templates (e.g., Territory Demo, Golden Path) are **not shown** in the RSG UI New Project flow. They exist in `EXAMPLE_TEMPLATES` for internal use and can still be accessed via API by template ID.

## KDS Compliance

The UI uses Kearney Design System tokens:
- Purple (`#7823DC`) for emphasis and selected states
- Violet tints for backgrounds
- Charcoal for text
- **No red/green** - purple used for all status indicators
