# Intake System Design Document

## Overview

The Intake Template System provides structured, adaptive interviews that gather comprehensive project requirements before orchestrator workflow execution. This system implements "perfect prompts for perfect prompts" by ensuring the orchestrator has all necessary context to generate optimal outputs.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             Client Tier                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │  IntakeWizard   │    │  QuestionForm   │    │ ProgressTracker │     │
│  │  (React)        │    │  (React)        │    │  (React)        │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│           │                       │                       │             │
└───────────┼───────────────────────┼───────────────────────┼─────────────┘
            │                       │                       │
            │                  HTTP/JSON API                │
            │                       │                       │
┌───────────┼───────────────────────┼───────────────────────┼─────────────┐
│           │              Application Tier                │             │
├───────────┼───────────────────────┼───────────────────────┼─────────────┤
│           ▼                       ▼                       ▼             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Intake Router   │    │ Session Manager │    │ Validation Svc  │     │
│  │ (FastAPI)       │    │ (Python)        │    │ (Python)        │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│           │                       │                       │             │
│           │              ┌─────────────────┐              │             │
│           └──────────────►│ Logic Engine    │◄─────────────┘             │
│                          │ (Conditional)   │                            │
│                          └─────────────────┘                            │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                          Data Tier │                                     │
├───────────────────────────────────┼─────────────────────────────────────┤
│                                   ▼                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │ Session Store   │    │ Template Store  │    │ Governance Data │     │
│  │ (FileSystem)    │    │ (YAML Files)    │    │ (YAML Files)    │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Interactions

```
User Request → IntakeWizard → Intake Router → Session Manager → Template Engine
                    ↓               ↓              ↓              ↓
             Progress Update ← Response JSON ← Session State ← Template Logic
                    │               │              │              │
                    ▼               ▼              ▼              ▼
             Question Render ← Validation ← Logic Engine ← Governance Rules
```

## Data Models

### Core Entities

#### IntakeSession
```python
class IntakeSession(BaseModel):
    """Represents an active intake interview session"""
    
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
    governance_data: dict[str, Any] = Field(default_factory=dict)
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
```

#### TemplateDefinition
```python
class TemplateDefinition(BaseModel):
    """Loaded and parsed template with resolved inheritance"""
    
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
    
    def model_post_init(self, __context: Any) -> None:
        """Build lookup maps and dependency graph"""
        self.phase_map = {phase.id: phase for phase in self.phases}
        
        for phase in self.phases:
            for question in phase.questions:
                self.question_map[question.id] = question
                
        self._build_dependency_graph()
        
    def _build_dependency_graph(self):
        """Build question dependency graph for conditional logic"""
        for phase in self.phases:
            for question in phase.questions:
                if question.condition:
                    self.dependency_graph.setdefault(question.condition.field, []).append(question.id)
```

#### PhaseDefinition
```python
class PhaseDefinition(BaseModel):
    """Defines an intake phase with questions and logic"""
    
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
```

#### QuestionDefinition
```python
class QuestionDefinition(BaseModel):
    """Defines a single question with validation and logic"""
    
    id: str
    question: str | None  # None for derived fields
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
    properties: dict[str, QuestionDefinition] = Field(default_factory=dict)  # For object type
    
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
```

#### ConditionDefinition
```python
class ConditionDefinition(BaseModel):
    """Defines conditional logic for questions and phases"""
    
    field: str  # Field ID to evaluate
    operator: ConditionOperator
    value: Any  # Value to compare against
    
    # Complex conditions
    and_conditions: list['ConditionDefinition'] = Field(default_factory=list)
    or_conditions: list['ConditionDefinition'] = Field(default_factory=list)

class ConditionOperator(str, Enum):
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
```

### Supporting Models

#### ValidationError
```python
class ValidationError(BaseModel):
    field_id: str
    error_type: str  # "required", "invalid_format", "constraint_violation", etc.
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
```

#### GovernanceData
```python
class GovernanceData(BaseModel):
    """Client-specific governance constraints applied to intake"""
    
    client_slug: str
    brand: BrandConstraints | None = None
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    field_defaults: dict[str, Any] = Field(default_factory=dict)
    field_overrides: dict[str, Any] = Field(default_factory=dict)
    notices: list[str] = Field(default_factory=list)
```

## API Endpoints

### Session Management

#### POST /api/intake/sessions
Create a new intake session.

**Request:**
```json
{
  "template_id": "presentation",
  "client_slug": "kearney-default",
  "user_id": "user-123",
  "metadata": {
    "source": "project_wizard",
    "referrer": "/dashboard"
  }
}
```

**Response:**
```json
{
  "session_id": "session-abc123",
  "template_id": "presentation",
  "client_slug": "kearney-default",
  "current_phase_id": "project_identity",
  "progress_percent": 0.0,
  "is_complete": false,
  "created_at": "2024-01-15T10:00:00Z",
  "governance_notices": [
    "Kearney brand standards will be applied automatically"
  ]
}
```

#### GET /api/intake/sessions/{session_id}
Get current session state.

**Response:**
```json
{
  "session_id": "session-abc123",
  "template_id": "presentation",
  "current_phase_id": "project_identity",
  "progress_percent": 25.0,
  "phases": [
    {
      "phase_id": "project_identity",
      "name": "Project Identity",
      "is_current": true,
      "is_complete": false,
      "is_available": true
    },
    {
      "phase_id": "audience_analysis",
      "name": "Audience Analysis", 
      "is_current": false,
      "is_complete": false,
      "is_available": false
    }
  ],
  "current_questions": [...],
  "responses": {...},
  "validation_errors": []
}
```

#### PUT /api/intake/sessions/{session_id}/responses
Submit responses for current phase.

**Request:**
```json
{
  "phase_id": "project_identity",
  "responses": {
    "project_name": "Q4 Strategy Review",
    "project_description": "Comprehensive review of our Q4 strategic initiatives and performance metrics."
  },
  "auto_advance": true
}
```

**Response:**
```json
{
  "success": true,
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "next_phase_id": "audience_analysis",
  "advanced": true,
  "progress_percent": 50.0
}
```

#### POST /api/intake/sessions/{session_id}/navigate
Navigate between phases.

**Request:**
```json
{
  "action": "next",  // "next", "previous", "goto"
  "target_phase_id": "audience_analysis"  // For "goto" action
}
```

#### POST /api/intake/sessions/{session_id}/complete
Complete intake and create project.

**Request:**
```json
{
  "final_validation": true,
  "create_project": true
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "project-xyz789",
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "intake_summary": {
    "total_responses": 15,
    "governance_applied": true,
    "project_type": "presentation"
  },
  "next_steps": {
    "redirect_url": "/projects/project-xyz789/ready",
    "workflow_status": "ready_to_start"
  }
}
```

### Template Operations

#### GET /api/intake/templates
List available templates.

**Query Parameters:**
- `client_slug` (optional): Filter by client
- `category` (optional): Filter by category
- `include_abstract` (optional): Include abstract templates

**Response:**
```json
[
  {
    "template_id": "presentation",
    "name": "Presentation Content",
    "description": "Create consulting project deliverables or client pitch decks",
    "category": "consulting",
    "estimated_time_minutes": 15,
    "question_count": 12,
    "phase_count": 4,
    "icon": "presentation",
    "color": "#7823DC"
  }
]
```

#### GET /api/intake/templates/{template_id}
Get template definition with governance applied.

**Query Parameters:**
- `client_slug` (optional): Apply client-specific governance

**Response:**
```json
{
  "template": {
    "id": "presentation",
    "name": "Presentation Content",
    "description": "...",
    "version": "1.0.0"
  },
  "phases": [...],
  "governance_applied": true,
  "brand_constraints": {...},
  "estimated_completion_time": 900
}
```

### Utility Endpoints

#### POST /api/intake/validate
Validate responses against template and governance.

**Request:**
```json
{
  "template_id": "presentation",
  "client_slug": "kearney-default",
  "responses": {...}
}
```

#### GET /api/intake/preview/{template_id}
Preview template structure for development/debugging.

## Service Layer

### IntakeSessionService

```python
class IntakeSessionService:
    """Primary service for managing intake sessions"""
    
    def __init__(
        self,
        session_repository: IntakeSessionRepository,
        template_service: TemplateService,
        governance_service: GovernanceService,
        validation_service: ValidationService
    ):
        self.session_repo = session_repository
        self.template_svc = template_service
        self.governance_svc = governance_service
        self.validation_svc = validation_service
    
    async def create_session(
        self,
        template_id: str,
        client_slug: str = "kearney-default",
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> IntakeSession:
        """Create new intake session with governance applied"""
        
        # Load template
        template = await self.template_svc.load_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Load and apply governance
        governance = await self.governance_svc.load_governance(client_slug)
        template = self.governance_svc.apply_governance(template, governance)
        
        # Create session
        session = IntakeSession(
            template_id=template_id,
            client_slug=client_slug,
            user_id=user_id,
            metadata=metadata or {},
            governance_data=governance,
            current_phase_id=self._determine_first_phase(template),
            phase_order=self._build_phase_order(template)
        )
        
        # Save session
        await self.session_repo.save(session)
        
        return session
    
    async def submit_responses(
        self,
        session_id: str,
        phase_id: str,
        responses: dict[str, Any],
        auto_advance: bool = False
    ) -> ResponseSubmissionResult:
        """Submit responses for a phase with validation"""
        
        session = await self.session_repo.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        template = await self.template_svc.load_template(session.template_id)
        
        # Validate responses
        validation_result = await self.validation_svc.validate_phase_responses(
            template, phase_id, responses, session.governance_data
        )
        
        # Update session
        session.responses.update(responses)
        session.last_activity = datetime.utcnow()
        
        # Process derived fields
        await self._process_derived_fields(session, template)
        
        # Check if phase is complete
        phase_complete = validation_result.is_valid
        if phase_complete:
            session.completed_phases.add(phase_id)
            
            # Auto-advance if requested
            if auto_advance:
                next_phase = self._determine_next_phase(session, template)
                if next_phase:
                    session.current_phase_id = next_phase
        
        # Update validation errors
        session.validation_errors = [
            err for err in session.validation_errors 
            if not err.field_id.startswith(f"{phase_id}.")
        ]
        session.validation_errors.extend(validation_result.errors)
        
        await self.session_repo.save(session)
        
        return ResponseSubmissionResult(
            success=True,
            validation_result=validation_result,
            phase_complete=phase_complete,
            next_phase_id=session.current_phase_id,
            progress_percent=self._calculate_progress(session, template)
        )
    
    async def complete_session(self, session_id: str) -> ProjectCreationResult:
        """Complete intake session and create project"""
        
        session = await self.session_repo.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        template = await self.template_svc.load_template(session.template_id)
        
        # Final validation
        validation_result = await self.validation_svc.validate_complete_intake(
            template, session.responses, session.governance_data
        )
        
        if not validation_result.is_valid:
            raise ValidationError(validation_result.errors)
        
        # Format intake description for orchestrator
        intake_description = await self._format_intake_description(session, template)
        
        # Create project
        project_request = CreateProjectRequest(
            project_name=session.responses["project_name"],
            client=session.client_slug,
            project_type=session.template_id,
            template_id=session.template_id,
            description=intake_description,
            metadata={
                "intake_session_id": session_id,
                "intake_responses": session.responses,
                "governance_applied": session.governance_data,
                "completion_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        project = await self._create_project(project_request)
        
        # Mark session complete
        session.is_complete = True
        session.project_id = project.project_id
        await self.session_repo.save(session)
        
        return ProjectCreationResult(
            project_id=project.project_id,
            success=True,
            intake_summary=self._build_intake_summary(session, template),
            next_steps=NextSteps(
                redirect_url=f"/projects/{project.project_id}/ready",
                workflow_status="ready_to_start"
            )
        )
```

### TemplateService

```python
class TemplateService:
    """Service for loading and processing intake templates"""
    
    def __init__(self, template_loader: TemplateLoader):
        self.loader = template_loader
        self._template_cache: dict[str, TemplateDefinition] = {}
    
    async def load_template(self, template_id: str) -> TemplateDefinition:
        """Load template with inheritance resolution"""
        
        if template_id in self._template_cache:
            return self._template_cache[template_id]
            
        template = await self.loader.load_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
            
        # Resolve inheritance
        if template.template.extends:
            parent = await self.load_template(template.template.extends)
            template = self._merge_templates(parent, template)
            
        self._template_cache[template_id] = template
        return template
    
    def _merge_templates(self, parent: TemplateDefinition, child: TemplateDefinition) -> TemplateDefinition:
        """Merge child template with parent, handling inheritance"""
        
        # Start with parent as base
        merged = parent.model_copy(deep=True)
        
        # Override with child metadata
        merged.template = child.template
        
        # Merge phases - child phases override parent phases with same ID
        child_phase_ids = {phase.id for phase in child.phases}
        merged.phases = [
            phase for phase in parent.phases 
            if phase.id not in child_phase_ids
        ]
        merged.phases.extend(child.phases)
        
        # Sort phases by order
        merged.phases.sort(key=lambda p: p.order)
        
        # Override other sections
        if child.brand_constraints:
            merged.brand_constraints = child.brand_constraints
        if child.ad_hoc:
            merged.ad_hoc = child.ad_hoc
        if child.governance:
            merged.governance = child.governance
        if child.output:
            merged.output = child.output
            
        return merged
```

### ConditionalLogicEngine

```python
class ConditionalLogicEngine:
    """Engine for evaluating conditional logic in templates"""
    
    def evaluate_condition(
        self, 
        condition: ConditionDefinition, 
        responses: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition against responses"""
        
        field_value = responses.get(condition.field)
        
        match condition.operator:
            case ConditionOperator.EQUALS:
                return field_value == condition.value
                
            case ConditionOperator.NOT_EQUALS:
                return field_value != condition.value
                
            case ConditionOperator.IN:
                return field_value in condition.value if isinstance(condition.value, list) else False
                
            case ConditionOperator.NOT_IN:
                return field_value not in condition.value if isinstance(condition.value, list) else True
                
            case ConditionOperator.CONTAINS:
                return condition.value in str(field_value) if field_value is not None else False
                
            case ConditionOperator.NOT_CONTAINS:
                return condition.value not in str(field_value) if field_value is not None else True
                
            case ConditionOperator.GREATER_THAN:
                return float(field_value) > float(condition.value) if field_value is not None else False
                
            case ConditionOperator.LESS_THAN:
                return float(field_value) < float(condition.value) if field_value is not None else False
                
            case ConditionOperator.GREATER_EQUAL:
                return float(field_value) >= float(condition.value) if field_value is not None else False
                
            case ConditionOperator.LESS_EQUAL:
                return float(field_value) <= float(condition.value) if field_value is not None else False
                
            case ConditionOperator.IS_SET:
                return field_value is not None
                
            case ConditionOperator.IS_NOT_SET:
                return field_value is None
                
            case ConditionOperator.REGEX_MATCH:
                import re
                return bool(re.match(condition.value, str(field_value))) if field_value is not None else False
                
            case _:
                raise ValueError(f"Unknown operator: {condition.operator}")
    
    def evaluate_complex_condition(
        self,
        condition: ConditionDefinition,
        responses: dict[str, Any]
    ) -> bool:
        """Evaluate condition with AND/OR logic"""
        
        # Evaluate base condition
        result = self.evaluate_condition(condition, responses)
        
        # Evaluate AND conditions (all must be true)
        if condition.and_conditions:
            for and_cond in condition.and_conditions:
                if not self.evaluate_complex_condition(and_cond, responses):
                    result = False
                    break
        
        # Evaluate OR conditions (any can be true)
        if condition.or_conditions:
            or_result = any(
                self.evaluate_complex_condition(or_cond, responses)
                for or_cond in condition.or_conditions
            )
            result = result or or_result
            
        return result
    
    def determine_visible_questions(
        self,
        phase: PhaseDefinition,
        responses: dict[str, Any]
    ) -> list[QuestionDefinition]:
        """Determine which questions in a phase should be visible"""
        
        visible_questions = []
        
        for question in phase.questions:
            if question.hidden:
                continue
                
            if question.condition:
                if not self.evaluate_complex_condition(question.condition, responses):
                    continue
                    
            visible_questions.append(question)
            
        return visible_questions
    
    def determine_next_phase(
        self,
        current_phase: PhaseDefinition,
        responses: dict[str, Any],
        template: TemplateDefinition
    ) -> str | None:
        """Determine next phase based on conditional logic"""
        
        # Check for conditional next phase logic in questions
        for question in current_phase.questions:
            if question.conditional_next and question.id in responses:
                response_value = responses[question.id]
                if str(response_value) in question.conditional_next:
                    return question.conditional_next[str(response_value)]
        
        # Check phase-level conditional next
        if current_phase.conditional_next:
            for value, next_phase_id in current_phase.conditional_next.items():
                # This is simplified - real implementation would evaluate conditions
                if value in str(responses):  # Simplified logic
                    return next_phase_id
        
        # Fall back to linear progression
        if current_phase.next_phase_id:
            return current_phase.next_phase_id
            
        # Find next phase in order
        current_order = current_phase.order
        next_phases = [
            phase for phase in template.phases 
            if phase.order > current_order
        ]
        
        if next_phases:
            next_phase = min(next_phases, key=lambda p: p.order)
            
            # Check if next phase is conditionally visible
            if next_phase.condition:
                if not self.evaluate_complex_condition(next_phase.condition, responses):
                    # Skip this phase and try the next one
                    return self.determine_next_phase(next_phase, responses, template)
            
            return next_phase.id
            
        return None  # No more phases
```

### ValidationService

```python
class ValidationService:
    """Service for validating intake responses"""
    
    def __init__(self, governance_service: GovernanceService):
        self.governance_svc = governance_service
    
    async def validate_phase_responses(
        self,
        template: TemplateDefinition,
        phase_id: str,
        responses: dict[str, Any],
        governance_data: dict[str, Any]
    ) -> ValidationResult:
        """Validate responses for a specific phase"""
        
        phase = template.phase_map.get(phase_id)
        if not phase:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    field_id=phase_id,
                    error_type="phase_not_found",
                    message=f"Phase not found: {phase_id}"
                )]
            )
        
        errors = []
        warnings = []
        
        # Validate each question in the phase
        for question in phase.questions:
            if question.hidden or question.type == "derived":
                continue
                
            question_errors = await self._validate_question_response(
                question, responses.get(question.id), responses, governance_data
            )
            errors.extend(question_errors)
        
        # Check governance constraints
        governance_errors = await self.governance_svc.validate_responses(
            responses, governance_data
        )
        warnings.extend(governance_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_question_response(
        self,
        question: QuestionDefinition,
        response_value: Any,
        all_responses: dict[str, Any],
        governance_data: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate a single question response"""
        
        errors = []
        field_id = question.id
        
        # Required field validation
        if question.required and (response_value is None or response_value == ""):
            errors.append(ValidationError(
                field_id=field_id,
                error_type="required",
                message=f"{question.question or question.id} is required"
            ))
            return errors  # Skip other validations if required field is missing
        
        # Skip validation if field is not set and not required
        if response_value is None or response_value == "":
            return errors
        
        # Type-specific validation
        match question.type:
            case "text" | "textarea":
                errors.extend(self._validate_text(field_id, response_value, question))
                
            case "number":
                errors.extend(self._validate_number(field_id, response_value, question))
                
            case "choice":
                errors.extend(self._validate_choice(field_id, response_value, question))
                
            case "multi_choice":
                errors.extend(self._validate_multi_choice(field_id, response_value, question))
                
            case "date":
                errors.extend(self._validate_date(field_id, response_value, question))
                
            case "list":
                errors.extend(self._validate_list(field_id, response_value, question))
        
        # Custom validation rules
        if question.validation:
            errors.extend(self._apply_validation_rules(
                field_id, response_value, question.validation
            ))
        
        return errors
    
    def _validate_text(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate text field"""
        errors = []
        text_value = str(value)
        
        if question.validation:
            if question.validation.min_length and len(text_value) < question.validation.min_length:
                errors.append(ValidationError(
                    field_id=field_id,
                    error_type="min_length",
                    message=f"Minimum length is {question.validation.min_length} characters"
                ))
                
            if question.validation.max_length and len(text_value) > question.validation.max_length:
                errors.append(ValidationError(
                    field_id=field_id,
                    error_type="max_length",
                    message=f"Maximum length is {question.validation.max_length} characters"
                ))
                
            if question.validation.pattern:
                import re
                if not re.match(question.validation.pattern, text_value):
                    errors.append(ValidationError(
                        field_id=field_id,
                        error_type="pattern",
                        message="Invalid format"
                    ))
        
        return errors
    
    def _validate_choice(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate choice field"""
        errors = []
        
        valid_options = [opt.value for opt in question.options]
        if str(value) not in valid_options:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_choice",
                message=f"Invalid choice. Must be one of: {', '.join(valid_options)}"
            ))
            
        return errors
```

## Frontend Implementation (React)

### Component Architecture

```typescript
// Main intake wizard component
export const IntakeWizard: React.FC<IntakeWizardProps> = ({
  templateId,
  clientSlug = "kearney-default",
  onComplete,
  onCancel
}) => {
  const [session, setSession] = useState<IntakeSession | null>(null);
  const [currentPhase, setCurrentPhase] = useState<PhaseDefinition | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        setLoading(true);
        const newSession = await intakeApi.createSession({
          template_id: templateId,
          client_slug: clientSlug
        });
        setSession(newSession);
        
        // Load current phase
        const phase = await intakeApi.getCurrentPhase(newSession.session_id);
        setCurrentPhase(phase);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    initializeSession();
  }, [templateId, clientSlug]);

  const handleResponseSubmit = async (responses: Record<string, any>) => {
    if (!session || !currentPhase) return;

    try {
      setLoading(true);
      const result = await intakeApi.submitResponses(
        session.session_id,
        currentPhase.id,
        responses,
        true // auto_advance
      );

      // Update session with new state
      const updatedSession = await intakeApi.getSession(session.session_id);
      setSession(updatedSession);

      // Load next phase if advanced
      if (result.next_phase_id) {
        const nextPhase = await intakeApi.getPhase(
          session.session_id,
          result.next_phase_id
        );
        setCurrentPhase(nextPhase);
      }

      // Check if intake is complete
      if (updatedSession.is_complete) {
        const completionResult = await intakeApi.completeSession(session.session_id);
        onComplete(completionResult.project_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigation = async (direction: 'next' | 'previous') => {
    if (!session) return;

    try {
      const result = await intakeApi.navigate(session.session_id, direction);
      if (result.target_phase_id) {
        const phase = await intakeApi.getPhase(session.session_id, result.target_phase_id);
        setCurrentPhase(phase);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading && !session) {
    return <IntakeLoadingSpinner />;
  }

  if (error) {
    return <IntakeErrorDisplay error={error} onRetry={() => window.location.reload()} />;
  }

  if (!session || !currentPhase) {
    return <IntakeErrorDisplay error="Session not initialized" />;
  }

  return (
    <div className="intake-wizard">
      <IntakeHeader
        session={session}
        currentPhase={currentPhase}
      />
      
      <ProgressTracker
        session={session}
        currentPhase={currentPhase}
      />
      
      <PhaseForm
        phase={currentPhase}
        session={session}
        onSubmit={handleResponseSubmit}
        onNavigate={handleNavigation}
        loading={loading}
      />
    </div>
  );
};

// Phase form component
const PhaseForm: React.FC<PhaseFormProps> = ({
  phase,
  session,
  onSubmit,
  onNavigate,
  loading
}) => {
  const [responses, setResponses] = useState<Record<string, any>>({});
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [touched, setTouched] = useState<Set<string>>(new Set());

  // Load existing responses for this phase
  useEffect(() => {
    const phaseResponses = Object.fromEntries(
      Object.entries(session.responses).filter(([key]) =>
        phase.questions.some(q => q.id === key)
      )
    );
    setResponses(phaseResponses);
  }, [phase, session.responses]);

  // Auto-save responses
  useEffect(() => {
    const autoSave = async () => {
      if (Object.keys(responses).length > 0) {
        try {
          await intakeApi.autoSaveResponses(session.session_id, responses);
        } catch (err) {
          console.warn('Auto-save failed:', err);
        }
      }
    };

    const timer = setTimeout(autoSave, 2000);
    return () => clearTimeout(timer);
  }, [responses, session.session_id]);

  const handleFieldChange = (questionId: string, value: any) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
    setTouched(prev => new Set(prev).add(questionId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched for validation display
    const allQuestionIds = phase.questions.map(q => q.id);
    setTouched(new Set(allQuestionIds));
    
    // Validate before submitting
    const validation = await intakeApi.validateResponses(
      session.session_id,
      phase.id,
      responses
    );
    
    setValidationErrors(validation.errors);
    
    if (validation.is_valid) {
      onSubmit(responses);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="phase-form">
      <div className="phase-header">
        <h2>{phase.name}</h2>
        {phase.description && (
          <p className="phase-description">{phase.description}</p>
        )}
      </div>

      <div className="questions">
        {phase.questions
          .filter(q => !q.hidden)
          .map(question => (
            <QuestionRenderer
              key={question.id}
              question={question}
              value={responses[question.id]}
              onChange={(value) => handleFieldChange(question.id, value)}
              error={validationErrors.find(e => e.field_id === question.id)}
              touched={touched.has(question.id)}
            />
          ))}
      </div>

      <div className="form-actions">
        {phase.allow_back && (
          <Button
            type="button"
            variant="secondary"
            onClick={() => onNavigate('previous')}
            disabled={loading}
          >
            Back
          </Button>
        )}
        
        <Button
          type="submit"
          variant="primary"
          disabled={loading}
          loading={loading}
        >
          {phase.next_phase_id ? 'Continue' : 'Complete'}
        </Button>
      </div>
    </form>
  );
};

// Dynamic question renderer
const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  question,
  value,
  onChange,
  error,
  touched
}) => {
  const renderInput = () => {
    switch (question.type) {
      case 'text':
        return (
          <TextInput
            value={value || ''}
            onChange={onChange}
            placeholder={question.placeholder}
            required={question.required}
            maxLength={question.validation?.max_length}
          />
        );

      case 'textarea':
        return (
          <TextArea
            value={value || ''}
            onChange={onChange}
            placeholder={question.placeholder}
            required={question.required}
            rows={4}
            maxLength={question.validation?.max_length}
          />
        );

      case 'choice':
        return (
          <RadioGroup
            value={value || ''}
            onChange={onChange}
            required={question.required}
          >
            {question.options.map(option => (
              <Radio key={option.value} value={option.value}>
                {option.label}
                {option.description && (
                  <span className="option-description">{option.description}</span>
                )}
              </Radio>
            ))}
          </RadioGroup>
        );

      case 'multi_choice':
        return (
          <CheckboxGroup
            value={value || []}
            onChange={onChange}
            required={question.required}
          >
            {question.options.map(option => (
              <Checkbox key={option.value} value={option.value}>
                {option.label}
              </Checkbox>
            ))}
          </CheckboxGroup>
        );

      case 'number':
        return (
          <NumberInput
            value={value ?? ''}
            onChange={onChange}
            placeholder={question.placeholder}
            required={question.required}
            min={question.min_value}
            max={question.max_value}
            step={question.step}
            unit={question.unit}
          />
        );

      case 'date':
        return (
          <DateInput
            value={value || ''}
            onChange={onChange}
            required={question.required}
            min={question.validation?.min_date}
            max={question.validation?.max_date}
          />
        );

      case 'list':
        return (
          <ListInput
            value={value || []}
            onChange={onChange}
            itemSchema={question.item_schema}
            minItems={question.min_items}
            maxItems={question.max_items}
            required={question.required}
          />
        );

      default:
        return <div>Unsupported question type: {question.type}</div>;
    }
  };

  return (
    <div className={`question ${question.width}`}>
      {question.question && (
        <label className="question-label">
          {question.question}
          {question.required && <span className="required">*</span>}
        </label>
      )}
      
      {question.help_text && (
        <p className="help-text">{question.help_text}</p>
      )}
      
      <div className="question-input">
        {renderInput()}
      </div>
      
      {error && touched && (
        <div className="error-message">{error.message}</div>
      )}
    </div>
  );
};
```

## Security Considerations

### Data Protection
- **Session Isolation**: Sessions are user-specific and properly isolated
- **Input Validation**: All responses validated against schema and business rules
- **XSS Prevention**: All user inputs sanitized before display
- **CSRF Protection**: Standard FastAPI CSRF protection enabled

### Access Control
- **Authentication**: Session creation requires authenticated user
- **Authorization**: Users can only access their own sessions
- **Session Expiry**: Sessions expire after configurable idle time
- **Cleanup**: Expired sessions automatically purged

### Data Storage
- **Encryption**: Sensitive responses encrypted at rest
- **Audit Trail**: All session operations logged
- **GDPR Compliance**: Session data can be deleted on user request
- **Backup Strategy**: Session data included in regular backups

## Performance Considerations

### Caching Strategy
- **Template Caching**: Templates cached in memory with invalidation
- **Governance Caching**: Client governance cached per request
- **Session Caching**: Recent sessions cached in Redis (future)

### Optimization
- **Lazy Loading**: Questions loaded incrementally as phases are accessed
- **Response Compression**: Large responses compressed before storage
- **Database Indexing**: Proper indexing on session queries
- **Auto-cleanup**: Old sessions automatically archived/deleted

### Scalability
- **Horizontal Scaling**: Stateless API design supports multiple instances
- **Session Store**: Pluggable session storage (FS → Redis → Database)
- **Rate Limiting**: API rate limiting to prevent abuse
- **Health Checks**: Comprehensive health monitoring

## Testing Strategy

### Unit Tests
- Model validation and serialization
- Conditional logic engine
- Validation service logic
- Template inheritance resolution

### Integration Tests
- API endpoint functionality
- Session lifecycle management
- Template loading and processing
- Governance application

### End-to-End Tests
- Complete intake workflows
- Error handling scenarios
- Browser compatibility
- Performance benchmarks

### Test Data
- Template fixtures for common scenarios
- Mock governance configurations
- Realistic user response patterns
- Edge case validation scenarios

## Deployment

### Environment Configuration
```python
# Environment variables
INTAKE_SESSION_STORAGE = "filesystem"  # filesystem, redis, database
INTAKE_SESSION_TTL = 86400  # 24 hours
INTAKE_TEMPLATE_PATH = "/app/intake/templates"
INTAKE_GOVERNANCE_PATH = "/app/clients"
INTAKE_AUTO_SAVE_INTERVAL = 30  # seconds
```

### Infrastructure Requirements
- **Storage**: Persistent storage for sessions and templates
- **Memory**: 512MB+ for template caching
- **CPU**: Minimal, mostly I/O bound operations
- **Network**: Standard HTTP/JSON API bandwidth

### Monitoring
- **Session Metrics**: Creation, completion, abandonment rates
- **Performance Metrics**: Response times, validation failures
- **Error Tracking**: Failed validations, system errors
- **User Analytics**: Template usage patterns, completion paths

This design provides a comprehensive, scalable architecture for the intake template system that integrates seamlessly with the existing orchestrator workflow while providing an excellent user experience for structured requirement gathering.