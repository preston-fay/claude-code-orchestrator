"""
Unit Tests for Intake Template System Service Layer.

Tests the business logic for managing intake sessions, loading templates,
conditional logic evaluation, and validation.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from pydantic import ValidationError

from orchestrator_v2.models.intake import (
    ConditionDefinition,
    ConditionOperator,
    CompleteSessionRequest,
    CreateSessionRequest,
    IntakeSession,
    NavigationRequest,
    PhaseDefinition,
    QuestionDefinition,
    QuestionType,
    SubmitResponsesRequest,
    TemplateDefinition,
    TemplateMetadata,
    ValidateRequest,
    ValidationError as IntakeValidationError,
    ValidationRules,
)
from orchestrator_v2.services.intake_service import (
    ConditionalLogicEngine,
    IntakeSessionRepository,
    IntakeSessionService,
    IntakeServiceError,
    SessionNotFoundError,
    TemplateLoader,
    TemplateNotFoundError,
    ValidationService,
    ValidationServiceError,
)


class TestIntakeSessionRepository:
    """Test the intake session repository."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def repository(self, temp_storage):
        """Create repository instance."""
        return IntakeSessionRepository(storage_path=temp_storage)
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample intake session."""
        return IntakeSession(
            session_id="test-session-123",
            user_id="test-user",
            template_id="general",
            client_slug="test-client",
            current_phase_id="phase1",
            responses={"field1": "value1"},
            completed_phases={"phase0"}
        )
    
    async def test_create_session(self, repository, sample_session):
        """Test creating a new session."""
        session_id = await repository.create(sample_session)
        assert session_id == sample_session.session_id
        
        # Verify file was created
        session_file = Path(repository.storage_path) / f"{session_id}.json"
        assert session_file.exists()
        
        # Verify content
        with open(session_file) as f:
            data = json.load(f)
        assert data["session_id"] == session_id
        assert data["template_id"] == "general"
        assert isinstance(data["completed_phases"], list)
    
    async def test_get_session(self, repository, sample_session):
        """Test retrieving a session."""
        # Create session
        await repository.create(sample_session)
        
        # Retrieve session
        retrieved = await repository.get(sample_session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == sample_session.session_id
        assert retrieved.template_id == sample_session.template_id
        assert retrieved.responses == sample_session.responses
        assert retrieved.completed_phases == sample_session.completed_phases
    
    async def test_get_nonexistent_session(self, repository):
        """Test retrieving a non-existent session."""
        result = await repository.get("nonexistent")
        assert result is None
    
    async def test_update_session(self, repository, sample_session):
        """Test updating an existing session."""
        # Create session
        await repository.create(sample_session)
        original_updated_at = sample_session.updated_at
        
        # Update responses
        sample_session.responses["field2"] = "value2"
        await repository.update(sample_session)
        
        # Verify update
        updated = await repository.get(sample_session.session_id)
        assert updated.responses["field2"] == "value2"
        assert updated.updated_at > original_updated_at
        assert updated.last_activity > original_updated_at
    
    async def test_delete_session(self, repository, sample_session):
        """Test deleting a session."""
        # Create session
        await repository.create(sample_session)
        assert await repository.get(sample_session.session_id) is not None
        
        # Delete session
        deleted = await repository.delete(sample_session.session_id)
        assert deleted is True
        
        # Verify deletion
        assert await repository.get(sample_session.session_id) is None
    
    async def test_delete_nonexistent_session(self, repository):
        """Test deleting a non-existent session."""
        result = await repository.delete("nonexistent")
        assert result is False
    
    async def test_list_by_user(self, repository):
        """Test listing sessions by user."""
        # Create sessions for different users
        session1 = IntakeSession(template_id="general", user_id="user1")
        session2 = IntakeSession(template_id="general", user_id="user2")
        session3 = IntakeSession(template_id="general", user_id="user1")
        
        await repository.create(session1)
        await repository.create(session2)
        await repository.create(session3)
        
        # List sessions for user1
        user1_sessions = await repository.list_by_user("user1")
        assert len(user1_sessions) == 2
        assert all(s.user_id == "user1" for s in user1_sessions)
        
        # List sessions for user2
        user2_sessions = await repository.list_by_user("user2")
        assert len(user2_sessions) == 1
        assert user2_sessions[0].user_id == "user2"
        
        # List sessions for non-existent user
        empty_sessions = await repository.list_by_user("user3")
        assert len(empty_sessions) == 0


class TestTemplateLoader:
    """Test the template loader."""
    
    @pytest.fixture
    def temp_templates(self):
        """Create temporary templates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample templates
            general_template = {
                "template": {
                    "id": "general",
                    "name": "General Project",
                    "description": "A general project template",
                    "version": "1.0.0",
                    "category": "general",
                    "estimated_time_minutes": 15
                },
                "phases": [
                    {
                        "id": "phase1",
                        "name": "Phase 1",
                        "description": "First phase",
                        "order": 1,
                        "questions": [
                            {
                                "id": "question1",
                                "question": "What is your name?",
                                "type": "text",
                                "required": True,
                                "properties": {
                                    "prop1": {
                                        "type": "text",
                                        "required": True
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
            
            with open(f"{temp_dir}/general.yaml", "w") as f:
                yaml.dump(general_template, f)
            
            # Create an abstract template (starts with _)
            abstract_template = {
                "template": {
                    "id": "_base",
                    "name": "Base Template"
                }
            }
            with open(f"{temp_dir}/_base.yaml", "w") as f:
                yaml.dump(abstract_template, f)
            
            # Create invalid template
            with open(f"{temp_dir}/invalid.yaml", "w") as f:
                f.write("invalid: yaml: content:")
            
            yield temp_dir
    
    @pytest.fixture
    def loader(self, temp_templates):
        """Create template loader instance."""
        return TemplateLoader(templates_path=temp_templates)
    
    async def test_load_template(self, loader):
        """Test loading a valid template."""
        template = await loader.load_template("general")
        assert template is not None
        assert template.template.id == "general"
        assert template.template.name == "General Project"
        assert len(template.phases) == 1
        assert template.phases[0].id == "phase1"
        assert len(template.phases[0].questions) == 1
        
        # Check that property IDs were added
        question = template.phases[0].questions[0]
        assert "prop1" in question.properties
        assert question.properties["prop1"].get("id") == "prop1"
    
    async def test_load_nonexistent_template(self, loader):
        """Test loading a non-existent template."""
        template = await loader.load_template("nonexistent")
        assert template is None
    
    async def test_load_invalid_template(self, loader):
        """Test loading an invalid template."""
        template = await loader.load_template("invalid")
        assert template is None
    
    async def test_list_templates(self, loader):
        """Test listing available templates."""
        templates = await loader.list_templates()
        assert len(templates) == 1  # Only general, not _base (abstract)
        assert templates[0].template_id == "general"
        assert templates[0].name == "General Project"
        assert templates[0].question_count == 1
        assert templates[0].phase_count == 1


class TestConditionalLogicEngine:
    """Test the conditional logic engine."""
    
    @pytest.fixture
    def engine(self):
        """Create conditional logic engine instance."""
        return ConditionalLogicEngine()
    
    @pytest.fixture
    def sample_responses(self):
        """Sample responses for testing."""
        return {
            "name": "John Doe",
            "age": 30,
            "skills": ["python", "javascript"],
            "active": True,
            "score": 85.5,
            "empty_field": "",
            "null_field": None
        }
    
    def test_evaluate_equals_condition(self, engine, sample_responses):
        """Test EQUALS condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.EQUALS,
            value="John Doe"
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = "Jane Doe"
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_not_equals_condition(self, engine, sample_responses):
        """Test NOT_EQUALS condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.NOT_EQUALS,
            value="Jane Doe"
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = "John Doe"
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_in_condition(self, engine, sample_responses):
        """Test IN condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.IN,
            value=["John Doe", "Jane Smith"]
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = ["Jane Doe", "Bob Smith"]
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_contains_condition(self, engine, sample_responses):
        """Test CONTAINS condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.CONTAINS,
            value="John"
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = "Jane"
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_greater_than_condition(self, engine, sample_responses):
        """Test GREATER_THAN condition evaluation."""
        condition = ConditionDefinition(
            field="age",
            operator=ConditionOperator.GREATER_THAN,
            value=25
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = 35
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_is_set_condition(self, engine, sample_responses):
        """Test IS_SET condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.IS_SET,
            value=None
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.field = "empty_field"
        assert engine.evaluate_condition(condition, sample_responses) is False
        
        condition.field = "null_field"
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_regex_match_condition(self, engine, sample_responses):
        """Test REGEX_MATCH condition evaluation."""
        condition = ConditionDefinition(
            field="name",
            operator=ConditionOperator.REGEX_MATCH,
            value=r"^John.*"
        )
        assert engine.evaluate_condition(condition, sample_responses) is True
        
        condition.value = r"^Jane.*"
        assert engine.evaluate_condition(condition, sample_responses) is False
    
    def test_evaluate_complex_and_condition(self, engine, sample_responses):
        """Test complex AND condition evaluation."""
        condition = ConditionDefinition(
            field="age",
            operator=ConditionOperator.GREATER_THAN,
            value=25,
            and_conditions=[
                ConditionDefinition(
                    field="name",
                    operator=ConditionOperator.CONTAINS,
                    value="John"
                )
            ]
        )
        assert engine.evaluate_complex_condition(condition, sample_responses) is True
        
        # Change AND condition to fail
        condition.and_conditions[0].value = "Jane"
        assert engine.evaluate_complex_condition(condition, sample_responses) is False
    
    def test_evaluate_complex_or_condition(self, engine, sample_responses):
        """Test complex OR condition evaluation."""
        condition = ConditionDefinition(
            field="age",
            operator=ConditionOperator.LESS_THAN,
            value=25,  # This will be False
            or_conditions=[
                ConditionDefinition(
                    field="name",
                    operator=ConditionOperator.CONTAINS,
                    value="John"  # This will be True
                )
            ]
        )
        assert engine.evaluate_complex_condition(condition, sample_responses) is True
        
        # Change OR condition to also fail
        condition.or_conditions[0].value = "Jane"
        assert engine.evaluate_complex_condition(condition, sample_responses) is False
    
    def test_determine_visible_questions(self, engine):
        """Test determining visible questions based on conditions."""
        responses = {"show_advanced": True}
        
        phase = PhaseDefinition(
            id="test_phase",
            name="Test Phase",
            questions=[
                QuestionDefinition(
                    id="basic_question",
                    question="Basic question",
                    type=QuestionType.TEXT
                ),
                QuestionDefinition(
                    id="advanced_question",
                    question="Advanced question",
                    type=QuestionType.TEXT,
                    condition=ConditionDefinition(
                        field="show_advanced",
                        operator=ConditionOperator.EQUALS,
                        value=True
                    )
                ),
                QuestionDefinition(
                    id="hidden_question",
                    question="Hidden question",
                    type=QuestionType.TEXT,
                    hidden=True
                )
            ]
        )
        
        visible = engine.determine_visible_questions(phase, responses)
        assert len(visible) == 2  # basic + advanced, not hidden
        assert visible[0].id == "basic_question"
        assert visible[1].id == "advanced_question"
        
        # Change response to hide advanced question
        responses["show_advanced"] = False
        visible = engine.determine_visible_questions(phase, responses)
        assert len(visible) == 1
        assert visible[0].id == "basic_question"


class TestValidationService:
    """Test the validation service."""
    
    @pytest.fixture
    def service(self):
        """Create validation service instance."""
        return ValidationService()
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template for validation."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="test",
                name="Test Template",
                description="A test template"
            ),
            phases=[
                PhaseDefinition(
                    id="phase1",
                    name="Phase 1",
                    questions=[
                        QuestionDefinition(
                            id="name",
                            question="Your name",
                            type=QuestionType.TEXT,
                            required=True,
                            validation=ValidationRules(
                                min_length=2,
                                max_length=50
                            )
                        ),
                        QuestionDefinition(
                            id="age",
                            question="Your age",
                            type=QuestionType.NUMBER,
                            required=True,
                            min_value=0,
                            max_value=120
                        ),
                        QuestionDefinition(
                            id="skills",
                            question="Your skills",
                            type=QuestionType.MULTI_CHOICE,
                            required=False,
                            options=[
                                {"value": "python", "label": "Python"},
                                {"value": "javascript", "label": "JavaScript"}
                            ]
                        )
                    ]
                )
            ]
        )
    
    async def test_validate_required_field_missing(self, service, sample_template):
        """Test validation fails for missing required field."""
        responses = {"age": 25}  # Missing required 'name'
        
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].field_id == "name"
        assert result.errors[0].error_type == "required"
    
    async def test_validate_text_length(self, service, sample_template):
        """Test text length validation."""
        # Test too short
        responses = {"name": "A", "age": 25}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "min_length" for e in result.errors)
        
        # Test too long
        responses = {"name": "A" * 60, "age": 25}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "max_length" for e in result.errors)
        
        # Test valid length
        responses = {"name": "John Doe", "age": 25}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert result.is_valid
    
    async def test_validate_number_range(self, service, sample_template):
        """Test number range validation."""
        # Test too low
        responses = {"name": "John", "age": -5}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "min_value" for e in result.errors)
        
        # Test too high
        responses = {"name": "John", "age": 150}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "max_value" for e in result.errors)
        
        # Test invalid type
        responses = {"name": "John", "age": "not a number"}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_type" for e in result.errors)
    
    async def test_validate_choice_options(self, service, sample_template):
        """Test choice validation."""
        # Valid choices
        responses = {"name": "John", "age": 25, "skills": ["python"]}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert result.is_valid
        
        # Invalid choice
        responses = {"name": "John", "age": 25, "skills": ["ruby"]}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_choice" for e in result.errors)
        
        # Wrong type (not list)
        responses = {"name": "John", "age": 25, "skills": "python"}
        result = await service.validate_phase_responses(
            sample_template, "phase1", responses
        )
        assert not result.is_valid
        assert any(e.error_type == "invalid_type" for e in result.errors)
    
    async def test_validate_complete_intake(self, service, sample_template):
        """Test validating complete intake."""
        responses = {"name": "John Doe", "age": 30}
        
        result = await service.validate_complete_intake(
            sample_template, responses
        )
        assert result.is_valid
        assert len(result.errors) == 0
    
    async def test_validate_unknown_phase(self, service, sample_template):
        """Test validation fails for unknown phase."""
        responses = {"name": "John"}
        
        result = await service.validate_phase_responses(
            sample_template, "unknown_phase", responses
        )
        assert not result.is_valid
        assert result.errors[0].error_type == "phase_not_found"


class TestIntakeSessionService:
    """Test the main intake session service."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        session_repo = AsyncMock(spec=IntakeSessionRepository)
        template_loader = AsyncMock(spec=TemplateLoader)
        validation_service = AsyncMock(spec=ValidationService)
        logic_engine = MagicMock(spec=ConditionalLogicEngine)
        return {
            "session_repo": session_repo,
            "template_loader": template_loader,
            "validation_service": validation_service,
            "logic_engine": logic_engine
        }
    
    @pytest.fixture
    def service(self, mock_dependencies):
        """Create service instance with mocked dependencies."""
        return IntakeSessionService(**mock_dependencies)
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="general",
                name="General Template",
                description="A general template"
            ),
            phases=[
                PhaseDefinition(
                    id="phase1",
                    name="Phase 1",
                    order=1,
                    questions=[
                        QuestionDefinition(
                            id="question1",
                            question="Test question",
                            type=QuestionType.TEXT
                        )
                    ]
                ),
                PhaseDefinition(
                    id="phase2",
                    name="Phase 2",
                    order=2,
                    questions=[]
                )
            ]
        )
    
    async def test_create_session_success(self, service, mock_dependencies, sample_template):
        """Test successful session creation."""
        # Setup mocks
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["session_repo"].create.return_value = "session-123"
        
        request = CreateSessionRequest(
            template_id="general",
            client_slug="test-client",
            user_id="test-user"
        )
        
        result = await service.create_session(request)
        
        assert result.session_id is not None
        assert result.template_id == "general"
        assert result.client_slug == "test-client"
        assert result.current_phase_id == "phase1"  # First phase
        assert result.progress_percent == 0.0
        assert not result.is_complete
        
        # Verify dependencies were called
        mock_dependencies["template_loader"].load_template.assert_called_once_with("general")
        mock_dependencies["session_repo"].create.assert_called_once()
    
    async def test_create_session_template_not_found(self, service, mock_dependencies):
        """Test session creation with non-existent template."""
        mock_dependencies["template_loader"].load_template.return_value = None
        
        request = CreateSessionRequest(template_id="nonexistent")
        
        with pytest.raises(TemplateNotFoundError):
            await service.create_session(request)
    
    async def test_create_session_no_phases(self, service, mock_dependencies):
        """Test session creation with template having no phases."""
        empty_template = TemplateDefinition(
            template=TemplateMetadata(
                id="empty",
                name="Empty Template",
                description="No phases"
            ),
            phases=[]
        )
        mock_dependencies["template_loader"].load_template.return_value = empty_template
        
        request = CreateSessionRequest(template_id="empty")
        
        with pytest.raises(IntakeServiceError, match="Template has no phases"):
            await service.create_session(request)
    
    async def test_get_session_status_success(self, service, mock_dependencies, sample_template):
        """Test getting session status."""
        # Create sample session
        session = IntakeSession(
            session_id="session-123",
            template_id="general",
            current_phase_id="phase1",
            responses={"question1": "answer1"},
            completed_phases=set()
        )
        
        # Setup mocks
        mock_dependencies["session_repo"].get.return_value = session
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["logic_engine"].determine_visible_questions.return_value = sample_template.phases[0].questions
        
        result = await service.get_session_status("session-123")
        
        assert result.session_id == "session-123"
        assert result.template_id == "general"
        assert result.current_phase_id == "phase1"
        assert len(result.phases) == 2
        assert len(result.current_questions) == 1
        assert result.responses == {"question1": "answer1"}
    
    async def test_get_session_status_not_found(self, service, mock_dependencies):
        """Test getting status for non-existent session."""
        mock_dependencies["session_repo"].get.return_value = None
        
        with pytest.raises(SessionNotFoundError):
            await service.get_session_status("nonexistent")
    
    async def test_submit_responses_success(self, service, mock_dependencies, sample_template):
        """Test successful response submission."""
        from orchestrator_v2.models.intake import ValidationResult
        
        # Create sample session
        session = IntakeSession(
            session_id="session-123",
            template_id="general",
            current_phase_id="phase1",
            responses={},
            completed_phases=set()
        )
        
        # Setup mocks
        mock_dependencies["session_repo"].get.return_value = session
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["validation_service"].validate_phase_responses.return_value = ValidationResult(is_valid=True)
        mock_dependencies["session_repo"].update.return_value = None
        
        request = SubmitResponsesRequest(
            phase_id="phase1",
            responses={"question1": "answer1"},
            auto_advance=False
        )
        
        result = await service.submit_responses("session-123", request)
        
        assert result.success
        assert result.validation_result.is_valid
        assert not result.advanced  # auto_advance was False
        
        # Verify session was updated
        mock_dependencies["session_repo"].update.assert_called_once()
    
    async def test_navigate_session_next(self, service, mock_dependencies, sample_template):
        """Test navigating to next phase."""
        session = IntakeSession(
            session_id="session-123",
            template_id="general",
            current_phase_id="phase1",
            phase_order=["phase1", "phase2"]
        )
        
        # Setup mocks
        mock_dependencies["session_repo"].get.return_value = session
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["session_repo"].update.return_value = None
        
        request = NavigationRequest(action="next")
        
        result = await service.navigate_session("session-123", request)
        
        assert result.success
        assert result.current_phase_id == "phase2"
        mock_dependencies["session_repo"].update.assert_called_once()
    
    async def test_navigate_session_goto(self, service, mock_dependencies, sample_template):
        """Test direct navigation to specific phase."""
        session = IntakeSession(
            session_id="session-123",
            template_id="general",
            current_phase_id="phase1"
        )
        
        # Setup mocks
        mock_dependencies["session_repo"].get.return_value = session
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["session_repo"].update.return_value = None
        
        request = NavigationRequest(action="goto", target_phase_id="phase2")
        
        result = await service.navigate_session("session-123", request)
        
        assert result.success
        assert result.current_phase_id == "phase2"
        assert result.target_phase_id == "phase2"
    
    async def test_complete_session_success(self, service, mock_dependencies, sample_template):
        """Test successful session completion."""
        from orchestrator_v2.models.intake import ValidationResult
        
        session = IntakeSession(
            session_id="session-123",
            template_id="general",
            responses={"question1": "answer1"}
        )
        
        # Setup mocks
        mock_dependencies["session_repo"].get.return_value = session
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["validation_service"].validate_complete_intake.return_value = ValidationResult(is_valid=True)
        mock_dependencies["session_repo"].update.return_value = None
        
        with patch.object(service, '_create_project', return_value="project-123"):
            request = CompleteSessionRequest(final_validation=True, create_project=True)
            result = await service.complete_session("session-123", request)
        
        assert result.success
        assert result.project_id == "project-123"
        assert result.validation_result.is_valid
        assert result.intake_summary.project_type == "general"
        
        # Verify session was marked complete
        mock_dependencies["session_repo"].update.assert_called_once()
    
    async def test_validate_responses(self, service, mock_dependencies, sample_template):
        """Test response validation endpoint."""
        from orchestrator_v2.models.intake import ValidationResult
        
        # Setup mocks
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        mock_dependencies["validation_service"].validate_complete_intake.return_value = ValidationResult(is_valid=True)
        
        request = ValidateRequest(
            template_id="general",
            responses={"question1": "answer1"}
        )
        
        result = await service.validate_responses(request)
        
        assert result.is_valid
        mock_dependencies["validation_service"].validate_complete_intake.assert_called_once()
    
    async def test_list_templates(self, service, mock_dependencies):
        """Test listing available templates."""
        from orchestrator_v2.models.intake import TemplateListItem
        
        templates = [
            TemplateListItem(
                template_id="general",
                name="General",
                description="General template",
                category="general",
                estimated_time_minutes=15,
                question_count=5,
                phase_count=2
            )
        ]
        
        mock_dependencies["template_loader"].list_templates.return_value = templates
        
        result = await service.list_templates()
        
        assert len(result) == 1
        assert result[0].template_id == "general"
    
    async def test_get_template(self, service, mock_dependencies, sample_template):
        """Test getting template definition."""
        mock_dependencies["template_loader"].load_template.return_value = sample_template
        
        result = await service.get_template("general")
        
        assert result is not None
        assert result.template.id == "general"
        mock_dependencies["template_loader"].load_template.assert_called_once_with("general")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])