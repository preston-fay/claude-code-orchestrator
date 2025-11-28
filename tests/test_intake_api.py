"""
Integration Tests for Intake Template System API Endpoints.

Tests the REST API endpoints for the intake template system,
covering session management, template operations, and error handling.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from fastapi.testclient import TestClient
from fastapi import FastAPI

from orchestrator_v2.api.routes.intake import router
from orchestrator_v2.models.intake import (
    CompleteSessionRequest,
    CreateSessionRequest,
    IntakeSession,
    NavigationRequest,
    PhaseDefinition,
    QuestionDefinition,
    QuestionType,
    SubmitResponsesRequest,
    TemplateDefinition,
    TemplateListItem,
    TemplateMetadata,
    ValidateRequest,
    ValidationResult,
)
from orchestrator_v2.services.intake_service import (
    IntakeSessionService,
    SessionNotFoundError,
    TemplateNotFoundError,
)


class TestIntakeAPI:
    """Test the intake API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI application with intake routes."""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_template(self):
        """Create a sample template definition."""
        return TemplateDefinition(
            template=TemplateMetadata(
                id="test-template",
                name="Test Template",
                description="A template for testing",
                version="1.0.0",
                category="test",
                estimated_time_minutes=10
            ),
            phases=[
                PhaseDefinition(
                    id="phase1",
                    name="Test Phase",
                    description="First phase",
                    order=1,
                    required=True,
                    questions=[
                        QuestionDefinition(
                            id="name",
                            question="What is your name?",
                            type=QuestionType.TEXT,
                            required=True
                        ),
                        QuestionDefinition(
                            id="age",
                            question="What is your age?",
                            type=QuestionType.NUMBER,
                            required=False,
                            min_value=0,
                            max_value=150
                        )
                    ]
                )
            ]
        )
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample session."""
        return IntakeSession(
            session_id="test-session-123",
            template_id="test-template",
            client_slug="test-client",
            user_id="test-user",
            current_phase_id="phase1",
            responses={},
            completed_phases=set()
        )


class TestSessionManagementEndpoints:
    """Test session management API endpoints."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock intake service."""
        return AsyncMock(spec=IntakeSessionService)
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_create_session_success(self, mock_get_service, client, sample_template, mock_service):
        """Test successful session creation."""
        from orchestrator_v2.models.intake import SessionResponse
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.create_session.return_value = SessionResponse(
            session_id="session-123",
            template_id="test-template",
            client_slug="test-client",
            current_phase_id="phase1",
            progress_percent=0.0,
            is_complete=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            governance_notices=[]
        )
        
        # Make request
        request_data = {
            "template_id": "test-template",
            "client_slug": "test-client",
            "user_id": "test-user"
        }
        response = client.post("/api/intake/sessions", json=request_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "session-123"
        assert data["template_id"] == "test-template"
        assert data["client_slug"] == "test-client"
        assert data["progress_percent"] == 0.0
        assert data["is_complete"] is False
        
        # Verify service was called
        mock_service.create_session.assert_called_once()
        call_args = mock_service.create_session.call_args[0][0]
        assert call_args.template_id == "test-template"
        assert call_args.client_slug == "test-client"
        assert call_args.user_id == "test-user"
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_create_session_template_not_found(self, mock_get_service, client, mock_service):
        """Test session creation with non-existent template."""
        # Setup mock to raise error
        mock_get_service.return_value = mock_service
        mock_service.create_session.side_effect = TemplateNotFoundError("Template not found: nonexistent")
        
        # Make request
        request_data = {
            "template_id": "nonexistent",
            "client_slug": "test-client"
        }
        response = client.post("/api/intake/sessions", json=request_data)
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_get_session_status_success(self, mock_get_service, client, sample_session, sample_template, mock_service):
        """Test getting session status."""
        from orchestrator_v2.models.intake import SessionStatusResponse, PhaseResponse
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.get_session_status.return_value = SessionStatusResponse(
            session_id="test-session-123",
            template_id="test-template",
            current_phase_id="phase1",
            progress_percent=25.0,
            phases=[
                PhaseResponse(
                    phase_id="phase1",
                    name="Test Phase",
                    description="First phase",
                    required=True,
                    questions=sample_template.phases[0].questions,
                    is_current=True,
                    is_complete=False,
                    is_available=True
                )
            ],
            current_questions=sample_template.phases[0].questions,
            responses={},
            validation_errors=[]
        )
        
        # Make request
        response = client.get("/api/intake/sessions/test-session-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["template_id"] == "test-template"
        assert data["current_phase_id"] == "phase1"
        assert data["progress_percent"] == 25.0
        assert len(data["phases"]) == 1
        assert len(data["current_questions"]) == 2
        
        # Verify service was called
        mock_service.get_session_status.assert_called_once_with("test-session-123")
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_get_session_status_not_found(self, mock_get_service, client, mock_service):
        """Test getting status for non-existent session."""
        # Setup mock to raise error
        mock_get_service.return_value = mock_service
        mock_service.get_session_status.side_effect = SessionNotFoundError("Session not found: nonexistent")
        
        # Make request
        response = client.get("/api/intake/sessions/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_submit_responses_success(self, mock_get_service, client, mock_service):
        """Test successful response submission."""
        from orchestrator_v2.models.intake import ResponseSubmissionResult, ValidationResult
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.submit_responses.return_value = ResponseSubmissionResult(
            success=True,
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            next_phase_id="phase1",
            advanced=False,
            progress_percent=50.0
        )
        
        # Make request
        request_data = {
            "phase_id": "phase1",
            "responses": {
                "name": "John Doe",
                "age": 30
            },
            "auto_advance": False
        }
        response = client.put("/api/intake/sessions/test-session-123/responses", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["validation_result"]["is_valid"] is True
        assert data["next_phase_id"] == "phase1"
        assert data["advanced"] is False
        assert data["progress_percent"] == 50.0
        
        # Verify service was called
        mock_service.submit_responses.assert_called_once()
        call_args = mock_service.submit_responses.call_args[0]
        assert call_args[0] == "test-session-123"
        assert call_args[1].phase_id == "phase1"
        assert call_args[1].responses == {"name": "John Doe", "age": 30}
        assert call_args[1].auto_advance is False
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_submit_responses_with_validation_errors(self, mock_get_service, client, mock_service):
        """Test response submission with validation errors."""
        from orchestrator_v2.models.intake import ResponseSubmissionResult, ValidationResult, ValidationError
        
        # Setup mock with validation errors
        mock_get_service.return_value = mock_service
        mock_service.submit_responses.return_value = ResponseSubmissionResult(
            success=False,
            validation_result=ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        field_id="name",
                        error_type="required",
                        message="Name is required"
                    )
                ],
                warnings=[]
            ),
            next_phase_id="phase1",
            advanced=False,
            progress_percent=0.0
        )
        
        # Make request with missing required field
        request_data = {
            "phase_id": "phase1",
            "responses": {
                "age": 30
            }
        }
        response = client.put("/api/intake/sessions/test-session-123/responses", json=request_data)
        
        # Verify response
        assert response.status_code == 200  # Still 200, but with validation errors
        data = response.json()
        assert data["success"] is False
        assert data["validation_result"]["is_valid"] is False
        assert len(data["validation_result"]["errors"]) == 1
        assert data["validation_result"]["errors"][0]["field_id"] == "name"
        assert data["validation_result"]["errors"][0]["error_type"] == "required"
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_navigate_session_success(self, mock_get_service, client, mock_service):
        """Test successful session navigation."""
        from orchestrator_v2.models.intake import NavigationResult
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.navigate_session.return_value = NavigationResult(
            success=True,
            current_phase_id="phase2",
            target_phase_id="phase2",
            message=None
        )
        
        # Make request
        request_data = {
            "action": "next"
        }
        response = client.post("/api/intake/sessions/test-session-123/navigate", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["current_phase_id"] == "phase2"
        assert data["target_phase_id"] == "phase2"
        
        # Verify service was called
        mock_service.navigate_session.assert_called_once()
        call_args = mock_service.navigate_session.call_args[0]
        assert call_args[0] == "test-session-123"
        assert call_args[1].action == "next"
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_navigate_session_goto(self, mock_get_service, client, mock_service):
        """Test direct navigation to specific phase."""
        from orchestrator_v2.models.intake import NavigationResult
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.navigate_session.return_value = NavigationResult(
            success=True,
            current_phase_id="phase3",
            target_phase_id="phase3",
            message=None
        )
        
        # Make request
        request_data = {
            "action": "goto",
            "target_phase_id": "phase3"
        }
        response = client.post("/api/intake/sessions/test-session-123/navigate", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["current_phase_id"] == "phase3"
        assert data["target_phase_id"] == "phase3"
        
        # Verify navigation request
        call_args = mock_service.navigate_session.call_args[0]
        assert call_args[1].action == "goto"
        assert call_args[1].target_phase_id == "phase3"
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_complete_session_success(self, mock_get_service, client, mock_service):
        """Test successful session completion."""
        from orchestrator_v2.models.intake import (
            ProjectCreationResult,
            ValidationResult,
            IntakeSummary,
            NextSteps
        )
        
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.complete_session.return_value = ProjectCreationResult(
            success=True,
            project_id="project-123",
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            intake_summary=IntakeSummary(
                total_responses=5,
                governance_applied=False,
                project_type="test-template",
                completion_time_minutes=15.5
            ),
            next_steps=NextSteps(
                redirect_url="/projects/project-123/ready",
                workflow_status="ready_to_start"
            )
        )
        
        # Make request
        request_data = {
            "final_validation": True,
            "create_project": True
        }
        response = client.post("/api/intake/sessions/test-session-123/complete", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["project_id"] == "project-123"
        assert data["validation_result"]["is_valid"] is True
        assert data["intake_summary"]["total_responses"] == 5
        assert data["intake_summary"]["project_type"] == "test-template"
        assert data["next_steps"]["workflow_status"] == "ready_to_start"
        
        # Verify service was called
        mock_service.complete_session.assert_called_once()
        call_args = mock_service.complete_session.call_args[0]
        assert call_args[0] == "test-session-123"
        assert call_args[1].final_validation is True
        assert call_args[1].create_project is True
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_complete_session_validation_failed(self, mock_get_service, client, mock_service):
        """Test session completion with validation failures."""
        from orchestrator_v2.models.intake import (
            ProjectCreationResult,
            ValidationResult,
            ValidationError,
            IntakeSummary,
            NextSteps
        )
        
        # Setup mock with validation failure
        mock_get_service.return_value = mock_service
        mock_service.complete_session.return_value = ProjectCreationResult(
            success=False,
            project_id=None,
            validation_result=ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        field_id="required_field",
                        error_type="required",
                        message="Required field is missing"
                    )
                ],
                warnings=[]
            ),
            intake_summary=IntakeSummary(
                total_responses=3,
                governance_applied=False,
                project_type="test-template",
                completion_time_minutes=0.0
            ),
            next_steps=NextSteps(
                redirect_url="",
                workflow_status="validation_failed"
            )
        )
        
        # Make request
        request_data = {
            "final_validation": True,
            "create_project": True
        }
        response = client.post("/api/intake/sessions/test-session-123/complete", json=request_data)
        
        # Verify response
        assert response.status_code == 200  # Still 200, but success=False
        data = response.json()
        assert data["success"] is False
        assert data["project_id"] is None
        assert data["validation_result"]["is_valid"] is False
        assert len(data["validation_result"]["errors"]) == 1
        assert data["next_steps"]["workflow_status"] == "validation_failed"
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_delete_session_success(self, mock_get_service, client, mock_service):
        """Test successful session deletion."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.session_repo.delete.return_value = True
        
        # Make request
        response = client.delete("/api/intake/sessions/test-session-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == "test-session-123"
        
        # Verify service was called
        mock_service.session_repo.delete.assert_called_once_with("test-session-123")
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_delete_session_not_found(self, mock_get_service, client, mock_service):
        """Test deleting non-existent session."""
        # Setup mock to return False (not found)
        mock_get_service.return_value = mock_service
        mock_service.session_repo.delete.return_value = False
        
        # Make request
        response = client.delete("/api/intake/sessions/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]


class TestTemplateOperationEndpoints:
    """Test template operation API endpoints."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock intake service."""
        return AsyncMock(spec=IntakeSessionService)
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_list_templates_success(self, mock_get_service, client, mock_service):
        """Test listing templates."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.list_templates.return_value = [
            TemplateListItem(
                template_id="general",
                name="General Project",
                description="General project template",
                category="general",
                estimated_time_minutes=15,
                question_count=10,
                phase_count=3,
                icon="folder",
                color="#6B7280"
            ),
            TemplateListItem(
                template_id="webapp",
                name="Web Application",
                description="Web app template",
                category="development",
                estimated_time_minutes=20,
                question_count=15,
                phase_count=4,
                icon="code",
                color="#3B82F6"
            )
        ]
        
        # Make request
        response = client.get("/api/intake/templates")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["template_id"] == "general"
        assert data[0]["name"] == "General Project"
        assert data[0]["question_count"] == 10
        assert data[1]["template_id"] == "webapp"
        assert data[1]["name"] == "Web Application"
        
        # Verify service was called with default parameters
        mock_service.list_templates.assert_called_once_with(
            client_slug=None,
            category=None,
            include_abstract=False
        )
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_list_templates_with_filters(self, mock_get_service, client, mock_service):
        """Test listing templates with filters."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.list_templates.return_value = []
        
        # Make request with query parameters
        response = client.get("/api/intake/templates?category=development&client_slug=test-client&include_abstract=true")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called with filters
        mock_service.list_templates.assert_called_once_with(
            client_slug="test-client",
            category="development",
            include_abstract=True
        )
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_get_template_success(self, mock_get_service, client, sample_template, mock_service):
        """Test getting template definition."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.get_template.return_value = sample_template
        
        # Make request
        response = client.get("/api/intake/templates/test-template")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["template"]["id"] == "test-template"
        assert data["template"]["name"] == "Test Template"
        assert len(data["phases"]) == 1
        assert data["phases"][0]["id"] == "phase1"
        assert len(data["phases"][0]["questions"]) == 2
        
        # Verify service was called
        mock_service.get_template.assert_called_once_with("test-template", None)
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_get_template_with_client(self, mock_get_service, client, sample_template, mock_service):
        """Test getting template with client-specific governance."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.get_template.return_value = sample_template
        
        # Make request with client parameter
        response = client.get("/api/intake/templates/test-template?client_slug=test-client")
        
        # Verify response
        assert response.status_code == 200
        
        # Verify service was called with client
        mock_service.get_template.assert_called_once_with("test-template", "test-client")
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_get_template_not_found(self, mock_get_service, client, mock_service):
        """Test getting non-existent template."""
        # Setup mock to return None
        mock_get_service.return_value = mock_service
        mock_service.get_template.return_value = None
        
        # Make request
        response = client.get("/api/intake/templates/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]


class TestUtilityEndpoints:
    """Test utility API endpoints."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock intake service."""
        return AsyncMock(spec=IntakeSessionService)
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_validate_responses_success(self, mock_get_service, client, mock_service):
        """Test response validation."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.validate_responses.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        
        # Make request
        request_data = {
            "template_id": "test-template",
            "client_slug": "test-client",
            "responses": {
                "name": "John Doe",
                "age": 30
            }
        }
        response = client.post("/api/intake/validate", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert len(data["errors"]) == 0
        assert len(data["warnings"]) == 0
        
        # Verify service was called
        mock_service.validate_responses.assert_called_once()
        call_args = mock_service.validate_responses.call_args[0][0]
        assert call_args.template_id == "test-template"
        assert call_args.client_slug == "test-client"
        assert call_args.responses == {"name": "John Doe", "age": 30}
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_validate_responses_with_errors(self, mock_get_service, client, mock_service):
        """Test response validation with errors."""
        from orchestrator_v2.models.intake import ValidationError
        
        # Setup mock with validation errors
        mock_get_service.return_value = mock_service
        mock_service.validate_responses.return_value = ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    field_id="name",
                    error_type="required",
                    message="Name is required"
                ),
                ValidationError(
                    field_id="age",
                    error_type="min_value",
                    message="Age must be at least 0"
                )
            ],
            warnings=["Consider providing more details"]
        )
        
        # Make request
        request_data = {
            "template_id": "test-template",
            "responses": {
                "age": -5
            }
        }
        response = client.post("/api/intake/validate", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert len(data["errors"]) == 2
        assert data["errors"][0]["field_id"] == "name"
        assert data["errors"][0]["error_type"] == "required"
        assert data["errors"][1]["field_id"] == "age"
        assert data["errors"][1]["error_type"] == "min_value"
        assert len(data["warnings"]) == 1
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_validate_responses_template_not_found(self, mock_get_service, client, mock_service):
        """Test validation with non-existent template."""
        # Setup mock to raise error
        mock_get_service.return_value = mock_service
        mock_service.validate_responses.side_effect = TemplateNotFoundError("Template not found: nonexistent")
        
        # Make request
        request_data = {
            "template_id": "nonexistent",
            "responses": {}
        }
        response = client.post("/api/intake/validate", json=request_data)
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_preview_template_success(self, mock_get_service, client, sample_template, mock_service):
        """Test template preview."""
        # Setup mock
        mock_get_service.return_value = mock_service
        mock_service.get_template.return_value = sample_template
        
        # Make request
        response = client.get("/api/intake/preview/test-template")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check template section
        assert data["template"]["id"] == "test-template"
        assert data["template"]["name"] == "Test Template"
        assert data["template"]["category"] == "test"
        
        # Check structure section
        assert data["structure"]["total_phases"] == 1
        assert data["structure"]["total_questions"] == 2  # Both questions are visible
        assert len(data["structure"]["phases"]) == 1
        assert data["structure"]["phases"][0]["id"] == "phase1"
        assert data["structure"]["phases"][0]["question_count"] == 2
        
        # Check features section
        assert "features" in data
        assert "has_brand_constraints" in data["features"]
        assert "has_governance" in data["features"]
        assert "has_conditional_logic" in data["features"]
        assert "supports_inheritance" in data["features"]
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_preview_template_not_found(self, mock_get_service, client, mock_service):
        """Test preview for non-existent template."""
        # Setup mock to return None
        mock_get_service.return_value = mock_service
        mock_service.get_template.return_value = None
        
        # Make request
        response = client.get("/api/intake/preview/nonexistent")
        
        # Verify response
        assert response.status_code == 404
        data = response.json()
        assert "Template not found" in data["detail"]


class TestHealthAndErrorHandling:
    """Test health endpoint and error handling."""
    
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/intake/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "intake"
        assert "timestamp" in data
    
    async def test_invalid_request_body(self, client):
        """Test handling of invalid request bodies."""
        # Make request with invalid JSON
        response = client.post(
            "/api/intake/sessions",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        # Should get 422 Unprocessable Entity for invalid JSON
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        # Make request without required template_id
        response = client.post("/api/intake/sessions", json={})
        
        # Should get 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_internal_server_error(self, mock_get_service, client):
        """Test handling of internal server errors."""
        # Setup mock to raise unexpected exception
        mock_service = AsyncMock(spec=IntakeSessionService)
        mock_get_service.return_value = mock_service
        mock_service.create_session.side_effect = Exception("Database connection failed")
        
        # Make request
        request_data = {
            "template_id": "test-template",
            "client_slug": "test-client"
        }
        response = client.post("/api/intake/sessions", json=request_data)
        
        # Should get 500 for internal server error
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock intake service for E2E tests."""
        return AsyncMock(spec=IntakeSessionService)
    
    @patch('orchestrator_v2.api.routes.intake.get_intake_service')
    async def test_complete_intake_workflow(self, mock_get_service, client, sample_template, mock_service):
        """Test a complete intake workflow from start to finish."""
        from orchestrator_v2.models.intake import (
            SessionResponse,
            SessionStatusResponse,
            PhaseResponse,
            ResponseSubmissionResult,
            ValidationResult,
            ProjectCreationResult,
            IntakeSummary,
            NextSteps
        )
        
        mock_get_service.return_value = mock_service
        
        # Step 1: Create session
        mock_service.create_session.return_value = SessionResponse(
            session_id="workflow-session",
            template_id="test-template",
            client_slug="test-client",
            current_phase_id="phase1",
            progress_percent=0.0,
            is_complete=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            governance_notices=[]
        )
        
        create_response = client.post("/api/intake/sessions", json={
            "template_id": "test-template",
            "client_slug": "test-client"
        })
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]
        
        # Step 2: Get session status
        mock_service.get_session_status.return_value = SessionStatusResponse(
            session_id=session_id,
            template_id="test-template",
            current_phase_id="phase1",
            progress_percent=0.0,
            phases=[
                PhaseResponse(
                    phase_id="phase1",
                    name="Test Phase",
                    description="First phase",
                    required=True,
                    questions=sample_template.phases[0].questions,
                    is_current=True,
                    is_complete=False,
                    is_available=True
                )
            ],
            current_questions=sample_template.phases[0].questions,
            responses={},
            validation_errors=[]
        )
        
        status_response = client.get(f"/api/intake/sessions/{session_id}")
        assert status_response.status_code == 200
        assert status_response.json()["current_phase_id"] == "phase1"
        
        # Step 3: Submit responses
        mock_service.submit_responses.return_value = ResponseSubmissionResult(
            success=True,
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            next_phase_id="phase1",
            advanced=False,
            progress_percent=100.0
        )
        
        submit_response = client.put(f"/api/intake/sessions/{session_id}/responses", json={
            "phase_id": "phase1",
            "responses": {
                "name": "Test User",
                "age": 25
            }
        })
        assert submit_response.status_code == 200
        assert submit_response.json()["success"] is True
        
        # Step 4: Complete session
        mock_service.complete_session.return_value = ProjectCreationResult(
            success=True,
            project_id="project-123",
            validation_result=ValidationResult(is_valid=True, errors=[], warnings=[]),
            intake_summary=IntakeSummary(
                total_responses=2,
                governance_applied=False,
                project_type="test-template",
                completion_time_minutes=5.0
            ),
            next_steps=NextSteps(
                redirect_url="/projects/project-123/ready",
                workflow_status="ready_to_start"
            )
        )
        
        complete_response = client.post(f"/api/intake/sessions/{session_id}/complete", json={
            "final_validation": True,
            "create_project": True
        })
        assert complete_response.status_code == 200
        data = complete_response.json()
        assert data["success"] is True
        assert data["project_id"] == "project-123"
        
        # Verify all service calls were made
        assert mock_service.create_session.called
        assert mock_service.get_session_status.called
        assert mock_service.submit_responses.called
        assert mock_service.complete_session.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])