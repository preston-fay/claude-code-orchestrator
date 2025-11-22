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


# Available project templates
TEMPLATES = [
    ProjectTemplate(
        id="blank",
        name="Blank Project",
        description="Start with an empty project workspace",
        project_type="generic",
        category="general",
    ),
    ProjectTemplate(
        id="golden_path_analytics",
        name="Golden Path - Demand Forecasting",
        description="Analytics project with time-series forecasting template",
        project_type="analytics_forecasting",
        default_intake_path="examples/golden_path/intake_analytics_forecasting.yaml",
        category="analytics",
    ),
    # Territory Demo - backend endpoints remain for external Territory Optimizer app
    ProjectTemplate(
        id="territory_poc_midwest",
        name="Territory Demo (internal)",
        description="Demo template for Territory Optimizer app - creates workspace for scoring/clustering",
        project_type="territory_poc",
        default_intake_path="examples/territory_poc/intake_territory_poc.yaml",
        category="demo",
    ),
    # App Builder - for building complete applications
    ProjectTemplate(
        id="app_build",
        name="App Build (React + FastAPI)",
        description="Build complete applications with React frontend and FastAPI backend using agent-driven development",
        project_type="app_build",
        default_intake_path=None,
        default_metadata={
            "stack": ["react", "fastapi"],
            "include_scaffolding": True,
            "use_kds": True,
        },
        category="application",
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
