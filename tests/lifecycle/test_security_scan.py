"""
Tests for security scanning module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from lifecycle.security_scan import (
    run_bandit_scan,
    run_pip_audit,
    run_npm_audit,
    compute_platform_security_score,
    aggregate_scan_results
)


def test_compute_platform_security_score_perfect():
    """Test security score computation with no vulnerabilities."""
    scan_results = {
        "bandit": {"status": "clean", "summary": {"high": 0, "medium": 0, "low": 0}},
        "pip_audit": {"status": "clean", "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}},
        "npm_audit": []
    }

    score = compute_platform_security_score(scan_results)
    assert score == 100.0


def test_compute_platform_security_score_with_critical_vuln():
    """Test security score computation with critical vulnerability."""
    scan_results = {
        "pip_audit": {
            "status": "vulnerabilities",
            "summary": {"critical": 1, "high": 0, "medium": 0, "low": 0}
        }
    }

    score = compute_platform_security_score(scan_results)
    # Should deduct 20 points for critical
    assert score == 80.0


def test_compute_platform_security_score_with_multiple_vulns():
    """Test security score computation with multiple vulnerabilities."""
    scan_results = {
        "pip_audit": {
            "status": "vulnerabilities",
            "summary": {"critical": 1, "high": 2, "medium": 1, "low": 1}
        },
        "bandit": {
            "status": "findings",
            "summary": {"high": 1, "medium": 2, "low": 3}
        }
    }

    score = compute_platform_security_score(scan_results)
    # Deductions: critical(20) + high(2*10) + medium(5) + low(2) + bandit_high(5) + bandit_medium(2*2) + bandit_low(3*1)
    # = 20 + 20 + 5 + 2 + 5 + 4 + 3 = 59
    # Score = 100 - 59 = 41
    assert score == 41.0


def test_compute_platform_security_score_minimum_zero():
    """Test that security score doesn't go below 0."""
    scan_results = {
        "pip_audit": {
            "status": "vulnerabilities",
            "summary": {"critical": 10, "high": 10, "medium": 0, "low": 0}
        }
    }

    score = compute_platform_security_score(scan_results)
    # Deductions would be 10*20 + 10*10 = 300, but score should be clamped at 0
    assert score == 0.0


@patch('subprocess.run')
def test_run_bandit_scan_clean(mock_run):
    """Test Bandit scan with no findings."""
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"results": []}'
    )

    result = run_bandit_scan(Path("/fake/path"))

    assert result["status"] == "clean"
    assert len(result["findings"]) == 0
    assert result["summary"]["high"] == 0


@patch('subprocess.run')
def test_run_bandit_scan_with_findings(mock_run):
    """Test Bandit scan with security findings."""
    mock_stdout = json.dumps({
        "results": [
            {
                "issue_severity": "HIGH",
                "issue_confidence": "HIGH",
                "issue_text": "Use of exec detected",
                "filename": "/path/to/file.py",
                "line_number": 42,
                "test_id": "B102"
            },
            {
                "issue_severity": "MEDIUM",
                "issue_confidence": "MEDIUM",
                "issue_text": "Possible SQL injection",
                "filename": "/path/to/db.py",
                "line_number": 100,
                "test_id": "B608"
            }
        ]
    })

    mock_run.return_value = Mock(
        returncode=1,
        stdout=mock_stdout
    )

    result = run_bandit_scan(Path("/fake/path"))

    assert result["status"] == "findings"
    assert len(result["findings"]) == 2
    assert result["summary"]["high"] == 1
    assert result["summary"]["medium"] == 1
    assert result["findings"][0]["severity"] == "high"


@patch('subprocess.run')
def test_run_pip_audit_clean(mock_run):
    """Test pip-audit with no vulnerabilities."""
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"dependencies": []}'
    )

    result = run_pip_audit()

    assert result["status"] == "clean"
    assert len(result["vulnerabilities"]) == 0


@patch('subprocess.run')
def test_run_pip_audit_with_vulnerabilities(mock_run):
    """Test pip-audit with vulnerabilities."""
    mock_stdout = json.dumps({
        "dependencies": [
            {
                "name": "requests",
                "version": "2.25.0",
                "vulns": [
                    {
                        "id": "CVE-2021-12345",
                        "severity": "HIGH",
                        "description": "Security vulnerability",
                        "fix_versions": ["2.26.0"]
                    }
                ]
            }
        ]
    })

    mock_run.return_value = Mock(
        returncode=1,
        stdout=mock_stdout
    )

    result = run_pip_audit()

    assert result["status"] == "vulnerabilities"
    assert len(result["vulnerabilities"]) == 1
    assert result["vulnerabilities"][0]["package"] == "requests"
    assert result["vulnerabilities"][0]["severity"] == "high"
    assert result["summary"]["high"] == 1


@patch('subprocess.run')
def test_run_npm_audit_clean(mock_run, tmp_path):
    """Test npm audit with no vulnerabilities."""
    # Create fake package.json
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / "package.json").write_text('{"name": "test"}')

    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"vulnerabilities": {}}'
    )

    result = run_npm_audit(project_path)

    assert result["status"] == "clean"
    assert len(result["vulnerabilities"]) == 0


@patch('subprocess.run')
def test_run_npm_audit_with_vulnerabilities(mock_run, tmp_path):
    """Test npm audit with vulnerabilities."""
    # Create fake package.json
    project_path = tmp_path / "project"
    project_path.mkdir()
    (project_path / "package.json").write_text('{"name": "test"}')

    mock_stdout = json.dumps({
        "vulnerabilities": {
            "express": {
                "severity": "high",
                "via": ["CVE-2021-12345"],
                "fixAvailable": True,
                "range": ">=4.0.0 <4.17.3"
            },
            "lodash": {
                "severity": "moderate",
                "via": ["CVE-2021-67890"],
                "fixAvailable": True,
                "range": ">=4.0.0 <4.17.21"
            }
        }
    })

    mock_run.return_value = Mock(
        returncode=1,
        stdout=mock_stdout
    )

    result = run_npm_audit(project_path)

    assert result["status"] == "vulnerabilities"
    assert len(result["vulnerabilities"]) == 2
    assert result["summary"]["high"] == 1
    assert result["summary"]["moderate"] == 1


def test_run_npm_audit_no_package_json(tmp_path):
    """Test npm audit when package.json doesn't exist."""
    project_path = tmp_path / "project"
    project_path.mkdir()

    result = run_npm_audit(project_path)

    assert result["status"] == "no_package_json"
    assert len(result["vulnerabilities"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
