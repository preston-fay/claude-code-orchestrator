# RSC Orchestration Profiles

Orchestration Profiles define how the RSC engine executes projects based on their template type, specifying phases, agents, skills, and governance rules.

## Profile Structure

```python
class OrchestrationProfile(BaseModel):
    template_id: str                           # Maps to template ID
    phases: list[str]                          # Phases to execute
    agents_by_phase: dict[str, list[str]]      # Agents for each phase
    skills_by_phase: dict[str, list[str]]      # Skills for each phase
    governance_rules: list[str]                # Quality gates to enforce
```

## Available Profiles

### Analytics Forecasting App

**Phases**: planning → architecture → data → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect, data | requirements_analysis, data_assessment |
| architecture | architect | system_design, data_architecture |
| data | data | time_series_analytics, data_pipeline, feature_engineering |
| development | developer, data | forecasting_models, dashboard_development |
| qa | qa | model_validation, integration_testing |
| documentation | documentarian | technical_writing, api_documentation |

**Governance Rules**:
- data_quality_check
- model_performance_threshold
- code_review_required
- documentation_complete

### ML Classification

**Phases**: planning → architecture → data → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect, data | requirements_analysis, ml_problem_framing |
| architecture | architect | ml_architecture, data_architecture |
| data | data | data_pipeline, feature_engineering, data_validation |
| development | developer, data | classification_models, model_training |
| qa | qa | model_evaluation, cross_validation, bias_testing |
| documentation | documentarian | model_documentation, api_documentation |

**Governance Rules**:
- data_quality_check
- model_accuracy_threshold
- bias_fairness_check
- code_review_required

### ML Regression

**Phases**: planning → architecture → data → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect, data | requirements_analysis, ml_problem_framing |
| architecture | architect | ml_architecture, data_architecture |
| data | data | data_pipeline, feature_engineering, data_validation |
| development | developer, data | regression_models, model_training |
| qa | qa | model_evaluation, residual_analysis, performance_testing |
| documentation | documentarian | model_documentation, api_documentation |

**Governance Rules**:
- data_quality_check
- model_rmse_threshold
- code_review_required
- documentation_complete

### Optimization

**Phases**: planning → architecture → data → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect, data | requirements_analysis, optimization_problem_framing |
| architecture | architect | optimization_architecture, data_architecture |
| data | data | data_pipeline, constraint_modeling |
| development | developer | optimization_solvers, constraint_programming |
| qa | qa | solution_validation, sensitivity_analysis |
| documentation | documentarian | technical_writing, solution_documentation |

**Governance Rules**:
- data_quality_check
- solution_feasibility_check
- code_review_required
- documentation_complete

### Web App

**Phases**: planning → architecture → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect | requirements_analysis, ui_ux_design |
| architecture | architect | system_design, api_design, database_design |
| development | developer | react_development, fastapi_development, database_integration |
| qa | qa | unit_testing, integration_testing, e2e_testing |
| documentation | documentarian | api_documentation, user_guide |

**Governance Rules**:
- code_review_required
- test_coverage_threshold
- security_scan
- documentation_complete

### Backend API

**Phases**: planning → architecture → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect | requirements_analysis, api_design |
| architecture | architect | system_design, api_design, database_design |
| development | developer | fastapi_development, database_integration, auth_implementation |
| qa | qa | unit_testing, api_testing, load_testing |
| documentation | documentarian | api_documentation, openapi_spec |

**Governance Rules**:
- code_review_required
- test_coverage_threshold
- security_scan
- api_documentation_complete

### Dashboard

**Phases**: planning → architecture → data → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect, data | requirements_analysis, dashboard_design |
| architecture | architect | dashboard_architecture, data_architecture |
| data | data | data_pipeline, data_aggregation, kpi_calculation |
| development | developer | dashboard_development, visualization |
| qa | qa | visual_testing, data_validation |
| documentation | documentarian | user_guide, data_dictionary |

**Governance Rules**:
- data_quality_check
- visual_consistency_check
- code_review_required
- documentation_complete

### Blank Project

**Phases**: planning → architecture → development → qa → documentation

| Phase | Agents | Skills |
|-------|--------|--------|
| planning | architect | requirements_analysis |
| architecture | architect | system_design |
| development | developer | generic_development |
| qa | qa | unit_testing, integration_testing |
| documentation | documentarian | technical_writing |

**Governance Rules**:
- code_review_required
- documentation_complete

## API Usage

### Get Profile for Template

```python
from orchestrator_v2.engine.orchestration_profiles import get_profile_for_template

profile = get_profile_for_template("analytics_forecast_app")
if profile:
    print(f"Phases: {profile.phases}")
    print(f"Agents: {profile.agents_by_phase}")
```

### Get Default Profile

```python
from orchestrator_v2.engine.orchestration_profiles import get_default_profile

default = get_default_profile()  # Returns blank template profile
```

### List All Profiles

```python
from orchestrator_v2.engine.orchestration_profiles import list_all_profiles

all_profiles = list_all_profiles()
```

## Integration Points

### Project Creation

When a project is created with a template:

1. Template's `default_capabilities` are assigned to the project
2. Orchestration profile is retrieved via `get_profile_for_template()`
3. Profile's phases are used to determine execution order
4. Agents and skills are loaded per phase during RSG execution

### RSG Stage Mapping

Profile phases map to RSG stages:

| RSG Stage | Typical Phases |
|-----------|----------------|
| Ready | planning, architecture |
| Set | data, development |
| Go | qa, documentation |

### Governance Enforcement

Each profile's governance rules are checked at phase completion:

- `data_quality_check` - Validates data quality metrics
- `model_*_threshold` - Checks model performance
- `code_review_required` - Ensures code review completion
- `test_coverage_threshold` - Validates test coverage percentage
- `security_scan` - Runs security analysis
- `documentation_complete` - Checks documentation artifacts

## Creating Custom Profiles

To add a new orchestration profile:

1. Add entry to `ORCHESTRATION_PROFILES` in `orchestrator_v2/engine/orchestration_profiles.py`
2. Ensure corresponding template exists in `orchestrator_v2/config/templates.py`
3. Define appropriate phases, agents, skills, and governance rules

Example:

```python
"custom_template": OrchestrationProfile(
    template_id="custom_template",
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
        "development": ["custom_development"],
        "qa": ["unit_testing"],
        "documentation": ["technical_writing"],
    },
    governance_rules=[
        "code_review_required",
        "documentation_complete",
    ],
)
```

## Agent Reference

| Agent | Role |
|-------|------|
| architect | System design, technical specifications |
| data | Data engineering, pipelines, ML models |
| developer | Implementation, coding |
| qa | Testing, validation, quality assurance |
| documentarian | Documentation, user guides |
| consensus | Decision making, conflict resolution |
| reviewer | Code review, feedback |
| steward | Repository hygiene, maintenance |

## Related Documentation

- [RSC Launchpad](RSC_LAUNCHPAD.md)
- [RSC Template Catalog](RSC_TEMPLATE_CATALOG.md)
- [CLAUDE.md](../CLAUDE.md) - Orchestration principles
