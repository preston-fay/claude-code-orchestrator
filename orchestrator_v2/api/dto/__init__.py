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

# Common DTOs (RSC + legacy)
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
    # RSC DTOs (primary)
    ReadyStatusDTO,
    SetStatusDTO,
    CodeStatusDTO,
    RscOverviewDTO,
    PhaseAdvanceResultDTO,
    # Converters (primary)
    ready_status_to_dto,
    set_status_to_dto,
    code_status_to_dto,
    rsc_overview_to_dto,
    phase_advance_result_to_dto,
    # Backward compatibility aliases
    GoStatusDTO,
    RsgOverviewDTO,
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
    # Common DTOs
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
    # RSC DTOs (primary)
    "ReadyStatusDTO",
    "SetStatusDTO",
    "CodeStatusDTO",
    "RscOverviewDTO",
    "PhaseAdvanceResultDTO",
    # Converters (primary)
    "ready_status_to_dto",
    "set_status_to_dto",
    "code_status_to_dto",
    "rsc_overview_to_dto",
    "phase_advance_result_to_dto",
    # Backward compatibility aliases
    "GoStatusDTO",
    "RsgOverviewDTO",
    "go_status_to_dto",
    "rsg_overview_to_dto",
]
