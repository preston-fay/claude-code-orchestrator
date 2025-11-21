"""
Base tool protocol for Orchestrator v2.

Defines the standard interface for tool wrappers.

See ADR-003 for tools architecture.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field


class ToolAction(BaseModel):
    """Definition of a tool action."""
    name: str
    description: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    returns: dict[str, Any] = Field(default_factory=dict)


class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    id: str
    version: str = "1.0.0"
    category: str  # version_control, file_system, data, etc.
    description: str = ""

    actions: list[ToolAction] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Result from a tool invocation."""
    success: bool = True
    result: Any = None
    error_message: str | None = None
    duration_ms: int = 0


class BaseTool(Protocol):
    """Base protocol for tool wrappers.

    Tools wrap environment interactions with:
    - Consistent interfaces
    - Parameter validation
    - Safety constraints
    - Timeout limits
    - Audit logging

    See ADR-003 for tool architecture.
    """

    metadata: ToolMetadata

    async def invoke(
        self,
        action: str,
        params: dict[str, Any],
    ) -> ToolResult:
        """Invoke a tool action.

        Args:
            action: Action name to invoke.
            params: Parameters for the action.

        Returns:
            Result of the invocation.

        TODO: Implement action dispatch
        TODO: Validate parameters
        TODO: Apply constraints
        TODO: Log invocation
        """
        ...

    def get_capabilities(self) -> list[ToolAction]:
        """Get tool capabilities.

        Returns:
            List of available actions.

        TODO: Return metadata actions
        """
        ...

    def validate_params(
        self,
        action: str,
        params: dict[str, Any],
    ) -> list[str]:
        """Validate parameters for an action.

        Args:
            action: Action name.
            params: Parameters to validate.

        Returns:
            List of validation errors.

        TODO: Implement parameter validation
        TODO: Check required params
        TODO: Validate types
        """
        ...


class ToolMixin:
    """Mixin providing common tool functionality."""

    metadata: ToolMetadata
    _timeout_ms: int = 30000

    def get_capabilities(self) -> list[ToolAction]:
        """Get tool capabilities."""
        return self.metadata.actions

    def _check_constraints(self, action: str, params: dict[str, Any]) -> list[str]:
        """Check safety constraints.

        TODO: Implement constraint checking
        """
        return []
