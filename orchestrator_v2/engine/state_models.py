"""
State models for Orchestrator v2.

These Pydantic models define the typed data structures used throughout
the orchestration system for state management and data transfer.

See ADR-002 for checkpoint and state management details.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PhaseType(str, Enum):
    """Canonical phase types in workflow.

    See ADR-002 for phase graph details.
    """
    INTAKE = "intake"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    DATA = "data"
    SECURITY = "security"
    CONSENSUS = "consensus"
    DEVELOPMENT = "development"
    QA = "qa"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    HYGIENE = "hygiene"
    COMPLETE = "complete"


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    ACTING = "acting"
    SUMMARIZING = "summarizing"
    COMPLETE = "complete"
    FAILED = "failed"


class CheckpointType(str, Enum):
    """Checkpoint type indicator."""
    PRE = "pre"
    POST = "post"


class GateStatus(str, Enum):
    """Quality gate evaluation status."""
    PASSED = "passed"
    WARNED = "warned"
    BLOCKED = "blocked"


class RsgStage(str, Enum):
    """Ready/Set/Go macro stage.

    Maps to engine phases:
    - READY = PLANNING + ARCHITECTURE
    - SET = DATA + early DEVELOPMENT
    - GO = full DEVELOPMENT + QA + DOCUMENTATION
    """
    NOT_STARTED = "not_started"
    READY = "ready"
    SET = "set"
    GO = "go"
    COMPLETE = "complete"


class RsgProgress(BaseModel):
    """Progress tracking for Ready/Set/Go stages."""
    ready_completed: bool = False
    set_completed: bool = False
    go_completed: bool = False
    last_ready_phase: PhaseType | None = None
    last_set_phase: PhaseType | None = None
    last_go_phase: PhaseType | None = None


# -----------------------------------------------------------------------------
# Token and Cost Tracking (ADR-005)
# -----------------------------------------------------------------------------

class TokenUsage(BaseModel):
    """Token usage tracking for a single operation."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Decimal = Decimal("0.00")


class BudgetConfig(BaseModel):
    """Budget configuration for token/cost limits.

    See ADR-005 for budget hierarchy details.
    """
    max_tokens: int = 2_000_000
    max_cost_usd: Decimal = Decimal("50.00")
    alert_threshold: float = 0.8


# -----------------------------------------------------------------------------
# Tool Invocations (ADR-003)
# -----------------------------------------------------------------------------

class ToolInvocation(BaseModel):
    """Record of a tool invocation."""
    tool_id: str
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    success: bool = True
    error_message: str | None = None
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Artifact Tracking (ADR-002)
# -----------------------------------------------------------------------------

class ArtifactInfo(BaseModel):
    """Information about a checkpoint artifact."""
    path: str
    hash: str  # SHA-256
    size_bytes: int
    artifact_type: str = "file"


# -----------------------------------------------------------------------------
# Governance Results (ADR-004)
# -----------------------------------------------------------------------------

class GateResult(BaseModel):
    """Result of a quality gate evaluation."""
    gate_id: str
    status: GateStatus
    message: str
    threshold: Any = None
    actual: Any = None
    remediation: str | None = None


class ComplianceResult(BaseModel):
    """Result of a compliance check."""
    compliance_type: str  # e.g., "gdpr", "hipaa"
    passed: bool
    violations: list[str] = Field(default_factory=list)


class GovernanceResults(BaseModel):
    """Complete governance evaluation results."""
    quality_gates: list[GateResult] = Field(default_factory=list)
    compliance_checks: list[ComplianceResult] = Field(default_factory=list)
    passed: bool = True
    failed_rules: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Agent State (ADR-001)
# -----------------------------------------------------------------------------

class AgentState(BaseModel):
    """State of an agent during workflow execution.

    See ADR-001 for agent lifecycle details.
    """
    agent_id: str
    status: AgentStatus = AgentStatus.PENDING
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    tool_invocations: list[ToolInvocation] = Field(default_factory=list)
    summary: str = ""
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # Model used for this agent execution
    model_used: str | None = None
    provider_used: str | None = None


# -----------------------------------------------------------------------------
# Checkpoint State (ADR-002)
# -----------------------------------------------------------------------------

class CheckpointState(BaseModel):
    """Complete checkpoint state snapshot.

    See ADR-002 for checkpoint structure details.
    """
    # Identity
    id: str
    phase: PhaseType
    checkpoint_type: CheckpointType
    version: int = 1

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0

    # State references
    run_id: str
    current_phase: PhaseType
    completed_phases: list[PhaseType] = Field(default_factory=list)

    # Agent states
    agent_states: dict[str, AgentState] = Field(default_factory=dict)

    # Artifacts
    artifacts: dict[str, ArtifactInfo] = Field(default_factory=dict)

    # Governance
    governance_results: GovernanceResults = Field(default_factory=GovernanceResults)

    # Lineage
    parent_checkpoint_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Phase State (ADR-002)
# -----------------------------------------------------------------------------

class PhaseState(BaseModel):
    """State of a workflow phase."""
    phase: PhaseType
    status: str = "pending"  # pending, running, complete, failed, skipped
    started_at: datetime | None = None
    completed_at: datetime | None = None
    agent_ids: list[str] = Field(default_factory=list)
    artifacts: dict[str, ArtifactInfo] = Field(default_factory=dict)
    error_message: str | None = None


# -----------------------------------------------------------------------------
# Project State
# -----------------------------------------------------------------------------

class ProjectState(BaseModel):
    """Complete project/workflow state.

    This is the master state object maintained by the WorkflowEngine.
    """
    # Identity
    project_id: str
    run_id: str
    project_name: str
    client: str = "kearney-default"
    project_type: str = "generic"

    # Project brief and capabilities (capability-driven phases)
    brief: str | None = None
    capabilities: list[str] = Field(default_factory=list)

    # External links (for deliverable apps built outside RSC)
    app_repo_url: str | None = None
    app_url: str | None = None

    # Workspace path (absolute path to workspace root)
    workspace_path: str | None = None

    # Template reference
    template_id: str | None = None

    # Workflow progress
    current_phase: PhaseType = PhaseType.INTAKE
    completed_phases: list[PhaseType] = Field(default_factory=list)
    phase_states: dict[str, PhaseState] = Field(default_factory=dict)

    # Agent tracking
    agent_states: dict[str, AgentState] = Field(default_factory=dict)

    # Token/cost tracking
    total_token_usage: TokenUsage = Field(default_factory=TokenUsage)
    budget_config: BudgetConfig = Field(default_factory=BudgetConfig)

    # Checkpoints
    checkpoints: list[str] = Field(default_factory=list)  # Checkpoint IDs
    current_checkpoint_id: str | None = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Ready/Set/Go stage tracking
    rsg_stage: RsgStage = RsgStage.NOT_STARTED
    rsg_progress: RsgProgress = Field(default_factory=RsgProgress)


# -----------------------------------------------------------------------------
# Configuration Models
# -----------------------------------------------------------------------------

class WorkflowConfig(BaseModel):
    """Workflow configuration from intake.yaml."""
    project_name: str
    project_type: str = "analytics"
    client: str = "kearney-default"

    # Phase configuration
    enabled_phases: list[PhaseType] = Field(default_factory=list)
    skip_phases: list[PhaseType] = Field(default_factory=list)

    # Agent configuration
    enabled_agents: list[str] = Field(default_factory=list)

    # Budget configuration
    budget: BudgetConfig = Field(default_factory=BudgetConfig)

    # Requirements
    requirements: list[str] = Field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskDefinition(BaseModel):
    """Definition of a task to be executed by an agent."""
    task_id: str
    description: str
    requirements: list[str] = Field(default_factory=list)
    skill_id: str | None = None
    tool_ids: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    budget: BudgetConfig | None = None


class AgentPlanStep(BaseModel):
    """A single step in an agent's execution plan."""
    step_id: str
    description: str
    tool_id: str | None = None
    skill_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_output: str = ""


class AgentPlan(BaseModel):
    """Execution plan created by an agent."""
    plan_id: str
    agent_id: str
    task_id: str
    steps: list[AgentPlanStep] = Field(default_factory=list)
    estimated_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentOutput(BaseModel):
    """Output from an agent action step."""
    step_id: str
    success: bool = True
    output: Any = None
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    error_message: str | None = None


class AgentSummary(BaseModel):
    """Summary of an agent's complete execution."""
    agent_id: str
    task_id: str
    success: bool = True
    summary: str = ""
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    total_token_usage: TokenUsage = Field(default_factory=TokenUsage)
    recommendations: list[str] = Field(default_factory=list)


class AgentContext(BaseModel):
    """Context provided to an agent for execution."""
    project_state: ProjectState
    task: TaskDefinition
    previous_outputs: list[AgentOutput] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    available_skills: list[str] = Field(default_factory=list)
    governance_constraints: dict[str, Any] = Field(default_factory=dict)
    budget_remaining: TokenUsage = Field(default_factory=TokenUsage)
    # Workspace paths for file operations
    workspace_root: str | None = None
    repo_path: str | None = None
    artifacts_path: str | None = None
    logs_path: str | None = None
    tmp_path: str | None = None
    # User context for BYOK and entitlements
    user_id: str | None = None
    llm_api_key: str | None = None
    llm_provider: str = "anthropic"
    model_preferences: list[str] = Field(default_factory=list)
    # Selected model for this execution
    provider: str | None = None
    model: str | None = None


# -----------------------------------------------------------------------------
# Phase Definition (ADR-002)
# -----------------------------------------------------------------------------

class PhaseDefinition(BaseModel):
    """Definition of a workflow phase.

    See ADR-002 for phase model details.
    """
    name: PhaseType
    order: int
    responsible_agents: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)
    description: str = ""
    optional: bool = False


class WorkflowDefinition(BaseModel):
    """Definition of a complete workflow.

    See ADR-002 for workflow structure.
    """
    name: str
    description: str = ""
    phases: list[PhaseDefinition] = Field(default_factory=list)
    project_type: str = "analytics"

    def get_phase_by_type(self, phase_type: PhaseType) -> PhaseDefinition | None:
        """Get phase definition by type."""
        for phase in self.phases:
            if phase.name == phase_type:
                return phase
        return None

    def get_phase_order(self, phase_type: PhaseType) -> int:
        """Get the order index of a phase."""
        for phase in self.phases:
            if phase.name == phase_type:
                return phase.order
        return -1


# -----------------------------------------------------------------------------
# Capability to Phases Mapping
# -----------------------------------------------------------------------------

# Map capabilities to the phases they require
CAPABILITY_PHASE_MAP: dict[str, list[PhaseType]] = {
    # Data capabilities
    "data_pipeline": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "data_ingestion": [
        PhaseType.PLANNING, PhaseType.DATA, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "data_validation": [
        PhaseType.PLANNING, PhaseType.DATA, PhaseType.QA, PhaseType.DOCUMENTATION
    ],

    # Analytics capabilities
    "analytics_forecasting": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "analytics_dashboard": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "analytics_reporting": [
        PhaseType.PLANNING, PhaseType.DATA, PhaseType.DEVELOPMENT,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],

    # ML capabilities
    "ml_classification": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "ml_regression": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "ml_clustering": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],

    # Optimization capabilities
    "optimization": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "territory_alignment": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DATA,
        PhaseType.DEVELOPMENT, PhaseType.QA, PhaseType.DOCUMENTATION
    ],

    # App building capabilities
    "app_build": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DEVELOPMENT,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "backend_api": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DEVELOPMENT,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],
    "frontend_ui": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DEVELOPMENT,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],

    # Generic capability
    "generic": [
        PhaseType.PLANNING, PhaseType.ARCHITECTURE, PhaseType.DEVELOPMENT,
        PhaseType.QA, PhaseType.DOCUMENTATION
    ],
}

# Canonical phase order for sorting
PHASE_ORDER = [
    PhaseType.INTAKE,
    PhaseType.PLANNING,
    PhaseType.ARCHITECTURE,
    PhaseType.CONSENSUS,
    PhaseType.DATA,
    PhaseType.SECURITY,
    PhaseType.DEVELOPMENT,
    PhaseType.QA,
    PhaseType.DOCUMENTATION,
    PhaseType.REVIEW,
    PhaseType.HYGIENE,
    PhaseType.COMPLETE,
]


def get_phases_for_capabilities(capabilities: list[str]) -> list[PhaseType]:
    """Derive the phases for a project based on its capabilities.

    Args:
        capabilities: List of capability identifiers.

    Returns:
        Ordered list of phases to execute.
    """
    if not capabilities:
        # Default to generic project phases
        capabilities = ["generic"]

    # Collect all phases from capabilities
    phase_set: set[PhaseType] = set()
    for cap in capabilities:
        cap_phases = CAPABILITY_PHASE_MAP.get(cap, CAPABILITY_PHASE_MAP["generic"])
        phase_set.update(cap_phases)

    # Sort by canonical order
    sorted_phases = [p for p in PHASE_ORDER if p in phase_set]

    return sorted_phases
