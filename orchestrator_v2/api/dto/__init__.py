"""
DTOs for Orchestrator v2 API.
"""

# New runs API DTOs
from orchestrator_v2.api.dto.runs import (
    CreateRunRequest,
    PhaseInfo,
    RunSummary,
    RunDetail,
    ArtifactSummary,
    ArtifactsResponse,
    PhaseMetrics,
    MetricsSummary,
    AdvanceRunRequest,
    AdvanceRunResponse,
)

# Legacy DTOs (for backward compatibility)
from orchestrator_v2.api.dto.common import (
    ProjectDTO,
    ProjectTemplateDTO,
    PhaseDTO,
    CheckpointDTO,
    StatusDTO,
    AgentStatusDTO,
    GovernanceResultDTO,
    UpdateProviderSettingsDTO,
    ProviderTestResultDTO,
    EventDTO,
    ReadyStatusDTO,
    SetStatusDTO,
    GoStatusDTO,
    RsgOverviewDTO,
    ready_status_to_dto,
    set_status_to_dto,
    go_status_to_dto,
    rsg_overview_to_dto,
)

__all__ = [
    # Runs API DTOs
    "CreateRunRequest",
    "PhaseInfo",
    "RunSummary",
    "RunDetail",
    "ArtifactSummary",
    "ArtifactsResponse",
    "PhaseMetrics",
    "MetricsSummary",
    "AdvanceRunRequest",
    "AdvanceRunResponse",
    # Legacy DTOs
    "ProjectDTO",
    "ProjectTemplateDTO",
    "PhaseDTO",
    "CheckpointDTO",
    "StatusDTO",
    "AgentStatusDTO",
    "GovernanceResultDTO",
    "UpdateProviderSettingsDTO",
    "ProviderTestResultDTO",
    "EventDTO",
    "ReadyStatusDTO",
    "SetStatusDTO",
    "GoStatusDTO",
    "RsgOverviewDTO",
    "ready_status_to_dto",
    "set_status_to_dto",
    "go_status_to_dto",
    "rsg_overview_to_dto",
]
