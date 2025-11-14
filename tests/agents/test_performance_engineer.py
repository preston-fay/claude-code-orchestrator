"""Tests for Performance Engineer agent."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_performance_engineer_import():
    """Test that PerformanceEngineer can be imported."""
    from orchestrator.agents import PerformanceEngineer
    assert PerformanceEngineer is not None


def test_performance_engineer_run(tmp_path, monkeypatch):
    """Test basic performance engineer execution."""
    from orchestrator.agents import PerformanceEngineer

    monkeypatch.chdir(tmp_path)
    engineer = PerformanceEngineer(project_root=tmp_path)

    result = engineer.run(sla_latency_p95_ms=200)

    assert result["success"] is True
    assert "artifacts" in result
    assert len(result["artifacts"]) >= 2
    assert "summary" in result

    # Check artifacts were created
    assert (tmp_path / "reports" / "performance_profile.json").exists()
    assert (tmp_path / "reports" / "performance_recommendations.md").exists()


def test_performance_engineer_sla_compliance(tmp_path, monkeypatch):
    """Test SLA compliance detection."""
    from orchestrator.agents import PerformanceEngineer

    monkeypatch.chdir(tmp_path)
    engineer = PerformanceEngineer(project_root=tmp_path)

    # With very tight SLA (will fail)
    result = engineer.run(sla_latency_p95_ms=50)
    assert result["summary"]["sla_compliance"] is False

    # With loose SLA (will pass)
    result2 = engineer.run(sla_latency_p95_ms=500)
    assert result2["summary"]["sla_compliance"] is True


def test_performance_engineer_recommendations(tmp_path, monkeypatch):
    """Test that recommendations are generated."""
    from orchestrator.agents import PerformanceEngineer
    import json

    monkeypatch.chdir(tmp_path)
    engineer = PerformanceEngineer(project_root=tmp_path)

    result = engineer.run(sla_latency_p95_ms=100)

    # Check recommendations file exists
    rec_path = tmp_path / "reports" / "performance_recommendations.md"
    assert rec_path.exists()

    # Check content has recommendations
    content = rec_path.read_text()
    assert "Recommendations" in content
    assert "database" in content.lower() or "optimization" in content.lower()
