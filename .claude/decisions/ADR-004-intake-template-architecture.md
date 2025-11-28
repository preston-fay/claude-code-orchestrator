# ADR-004: Intake Template System Architecture

## Status
Proposed

## Context
The orchestrator requires comprehensive project requirements before it can generate optimal outputs. The intake template system provides structured interviews that adapt based on project type and user responses to gather "perfect prompts for perfect prompts."

### Current State
- Intake templates exist in `/intake/templates/` with YAML definitions
- JSON schema validation exists in `/intake/schema/`
- FastAPI backend supports basic project creation with `description` field
- React frontend (RSG-UI) needs intake wizard implementation
- No structured session management for intake workflows

### Requirements
1. **Structured Interviews**: Guide users through project-specific questionnaires
2. **Conditional Logic**: Questions adapt based on previous answers
3. **Session Management**: Support multi-step interviews with save/resume
4. **Validation**: Ensure data integrity and completeness
5. **Client Governance**: Automatically apply client-specific constraints
6. **Integration**: Seamless handoff to orchestrator workflow

## Decision

### 1. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RSG-UI        │    │   FastAPI API    │    │  Template       │
│   (React)       │    │   Endpoints      │    │  Engine         │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ IntakeWizard    │◄──►│ /api/intake/*    │◄──►│ YAML Parser     │
│ QuestionForm    │    │ SessionManager   │    │ Validator       │
│ ProgressTracker │    │ ResponseStore    │    │ Logic Engine    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │                       ▼                       ▼
        │              ┌──────────────────┐    ┌─────────────────┐
        │              │  Session Store   │    │  Governance     │
        │              │  (FileSystem)    │    │  Integration    │
        └──────────────┤  Redis (Future)  │    │  (Client Rules) │
                       └──────────────────┘    └─────────────────┘
```

### 2. API Endpoint Design

#### Core Endpoints
```python
# Session Management
POST   /api/intake/sessions                    # Start new intake session
GET    /api/intake/sessions/{session_id}      # Get session state
PUT    /api/intake/sessions/{session_id}      # Update session
DELETE /api/intake/sessions/{session_id}      # Delete session

# Template Operations
GET    /api/intake/templates                  # List available templates
GET    /api/intake/templates/{template_id}    # Get template definition

# Response Management
POST   /api/intake/sessions/{session_id}/responses  # Submit responses
GET    /api/intake/sessions/{session_id}/responses  # Get current responses
POST   /api/intake/sessions/{session_id}/validate   # Validate current state
POST   /api/intake/sessions/{session_id}/complete   # Complete intake & start project

# Navigation
GET    /api/intake/sessions/{session_id}/current-phase     # Get current phase
POST   /api/intake/sessions/{session_id}/advance          # Advance to next phase
POST   /api/intake/sessions/{session_id}/back             # Go to previous phase
```

#### Request/Response Models
```python
class IntakeSessionRequest(BaseModel):
    template_id: str
    client_slug: str = "kearney-default"
    metadata: dict[str, Any] = Field(default_factory=dict)

class IntakeSessionResponse(BaseModel):
    session_id: str
    template_id: str
    client_slug: str
    current_phase_id: str
    progress_percent: float
    is_complete: bool
    created_at: datetime
    updated_at: datetime

class PhaseResponse(BaseModel):
    phase_id: str
    name: str
    description: str
    required: bool
    questions: list[QuestionDefinition]
    is_current: bool
    is_complete: bool

class ResponseSubmission(BaseModel):
    phase_id: str
    responses: dict[str, Any]
    
class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[ValidationError]
    warnings: list[str]
```

### 3. Data Models

#### Session State
```python
class IntakeSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    template_id: str
    client_slug: str
    current_phase_id: str | None = None
    phase_order: list[str] = Field(default_factory=list)
    responses: dict[str, Any] = Field(default_factory=dict)
    governance_data: dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

#### Template Definition
```python
class TemplateDefinition(BaseModel):
    template: TemplateMetadata
    phases: list[PhaseDefinition]
    brand_constraints: BrandConstraints | None = None
    ad_hoc: AdHocConfig | None = None
    governance: GovernanceConfig | None = None
    output: OutputConfig | None = None

class PhaseDefinition(BaseModel):
    id: str
    name: str
    description: str | None = None
    required: bool = False
    condition: ConditionDefinition | None = None
    questions: list[QuestionDefinition]
```

### 4. Session Management Strategy

#### Session Storage
- **Primary**: FileSystem-based storage in `data/intake_sessions/`
- **Format**: JSON files named `{session_id}.json`
- **Future**: Redis for production scalability

#### Session Lifecycle
1. **Creation**: Template loaded, governance applied, initial phase determined
2. **Progression**: Conditional logic determines next phases
3. **Validation**: Real-time validation as responses are submitted
4. **Completion**: Final validation, project creation, session archival

#### Session Persistence
```python
class IntakeSessionRepository:
    async def create(self, session: IntakeSession) -> str
    async def get(self, session_id: str) -> IntakeSession | None
    async def update(self, session: IntakeSession) -> None
    async def delete(self, session_id: str) -> bool
    async def list_by_user(self, user_id: str) -> list[IntakeSession]
```

### 5. Validation Strategy

#### Multi-Level Validation
1. **Schema Validation**: JSON schema enforcement at API boundary
2. **Template Validation**: Questions answered per template requirements
3. **Governance Validation**: Client-specific constraints applied
4. **Business Logic**: Custom validators for complex rules

#### Validation Implementation
```python
class IntakeValidator:
    def __init__(self, template: TemplateDefinition, governance: dict):
        self.template = template
        self.governance = governance
        
    async def validate_responses(self, responses: dict) -> ValidationResult:
        errors = []
        warnings = []
        
        # Schema validation
        errors.extend(self._validate_schema(responses))
        
        # Template validation
        errors.extend(self._validate_template_requirements(responses))
        
        # Governance validation
        warnings.extend(self._validate_governance_constraints(responses))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 6. Conditional Logic Engine

#### Logic Evaluation
```python
class ConditionalLogicEngine:
    def evaluate_condition(self, condition: ConditionDefinition, responses: dict) -> bool:
        field_value = responses.get(condition.field)
        
        match condition.operator:
            case "equals":
                return field_value == condition.value
            case "in":
                return field_value in condition.value
            case "contains":
                return condition.value in str(field_value)
            case "is_set":
                return field_value is not None
            # ... other operators
                
    def determine_next_phases(self, current_phase: str, responses: dict, template: TemplateDefinition) -> list[str]:
        # Logic to determine which phases to show next based on responses
        pass
```

#### Phase Navigation
- **Linear**: Default sequential progression through phases
- **Conditional**: Phases appear/disappear based on responses
- **Branching**: Different phase sequences based on choices
- **Skip Logic**: Auto-skip phases when conditions aren't met

### 7. Client Governance Integration

#### Governance Loading
```python
class GovernanceManager:
    def load_client_governance(self, client_slug: str) -> dict:
        governance_path = f"clients/{client_slug}/governance.yaml"
        return self._load_yaml(governance_path)
        
    def apply_governance_to_template(self, template: TemplateDefinition, governance: dict) -> TemplateDefinition:
        # Apply brand constraints, validation rules, etc.
        pass
        
    def validate_against_governance(self, responses: dict, governance: dict) -> list[ValidationError]:
        # Check responses against client-specific rules
        pass
```

#### Brand Constraint Application
- **Automatic**: Colors, fonts, and styles applied from governance
- **Validation**: Ensure user inputs comply with client standards
- **Notification**: Show governance notices to users

### 8. Frontend Integration (RSG-UI)

#### Component Architecture
```typescript
// Main intake wizard component
interface IntakeWizardProps {
  templateId: string;
  clientSlug?: string;
  onComplete: (sessionId: string) => void;
}

// Phase progression component
interface PhaseNavigatorProps {
  session: IntakeSession;
  onPhaseChange: (phaseId: string) => void;
}

// Dynamic question renderer
interface QuestionFormProps {
  question: QuestionDefinition;
  value?: any;
  onChange: (value: any) => void;
  errors?: ValidationError[];
}
```

#### State Management
- **Context**: React Context for session state
- **Persistence**: Auto-save responses to backend
- **Validation**: Real-time validation with debouncing

### 9. Integration with Orchestrator Workflow

#### Handoff Process
1. **Complete Intake**: User completes all required phases
2. **Final Validation**: System validates complete response set
3. **Project Creation**: Create project with intake data
4. **Context Passing**: Intake responses become project context
5. **Workflow Start**: Orchestrator begins with comprehensive requirements

#### Data Flow
```python
# After intake completion
async def complete_intake(session_id: str) -> ProjectDTO:
    session = await session_repo.get(session_id)
    
    # Validate complete intake
    validation = await validator.validate_complete(session.responses)
    if not validation.is_valid:
        raise ValidationError(validation.errors)
    
    # Create project with intake context
    project_request = CreateProjectRequest(
        project_name=session.responses["project_name"],
        client=session.client_slug,
        project_type=session.template_id,
        template_id=session.template_id,
        description=await self._format_intake_description(session.responses),
        intake_path=None,  # Already processed
        metadata={
            "intake_session_id": session_id,
            "intake_responses": session.responses,
            "governance_applied": session.governance_data
        }
    )
    
    project = await create_project(project_request)
    await session_repo.mark_completed(session_id, project.project_id)
    
    return project
```

## Consequences

### Positive
1. **Structured Requirements**: Comprehensive project context before orchestration
2. **Adaptive Interviews**: Questions adapt to project type and previous answers
3. **Client Compliance**: Automatic application of governance constraints
4. **User Experience**: Progressive disclosure and guided workflows
5. **Data Quality**: Validation ensures complete, correct inputs
6. **Scalability**: Session-based architecture supports concurrent users

### Negative
1. **Complexity**: Additional layer between user and orchestrator
2. **Development Effort**: Significant implementation for conditional logic
3. **Storage Requirements**: Session state persistence needs
4. **Template Maintenance**: YAML templates require ongoing maintenance

### Neutral
1. **Performance Impact**: Additional API calls for session management
2. **State Management**: Need for robust session cleanup and expiration
3. **Testing Complexity**: Conditional logic requires comprehensive test coverage

## Implementation Plan

### Phase 1: Core Infrastructure
- [ ] Intake session data models
- [ ] Session repository (filesystem-based)
- [ ] Template loading and parsing
- [ ] Basic API endpoints

### Phase 2: Logic Engine
- [ ] Conditional logic evaluation
- [ ] Phase navigation engine
- [ ] Validation framework
- [ ] Governance integration

### Phase 3: Frontend Implementation
- [ ] React intake wizard components
- [ ] Question form renderers
- [ ] Progress tracking
- [ ] Auto-save functionality

### Phase 4: Integration
- [ ] Orchestrator handoff
- [ ] Project creation with intake context
- [ ] End-to-end testing
- [ ] Performance optimization

## Alternatives Considered

### 1. Direct Form Integration
**Rejected**: Single large form lacks adaptability and progressive disclosure

### 2. External Survey Tools
**Rejected**: Poor integration with orchestrator and governance systems

### 3. Database-Only Session Storage
**Rejected**: Adds infrastructure dependency, filesystem adequate for MVP

## References
- Intake Template README: `/intake/README.md`
- Intake Schema: `/intake/schema/intake.schema.json`
- Existing API: `/orchestrator_v2/api/server.py`
- Template Examples: `/intake/templates/*.yaml`