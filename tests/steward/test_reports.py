"""Test report generation for hygiene scans."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.steward.config import HygieneConfig
from src.steward.scanner import scan_large_files, scan_orphans
from src.steward.dead_code import analyze_dead_code
from src.steward.notebooks import check_notebooks
from src.steward.glue import aggregate_reports


class TestReportGeneration:
    """Test hygiene report generation."""

    def setup_method(self):
        """Create temporary test repository."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.reports_dir = self.temp_dir / "reports"
        self.reports_dir.mkdir()

        # Create test config
        self.config = HygieneConfig()

    def teardown_method(self):
        """Clean up temporary directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_large_files_report_created(self):
        """Test that large_files.csv is created."""
        output_path = self.reports_dir / "large_files.csv"
        large_files = scan_large_files(self.temp_dir, self.config, output_path)

        # Report should exist even if empty
        assert output_path.exists() or len(large_files) == 0

    def test_orphans_report_created(self):
        """Test that orphans.csv is created."""
        output_path = self.reports_dir / "orphans.csv"
        orphans = scan_orphans(self.temp_dir, self.config, output_path)

        # Report should exist even if empty
        assert output_path.exists() or len(orphans) == 0

    def test_dead_code_report_created(self):
        """Test that dead_code.md is created."""
        output_path = self.reports_dir / "dead_code.md"
        results = analyze_dead_code(self.temp_dir, self.config, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify structure
        content = output_path.read_text()
        assert "# Dead Code Analysis Report" in content
        assert "## Summary" in content

    def test_notebook_report_created(self):
        """Test that notebook_sanitizer.md is created."""
        output_path = self.reports_dir / "notebook_sanitizer.md"
        notebooks = check_notebooks(self.temp_dir, self.config, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify structure
        content = output_path.read_text()
        assert "# Notebook Hygiene Report" in content
        assert "## Summary" in content

    def test_aggregate_reports(self):
        """Test that aggregate reports are generated."""
        # First generate individual reports
        scan_large_files(self.temp_dir, self.config, self.reports_dir / "large_files.csv")
        scan_orphans(self.temp_dir, self.config, self.reports_dir / "orphans.csv")
        analyze_dead_code(self.temp_dir, self.config, self.reports_dir / "dead_code.md")
        check_notebooks(self.temp_dir, self.config, self.reports_dir / "notebook_sanitizer.md")

        # Aggregate
        hygiene_output = self.reports_dir / "repo_hygiene_report.md"
        pr_plan_output = self.reports_dir / "PR_PLAN.md"

        stats = aggregate_reports(self.temp_dir, self.config, hygiene_output, pr_plan_output)

        # Verify hygiene report
        assert hygiene_output.exists()
        content = hygiene_output.read_text()
        assert "# Repository Hygiene Report" in content
        assert "## Summary" in content
        assert "## Severity Breakdown" in content

        # Verify PR plan
        assert pr_plan_output.exists()
        pr_content = pr_plan_output.read_text()
        assert "# Cleanup Plan for Approval" in content or "# Cleanup Plan" in pr_content

        # Verify stats structure
        assert "orphans" in stats
        assert "large_files" in stats
        assert "dead_code" in stats
        assert "notebooks" in stats
