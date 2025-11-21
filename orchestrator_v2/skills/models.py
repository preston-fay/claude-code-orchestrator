"""
Skill models for Orchestrator v2.

Defines the base skill protocol and metadata structures.

See ADR-003 for skills architecture.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from orchestrator_v2.core.state_models import (
    ArtifactInfo,
    PhaseType,
    ProjectState,
    TokenUsage,
)


class MethodologyStep(BaseModel):
    """A step in a skill's methodology."""
    step: str
    description: str
    tools: list[str] = Field(default_factory=list)
    decision_factors: list[str] = Field(default_factory=list)
    rationale: str = ""


class SkillMetadata(BaseModel):
    """Metadata for a skill.

    See ADR-003 for skill YAML structure.
    """
    id: str
    version: str = "1.0.0"
    category: str  # analytics, ml, optimization, survey
    description: str = ""

    # Discovery
    triggers: list[str] = Field(default_factory=list)

    # Schema
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)

    # Methodology
    methodology: list[MethodologyStep] = Field(default_factory=list)

    # Guidance
    best_practices: list[str] = Field(default_factory=list)
    common_pitfalls: list[str] = Field(default_factory=list)

    # Requirements
    tools_required: list[str] = Field(default_factory=list)
    validation_criteria: str = ""


class SkillResult(BaseModel):
    """Result from skill execution."""
    skill_id: str
    success: bool = True
    messages: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    error_message: str | None = None


class SkillInput(BaseModel):
    """Input to a skill execution."""
    skill_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class SkillOutput(BaseModel):
    """Output from a skill execution."""
    skill_id: str
    success: bool = True
    result: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    error_message: str | None = None


class BaseSkill(Protocol):
    """Base protocol for executable skills.

    Skills encode domain-agnostic methodologies that agents
    can apply to specific tasks.

    See ADR-003 for skill architecture.
    """

    id: str
    name: str
    triggers: list[str]
    metadata: SkillMetadata

    def matches(self, text: str) -> bool:
        """Check if skill matches given text based on triggers.

        Args:
            text: Text to check against triggers.

        Returns:
            True if any trigger matches.
        """
        ...

    async def execute(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> SkillResult:
        """Execute the skill methodology.

        Args:
            agent_id: ID of the executing agent.
            phase: Current workflow phase.
            project_state: Current project state.
            context: Additional context for execution.

        Returns:
            Skill execution result with artifacts and messages.
        """
        ...


class BaseSkillImpl:
    """Base implementation for skills."""

    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self.id = metadata.id
        self.name = metadata.id
        self.triggers = metadata.triggers

    def matches(self, text: str) -> bool:
        """Check if skill matches given text."""
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.triggers)

    async def execute(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        context: dict[str, Any],
    ) -> SkillResult:
        """Execute the skill - to be overridden by subclasses."""
        return SkillResult(
            skill_id=self.id,
            success=True,
            messages=[f"Skill {self.id} executed by {agent_id}"],
            token_usage=TokenUsage(input_tokens=50, output_tokens=25, total_tokens=75),
        )
