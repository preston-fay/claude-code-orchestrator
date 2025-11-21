"""
Skill models for Orchestrator v2.

Defines the base skill protocol and metadata structures.

See ADR-003 for skills architecture.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field


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

    metadata: SkillMetadata

    def detect_trigger(self, task_description: str) -> float:
        """Calculate relevance score for a task description.

        Args:
            task_description: Description of the task.

        Returns:
            Relevance score from 0.0 to 1.0.

        TODO: Implement trigger detection
        TODO: Match against trigger keywords
        TODO: Consider semantic similarity
        """
        ...

    def validate_inputs(self, inputs: SkillInput) -> list[str]:
        """Validate inputs against the skill's input schema.

        Args:
            inputs: Skill inputs to validate.

        Returns:
            List of validation errors (empty if valid).

        TODO: Implement schema validation
        TODO: Check required fields
        TODO: Validate field types
        """
        ...

    async def execute(
        self,
        inputs: SkillInput,
        tools: dict[str, Any],
    ) -> SkillOutput:
        """Execute the skill methodology.

        This runs through the skill's methodology steps
        using the provided tools.

        Args:
            inputs: Validated skill inputs.
            tools: Available tools for execution.

        Returns:
            Skill execution output.

        TODO: Implement methodology execution
        TODO: Track step progress
        TODO: Collect artifacts
        """
        ...

    def validate_outputs(self, outputs: SkillOutput) -> list[str]:
        """Validate outputs against the skill's output schema.

        Args:
            outputs: Skill outputs to validate.

        Returns:
            List of validation errors (empty if valid).

        TODO: Implement output validation
        TODO: Check required fields
        TODO: Validate result structure
        """
        ...
