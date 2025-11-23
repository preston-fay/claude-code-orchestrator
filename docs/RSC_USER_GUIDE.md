# Ready-Set-Code User Guide

This guide explains how to use the Ready-Set-Code (RSC) orchestrator to manage projects end-to-end.

## Creating a Project

### Required Fields

When creating a new project via the UI or API, you must provide:

1. **Project Name** - A descriptive name for your project
2. **Project Brief** - A clear description of the project goals, requirements, and expected outcomes
3. **Capabilities** (optional) - The types of work the project involves

### Using Templates

Templates provide pre-configured capabilities and a brief stub:

| Template | Capabilities | Use Case |
|----------|-------------|----------|
| Blank Project | None | Manual configuration |
| Data Pipeline | data_pipeline | ETL and data processing |
| Analytics & Forecasting | analytics_forecasting, data_pipeline | Time-series predictions |
| ML Classification | ml_classification, data_pipeline | Categorization models |
| Application Build | app_build | Web apps and dashboards |
| Service API | service_api | Backend API development |
| Optimization | optimization, data_pipeline | Operations research |

### API Example

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Sales Forecasting Q1",
    "brief": "Develop a forecasting model to predict Q1 sales using historical transaction data with 85% accuracy target.",
    "capabilities": ["analytics_forecasting", "data_pipeline"],
    "client": "acme-corp"
  }'
```

## Understanding Phases and RSG Mapping

### Capability-Driven Phases

The phases in your project are determined by the capabilities you select:

| Capability | Phases |
|------------|--------|
| data_pipeline | planning, architecture, data |
| analytics_forecasting | planning, architecture, data, development, qa, documentation |
| app_build | planning, architecture, development, qa, documentation |
| service_api | planning, architecture, development, qa, documentation |

If multiple capabilities are selected, the system combines all required phases.

### RSG Stage Mapping

The Ready-Set-Go framework maps to phases as follows:

- **READY**: Planning + Architecture
  - System design and technical specifications
  - Data models and schemas
  - Technology selection

- **SET**: Data + Early Development
  - Data pipelines and processing
  - Core implementation
  - Feature development

- **GO**: Development + QA + Documentation
  - Testing and validation
  - Documentation
  - Final review

## Project Detail Page

The project detail page shows:

- **Project Info**: Type, client, status, created date
- **Capabilities**: Badge display of selected capabilities
- **Project Brief**: The description you provided
- **Workspace Path**: Where project files are stored
- **External Links**: Links to code repository and live application (if configured)
- **RSG Status**: Cards showing Ready/Set/Go progress
- **Phases**: List of phases derived from capabilities
- **Checkpoints**: History of completed phase checkpoints

## External Links (Deliverables)

RSC is the control plane - your deliverables (apps, APIs) live externally.

### Setting Links via API

```bash
curl -X POST http://localhost:8000/projects/{project_id}/links \
  -H "Content-Type: application/json" \
  -d '{
    "app_repo_url": "https://github.com/org/my-app",
    "app_url": "https://my-app.example.com"
  }'
```

Once set, these links appear in the "Deliverables" section of the project detail page.

## Running Phases

### Via UI

1. Navigate to the project detail page
2. In the RSG Status section, click "Start Ready", "Start Set", or "Start Go"
3. Monitor progress in the Run Activity panel

### Via API

```bash
# Start Ready (Planning + Architecture)
curl -X POST http://localhost:8000/rsg/{project_id}/ready/start

# Start Set (Data + Development)
curl -X POST http://localhost:8000/rsg/{project_id}/set/start

# Start Go (Development + QA + Documentation)
curl -X POST http://localhost:8000/rsg/{project_id}/go/start

# Get RSG overview
curl http://localhost:8000/rsg/{project_id}/overview
```

## Templates API

List available templates:

```bash
curl http://localhost:8000/project-templates
```

Each template includes:
- `id` - Template identifier
- `name` - Display name
- `description` - What the template is for
- `project_type` - Internal type
- `category` - Grouping (general, analytics, ml, app, etc.)
- `capabilities` - Pre-configured capabilities
- `brief_template` - Suggested brief text

## Project Lifecycle

1. **Create** - Define project with name, brief, capabilities
2. **Ready** - Run planning and architecture phases
3. **Set** - Run data engineering and initial development
4. **Go** - Complete development, testing, and documentation
5. **Deliver** - Link external repository and live application

## API Reference

### Projects

- `GET /projects` - List all projects
- `POST /projects` - Create a new project
- `GET /projects/{id}` - Get project details
- `DELETE /projects/{id}` - Delete a project
- `POST /projects/{id}/links` - Update external links
- `GET /projects/{id}/status` - Get workflow status
- `POST /projects/{id}/advance` - Advance to next phase

### RSG

- `POST /rsg/{id}/ready/start` - Start Ready stage
- `GET /rsg/{id}/ready/status` - Get Ready status
- `POST /rsg/{id}/set/start` - Start Set stage
- `GET /rsg/{id}/set/status` - Get Set status
- `POST /rsg/{id}/go/start` - Start Go stage
- `GET /rsg/{id}/go/status` - Get Go status
- `GET /rsg/{id}/overview` - Get combined RSG overview

### Templates

- `GET /project-templates` - List available templates

## Troubleshooting

### Project won't create

- Ensure both project name and brief are provided
- Check that the API server is running

### Phases don't match expected

- Verify the capabilities selected for your project
- Each capability determines which phases are included

### Links not showing

- Use the `/projects/{id}/links` endpoint to set them
- Refresh the project detail page after setting
