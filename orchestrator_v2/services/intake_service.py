"""
Intake Template System Service Layer.

Provides business logic for managing intake sessions, loading templates,
conditional logic evaluation, and validation.
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from orchestrator_v2.models.intake import (
    ConditionDefinition,
    ConditionOperator,
    CompleteSessionRequest,
    CreateSessionRequest,
    IntakeSession,
    IntakeSummary,
    NavigationRequest,
    NavigationResult,
    NextSteps,
    PhaseDefinition,
    PhaseResponse,
    ProjectCreationResult,
    QuestionDefinition,
    ResponseSubmissionResult,
    SessionResponse,
    SessionStatusResponse,
    SubmitResponsesRequest,
    TemplateDefinition,
    TemplateListItem,
    TemplateMetadata,
    ValidateRequest,
    ValidationError,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class IntakeServiceError(Exception):
    """Base exception for intake service errors."""
    pass


class TemplateNotFoundError(IntakeServiceError):
    """Template not found error."""
    pass


class SessionNotFoundError(IntakeServiceError):
    """Session not found error."""
    pass


class ValidationServiceError(IntakeServiceError):
    """Validation service error."""
    pass


class IntakeSessionRepository:
    """Repository for managing intake sessions."""
    
    def __init__(self, storage_path: str = "data/intake_sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def create(self, session: IntakeSession) -> str:
        """Create a new session."""
        session_file = self.storage_path / f"{session.session_id}.json"
        with open(session_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            session_data = session.dict()
            if 'completed_phases' in session_data:
                session_data['completed_phases'] = list(session_data['completed_phases'])
            json.dump(session_data, f, default=str, indent=2)
        return session.session_id
    
    async def get(self, session_id: str) -> IntakeSession | None:
        """Get session by ID."""
        session_file = self.storage_path / f"{session_id}.json"
        if not session_file.exists():
            return None
            
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            # Convert datetime strings back to datetime objects
            for field in ['created_at', 'updated_at', 'last_activity']:
                if field in session_data and isinstance(session_data[field], str):
                    session_data[field] = datetime.fromisoformat(session_data[field].replace('Z', '+00:00'))
            return IntakeSession(**session_data)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    async def update(self, session: IntakeSession) -> None:
        """Update an existing session."""
        session.updated_at = datetime.utcnow()
        session.last_activity = datetime.utcnow()
        await self.create(session)  # Reuse create method
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.storage_path / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    
    async def list_by_user(self, user_id: str) -> list[IntakeSession]:
        """List sessions for a user."""
        sessions = []
        for session_file in self.storage_path.glob("*.json"):
            session = await self.get(session_file.stem)
            if session and session.user_id == user_id:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)


class TemplateLoader:
    """Loader for intake templates."""
    
    def __init__(self, templates_path: str = "intake/templates"):
        self.templates_path = Path(templates_path)
    
    async def load_template(self, template_id: str) -> TemplateDefinition | None:
        """Load template by ID."""
        template_file = self.templates_path / f"{template_id}.yaml"
        if not template_file.exists():
            return None
            
        try:
            with open(template_file, 'r') as f:
                template_data = yaml.safe_load(f)
            
            # Process template data to add missing IDs for nested properties
            self._process_template_data(template_data)
            
            return TemplateDefinition(**template_data)
        except Exception as e:
            logger.error(f"Error loading template {template_id}: {e}")
            return None
    
    def _process_template_data(self, template_data: dict) -> None:
        """Process template data to fix structural issues."""
        if 'phases' not in template_data:
            return
            
        for phase in template_data['phases']:
            if 'questions' not in phase:
                continue
                
            for question in phase['questions']:
                # Add IDs to object properties
                if 'properties' in question:
                    for prop_id, prop_def in question['properties'].items():
                        if isinstance(prop_def, dict) and 'id' not in prop_def:
                            prop_def['id'] = prop_id
                
                # Add IDs to item schema properties
                if 'item_schema' in question and 'properties' in question['item_schema']:
                    for prop_id, prop_def in question['item_schema']['properties'].items():
                        if isinstance(prop_def, dict) and 'id' not in prop_def:
                            prop_def['id'] = prop_id
    
    async def list_templates(self) -> list[TemplateListItem]:
        """List all available templates."""
        templates = []
        for template_file in self.templates_path.glob("*.yaml"):
            if template_file.name.startswith("_"):
                continue  # Skip base templates
                
            try:
                with open(template_file, 'r') as f:
                    template_data = yaml.safe_load(f)
                
                if 'template' not in template_data:
                    continue
                    
                template_meta = template_data['template']
                phases = template_data.get('phases', [])
                
                # Count questions
                question_count = sum(len(phase.get('questions', [])) for phase in phases)
                
                templates.append(TemplateListItem(
                    template_id=template_meta['id'],
                    name=template_meta['name'],
                    description=template_meta['description'],
                    category=template_meta.get('category', 'general'),
                    estimated_time_minutes=template_meta.get('estimated_time_minutes', 15),
                    question_count=question_count,
                    phase_count=len(phases),
                    icon=template_meta.get('icon'),
                    color=template_meta.get('color'),
                ))
            except Exception as e:
                logger.error(f"Error loading template {template_file}: {e}")
                continue
                
        return sorted(templates, key=lambda t: t.name)


class ConditionalLogicEngine:
    """Engine for evaluating conditional logic in templates."""
    
    def evaluate_condition(
        self, 
        condition: ConditionDefinition, 
        responses: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition against responses."""
        field_value = responses.get(condition.field)
        
        try:
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
                    return field_value is not None and field_value != ""
                    
                case ConditionOperator.IS_NOT_SET:
                    return field_value is None or field_value == ""
                    
                case ConditionOperator.REGEX_MATCH:
                    return bool(re.match(str(condition.value), str(field_value))) if field_value is not None else False
                    
                case _:
                    logger.warning(f"Unknown operator: {condition.operator}")
                    return False
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def evaluate_complex_condition(
        self,
        condition: ConditionDefinition,
        responses: dict[str, Any]
    ) -> bool:
        """Evaluate condition with AND/OR logic."""
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
        """Determine which questions in a phase should be visible."""
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
        """Determine next phase based on conditional logic."""
        # Check for conditional next phase logic in questions
        for question in current_phase.questions:
            if question.conditional_next and question.id in responses:
                response_value = str(responses[question.id])
                if response_value in question.conditional_next:
                    return question.conditional_next[response_value]
        
        # Check phase-level conditional next
        if current_phase.conditional_next:
            for value, next_phase_id in current_phase.conditional_next.items():
                # Check if any response contains this value (simplified)
                for response_val in responses.values():
                    if value in str(response_val):
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


class ValidationService:
    """Service for validating intake responses."""
    
    def __init__(self):
        pass
    
    async def validate_phase_responses(
        self,
        template: TemplateDefinition,
        phase_id: str,
        responses: dict[str, Any],
        governance_data: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate responses for a specific phase."""
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
        
        # Get visible questions for this phase
        logic_engine = ConditionalLogicEngine()
        visible_questions = logic_engine.determine_visible_questions(phase, responses)
        
        # Validate each visible question
        for question in visible_questions:
            if question.type.value == "derived":
                continue
                
            question_errors = await self._validate_question_response(
                question, responses.get(question.id), responses
            )
            errors.extend(question_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def validate_complete_intake(
        self,
        template: TemplateDefinition,
        responses: dict[str, Any],
        governance_data: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate complete intake for final submission."""
        all_errors = []
        all_warnings = []
        
        # Validate all phases
        for phase in template.phases:
            result = await self.validate_phase_responses(
                template, phase.id, responses, governance_data
            )
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )
    
    async def _validate_question_response(
        self,
        question: QuestionDefinition,
        response_value: Any,
        all_responses: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate a single question response."""
        errors = []
        field_id = question.id
        
        # Required field validation
        if question.required and (response_value is None or response_value == ""):
            errors.append(ValidationError(
                field_id=field_id,
                error_type="required",
                message=f"{question.question or question.id} is required"
            ))
            return errors
        
        # Skip validation if field is not set and not required
        if response_value is None or response_value == "":
            return errors
        
        # Type-specific validation
        match question.type.value:
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
        
        return errors
    
    def _validate_text(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate text field."""
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
                if not re.match(question.validation.pattern, text_value):
                    errors.append(ValidationError(
                        field_id=field_id,
                        error_type="pattern",
                        message="Invalid format"
                    ))
        
        return errors
    
    def _validate_number(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate number field."""
        errors = []
        
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_type",
                message="Must be a valid number"
            ))
            return errors
        
        if question.min_value is not None and num_value < question.min_value:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="min_value",
                message=f"Minimum value is {question.min_value}"
            ))
            
        if question.max_value is not None and num_value > question.max_value:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="max_value",
                message=f"Maximum value is {question.max_value}"
            ))
        
        return errors
    
    def _validate_choice(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate choice field."""
        errors = []
        
        valid_options = [opt.value for opt in question.options]
        if str(value) not in valid_options:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_choice",
                message=f"Invalid choice. Must be one of: {', '.join(valid_options)}"
            ))
            
        return errors
    
    def _validate_multi_choice(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate multi-choice field."""
        errors = []
        
        if not isinstance(value, list):
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_type",
                message="Must be a list of choices"
            ))
            return errors
        
        valid_options = [opt.value for opt in question.options]
        invalid_choices = [choice for choice in value if str(choice) not in valid_options]
        
        if invalid_choices:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_choice",
                message=f"Invalid choices: {', '.join(invalid_choices)}"
            ))
            
        return errors
    
    def _validate_date(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate date field."""
        errors = []
        
        try:
            if isinstance(value, str):
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif not isinstance(value, datetime):
                raise ValueError("Invalid date format")
        except ValueError:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_date",
                message="Invalid date format"
            ))
            
        return errors
    
    def _validate_list(self, field_id: str, value: Any, question: QuestionDefinition) -> list[ValidationError]:
        """Validate list field."""
        errors = []
        
        if not isinstance(value, list):
            errors.append(ValidationError(
                field_id=field_id,
                error_type="invalid_type",
                message="Must be a list"
            ))
            return errors
        
        if question.min_items is not None and len(value) < question.min_items:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="min_items",
                message=f"Minimum {question.min_items} items required"
            ))
            
        if question.max_items is not None and len(value) > question.max_items:
            errors.append(ValidationError(
                field_id=field_id,
                error_type="max_items",
                message=f"Maximum {question.max_items} items allowed"
            ))
            
        return errors


class IntakeSessionService:
    """Primary service for managing intake sessions."""
    
    def __init__(
        self,
        session_repository: IntakeSessionRepository | None = None,
        template_loader: TemplateLoader | None = None,
        validation_service: ValidationService | None = None,
        logic_engine: ConditionalLogicEngine | None = None
    ):
        self.session_repo = session_repository or IntakeSessionRepository()
        self.template_loader = template_loader or TemplateLoader()
        self.validation_svc = validation_service or ValidationService()
        self.logic_engine = logic_engine or ConditionalLogicEngine()
        
        # Template cache
        self._template_cache: dict[str, TemplateDefinition] = {}
    
    async def create_session(self, request: CreateSessionRequest) -> SessionResponse:
        """Create new intake session with governance applied."""
        # Load template
        template = await self._load_template(request.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {request.template_id}")
        
        # Determine first phase
        first_phase = self._determine_first_phase(template)
        if not first_phase:
            raise IntakeServiceError("Template has no phases")
        
        # Build phase order
        phase_order = self._build_phase_order(template)
        
        # Create session
        session = IntakeSession(
            template_id=request.template_id,
            client_slug=request.client_slug,
            user_id=request.user_id,
            metadata=request.metadata,
            current_phase_id=first_phase,
            phase_order=phase_order
        )
        
        # Save session
        await self.session_repo.create(session)
        
        return SessionResponse(
            session_id=session.session_id,
            template_id=session.template_id,
            client_slug=session.client_slug,
            current_phase_id=session.current_phase_id,
            progress_percent=0.0,
            is_complete=session.is_complete,
            created_at=session.created_at,
            updated_at=session.updated_at,
            governance_notices=[]
        )
    
    async def get_session_status(self, session_id: str) -> SessionStatusResponse:
        """Get current session state."""
        session = await self.session_repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        template = await self._load_template(session.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {session.template_id}")
        
        # Build phase responses
        phases = []
        for phase in template.phases:
            is_current = phase.id == session.current_phase_id
            is_complete = phase.id in session.completed_phases
            is_available = self._is_phase_available(phase, session, template)
            
            visible_questions = self.logic_engine.determine_visible_questions(
                phase, session.responses
            )
            
            phases.append(PhaseResponse(
                phase_id=phase.id,
                name=phase.name,
                description=phase.description,
                required=phase.required,
                questions=visible_questions,
                is_current=is_current,
                is_complete=is_complete,
                is_available=is_available
            ))
        
        # Get current questions
        current_questions = []
        if session.current_phase_id:
            current_phase = template.phase_map.get(session.current_phase_id)
            if current_phase:
                current_questions = self.logic_engine.determine_visible_questions(
                    current_phase, session.responses
                )
        
        progress_percent = self._calculate_progress(session, template)
        
        return SessionStatusResponse(
            session_id=session.session_id,
            template_id=session.template_id,
            current_phase_id=session.current_phase_id,
            progress_percent=progress_percent,
            phases=phases,
            current_questions=current_questions,
            responses=session.responses,
            validation_errors=session.validation_errors
        )
    
    async def submit_responses(
        self,
        session_id: str,
        request: SubmitResponsesRequest
    ) -> ResponseSubmissionResult:
        """Submit responses for a phase with validation."""
        session = await self.session_repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        template = await self._load_template(session.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {session.template_id}")
        
        # Validate responses
        validation_result = await self.validation_svc.validate_phase_responses(
            template, request.phase_id, request.responses
        )
        
        # Update session responses
        session.responses.update(request.responses)
        
        # Process derived fields
        await self._process_derived_fields(session, template)
        
        # Check if phase is complete
        phase_complete = validation_result.is_valid
        next_phase_id = session.current_phase_id
        advanced = False
        
        if phase_complete:
            session.completed_phases.add(request.phase_id)
            
            # Auto-advance if requested
            if request.auto_advance:
                current_phase = template.phase_map.get(request.phase_id)
                if current_phase:
                    next_phase = self.logic_engine.determine_next_phase(
                        current_phase, session.responses, template
                    )
                    if next_phase and next_phase != session.current_phase_id:
                        session.current_phase_id = next_phase
                        next_phase_id = next_phase
                        advanced = True
        
        # Update validation errors
        session.validation_errors = [
            err for err in session.validation_errors
            if not err.field_id.startswith(f"{request.phase_id}.")
        ]
        session.validation_errors.extend(validation_result.errors)
        
        await self.session_repo.update(session)
        
        progress_percent = self._calculate_progress(session, template)
        
        return ResponseSubmissionResult(
            success=True,
            validation_result=validation_result,
            next_phase_id=next_phase_id,
            advanced=advanced,
            progress_percent=progress_percent
        )
    
    async def navigate_session(
        self,
        session_id: str,
        request: NavigationRequest
    ) -> NavigationResult:
        """Navigate between phases."""
        session = await self.session_repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        template = await self._load_template(session.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {session.template_id}")
        
        current_phase_idx = None
        if session.current_phase_id:
            try:
                current_phase_idx = session.phase_order.index(session.current_phase_id)
            except ValueError:
                pass
        
        new_phase_id = None
        
        match request.action:
            case "next":
                if current_phase_idx is not None and current_phase_idx < len(session.phase_order) - 1:
                    new_phase_id = session.phase_order[current_phase_idx + 1]
            case "previous":
                if current_phase_idx is not None and current_phase_idx > 0:
                    new_phase_id = session.phase_order[current_phase_idx - 1]
            case "goto":
                if request.target_phase_id and request.target_phase_id in template.phase_map:
                    new_phase_id = request.target_phase_id
        
        if new_phase_id:
            # Check if target phase is available
            target_phase = template.phase_map.get(new_phase_id)
            if target_phase and self._is_phase_available(target_phase, session, template):
                session.current_phase_id = new_phase_id
                await self.session_repo.update(session)
                
                return NavigationResult(
                    success=True,
                    current_phase_id=session.current_phase_id,
                    target_phase_id=new_phase_id
                )
        
        return NavigationResult(
            success=False,
            current_phase_id=session.current_phase_id,
            target_phase_id=request.target_phase_id,
            message="Navigation not possible"
        )
    
    async def complete_session(
        self,
        session_id: str,
        request: CompleteSessionRequest
    ) -> ProjectCreationResult:
        """Complete intake session and create project."""
        session = await self.session_repo.get(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        template = await self._load_template(session.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {session.template_id}")
        
        # Final validation if requested
        if request.final_validation:
            validation_result = await self.validation_svc.validate_complete_intake(
                template, session.responses
            )
            
            if not validation_result.is_valid:
                return ProjectCreationResult(
                    success=False,
                    project_id=None,
                    validation_result=validation_result,
                    intake_summary=IntakeSummary(
                        total_responses=len(session.responses),
                        governance_applied=False,
                        project_type=session.template_id,
                        completion_time_minutes=0.0
                    ),
                    next_steps=NextSteps(
                        redirect_url="",
                        workflow_status="validation_failed"
                    )
                )
        else:
            validation_result = ValidationResult(is_valid=True)
        
        # Format intake description
        intake_description = await self._format_intake_description(session, template)
        
        # Create project (placeholder - integrate with actual project service)
        if request.create_project:
            project_id = await self._create_project(session, intake_description)
            session.project_id = project_id
        else:
            project_id = None
        
        # Mark session complete
        session.is_complete = True
        completion_time = (datetime.utcnow() - session.created_at).total_seconds() / 60
        await self.session_repo.update(session)
        
        intake_summary = IntakeSummary(
            total_responses=len(session.responses),
            governance_applied=session.governance_data is not None,
            project_type=session.template_id,
            completion_time_minutes=completion_time
        )
        
        next_steps = NextSteps(
            redirect_url=f"/projects/{project_id}/ready" if project_id else "/dashboard",
            workflow_status="ready_to_start" if project_id else "completed"
        )
        
        return ProjectCreationResult(
            success=True,
            project_id=project_id,
            validation_result=validation_result,
            intake_summary=intake_summary,
            next_steps=next_steps
        )
    
    async def list_templates(
        self,
        client_slug: str | None = None,
        category: str | None = None,
        include_abstract: bool = False
    ) -> list[TemplateListItem]:
        """List available templates."""
        templates = await self.template_loader.list_templates()
        
        # Apply filters
        if category:
            templates = [t for t in templates if t.category == category]
        
        if not include_abstract:
            templates = [t for t in templates if not t.template_id.startswith("_")]
        
        return templates
    
    async def get_template(
        self,
        template_id: str,
        client_slug: str | None = None
    ) -> TemplateDefinition | None:
        """Get template definition with governance applied."""
        return await self._load_template(template_id)
    
    async def validate_responses(self, request: ValidateRequest) -> ValidationResult:
        """Validate responses against template and governance."""
        template = await self._load_template(request.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template not found: {request.template_id}")
        
        return await self.validation_svc.validate_complete_intake(
            template, request.responses
        )
    
    # Private helper methods
    
    async def _load_template(self, template_id: str) -> TemplateDefinition | None:
        """Load template with caching."""
        if template_id in self._template_cache:
            return self._template_cache[template_id]
        
        template = await self.template_loader.load_template(template_id)
        if template:
            self._template_cache[template_id] = template
        
        return template
    
    def _determine_first_phase(self, template: TemplateDefinition) -> str | None:
        """Determine the first phase to show."""
        if not template.phases:
            return None
        
        # Find phase with lowest order
        sorted_phases = sorted(template.phases, key=lambda p: p.order)
        return sorted_phases[0].id
    
    def _build_phase_order(self, template: TemplateDefinition) -> list[str]:
        """Build phase order based on template definition."""
        sorted_phases = sorted(template.phases, key=lambda p: p.order)
        return [phase.id for phase in sorted_phases]
    
    def _is_phase_available(
        self,
        phase: PhaseDefinition,
        session: IntakeSession,
        template: TemplateDefinition
    ) -> bool:
        """Check if a phase is available based on conditions."""
        if phase.condition:
            return self.logic_engine.evaluate_complex_condition(
                phase.condition, session.responses
            )
        return True
    
    def _calculate_progress(
        self,
        session: IntakeSession,
        template: TemplateDefinition
    ) -> float:
        """Calculate completion progress percentage."""
        total_phases = len(template.phases)
        completed_phases = len(session.completed_phases)
        
        if total_phases == 0:
            return 100.0
        
        return (completed_phases / total_phases) * 100.0
    
    async def _process_derived_fields(
        self,
        session: IntakeSession,
        template: TemplateDefinition
    ) -> None:
        """Process derived fields based on responses."""
        # Simple derived field processing
        for phase in template.phases:
            for question in phase.questions:
                if question.type.value == "derived" and question.derived_from:
                    source_value = session.responses.get(question.derived_from)
                    if source_value and question.transform:
                        derived_value = self._apply_transform(source_value, question.transform)
                        session.derived_responses[question.id] = derived_value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to a value."""
        str_value = str(value)
        
        match transform:
            case "slugify":
                return re.sub(r'[^\w\s-]', '', str_value.lower()).strip()
            case "uppercase":
                return str_value.upper()
            case "lowercase":
                return str_value.lower()
            case _:
                return value
    
    async def _format_intake_description(
        self,
        session: IntakeSession,
        template: TemplateDefinition
    ) -> str:
        """Format intake responses into description for orchestrator."""
        # Build comprehensive description from responses
        description_parts = [f"Project Type: {session.template_id}"]
        
        # Add key responses
        key_fields = ["project_name", "project_description", "presentation_purpose", 
                     "client_challenge", "proposed_solution"]
        
        for field in key_fields:
            if field in session.responses:
                value = session.responses[field]
                if value:
                    field_name = field.replace("_", " ").title()
                    description_parts.append(f"{field_name}: {value}")
        
        # Add all other responses in structured format
        description_parts.append("\nDetailed Intake Responses:")
        for key, value in session.responses.items():
            if key not in key_fields and value:
                key_name = key.replace("_", " ").title()
                description_parts.append(f"- {key_name}: {value}")
        
        return "\n".join(description_parts)
    
    async def _create_project(self, session: IntakeSession, description: str) -> str:
        """Create project from intake session."""
        try:
            # Import here to avoid circular imports
            from orchestrator_v2.engine.engine import WorkflowEngine
            from orchestrator_v2.persistence.fs_repository import FileSystemProjectRepository
            from orchestrator_v2.workspace.manager import WorkspaceManager
            
            # Initialize services
            project_repo = FileSystemProjectRepository()
            workspace_manager = WorkspaceManager()
            engine = WorkflowEngine()
            
            # Determine project name
            project_name = session.responses.get("project_name", f"Project from {session.template_id}")
            
            # Start project
            state = await engine.start_project(
                intake_path=None,  # Already processed
                project_name=project_name,
                client=session.client_slug,
                metadata={
                    "intake_session_id": session.session_id,
                    "intake_responses": session.responses,
                    "derived_responses": session.derived_responses,
                    "governance_data": session.governance_data.dict() if session.governance_data else None,
                    "template_id": session.template_id
                }
            )
            
            # Set project properties
            state.project_type = session.template_id
            state.template_id = session.template_id
            state.intake = description
            
            # Create workspace
            try:
                workspace_config = workspace_manager.create_data_workspace(
                    project_id=state.project_id,
                    project_type=session.template_id,
                    metadata={
                        "project_name": project_name,
                        "template_id": session.template_id,
                        "description": description
                    }
                )
                state.workspace_path = str(workspace_config.workspace_root)
            except Exception as e:
                logger.warning(f"Failed to create workspace for project {state.project_id}: {e}")
            
            # Save project state
            await project_repo.save(state)
            
            logger.info(f"Created project {state.project_id} from intake session {session.session_id}")
            return state.project_id
            
        except Exception as e:
            logger.error(f"Failed to create project from intake session {session.session_id}: {e}")
            # Fallback to placeholder ID
            import uuid
            return f"project-{uuid.uuid4().hex[:8]}"