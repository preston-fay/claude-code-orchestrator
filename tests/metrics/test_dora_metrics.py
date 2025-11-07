"""
Unit tests for DORA metrics calculator.

Tests deployment frequency, lead time, MTTR, and change failure rate calculations.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.orchestrator.metrics.dora_metrics import (
    DORAMetricsCalculator,
    DeploymentFrequencyMetrics,
    LeadTimeMetrics,
    MTTRMetrics,
    ChangeFailureRateMetrics
)


class TestDORAMetricsCalculator:
    """Test DORAMetricsCalculator class"""

    def test_init(self, temp_metrics_dir):
        """Test calculator initialization"""
        calculator = DORAMetricsCalculator(
            repo_path=Path.cwd(),
            days_back=30,
            project_root=temp_metrics_dir.parent.parent
        )

        assert calculator.repo_path == Path.cwd()
        assert calculator.days_back == 30
        assert calculator.output_dir == temp_metrics_dir / "dora"
        assert calculator.output_dir.exists()

    @patch('subprocess.run')
    def test_run_git_command(self, mock_run, temp_metrics_dir):
        """Test git command execution"""
        mock_run.return_value = Mock(stdout="test output", returncode=0)

        calculator = DORAMetricsCalculator(project_root=temp_metrics_dir.parent.parent)
        result = calculator._run_git_command(['status'])

        assert result == "test output"
        mock_run.assert_called_once()

    def test_parse_semver(self, temp_metrics_dir):
        """Test semantic version parsing"""
        calculator = DORAMetricsCalculator(project_root=temp_metrics_dir.parent.parent)

        assert calculator._parse_semver("v1.2.3") == (1, 2, 3)
        assert calculator._parse_semver("1.2.3") == (1, 2, 3)
        assert calculator._parse_semver("v1.0.0-alpha") == (1, 0, 0)
        assert calculator._parse_semver("invalid") is None

    def test_is_hotfix(self, temp_metrics_dir):
        """Test hotfix detection"""
        calculator = DORAMetricsCalculator(project_root=temp_metrics_dir.parent.parent)

        # Patch version bump within 48h = hotfix
        assert calculator._is_hotfix("v1.2.3", "v1.2.2", timedelta(hours=24)) is True

        # Patch version bump after 48h = not hotfix
        assert calculator._is_hotfix("v1.2.3", "v1.2.2", timedelta(hours=72)) is False

        # Minor version bump = not hotfix
        assert calculator._is_hotfix("v1.3.0", "v1.2.5", timedelta(hours=24)) is False

        # Tag with 'hotfix' keyword = hotfix
        assert calculator._is_hotfix("v1.2.3-hotfix", "v1.2.2", timedelta(hours=72)) is True

    @patch('subprocess.run')
    def test_collect_deployment_frequency(self, mock_run, temp_metrics_dir):
        """Test deployment frequency collection"""
        mock_run.return_value = Mock(
            stdout="2025-10-15 16:34:47 -0400|8f7674b| (tag: v1.4.0)\n2025-09-20 14:22:13 -0400|a1b2c3d| (tag: v1.3.0)",
            returncode=0
        )

        calculator = DORAMetricsCalculator(days_back=30, project_root=temp_metrics_dir.parent.parent)
        metrics = calculator.collect_deployment_frequency()

        assert metrics.metric == "deployment_frequency"
        assert metrics.summary["total_deployments"] == 2
        assert metrics.summary["deploys_per_week"] > 0
        assert metrics.summary["rating"] in ["elite", "high", "medium", "low"]

    @patch('subprocess.run')
    def test_collect_deployment_frequency_no_deployments(self, mock_run, temp_metrics_dir):
        """Test deployment frequency with no deployments"""
        mock_run.return_value = Mock(stdout="", returncode=0)

        calculator = DORAMetricsCalculator(days_back=30, project_root=temp_metrics_dir.parent.parent)
        metrics = calculator.collect_deployment_frequency()

        assert metrics.summary["total_deployments"] == 0
        assert metrics.summary["deploys_per_week"] == 0
        assert metrics.summary["rating"] == "low"

    @patch('subprocess.run')
    def test_calculate_lead_time(self, mock_run, temp_metrics_dir):
        """Test lead time calculation"""
        # Mock git commands for tags and commits
        def mock_run_side_effect(cmd, *args, **kwargs):
            result = Mock(returncode=0)

            if "--tags" in cmd:
                result.stdout = "2025-10-15 16:34:47 -0400|8f7674b| (tag: v1.4.0)\n2025-09-20 14:22:13 -0400|a1b2c3d| (tag: v1.3.0)"
            elif "rev-list" in cmd:
                result.stdout = "abc123\ndef456\nghi789"
            elif "show" in cmd and "-s" in cmd:
                result.stdout = "2025-10-14 10:00:00 -0400"
            else:
                result.stdout = ""

            return result

        mock_run.side_effect = mock_run_side_effect

        calculator = DORAMetricsCalculator(days_back=90, project_root=temp_metrics_dir.parent.parent)
        metrics = calculator.calculate_lead_time()

        assert metrics.metric == "lead_time"
        assert isinstance(metrics.summary.get("median_lead_time_hours"), (int, float))

    @patch('subprocess.run')
    def test_calculate_mttr(self, mock_run, temp_metrics_dir):
        """Test MTTR calculation"""
        def mock_run_side_effect(cmd, *args, **kwargs):
            result = Mock(returncode=0)

            if "--tags" in cmd:
                # v1.4.1 is hotfix (patch bump within 48h)
                result.stdout = "2025-10-16 10:00:00 -0400|8f7674b| (tag: v1.4.1)\n2025-10-15 16:34:47 -0400|8f7674a| (tag: v1.4.0)"
            elif "rev-list" in cmd:
                result.stdout = "abc123"
            else:
                result.stdout = ""

            return result

        mock_run.side_effect = mock_run_side_effect

        calculator = DORAMetricsCalculator(days_back=30, project_root=temp_metrics_dir.parent.parent)
        metrics = calculator.calculate_mttr()

        assert metrics.metric == "mttr"
        assert isinstance(metrics.summary.get("total_incidents"), int)

    @patch('subprocess.run')
    def test_calculate_change_failure_rate(self, mock_run, temp_metrics_dir):
        """Test change failure rate calculation"""
        def mock_run_side_effect(cmd, *args, **kwargs):
            result = Mock(returncode=0)

            if "--tags" in cmd:
                result.stdout = "2025-10-16 10:00:00 -0400|8f7674b| (tag: v1.4.1)\n2025-10-15 16:34:47 -0400|8f7674a| (tag: v1.4.0)\n2025-09-20 14:22:13 -0400|a1b2c3d| (tag: v1.3.0)"
            else:
                result.stdout = ""

            return result

        mock_run.side_effect = mock_run_side_effect

        calculator = DORAMetricsCalculator(days_back=90, project_root=temp_metrics_dir.parent.parent)
        metrics = calculator.calculate_change_failure_rate()

        assert metrics.metric == "change_failure_rate"
        assert isinstance(metrics.summary.get("failure_rate"), (int, float))
        assert 0 <= metrics.summary["failure_rate"] <= 100

    def test_rate_dora_metric(self, temp_metrics_dir):
        """Test DORA metric rating"""
        calculator = DORAMetricsCalculator(project_root=temp_metrics_dir.parent.parent)

        # Deployment frequency
        assert calculator._rate_dora_metric("deployment_frequency", 2.0) == "elite"
        assert calculator._rate_dora_metric("deployment_frequency", 0.5) == "high"
        assert calculator._rate_dora_metric("deployment_frequency", 0.1) == "medium"
        assert calculator._rate_dora_metric("deployment_frequency", 0.01) == "low"

        # Lead time (hours)
        assert calculator._rate_dora_metric("lead_time", 0.5) == "elite"
        assert calculator._rate_dora_metric("lead_time", 12) == "high"
        assert calculator._rate_dora_metric("lead_time", 100) == "medium"
        assert calculator._rate_dora_metric("lead_time", 200) == "low"

        # MTTR (hours)
        assert calculator._rate_dora_metric("mttr", 0.5) == "elite"
        assert calculator._rate_dora_metric("mttr", 12) == "high"
        assert calculator._rate_dora_metric("mttr", 48) == "medium"
        assert calculator._rate_dora_metric("mttr", 200) == "low"

        # Change failure rate (percentage)
        assert calculator._rate_dora_metric("change_failure_rate", 5) == "elite"
        assert calculator._rate_dora_metric("change_failure_rate", 10) == "high"
        assert calculator._rate_dora_metric("change_failure_rate", 20) == "medium"
        assert calculator._rate_dora_metric("change_failure_rate", 50) == "low"

    @patch('subprocess.run')
    def test_json_output(self, mock_run, temp_metrics_dir):
        """Test JSON file output"""
        mock_run.return_value = Mock(
            stdout="2025-10-15 16:34:47 -0400|8f7674b| (tag: v1.4.0)",
            returncode=0
        )

        calculator = DORAMetricsCalculator(days_back=30, project_root=temp_metrics_dir.parent.parent)
        calculator.collect_deployment_frequency()

        # Check JSON file was created
        output_file = temp_metrics_dir / "dora" / "deployments.json"
        assert output_file.exists()

        # Validate JSON structure
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert data["metric"] == "deployment_frequency"
        assert "period" in data
        assert "collection_timestamp" in data
        assert "deployments" in data
        assert "summary" in data
        assert "total_deployments" in data["summary"]

    def test_edge_cases(self, temp_metrics_dir):
        """Test edge cases and error handling"""
        calculator = DORAMetricsCalculator(project_root=temp_metrics_dir.parent.parent)

        # Test with invalid semver
        assert calculator._parse_semver("not-a-version") is None
        assert calculator._parse_semver("") is None

        # Test with None values
        assert calculator._is_hotfix("v1.0.0", None, timedelta(hours=1)) is False
        assert calculator._is_hotfix(None, "v1.0.0", timedelta(hours=1)) is False
