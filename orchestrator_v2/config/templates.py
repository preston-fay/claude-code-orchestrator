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
    title: str  # Display title for Launchpad
    description: str
    project_type: str
    default_intake_path: str | None = None  # Relative to repo root
    default_metadata: dict[str, Any] = {}
    category: str = "general"
    # Default capabilities for projects created from this template
    default_capabilities: list[str] = []
    # V2 fields for Launchpad
    suggested_brief: str = ""
    best_for: str = ""
    icon: str = "default"


# TEMPLATE_CATALOG - V2 template catalog with full metadata
TEMPLATE_CATALOG: list[ProjectTemplate] = [
    ProjectTemplate(
        id="analytics_forecast_app",
        name="Analytics - Forecasting App",
        title="Analytics Forecasting App",
        description="Build a complete forecasting pipeline with analytics dashboard support.",
        project_type="analytics",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_forecasting", "app_build"],
        suggested_brief="Build a forecasting pipeline and a web app to visualize predictions.",
        best_for="Analytics, Planning, Forecasting",
        icon="analytics",
    ),
    ProjectTemplate(
        id="ml_classification",
        name="Machine Learning - Classification",
        title="ML Classification Model",
        description="Build a classification model with data pipeline and evaluation metrics.",
        project_type="ml",
        category="ml",
        default_capabilities=["data_pipeline", "ml_classification", "model_evaluation"],
        suggested_brief="Build a classification model to categorize data into predefined classes with performance metrics.",
        best_for="Classification, Categorization, Prediction",
        icon="classification",
    ),
    ProjectTemplate(
        id="ml_regression",
        name="Machine Learning - Regression",
        title="ML Regression Model",
        description="Build a regression model for continuous value prediction with analytics.",
        project_type="ml",
        category="ml",
        default_capabilities=["data_pipeline", "ml_regression", "model_evaluation"],
        suggested_brief="Build a regression model to predict continuous values with statistical analysis.",
        best_for="Regression, Value Prediction, Trend Analysis",
        icon="regression",
    ),
    ProjectTemplate(
        id="optimization",
        name="Optimization & Operations Research",
        title="Optimization Solution",
        description="Build optimization models for resource allocation, scheduling, or routing problems.",
        project_type="optimization",
        category="optimization",
        default_capabilities=["data_pipeline", "optimization", "analytics_reporting"],
        suggested_brief="Build an optimization model to maximize efficiency or minimize costs in resource allocation.",
        best_for="Resource Allocation, Scheduling, Routing",
        icon="optimization",
    ),
    ProjectTemplate(
        id="web_app",
        name="Web Application",
        title="Full-Stack Web App",
        description="Full-stack web application with React frontend and FastAPI backend.",
        project_type="webapp",
        category="app",
        default_capabilities=["backend_api", "frontend_ui", "app_build"],
        suggested_brief="Build a modern web application with React frontend and FastAPI backend API.",
        best_for="Web Apps, User Interfaces, Full-Stack",
        icon="webapp",
    ),
    ProjectTemplate(
        id="backend_api",
        name="Backend API Service",
        title="API Service",
        description="RESTful API backend service with FastAPI and database integration.",
        project_type="api",
        category="app",
        default_capabilities=["backend_api", "database"],
        suggested_brief="Build a RESTful API service with proper authentication and database integration.",
        best_for="APIs, Microservices, Backend",
        icon="api",
    ),
    ProjectTemplate(
        id="dashboard",
        name="Analytics Dashboard",
        title="Analytics Dashboard",
        description="Interactive dashboard for data visualization and business intelligence.",
        project_type="dashboard",
        category="analytics",
        default_capabilities=["data_pipeline", "analytics_dashboard", "analytics_reporting"],
        suggested_brief="Build an interactive dashboard to visualize data insights and key performance indicators.",
        best_for="Data Visualization, BI, Reporting",
        icon="dashboard",
    ),
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        title="Blank Project",
        description="Start with an empty project workspace for custom development.",
        project_type="generic",
        category="general",
        default_capabilities=["generic"],
        suggested_brief="",
        best_for="Custom, Experimental, Ad-hoc",
        icon="blank",
    ),
]

# Legacy TEMPLATES list for backward compatibility
TEMPLATES = TEMPLATE_CATALOG


def get_template_by_id(template_id: str) -> ProjectTemplate | None:
    """Get a template by its ID.

    Args:
        template_id: Template identifier.

    Returns:
        ProjectTemplate if found, None otherwise.
    """
    for template in TEMPLATE_CATALOG:
        if template.id == template_id:
            return template
    return None


def list_templates() -> list[ProjectTemplate]:
    """List all available templates.

    Returns:
        List of all templates.
    """
    return TEMPLATE_CATALOG


def list_templates_by_category(category: str) -> list[ProjectTemplate]:
    """List templates by category.

    Args:
        category: Category to filter by.

    Returns:
        List of templates in category.
    """
    return [t for t in TEMPLATE_CATALOG if t.category == category]
