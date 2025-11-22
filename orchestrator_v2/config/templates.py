"""
Project templates for Orchestrator v2.

Defines generic, reusable project templates that provide
pre-configured project types with default settings.

Templates should be patterns of work, NOT example apps.
Example apps belong in /examples or separate repos.
"""

from typing import Any

from pydantic import BaseModel


class ProjectTemplate(BaseModel):
    """A project template definition."""
    id: str
    name: str
    description: str
    project_type: str
    default_intake_path: str | None = None  # Relative to repo root
    default_metadata: dict[str, Any] = {}
    category: str = "general"


# Available project templates - GENERIC PATTERNS ONLY
# Demo/example templates are NOT included here
TEMPLATES = [
    # General
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        description="Start with an empty project workspace",
        project_type="generic",
        category="general",
    ),

    # Application Development
    ProjectTemplate(
        id="app_build",
        name="App Build (React + API)",
        description="Full-stack application with React frontend and FastAPI backend",
        project_type="application",
        category="application",
    ),

    # Analytics
    ProjectTemplate(
        id="analytics_forecasting",
        name="Analytics - Forecasting",
        description="Time-series forecasting and demand prediction pipelines",
        project_type="analytics_forecasting",
        category="analytics",
    ),
    ProjectTemplate(
        id="analytics_bi",
        name="Analytics - BI Dashboard",
        description="Business intelligence and reporting dashboards",
        project_type="analytics_bi",
        category="analytics",
    ),

    # Machine Learning
    ProjectTemplate(
        id="ml_classification",
        name="ML - Classification",
        description="Classification model training and inference pipeline",
        project_type="ml_classification",
        category="ml",
    ),
    ProjectTemplate(
        id="ml_regression",
        name="ML - Regression",
        description="Regression model training and prediction pipeline",
        project_type="ml_regression",
        category="ml",
    ),

    # Optimization
    ProjectTemplate(
        id="optimization_resource",
        name="Optimization - Resource Allocation",
        description="Operations research and resource optimization solvers",
        project_type="optimization",
        category="optimization",
    ),

    # Backend Services
    ProjectTemplate(
        id="service_api",
        name="Service/API Project",
        description="Backend microservice with FastAPI or Node.js",
        project_type="service_api",
        category="backend",
    ),

    # Data Engineering
    ProjectTemplate(
        id="data_engineering",
        name="Data Engineering Pipeline",
        description="ETL/ELT pipelines and data warehouse workflows",
        project_type="data_engineering",
        category="data",
    ),
]


# Example/demo templates - NOT shown in New Project flow
# These are for reference and can be loaded separately
EXAMPLE_TEMPLATES = [
    ProjectTemplate(
        id="territory_poc_midwest",
        name="Territory Optimizer Demo",
        description="Demo: Territory scoring and clustering for retail optimization",
        project_type="territory_poc",
        default_intake_path="examples/territory_poc/intake_territory_poc.yaml",
        category="demo",
    ),
    ProjectTemplate(
        id="golden_path_analytics",
        name="Golden Path Forecasting Demo",
        description="Demo: Demand forecasting example with ARIMA/Prophet",
        project_type="analytics_forecasting",
        default_intake_path="examples/golden_path/intake_analytics_forecasting.yaml",
        category="demo",
    ),
]


def get_template_by_id(template_id: str) -> ProjectTemplate | None:
    """Get a template by its ID.

    Searches both active templates and examples.

    Args:
        template_id: Template identifier.

    Returns:
        ProjectTemplate if found, None otherwise.
    """
    # Check active templates first
    for template in TEMPLATES:
        if template.id == template_id:
            return template

    # Also check examples (for backward compatibility)
    for template in EXAMPLE_TEMPLATES:
        if template.id == template_id:
            return template

    return None


def list_templates(include_demos: bool = False) -> list[ProjectTemplate]:
    """List available templates.

    Args:
        include_demos: If True, include demo/example templates.

    Returns:
        List of templates.
    """
    if include_demos:
        return TEMPLATES + EXAMPLE_TEMPLATES
    return TEMPLATES


def list_templates_by_category(category: str) -> list[ProjectTemplate]:
    """List templates by category.

    Args:
        category: Category to filter by.

    Returns:
        List of templates in category.
    """
    return [t for t in TEMPLATES if t.category == category]


def list_example_templates() -> list[ProjectTemplate]:
    """List example/demo templates only.

    Returns:
        List of demo templates.
    """
    return EXAMPLE_TEMPLATES
