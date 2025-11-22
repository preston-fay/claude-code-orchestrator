"""
Project templates for Orchestrator v2.

Defines project templates that provide pre-configured
project types with default settings.
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
    # Default capabilities for this template
    default_capabilities: list[str] = []
    # Whether user can override default capabilities
    allow_capability_override: bool = True


# Available project templates (generic patterns only)
# These are surfaced in the RSG UI New Project flow
TEMPLATES = [
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        description="Start with an empty project workspace",
        project_type="generic",
        category="general",
        default_capabilities=[],  # User selects manually
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="app_build",
        name="App Build (React + API)",
        description="Full-stack application with React frontend and API backend",
        project_type="application",
        category="application",
        default_capabilities=["app_build", "service_api"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="analytics_forecasting",
        name="Analytics – Forecasting",
        description="Time-series forecasting with data pipeline",
        project_type="analytics_forecasting",
        default_intake_path="examples/golden_path/intake_analytics_forecasting.yaml",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_forecasting"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="analytics_bi_dashboard",
        name="Analytics – BI Dashboard",
        description="Business intelligence dashboard with data pipeline and UI",
        project_type="analytics_bi",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_bi_dashboard", "app_build"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="ml_classification",
        name="ML – Classification",
        description="Machine learning classification model with data pipeline",
        project_type="ml_classification",
        category="ml",
        default_capabilities=["data_pipeline", "ml_classification"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="ml_regression",
        name="ML – Regression",
        description="Machine learning regression model with data pipeline",
        project_type="ml_regression",
        category="ml",
        default_capabilities=["data_pipeline", "ml_regression"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="optimization",
        name="Optimization – Resource Allocation",
        description="Mathematical optimization for resource allocation problems",
        project_type="optimization",
        category="optimization",
        default_capabilities=["data_pipeline", "optimization"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="service_api",
        name="Service / API Project",
        description="Backend service or API without frontend",
        project_type="service",
        category="backend",
        default_capabilities=["service_api"],
        allow_capability_override=True,
    ),
    ProjectTemplate(
        id="data_engineering",
        name="Data Engineering Pipeline",
        description="Data engineering and ETL pipeline project",
        project_type="data_engineering",
        category="data",
        default_capabilities=["data_engineering"],
        allow_capability_override=True,
    ),
]

# Example/demo templates - NOT returned by normal template endpoints
# These are for internal testing and external apps like Territory Optimizer
EXAMPLE_TEMPLATES = [
    ProjectTemplate(
        id="territory_poc_midwest",
        name="Territory Demo (internal)",
        description="Demo template for Territory Optimizer app - creates workspace for scoring/clustering",
        project_type="territory_poc",
        default_intake_path="examples/territory_poc/intake_territory_poc.yaml",
        category="demo",
        default_capabilities=["data_pipeline", "optimization"],
        allow_capability_override=False,
    ),
    ProjectTemplate(
        id="golden_path_analytics",
        name="Golden Path Demo",
        description="Demo template showing golden path analytics workflow",
        project_type="analytics_forecasting",
        default_intake_path="examples/golden_path/intake_analytics_forecasting.yaml",
        category="demo",
        default_capabilities=["data_pipeline", "analytics_forecasting"],
        allow_capability_override=False,
    ),
]


def get_template_by_id(template_id: str) -> ProjectTemplate | None:
    """Get a template by its ID.

    Searches both public templates and example templates.

    Args:
        template_id: Template identifier.

    Returns:
        ProjectTemplate if found, None otherwise.
    """
    # Search public templates first
    for template in TEMPLATES:
        if template.id == template_id:
            return template
    # Then search example templates (for internal use)
    for template in EXAMPLE_TEMPLATES:
        if template.id == template_id:
            return template
    return None


def list_templates() -> list[ProjectTemplate]:
    """List all available templates (public only).

    Returns:
        List of public templates (excludes demo/example templates).
    """
    return TEMPLATES


def list_templates_by_category(category: str) -> list[ProjectTemplate]:
    """List templates by category (public only).

    Args:
        category: Category to filter by.

    Returns:
        List of public templates in category.
    """
    return [t for t in TEMPLATES if t.category == category]


def list_example_templates() -> list[ProjectTemplate]:
    """List example/demo templates (internal use only).

    Returns:
        List of example templates.
    """
    return EXAMPLE_TEMPLATES
