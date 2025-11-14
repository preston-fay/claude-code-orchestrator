"""Tests for Security Auditor agent."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_security_auditor_import():
    """Test that SecurityAuditor can be imported."""
    from orchestrator.agents import SecurityAuditor
    assert SecurityAuditor is not None


def test_security_auditor_run(tmp_path, monkeypatch):
    """Test basic security auditor execution."""
    from orchestrator.agents import SecurityAuditor

    monkeypatch.chdir(tmp_path)
    auditor = SecurityAuditor(project_root=tmp_path)

    result = auditor.run(scan_dependencies=True)

    assert result["success"] is True
    assert "artifacts" in result
    assert len(result["artifacts"]) >= 2
    assert "summary" in result

    # Check artifacts were created
    assert (tmp_path / "reports" / "security_scan.json").exists()


def test_security_auditor_vulnerabilities(tmp_path, monkeypatch):
    """Test vulnerability detection."""
    from orchestrator.agents import SecurityAuditor
    import json

    monkeypatch.chdir(tmp_path)
    auditor = SecurityAuditor(project_root=tmp_path)

    result = auditor.run()

    # Check vulnerabilities were found
    assert result["summary"]["vulnerabilities_total"] > 0
    assert result["summary"]["vulnerabilities_critical"] >= 0

    # Check scan file has vulnerability details
    scan_path = tmp_path / "reports" / "security_scan.json"
    scan_data = json.loads(scan_path.read_text())
    assert "vulnerabilities" in scan_data
    assert len(scan_data["vulnerabilities"]) > 0


def test_security_auditor_compliance(tmp_path, monkeypatch):
    """Test compliance checking."""
    from orchestrator.agents import SecurityAuditor

    monkeypatch.chdir(tmp_path)
    auditor = SecurityAuditor(project_root=tmp_path)

    result = auditor.run(compliance_requirements=["gdpr", "soc2"])

    # Compliance report should be created
    compliance_path = tmp_path / "reports" / "security_compliance.md"
    assert compliance_path.exists()

    # Check content mentions compliance frameworks
    content = compliance_path.read_text()
    assert "GDPR" in content or "SOC2" in content
