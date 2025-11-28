"""
Intake Template System Data Models.

Defines the data structures for managing intake sessions, templates,
and their constituent components.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, validator


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class QuestionType(str, Enum):
    """Types of questions in intake templates."""
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    DATE = "date"
    LIST = "list"
    OBJECT = "object"
    DERIVED = "derived"


class ConditionOperator(str, Enum):
    """Operators for conditional logic."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IS_SET = "is_set"
    IS_NOT_SET = "is_not_set"
    REGEX_MATCH = "regex_match"


# -----------------------------------------------------------------------------
# Core Data Models
# -----------------------------------------------------------------------------

class ConditionDefinition(BaseModel):
    """Defines conditional logic for questions and phases."""
    field: str  # Field ID to evaluate
    operator: ConditionOperator
    value: Any  # Value to compare against
    
    # Complex conditions
    and_conditions: list["ConditionDefinition"] = Field(default_factory=list)
    or_conditions: list["ConditionDefinition"] = Field(default_factory=list)


class ValidationRules(BaseModel):
    """Validation rules for question responses."""
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None  # Regex pattern
    min_value: float | None = None
    max_value: float | None = None
    min_date: str | None = None  # ISO date string
    max_date: str | None = None  # ISO date string
    required_fields: list[str] = Field(default_factory=list)  # For object types


class OptionDefinition(BaseModel):
    """Definition of a choice option."""
    value: str
    label: str
    description: str | None = None
    icon: str | None = None


class ItemSchema(BaseModel):
    """Schema definition for list items."""
    type: QuestionType
    properties: dict[str, Any] | None = None  # Raw dict to avoid validation issues
    validation: ValidationRules | None = None
    max_length: int | None = None
    options: list[OptionDefinition] = Field(default_factory=list)


class QuestionDefinition(BaseModel):
    """Defines a single question with validation and logic."""
    id: str
    question: str | None = None  # None for derived fields
    type: QuestionType
    required: bool = False
    
    # Default and placeholder values
    default: Any = None
    placeholder: str | None = None
    help_text: str | None = None
    
    # Validation rules
    validation: ValidationRules | None = None
    
    # Conditional logic
    condition: ConditionDefinition | None = None
    conditional_next: dict[str, str] = Field(default_factory=dict)
    conditional_phases: dict[str, list[str]] = Field(default_factory=dict)
    
    # Type-specific configuration
    options: list[OptionDefinition] = Field(default_factory=list)  # For choice types
    item_schema: ItemSchema | None = None  # For list type
    properties: dict[str, Any] = Field(default_factory=dict)  # For object type - raw dict
    
    # List constraints
    min_items: int | None = None
    max_items: int | None = None
    
    # Numeric constraints
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    unit: str | None = None
    
    # UI configuration
    hidden: bool = False
    readonly: bool = False
    width: str = "full"  # "full", "half", "third"
    
    # Derived field configuration
    derived_from: str | None = None
    transform: str | None = None  # "slugify", "uppercase", etc.


class PhaseDefinition(BaseModel):
    """Defines an intake phase with questions and logic."""
    id: str
    name: str
    description: str | None = None
    order: int = 0
    required: bool = False
    
    # Conditional visibility
    condition: ConditionDefinition | None = None
    
    # Questions in this phase
    questions: list[QuestionDefinition]
    
    # Navigation logic
    next_phase_id: str | None = None
    conditional_next: dict[str, str] = Field(default_factory=dict)  # response_value -> phase_id
    
    # UI configuration
    show_progress: bool = True
    allow_back: bool = True
    auto_advance: bool = False


class TemplateMetadata(BaseModel):
    """Template metadata."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    extends: str | None = None  # Template inheritance
    category: str = "general"
    estimated_time_minutes: int = 15
    icon: str | None = None
    color: str | None = None


class BrandConstraints(BaseModel):
    """Brand-specific constraints."""
    font: str | None = None
    font_fallback: str | None = None
    colors: dict[str, str] = Field(default_factory=dict)
    no_emojis: bool = False
    no_gridlines: bool = False
    label_first_approach: bool = False
    max_bullets_per_slide: int | None = None
    max_words_per_bullet: int | None = None
    inherit_from_governance: bool = True


class AdHocConfig(BaseModel):
    """Ad-hoc configuration."""
    enabled: bool = True
    max_questions: int = 5
    question_types: list[QuestionType] = Field(default_factory=lambda: [QuestionType.TEXT, QuestionType.TEXTAREA])


class GovernanceConfig(BaseModel):
    """Governance configuration."""
    required_approvals: list[str] = Field(default_factory=list)
    compliance_checks: list[str] = Field(default_factory=list)
    validation_rules: dict[str, Any] = Field(default_factory=dict)


class OutputConfig(BaseModel):
    """Output configuration."""
    format: str = "intake_response"
    validation: str = "strict"
    merge_with_governance: bool = True
    mapping: dict[str, Any] = Field(default_factory=dict)


class TemplateDefinition(BaseModel):
    """Loaded and parsed template with resolved inheritance."""
    template: TemplateMetadata
    phases: list[PhaseDefinition]
    brand_constraints: BrandConstraints | None = None
    ad_hoc: AdHocConfig | None = None
    governance: GovernanceConfig | None = None
    output: OutputConfig | None = None
    
    # Computed properties
    phase_map: dict[str, PhaseDefinition] = Field(default_factory=dict)
    question_map: dict[str, QuestionDefinition] = Field(default_factory=dict)
    dependency_graph: dict[str, list[str]] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._build_lookup_maps()
        
    def _build_lookup_maps(self):
        """Build lookup maps and dependency graph."""
        self.phase_map = {phase.id: phase for phase in self.phases}
        
        for phase in self.phases:
            for question in phase.questions:
                self.question_map[question.id] = question
                
        self._build_dependency_graph()
        
    def _build_dependency_graph(self):
        """Build question dependency graph for conditional logic."""
        self.dependency_graph = {}
        for phase in self.phases:
            for question in phase.questions:
                if question.condition:
                    self.dependency_graph.setdefault(question.condition.field, []).append(question.id)


class ValidationError(BaseModel):
    """Validation error for a specific field."""
    field_id: str
    error_type: str  # "required", "invalid_format", "constraint_violation", etc.
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of validation operation."""
    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GovernanceData(BaseModel):
    """Client-specific governance constraints applied to intake."""
    client_slug: str
    brand: BrandConstraints | None = None
    validation_rules: list[dict[str, Any]] = Field(default_factory=list)
    field_defaults: dict[str, Any] = Field(default_factory=dict)
    field_overrides: dict[str, Any] = Field(default_factory=dict)
    notices: list[str] = Field(default_factory=list)


class IntakeSession(BaseModel):
    """Represents an active intake interview session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    template_id: str
    client_slug: str = "kearney-default"
    
    # Navigation state
    current_phase_id: str | None = None
    phase_order: list[str] = Field(default_factory=list)
    completed_phases: set[str] = Field(default_factory=set)
    
    # Response data
    responses: dict[str, Any] = Field(default_factory=dict)
    derived_responses: dict[str, Any] = Field(default_factory=dict)
    
    # Governance and validation
    governance_data: GovernanceData | None = None
    validation_errors: list[ValidationError] = Field(default_factory=list)
    
    # Session metadata
    is_complete: bool = False
    project_id: str | None = None  # Set after completion
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Auto-save state
    auto_save_enabled: bool = True
    save_interval_seconds: int = 30

    @validator('completed_phases', pre=True)
    def convert_completed_phases(cls, v):
        """Convert list to set for completed_phases."""
        if isinstance(v, list):
            return set(v)
        return v


# -----------------------------------------------------------------------------
# API Request/Response Models
# -----------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    """Request to create new intake session."""
    template_id: str
    client_slug: str = "kearney-default"
    user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response for session operations."""
    session_id: str
    template_id: str
    client_slug: str
    current_phase_id: str | None
    progress_percent: float
    is_complete: bool
    created_at: datetime
    updated_at: datetime
    governance_notices: list[str] = Field(default_factory=list)


class PhaseResponse(BaseModel):
    """Response for phase information."""
    phase_id: str
    name: str
    description: str | None
    required: bool
    questions: list[QuestionDefinition]
    is_current: bool
    is_complete: bool
    is_available: bool


class SessionStatusResponse(BaseModel):
    """Full session status response."""
    session_id: str
    template_id: str
    current_phase_id: str | None
    progress_percent: float
    phases: list[PhaseResponse]
    current_questions: list[QuestionDefinition]
    responses: dict[str, Any]
    validation_errors: list[ValidationError]


class SubmitResponsesRequest(BaseModel):
    """Request to submit responses for a phase."""
    phase_id: str
    responses: dict[str, Any]
    auto_advance: bool = False


class ResponseSubmissionResult(BaseModel):
    """Result of response submission."""
    success: bool
    validation_result: ValidationResult
    next_phase_id: str | None
    advanced: bool = False
    progress_percent: float


class NavigationRequest(BaseModel):
    """Request for phase navigation."""
    action: str  # "next", "previous", "goto"
    target_phase_id: str | None = None  # For "goto" action


class NavigationResult(BaseModel):
    """Result of navigation operation."""
    success: bool
    current_phase_id: str | None
    target_phase_id: str | None
    message: str | None = None


class CompleteSessionRequest(BaseModel):
    """Request to complete intake session."""
    final_validation: bool = True
    create_project: bool = True


class IntakeSummary(BaseModel):
    """Summary of completed intake."""
    total_responses: int
    governance_applied: bool
    project_type: str
    completion_time_minutes: float


class NextSteps(BaseModel):
    """Next steps after completion."""
    redirect_url: str
    workflow_status: str


class ProjectCreationResult(BaseModel):
    """Result of completing intake and creating project."""
    success: bool
    project_id: str | None
    validation_result: ValidationResult
    intake_summary: IntakeSummary
    next_steps: NextSteps


class TemplateListItem(BaseModel):
    """Template list item for API responses."""
    template_id: str
    name: str
    description: str
    category: str
    estimated_time_minutes: int
    question_count: int
    phase_count: int
    icon: str | None
    color: str | None


class ValidateRequest(BaseModel):
    """Request to validate responses."""
    template_id: str
    client_slug: str = "kearney-default"
    responses: dict[str, Any]


# Enable forward references
ConditionDefinition.model_rebuild()
QuestionDefinition.model_rebuild()
ItemSchema.model_rebuild()