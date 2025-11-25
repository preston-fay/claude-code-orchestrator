"""
Tests for Orchestrator Runs API endpoints.

Tests the 5-endpoint runs API surface:
- POST /runs → create orchestrator run
- POST /runs/{id}/next → advance to next phase
- GET /runs/{id} → get run status and phases
- GET /runs/{id}/artifacts → list artifacts by phase
- GET /runs/{id}/metrics → governance, hygiene, timing, tokens
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from orchestrator_v2.api.server import app
from orchestrator_v2.api.dto.runs import (
    CreateRunRequest,
    RunSummary,
    RunDetail,
    PhaseInfo,
    ArtifactsResponse,
    MetricsSummary,
)
from orchestrator_v2.engine.state_models import ProjectState, PhaseType, PhaseState
from orchestrator_v2.user.models import UserProfile


# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create workspace structure
        artifacts_dir = workspace / "artifacts"
        artifacts_dir.mkdir()

        # Create phase directories with sample artifacts
        planning_dir = artifacts_dir / "planning"
        planning_dir.mkdir()
        (planning_dir / "PRD.md").write_text("# Product Requirements")
        (planning_dir / "requirements.txt").write_text("fastapi==0.104.1")

        architecture_dir = artifacts_dir / "architecture"
        architecture_dir.mkdir()
        (architecture_dir / "architecture.md").write_text("# Architecture Design")

        yield workspace


@pytest.fixture
def mock_user():
    """Mock user profile for testing."""
    return UserProfile(
        user_id="test-user-123",
        email="test@example.com",
        name="Test User",
        preferences={"theme": "dark"},
    )


@pytest.fixture
def sample_project_state(temp_workspace):
    """Sample project state for testing."""
    state = ProjectState(
        project_id="run-abc123",
        project_name="Test Project",
        client="default",
        user_id="test-user-123",
        project_type="analytics_forecast_app",
        template_id="analytics_forecast_app",
        current_phase=PhaseType.PLANNING,
        workspace_path=str(temp_workspace),
        metadata={"intake": "Build a forecasting app"},
    )

    # Add planning phase state
    planning_state = PhaseState(
        phase=PhaseType.PLANNING,
        status="running",
        started_at=datetime.utcnow(),
    )
    planning_state.artifacts = ["PRD.md", "requirements.txt"]
    state.phases["planning"] = planning_state

    return state


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# -------------------------------------------------------------------------
# Helper function for authentication headers
# -------------------------------------------------------------------------

def auth_headers(user: UserProfile = None):
    """Generate authentication headers."""
    if user is None:
        user = UserProfile(
            user_id="test-user-123",
            email="test@example.com",
            name="Test User",
        )

    return {
        "X-User-Id": user.user_id,
        "X-User-Email": user.email,
    }


# -------------------------------------------------------------------------
# Test: POST /runs - Create orchestrator run
# -------------------------------------------------------------------------

class TestCreateRun:
    """Test POST /runs endpoint."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.create_run")
    def test_create_run_success(self, mock_create, client, mock_user):
        """Should create a new run with valid request."""
        # Mock service response
        mock_create.return_value = RunSummary(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            current_phase="planning",
            status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        request_data = {
            "profile": "analytics_forecast_app",
            "intake": "Build a forecasting app",
            "project_name": "Test Project",
        }

        response = client.post(
            "/runs",
            json=request_data,
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["run_id"] == "run-abc123"
        assert data["profile"] == "analytics_forecast_app"
        assert data["current_phase"] == "planning"
        assert data["status"] == "running"

    def test_create_run_missing_auth(self, client):
        """Should fail without authentication headers."""
        request_data = {
            "profile": "analytics_forecast_app",
        }

        response = client.post("/runs", json=request_data)

        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.create_run")
    def test_create_run_minimal_request(self, mock_create, client, mock_user):
        """Should create run with minimal required fields."""
        mock_create.return_value = RunSummary(
            run_id="run-xyz789",
            profile="simple_app",
            project_name="run_xyz789",
            current_phase="planning",
            status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        request_data = {
            "profile": "simple_app",
        }

        response = client.post(
            "/runs",
            json=request_data,
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["profile"] == "simple_app"

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.create_run")
    def test_create_run_with_metadata(self, mock_create, client, mock_user):
        """Should create run with additional metadata."""
        mock_create.return_value = RunSummary(
            run_id="run-meta123",
            profile="analytics_forecast_app",
            project_name="Metadata Test",
            current_phase="planning",
            status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        request_data = {
            "profile": "analytics_forecast_app",
            "project_name": "Metadata Test",
            "metadata": {
                "client": "Acme Corp",
                "priority": "high",
                "tags": ["forecasting", "analytics"],
            },
        }

        response = client.post(
            "/runs",
            json=request_data,
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 201


# -------------------------------------------------------------------------
# Test: POST /runs/{run_id}/next - Advance to next phase
# -------------------------------------------------------------------------

class TestAdvanceRun:
    """Test POST /runs/{run_id}/next endpoint."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.advance_run")
    def test_advance_run_success(self, mock_advance, mock_get, client, mock_user):
        """Should advance run to next phase."""
        # Mock get_run (current state)
        mock_get.return_value = RunDetail(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            current_phase="planning",
            status="running",
            phases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock advance_run (updated state)
        mock_advance.return_value = RunDetail(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            current_phase="architecture",
            status="running",
            phases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        response = client.post(
            "/runs/run-abc123/next",
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-abc123"
        assert data["previous_phase"] == "planning"
        assert data["current_phase"] == "architecture"
        assert "Advanced from" in data["message"]

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    def test_advance_run_not_found(self, mock_get, client, mock_user):
        """Should return 404 for non-existent run."""
        mock_get.side_effect = KeyError("Run not found")

        response = client.post(
            "/runs/nonexistent-run/next",
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.advance_run")
    def test_advance_run_skip_validation(self, mock_advance, mock_get, client, mock_user):
        """Should advance run with skip_validation flag."""
        mock_get.return_value = RunDetail(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            current_phase="planning",
            status="running",
            phases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_advance.return_value = RunDetail(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            current_phase="architecture",
            status="running",
            phases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        request_data = {"skip_validation": True}

        response = client.post(
            "/runs/run-abc123/next",
            json=request_data,
            headers=auth_headers(mock_user),
        )

        assert response.status_code == 200


# -------------------------------------------------------------------------
# Test: GET /runs/{run_id} - Get run status and phases
# -------------------------------------------------------------------------

class TestGetRun:
    """Test GET /runs/{run_id} endpoint."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    def test_get_run_success(self, mock_get, client):
        """Should return detailed run information."""
        mock_get.return_value = RunDetail(
            run_id="run-abc123",
            profile="analytics_forecast_app",
            project_name="Test Project",
            intake="Build a forecasting app",
            current_phase="architecture",
            status="running",
            phases=[
                PhaseInfo(
                    phase="planning",
                    status="completed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_seconds=300.0,
                    agent_ids=["planner"],
                    artifacts_count=2,
                ),
                PhaseInfo(
                    phase="architecture",
                    status="in_progress",
                    started_at=datetime.utcnow(),
                    agent_ids=["architect"],
                    artifacts_count=0,
                ),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            total_duration_seconds=300.0,
        )

        response = client.get("/runs/run-abc123")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-abc123"
        assert data["current_phase"] == "architecture"
        assert len(data["phases"]) == 2
        assert data["phases"][0]["status"] == "completed"
        assert data["phases"][1]["status"] == "in_progress"

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    def test_get_run_not_found(self, mock_get, client):
        """Should return 404 for non-existent run."""
        mock_get.side_effect = KeyError("Run not found")

        response = client.get("/runs/nonexistent-run")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    def test_get_run_completed(self, mock_get, client):
        """Should return completed run with all phases."""
        mock_get.return_value = RunDetail(
            run_id="run-completed",
            profile="analytics_forecast_app",
            project_name="Completed Project",
            current_phase="documentation",
            status="completed",
            phases=[
                PhaseInfo(phase="planning", status="completed", artifacts_count=2),
                PhaseInfo(phase="architecture", status="completed", artifacts_count=3),
                PhaseInfo(phase="data", status="completed", artifacts_count=5),
                PhaseInfo(phase="development", status="completed", artifacts_count=10),
                PhaseInfo(phase="qa", status="completed", artifacts_count=4),
                PhaseInfo(phase="documentation", status="completed", artifacts_count=2),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_duration_seconds=3600.0,
        )

        response = client.get("/runs/run-completed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert len(data["phases"]) == 6


# -------------------------------------------------------------------------
# Test: GET /runs/{run_id}/artifacts - List artifacts by phase
# -------------------------------------------------------------------------

class TestGetRunArtifacts:
    """Test GET /runs/{run_id}/artifacts endpoint."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.list_artifacts")
    def test_get_artifacts_success(self, mock_list, client):
        """Should return artifacts grouped by phase."""
        from orchestrator_v2.api.dto.runs import ArtifactSummary

        mock_list.return_value = ArtifactsResponse(
            run_id="run-abc123",
            artifacts_by_phase={
                "planning": [
                    ArtifactSummary(
                        artifact_id="planning_PRD.md",
                        phase="planning",
                        path="/path/to/PRD.md",
                        name="PRD.md",
                        description="PRD artifact for planning",
                        artifact_type="prd",
                        size_bytes=1024,
                        created_at=datetime.utcnow(),
                    ),
                    ArtifactSummary(
                        artifact_id="planning_requirements.txt",
                        phase="planning",
                        path="/path/to/requirements.txt",
                        name="requirements.txt",
                        description="REQUIREMENTS artifact for planning",
                        artifact_type="requirements",
                        size_bytes=512,
                        created_at=datetime.utcnow(),
                    ),
                ],
                "architecture": [
                    ArtifactSummary(
                        artifact_id="architecture_architecture.md",
                        phase="architecture",
                        path="/path/to/architecture.md",
                        name="architecture.md",
                        description="ARCHITECTURE artifact for architecture",
                        artifact_type="architecture",
                        size_bytes=2048,
                        created_at=datetime.utcnow(),
                    ),
                ],
            },
            total_count=3,
        )

        response = client.get("/runs/run-abc123/artifacts")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-abc123"
        assert data["total_count"] == 3
        assert len(data["artifacts_by_phase"]["planning"]) == 2
        assert len(data["artifacts_by_phase"]["architecture"]) == 1
        assert data["artifacts_by_phase"]["planning"][0]["name"] == "PRD.md"

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.list_artifacts")
    def test_get_artifacts_empty(self, mock_list, client):
        """Should return empty artifacts for new run."""
        mock_list.return_value = ArtifactsResponse(
            run_id="run-new",
            artifacts_by_phase={},
            total_count=0,
        )

        response = client.get("/runs/run-new/artifacts")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["artifacts_by_phase"] == {}

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.list_artifacts")
    def test_get_artifacts_not_found(self, mock_list, client):
        """Should return 404 for non-existent run."""
        mock_list.side_effect = KeyError("Run not found")

        response = client.get("/runs/nonexistent-run/artifacts")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# -------------------------------------------------------------------------
# Test: GET /runs/{run_id}/metrics - Get governance, hygiene, and metrics
# -------------------------------------------------------------------------

class TestGetRunMetrics:
    """Test GET /runs/{run_id}/metrics endpoint."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_metrics")
    def test_get_metrics_success(self, mock_get_metrics, client):
        """Should return comprehensive metrics."""
        from orchestrator_v2.api.dto.runs import PhaseMetrics

        mock_get_metrics.return_value = MetricsSummary(
            run_id="run-abc123",
            total_duration_seconds=3600.0,
            total_token_usage={"input": 10000, "output": 5000},
            total_cost_usd=0.45,
            phases_metrics=[
                PhaseMetrics(
                    phase="planning",
                    duration_seconds=300.0,
                    token_usage={"input": 2000, "output": 1000},
                    cost_usd=0.09,
                    agents_executed=["planner"],
                    artifacts_generated=2,
                    governance_passed=True,
                    governance_warnings=[],
                ),
                PhaseMetrics(
                    phase="architecture",
                    duration_seconds=600.0,
                    token_usage={"input": 3000, "output": 1500},
                    cost_usd=0.135,
                    agents_executed=["architect"],
                    artifacts_generated=3,
                    governance_passed=True,
                    governance_warnings=[],
                ),
            ],
            governance_score=1.0,
            hygiene_score=0.95,
            artifacts_total=5,
            errors_count=0,
        )

        response = client.get("/runs/run-abc123/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-abc123"
        assert data["total_duration_seconds"] == 3600.0
        assert data["total_token_usage"]["input"] == 10000
        assert data["total_cost_usd"] == 0.45
        assert data["governance_score"] == 1.0
        assert len(data["phases_metrics"]) == 2

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_metrics")
    def test_get_metrics_with_errors(self, mock_get_metrics, client):
        """Should return metrics with error count."""
        from orchestrator_v2.api.dto.runs import PhaseMetrics

        mock_get_metrics.return_value = MetricsSummary(
            run_id="run-errors",
            total_duration_seconds=1800.0,
            total_token_usage={"input": 5000, "output": 2500},
            total_cost_usd=0.225,
            phases_metrics=[
                PhaseMetrics(
                    phase="development",
                    duration_seconds=1800.0,
                    token_usage={"input": 5000, "output": 2500},
                    cost_usd=0.225,
                    agents_executed=["developer"],
                    artifacts_generated=8,
                    governance_passed=False,
                    governance_warnings=["Code quality threshold not met"],
                ),
            ],
            governance_score=0.8,
            hygiene_score=0.85,
            artifacts_total=8,
            errors_count=1,
        )

        response = client.get("/runs/run-errors/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["errors_count"] == 1
        assert data["governance_score"] == 0.8
        assert len(data["phases_metrics"][0]["governance_warnings"]) > 0

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_metrics")
    def test_get_metrics_not_found(self, mock_get_metrics, client):
        """Should return 404 for non-existent run."""
        mock_get_metrics.side_effect = KeyError("Run not found")

        response = client.get("/runs/nonexistent-run/metrics")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# -------------------------------------------------------------------------
# Test: Full workflow
# -------------------------------------------------------------------------

class TestFullWorkflow:
    """Test complete API workflow: create -> advance -> get -> artifacts -> metrics."""

    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.create_run")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_run")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.advance_run")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.list_artifacts")
    @patch("orchestrator_v2.services.orchestrator_service.OrchestratorService.get_metrics")
    def test_complete_workflow(
        self, mock_metrics, mock_artifacts, mock_advance, mock_get, mock_create, client, mock_user
    ):
        """Test complete workflow from creation to metrics."""
        from orchestrator_v2.api.dto.runs import ArtifactSummary, PhaseMetrics

        # 1. Create run
        mock_create.return_value = RunSummary(
            run_id="run-workflow",
            profile="analytics_forecast_app",
            project_name="Workflow Test",
            current_phase="planning",
            status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        create_response = client.post(
            "/runs",
            json={
                "profile": "analytics_forecast_app",
                "project_name": "Workflow Test",
            },
            headers=auth_headers(mock_user),
        )
        assert create_response.status_code == 201
        run_id = create_response.json()["run_id"]

        # 2. Get run details
        mock_get.return_value = RunDetail(
            run_id=run_id,
            profile="analytics_forecast_app",
            project_name="Workflow Test",
            current_phase="planning",
            status="running",
            phases=[
                PhaseInfo(
                    phase="planning",
                    status="in_progress",
                    started_at=datetime.utcnow(),
                    artifacts_count=0,
                ),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        get_response = client.get(f"/runs/{run_id}")
        assert get_response.status_code == 200
        assert get_response.json()["current_phase"] == "planning"

        # 3. Advance to next phase
        mock_advance.return_value = RunDetail(
            run_id=run_id,
            profile="analytics_forecast_app",
            project_name="Workflow Test",
            current_phase="architecture",
            status="running",
            phases=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        advance_response = client.post(
            f"/runs/{run_id}/next",
            headers=auth_headers(mock_user),
        )
        assert advance_response.status_code == 200
        assert advance_response.json()["current_phase"] == "architecture"

        # 4. Get artifacts
        mock_artifacts.return_value = ArtifactsResponse(
            run_id=run_id,
            artifacts_by_phase={
                "planning": [
                    ArtifactSummary(
                        artifact_id="planning_PRD.md",
                        phase="planning",
                        path="/path/to/PRD.md",
                        name="PRD.md",
                        description="PRD artifact",
                        artifact_type="prd",
                        size_bytes=1024,
                        created_at=datetime.utcnow(),
                    ),
                ],
            },
            total_count=1,
        )

        artifacts_response = client.get(f"/runs/{run_id}/artifacts")
        assert artifacts_response.status_code == 200
        assert artifacts_response.json()["total_count"] == 1

        # 5. Get metrics
        mock_metrics.return_value = MetricsSummary(
            run_id=run_id,
            total_duration_seconds=300.0,
            total_token_usage={"input": 2000, "output": 1000},
            total_cost_usd=0.09,
            phases_metrics=[
                PhaseMetrics(
                    phase="planning",
                    duration_seconds=300.0,
                    token_usage={"input": 2000, "output": 1000},
                    cost_usd=0.09,
                    agents_executed=["planner"],
                    artifacts_generated=1,
                    governance_passed=True,
                    governance_warnings=[],
                ),
            ],
            governance_score=1.0,
            hygiene_score=1.0,
            artifacts_total=1,
            errors_count=0,
        )

        metrics_response = client.get(f"/runs/{run_id}/metrics")
        assert metrics_response.status_code == 200
        assert metrics_response.json()["governance_score"] == 1.0
