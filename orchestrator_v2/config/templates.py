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
    # Default capabilities for projects created from this template
    default_capabilities: list[str] = []


# Available project templates - Generic templates only (no demo-specific)
TEMPLATES = [
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        description="Start with an empty project workspace",
        project_type="generic",
        category="general",
        default_capabilities=["generic"],
    ),
    ProjectTemplate(
        id="analytics_forecasting",
        name="Analytics - Time Series Forecasting",
        description="Analytics project with time-series forecasting capabilities",
        project_type="analytics",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_forecasting"],
    ),
    ProjectTemplate(
        id="analytics_dashboard",
        name="Analytics - Dashboard & Reporting",
        description="Analytics project with dashboard and reporting capabilities",
        project_type="analytics",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_dashboard", "analytics_reporting"],
    ),
    ProjectTemplate(
        id="ml_classification",
        name="Machine Learning - Classification",
        description="ML project for classification tasks",
        project_type="ml",
        category="ml",
        default_capabilities=["data_pipeline", "ml_classification"],
    ),
    ProjectTemplate(
        id="ml_regression",
        name="Machine Learning - Regression",
        description="ML project for regression and prediction tasks",
        project_type="ml",
        category="ml",
        default_capabilities=["data_pipeline", "ml_regression"],
    ),
    ProjectTemplate(
        id="optimization",
        name="Optimization & Operations Research",
        description="Project for optimization and operations research problems",
        project_type="optimization",
        category="optimization",
        default_capabilities=["data_pipeline", "optimization"],
    ),
    ProjectTemplate(
        id="web_app",
        name="Web Application",
        description="Full-stack web application with backend API and frontend UI",
        project_type="webapp",
        category="app",
        default_capabilities=["backend_api", "frontend_ui", "app_build"],
    ),
    ProjectTemplate(
        id="backend_api",
        name="Backend API",
        description="RESTful API backend service",
        project_type="api",
        category="app",
        default_capabilities=["backend_api"],
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
