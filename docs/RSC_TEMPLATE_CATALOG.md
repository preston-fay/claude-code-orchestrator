# RSC Template Catalog V2

The Template Catalog V2 provides a rich set of project templates with full metadata for the Launchpad UI and orchestration integration.

## Template Structure

Each template includes:

```python
class ProjectTemplate(BaseModel):
    id: str                           # Unique identifier
    name: str                         # Template name
    title: str                        # Display title for Launchpad
    description: str                  # Brief description
    project_type: str                 # Project type classification
    category: str                     # Category for filtering
    default_capabilities: list[str]   # Capabilities to pre-select
    suggested_brief: str              # Pre-filled project brief
    best_for: str                     # Use case description
    icon: str                         # Icon identifier
```

## Available Templates

### Analytics Forecasting App

- **ID**: `analytics_forecast_app`
- **Category**: Analytics
- **Capabilities**: `data_pipeline`, `analytics_forecasting`, `app_build`
- **Best For**: Analytics, Planning, Forecasting
- **Description**: Build a complete forecasting pipeline with analytics dashboard support.

### ML Classification Model

- **ID**: `ml_classification`
- **Category**: ML
- **Capabilities**: `data_pipeline`, `ml_classification`, `model_evaluation`
- **Best For**: Classification, Categorization, Prediction
- **Description**: Build a classification model with data pipeline and evaluation metrics.

### ML Regression Model

- **ID**: `ml_regression`
- **Category**: ML
- **Capabilities**: `data_pipeline`, `ml_regression`, `model_evaluation`
- **Best For**: Regression, Value Prediction, Trend Analysis
- **Description**: Build a regression model for continuous value prediction with analytics.

### Optimization Solution

- **ID**: `optimization`
- **Category**: Optimization
- **Capabilities**: `data_pipeline`, `optimization`, `analytics_reporting`
- **Best For**: Resource Allocation, Scheduling, Routing
- **Description**: Build optimization models for resource allocation, scheduling, or routing problems.

### Full-Stack Web App

- **ID**: `web_app`
- **Category**: App
- **Capabilities**: `backend_api`, `frontend_ui`, `app_build`
- **Best For**: Web Apps, User Interfaces, Full-Stack
- **Description**: Full-stack web application with React frontend and FastAPI backend.

### API Service

- **ID**: `backend_api`
- **Category**: App
- **Capabilities**: `backend_api`, `database`
- **Best For**: APIs, Microservices, Backend
- **Description**: RESTful API backend service with FastAPI and database integration.

### Analytics Dashboard

- **ID**: `dashboard`
- **Category**: Analytics
- **Capabilities**: `data_pipeline`, `analytics_dashboard`, `analytics_reporting`
- **Best For**: Data Visualization, BI, Reporting
- **Description**: Interactive dashboard for data visualization and business intelligence.

### Blank Project

- **ID**: `blank`
- **Category**: General
- **Capabilities**: `generic`
- **Best For**: Custom, Experimental, Ad-hoc
- **Description**: Start with an empty project workspace for custom development.

## API Endpoints

### List Templates

```http
GET /project-templates
```

Returns all templates with V2 metadata:

```json
[
  {
    "id": "analytics_forecast_app",
    "name": "Analytics - Forecasting App",
    "title": "Analytics Forecasting App",
    "description": "Build a complete forecasting pipeline...",
    "project_type": "analytics",
    "category": "analytics",
    "default_capabilities": ["data_pipeline", "analytics_forecasting", "app_build"],
    "suggested_brief": "Build a forecasting pipeline and a web app...",
    "best_for": "Analytics, Planning, Forecasting",
    "icon": "analytics"
  }
]
```

### Get Template by ID

```python
from orchestrator_v2.config.templates import get_template_by_id

template = get_template_by_id("analytics_forecast_app")
```

### List by Category

```python
from orchestrator_v2.config.templates import list_templates_by_category

ml_templates = list_templates_by_category("ml")
```

## Template Icons

Icon identifiers used in the UI:

| Icon ID | Emoji | Template |
|---------|-------|----------|
| `analytics` | 📊 | Analytics Forecasting |
| `classification` | 🏷️ | ML Classification |
| `regression` | 📈 | ML Regression |
| `optimization` | ⚙️ | Optimization |
| `webapp` | 🌐 | Web Application |
| `api` | 🔌 | API Service |
| `dashboard` | 📉 | Analytics Dashboard |
| `blank` | 📄 | Blank Project |

## Capabilities Reference

| Capability | Description |
|------------|-------------|
| `data_pipeline` | Data ingestion, validation, transformation |
| `analytics_forecasting` | Time series and predictive analytics |
| `analytics_dashboard` | Interactive visualizations |
| `analytics_reporting` | Reports and KPI summaries |
| `ml_classification` | Classification model training |
| `ml_regression` | Regression model training |
| `model_evaluation` | Model performance metrics |
| `optimization` | Mathematical optimization |
| `backend_api` | REST API development |
| `frontend_ui` | React/web UI development |
| `app_build` | Full application scaffolding |
| `database` | Database integration |
| `generic` | General-purpose development |

## Integration with Orchestration

Each template maps to an orchestration profile that defines:

- Which phases to execute
- Which agents to use in each phase
- Which skills to apply
- Which governance rules to enforce

See [RSC Orchestration Profiles](RSC_ORCHESTRATION_PROFILES.md) for details.

## Creating Custom Templates

To add a new template:

1. Add entry to `TEMPLATE_CATALOG` in `orchestrator_v2/config/templates.py`
2. Create corresponding orchestration profile in `orchestrator_v2/engine/orchestration_profiles.py`
3. Update frontend types if adding new fields

Example:

```python
ProjectTemplate(
    id="custom_template",
    name="Custom Template",
    title="Custom Template Display",
    description="Description for users",
    project_type="custom",
    category="general",
    default_capabilities=["capability1", "capability2"],
    suggested_brief="Suggested brief text...",
    best_for="Use case 1, Use case 2",
    icon="default",
)
```

## Related Documentation

- [RSC Launchpad](RSC_LAUNCHPAD.md)
- [RSC Orchestration Profiles](RSC_ORCHESTRATION_PROFILES.md)
