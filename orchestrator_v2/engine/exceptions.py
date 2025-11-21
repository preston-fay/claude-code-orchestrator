"""
Custom exceptions for Orchestrator v2.

These exceptions provide clear error handling across the orchestration system.
"""


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""
    pass


class PhaseError(OrchestratorError):
    """Error during phase execution.

    Raised when a phase fails to complete successfully.
    See ADR-002 for phase model details.
    """
    pass


class CheckpointError(OrchestratorError):
    """Error in checkpoint operations.

    Raised during checkpoint save, load, or rollback operations.
    See ADR-002 for checkpoint system details.
    """
    pass


class GovernanceError(OrchestratorError):
    """Error in governance evaluation.

    Raised when governance gates block phase transitions.
    See ADR-004 for governance engine details.
    """
    pass


class BudgetExceededError(OrchestratorError):
    """Token or cost budget exceeded.

    Raised when workflow, phase, or agent budget limits are exceeded.
    See ADR-005 for token efficiency details.
    """

    def __init__(self, message: str, budget_type: str, limit: int, actual: int):
        super().__init__(message)
        self.budget_type = budget_type
        self.limit = limit
        self.actual = actual


class AgentError(OrchestratorError):
    """Error during agent execution.

    Raised when an agent fails to complete its task.
    See ADR-001 for agent architecture details.
    """
    pass


class SkillError(OrchestratorError):
    """Error in skill execution.

    Raised when a skill fails to execute or validate.
    See ADR-003 for skills architecture details.
    """
    pass


class ToolError(OrchestratorError):
    """Error in tool invocation.

    Raised when a tool wrapper fails to execute.
    See ADR-003 for tools architecture details.
    """
    pass


class ValidationError(OrchestratorError):
    """Schema or input validation error.

    Raised when inputs fail schema validation.
    """
    pass


class ConfigurationError(OrchestratorError):
    """Configuration error.

    Raised when configuration is invalid or missing.
    """
    pass
