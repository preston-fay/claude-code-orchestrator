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
    # RSC Hardening - capabilities and brief template
    capabilities: list[str] = []
    brief_template: str = ""  # Pre-filled brief stub for this template


# Available project templates
TEMPLATES = [
    # Generic templates (for general use)
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        description="Start with an empty project workspace - configure capabilities manually",
        project_type="generic",
        category="general",
        capabilities=[],
        brief_template="",
    ),
    ProjectTemplate(
        id="data_pipeline",
        name="Data Pipeline",
        description="Build ETL pipelines, data processing, and transformation workflows",
        project_type="data_pipeline",
        category="data",
        capabilities=["data_pipeline"],
        brief_template="Build a data pipeline to [describe data sources] and transform into [describe target format/destination].",
    ),
    ProjectTemplate(
        id="analytics_forecasting",
        name="Analytics & Forecasting",
        description="Time-series analysis, demand forecasting, and predictive analytics",
        project_type="analytics_forecasting",
        category="analytics",
        capabilities=["analytics_forecasting", "data_pipeline"],
        brief_template="Develop a forecasting solution to predict [what to predict] based on [data sources] with [accuracy/business goal].",
    ),
    ProjectTemplate(
        id="ml_classification",
        name="ML Classification",
        description="Machine learning classification models for categorization tasks",
        project_type="ml_classification",
        category="ml",
        capabilities=["ml_classification", "data_pipeline"],
        brief_template="Build a classification model to categorize [what] into [categories] using [data sources].",
    ),
    ProjectTemplate(
        id="app_build",
        name="Application Build",
        description="Web application or dashboard development",
        project_type="app_build",
        category="app",
        capabilities=["app_build"],
        brief_template="Build a [web app/dashboard] that enables users to [key functionality] with [key features].",
    ),
    ProjectTemplate(
        id="service_api",
        name="Service API",
        description="Backend API service development",
        project_type="service_api",
        category="api",
        capabilities=["service_api"],
        brief_template="Develop an API service that provides [functionality] with endpoints for [key operations].",
    ),
    ProjectTemplate(
        id="optimization",
        name="Optimization",
        description="Operations research and optimization solutions",
        project_type="optimization",
        category="optimization",
        capabilities=["optimization", "data_pipeline"],
        brief_template="Optimize [what to optimize] subject to [constraints] to achieve [objective].",
    ),
    # Demo/Example templates (moved to separate category)
    ProjectTemplate(
        id="golden_path_analytics",
        name="Golden Path - Demand Forecasting",
        description="Example: Analytics project with time-series forecasting template",
        project_type="analytics_forecasting",
        default_intake_path="examples/golden_path/intake_analytics_forecasting.yaml",
        category="example",
        capabilities=["analytics_forecasting", "data_pipeline"],
        brief_template="Build a demand forecasting model to predict sales volume using historical transaction data.",
    ),
    ProjectTemplate(
        id="territory_poc_midwest",
        name="Territory Demo (internal)",
        description="Example: Territory Optimizer app - creates workspace for scoring/clustering",
        project_type="territory_poc",
        default_intake_path="examples/territory_poc/intake_territory_poc.yaml",
        category="example",
        capabilities=["territory_poc", "data_pipeline", "optimization"],
        brief_template="Optimize territory assignments for sales representatives to balance workload and maximize coverage.",
    ),
]


def get_template_by_id(template_id: str) -> ProjectTemplate | None:
    """Get a template by its ID.

    Args:
        template_id: Template identifier.

    Returns:
        ProjectTemplate if found, None otherwise.
    """
    for template in TEMPLATES:
        if template.id == template_id:
            return template
    return None


def list_templates() -> list[ProjectTemplate]:
    """List all available templates.

    Returns:
        List of all templates.
    """
    return TEMPLATES


def list_templates_by_category(category: str) -> list[ProjectTemplate]:
    """List templates by category.

    Args:
        category: Category to filter by.

    Returns:
        List of templates in category.
    """
    return [t for t in TEMPLATES if t.category == category]
