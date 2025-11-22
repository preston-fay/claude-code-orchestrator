"""
Capability configuration for multi-capability projects.

This module defines the mapping between capabilities and workflow phases,
enabling projects to have multiple capabilities that determine their
effective phase list.
"""

from orchestrator_v2.engine.state_models import PhaseType


# Canonical order of phases
PHASE_ORDER = [
    PhaseType.PLANNING,
    PhaseType.ARCHITECTURE,
    PhaseType.DATA,
    PhaseType.DEVELOPMENT,
    PhaseType.QA,
    PhaseType.DOCUMENTATION,
]

# Default phases when no capabilities are specified
DEFAULT_PHASES = PHASE_ORDER.copy()


# Capability to phases mapping
# Each capability specifies which phases it participates in
CAPABILITY_PHASES: dict[str, list[PhaseType]] = {
    # Data pipeline: focus on data phases
    "data_pipeline": [
        PhaseType.PLANNING,
        PhaseType.DATA,
    ],

    # Analytics - Forecasting: full workflow with data emphasis
    "analytics_forecasting": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # Analytics - BI Dashboard: includes data and development
    "analytics_bi_dashboard": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # ML - Classification: data-heavy with development
    "ml_classification": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # ML - Regression: similar to classification
    "ml_regression": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # Optimization: data + development for solver implementation
    "optimization": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # App Build: architecture-focused application development
    "app_build": [
        PhaseType.PLANNING,
        PhaseType.ARCHITECTURE,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # Service / API: backend service development
    "service_api": [
        PhaseType.PLANNING,
        PhaseType.ARCHITECTURE,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],

    # Data Engineering: focused on data pipeline construction
    "data_engineering": [
        PhaseType.PLANNING,
        PhaseType.DATA,
        PhaseType.DEVELOPMENT,
        PhaseType.QA,
        PhaseType.DOCUMENTATION,
    ],
}


# Human-readable capability labels for UI display
CAPABILITY_LABELS: dict[str, str] = {
    "data_pipeline": "Data Pipeline",
    "analytics_forecasting": "Analytics (Forecasting)",
    "analytics_bi_dashboard": "Analytics (BI Dashboard)",
    "ml_classification": "ML (Classification)",
    "ml_regression": "ML (Regression)",
    "optimization": "Optimization",
    "app_build": "App Build / UI",
    "service_api": "Service / API",
    "data_engineering": "Data Engineering",
}


def get_capability_phases(capability: str) -> list[PhaseType]:
    """Get the phases for a specific capability.

    Args:
        capability: Capability identifier.

    Returns:
        List of phases for the capability, or empty list if unknown.
    """
    return CAPABILITY_PHASES.get(capability, [])


def get_project_phases(capabilities: list[str]) -> list[PhaseType]:
    """Derive the effective phases for a project based on its capabilities.

    This takes the union of phases for all capabilities and returns them
    in canonical phase order.

    Args:
        capabilities: List of capability identifiers for the project.

    Returns:
        List of effective phases in canonical order.
        Returns default 6-phase workflow if no capabilities specified.
    """
    if not capabilities:
        return DEFAULT_PHASES.copy()

    # Collect all phases from all capabilities
    phase_set = set()
    for capability in capabilities:
        phases = CAPABILITY_PHASES.get(capability, [])
        phase_set.update(phases)

    # If no valid capabilities were found, return default
    if not phase_set:
        return DEFAULT_PHASES.copy()

    # Return phases in canonical order
    return [p for p in PHASE_ORDER if p in phase_set]


def get_capability_label(capability: str) -> str:
    """Get the human-readable label for a capability.

    Args:
        capability: Capability identifier.

    Returns:
        Human-readable label, or the capability ID if not found.
    """
    return CAPABILITY_LABELS.get(capability, capability)


def list_all_capabilities() -> list[dict]:
    """List all available capabilities with their metadata.

    Returns:
        List of capability information dictionaries.
    """
    return [
        {
            "id": cap_id,
            "label": CAPABILITY_LABELS.get(cap_id, cap_id),
            "phases": [p.value for p in phases],
        }
        for cap_id, phases in CAPABILITY_PHASES.items()
    ]


def validate_capabilities(capabilities: list[str]) -> tuple[bool, list[str]]:
    """Validate a list of capabilities.

    Args:
        capabilities: List of capability identifiers to validate.

    Returns:
        Tuple of (is_valid, invalid_capabilities).
    """
    invalid = [c for c in capabilities if c not in CAPABILITY_PHASES]
    return len(invalid) == 0, invalid
