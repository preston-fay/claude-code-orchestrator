"""
Orchestration profiles for project templates.

Maps template IDs to orchestration configurations including
phases, agents, skills, and governance rules.
"""

from typing import Any
from pydantic import BaseModel


class OrchestrationProfile(BaseModel):
    """Orchestration profile for a project template."""
    template_id: str
    phases: list[str]
    agents_by_phase: dict[str, list[str]]
    skills_by_phase: dict[str, list[str]]
    governance_rules: list[str]


# Orchestration profile mapping
ORCHESTRATION_PROFILES: dict[str, OrchestrationProfile] = {
    "analytics_forecast_app": OrchestrationProfile(
        template_id="analytics_forecast_app",
        phases=["planning", "architecture", "data", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect", "data"],
            "architecture": ["architect"],
            "data": ["data"],
            "development": ["developer", "data"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "data_assessment"],
            "architecture": ["system_design", "data_architecture"],
            "data": ["time_series_analytics", "data_pipeline", "feature_engineering"],
            "development": ["forecasting_models", "dashboard_development"],
            "qa": ["model_validation", "integration_testing"],
            "documentation": ["technical_writing", "api_documentation"],
        },
        governance_rules=[
            "data_quality_check",
            "model_performance_threshold",
            "code_review_required",
            "documentation_complete",
        ],
    ),
    "ml_classification": OrchestrationProfile(
        template_id="ml_classification",
        phases=["planning", "architecture", "data", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect", "data"],
            "architecture": ["architect"],
            "data": ["data"],
            "development": ["developer", "data"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "ml_problem_framing"],
            "architecture": ["ml_architecture", "data_architecture"],
            "data": ["data_pipeline", "feature_engineering", "data_validation"],
            "development": ["classification_models", "model_training"],
            "qa": ["model_evaluation", "cross_validation", "bias_testing"],
            "documentation": ["model_documentation", "api_documentation"],
        },
        governance_rules=[
            "data_quality_check",
            "model_accuracy_threshold",
            "bias_fairness_check",
            "code_review_required",
        ],
    ),
    "ml_regression": OrchestrationProfile(
        template_id="ml_regression",
        phases=["planning", "architecture", "data", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect", "data"],
            "architecture": ["architect"],
            "data": ["data"],
            "development": ["developer", "data"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "ml_problem_framing"],
            "architecture": ["ml_architecture", "data_architecture"],
            "data": ["data_pipeline", "feature_engineering", "data_validation"],
            "development": ["regression_models", "model_training"],
            "qa": ["model_evaluation", "residual_analysis", "performance_testing"],
            "documentation": ["model_documentation", "api_documentation"],
        },
        governance_rules=[
            "data_quality_check",
            "model_rmse_threshold",
            "code_review_required",
            "documentation_complete",
        ],
    ),
    "optimization": OrchestrationProfile(
        template_id="optimization",
        phases=["planning", "architecture", "data", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect", "data"],
            "architecture": ["architect"],
            "data": ["data"],
            "development": ["developer"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "optimization_problem_framing"],
            "architecture": ["optimization_architecture", "data_architecture"],
            "data": ["data_pipeline", "constraint_modeling"],
            "development": ["optimization_solvers", "constraint_programming"],
            "qa": ["solution_validation", "sensitivity_analysis"],
            "documentation": ["technical_writing", "solution_documentation"],
        },
        governance_rules=[
            "data_quality_check",
            "solution_feasibility_check",
            "code_review_required",
            "documentation_complete",
        ],
    ),
    "web_app": OrchestrationProfile(
        template_id="web_app",
        phases=["planning", "architecture", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect"],
            "architecture": ["architect"],
            "development": ["developer"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "ui_ux_design"],
            "architecture": ["system_design", "api_design", "database_design"],
            "development": ["react_development", "fastapi_development", "database_integration"],
            "qa": ["unit_testing", "integration_testing", "e2e_testing"],
            "documentation": ["api_documentation", "user_guide"],
        },
        governance_rules=[
            "code_review_required",
            "test_coverage_threshold",
            "security_scan",
            "documentation_complete",
        ],
    ),
    "backend_api": OrchestrationProfile(
        template_id="backend_api",
        phases=["planning", "architecture", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect"],
            "architecture": ["architect"],
            "development": ["developer"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "api_design"],
            "architecture": ["system_design", "api_design", "database_design"],
            "development": ["fastapi_development", "database_integration", "auth_implementation"],
            "qa": ["unit_testing", "api_testing", "load_testing"],
            "documentation": ["api_documentation", "openapi_spec"],
        },
        governance_rules=[
            "code_review_required",
            "test_coverage_threshold",
            "security_scan",
            "api_documentation_complete",
        ],
    ),
    "dashboard": OrchestrationProfile(
        template_id="dashboard",
        phases=["planning", "architecture", "data", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect", "data"],
            "architecture": ["architect"],
            "data": ["data"],
            "development": ["developer"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis", "dashboard_design"],
            "architecture": ["dashboard_architecture", "data_architecture"],
            "data": ["data_pipeline", "data_aggregation", "kpi_calculation"],
            "development": ["dashboard_development", "visualization"],
            "qa": ["visual_testing", "data_validation"],
            "documentation": ["user_guide", "data_dictionary"],
        },
        governance_rules=[
            "data_quality_check",
            "visual_consistency_check",
            "code_review_required",
            "documentation_complete",
        ],
    ),
    "blank": OrchestrationProfile(
        template_id="blank",
        phases=["planning", "architecture", "development", "qa", "documentation"],
        agents_by_phase={
            "planning": ["architect"],
            "architecture": ["architect"],
            "development": ["developer"],
            "qa": ["qa"],
            "documentation": ["documentarian"],
        },
        skills_by_phase={
            "planning": ["requirements_analysis"],
            "architecture": ["system_design"],
            "development": ["generic_development"],
            "qa": ["unit_testing", "integration_testing"],
            "documentation": ["technical_writing"],
        },
        governance_rules=[
            "code_review_required",
            "documentation_complete",
        ],
    ),
}


def get_profile_for_template(template_id: str) -> OrchestrationProfile | None:
    """Get orchestration profile for a template.

    Args:
        template_id: Template identifier.

    Returns:
        OrchestrationProfile if found, None otherwise.
    """
    return ORCHESTRATION_PROFILES.get(template_id)


def get_default_profile() -> OrchestrationProfile:
    """Get default orchestration profile for unknown templates.

    Returns:
        Default OrchestrationProfile (blank template profile).
    """
    return ORCHESTRATION_PROFILES["blank"]


def list_all_profiles() -> list[OrchestrationProfile]:
    """List all orchestration profiles.

    Returns:
        List of all profiles.
    """
    return list(ORCHESTRATION_PROFILES.values())
