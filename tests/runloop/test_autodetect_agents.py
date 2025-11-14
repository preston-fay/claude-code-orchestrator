"""Tests for auto-detection of specialized agents in RunLoop."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.fixture
def mock_orchestrator(tmp_path, monkeypatch):
    """Create a mock Orchestrator instance for testing."""
    from orchestrator.runloop import Orchestrator

    monkeypatch.chdir(tmp_path)

    # Create minimal config
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
orchestrator:
  state_file: ".claude/orchestrator_state.json"

subagents: {}

workflow:
  phases: {}

governance:
  require_security_scan: false
  performance_slas:
    latency_p95_ms: 0
""")

    orch = Orchestrator(project_root=tmp_path)
    return orch


def test_detect_database_architect_keywords(mock_orchestrator):
    """Test database architect detection via keywords."""
    # Set intake with database keywords
    mock_orchestrator.state.intake_summary = {
        "requirements": ["Create database schema", "SQL migrations"]
    }

    base_agents = ["architect", "developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    # Should detect database-architect and insert before developer
    assert "database-architect" in detected
    assert detected.index("database-architect") < detected.index("developer")


def test_detect_performance_engineer_sla(mock_orchestrator):
    """Test performance engineer detection via SLA."""
    # Set governance with performance SLA
    mock_orchestrator.config["governance"] = {
        "performance_slas": {
            "latency_p95_ms": 200
        }
    }
    mock_orchestrator.state.intake_summary = {}

    base_agents = ["developer", "qa"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    # Should detect performance-engineer
    assert "performance-engineer" in detected


def test_detect_performance_engineer_keywords(mock_orchestrator):
    """Test performance engineer detection via keywords."""
    mock_orchestrator.state.intake_summary = {
        "requirements": ["Application must handle high throughput", "optimize performance"]
    }

    base_agents = ["developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    assert "performance-engineer" in detected


def test_detect_security_auditor_governance(mock_orchestrator):
    """Test security auditor detection via governance."""
    mock_orchestrator.config["governance"] = {
        "require_security_scan": True
    }
    mock_orchestrator.state.intake_summary = {}

    base_agents = ["developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    assert "security-auditor" in detected


def test_detect_security_auditor_compliance(mock_orchestrator):
    """Test security auditor detection via compliance requirements."""
    mock_orchestrator.config["governance"] = {
        "compliance": {
            "gdpr": {"enabled": True},
            "hipaa": {"enabled": True}
        }
    }
    mock_orchestrator.state.intake_summary = {}

    base_agents = ["developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    assert "security-auditor" in detected


def test_detect_security_auditor_production(mock_orchestrator):
    """Test security auditor detection in production environment."""
    mock_orchestrator.state.intake_summary = {
        "environment": "production"
    }

    base_agents = ["developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    # Production should trigger both performance and security
    assert "security-auditor" in detected
    assert "performance-engineer" in detected


def test_no_duplicates(mock_orchestrator):
    """Test that agents are not duplicated if already in base list."""
    mock_orchestrator.state.intake_summary = {
        "requirements": ["database schema"]
    }

    # Base list already has database-architect
    base_agents = ["database-architect", "developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    # Should not add duplicate
    assert detected.count("database-architect") == 1


def test_no_detection_without_triggers(mock_orchestrator):
    """Test that no agents are detected without triggers."""
    mock_orchestrator.state.intake_summary = {
        "requirements": ["Build a simple web app"]
    }
    mock_orchestrator.config["governance"] = {
        "require_security_scan": False,
        "performance_slas": {"latency_p95_ms": 0}
    }

    base_agents = ["developer"]
    detected = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)

    # Should not detect any specialized agents
    assert detected == base_agents
    assert "database-architect" not in detected
    assert "performance-engineer" not in detected
    assert "security-auditor" not in detected


def test_phase_specific_detection(mock_orchestrator):
    """Test that agents are only detected in appropriate phases."""
    mock_orchestrator.state.intake_summary = {
        "requirements": ["database", "performance"]
    }
    mock_orchestrator.config["governance"] = {
        "require_security_scan": True
    }

    # Database architect should be detected in planning
    base_agents = []
    detected_planning = mock_orchestrator._auto_detect_optional_agents("planning", base_agents)
    assert "database-architect" in detected_planning

    # Performance/security should be detected in developer/qa
    detected_dev = mock_orchestrator._auto_detect_optional_agents("developer", base_agents)
    assert "performance-engineer" in detected_dev
    assert "security-auditor" in detected_dev

    # But not in other phases
    detected_consensus = mock_orchestrator._auto_detect_optional_agents("consensus", base_agents)
    assert "performance-engineer" not in detected_consensus
    assert "security-auditor" not in detected_consensus
