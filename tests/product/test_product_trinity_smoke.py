"""Smoke tests for Product Trinity workflow."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.orchestrator.agents import product_manager, ux_designer, qa


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_product_manager_generates_artifacts(temp_workspace):
    """Test that PM agent generates required artifacts."""
    result = product_manager.run(project_root=temp_workspace)

    assert result["success"]
    assert len(result["artifacts"]) == 3

    # Verify files exist
    assert (temp_workspace / "reports" / "PRD.md").exists()
    assert (temp_workspace / "reports" / "user_stories.md").exists()
    assert (temp_workspace / "reports" / "acceptance_criteria.md").exists()

    # Verify content
    prd_content = (temp_workspace / "reports" / "PRD.md").read_text()
    assert "Product Requirements Document" in prd_content
    assert "Vision" in prd_content
    assert "Goals" in prd_content


def test_ux_designer_generates_artifacts(temp_workspace):
    """Test that UX agent generates required artifacts."""
    result = ux_designer.run(project_root=temp_workspace)

    assert result["success"]
    assert len(result["artifacts"]) >= 4

    # Verify wireframes exist
    assert (temp_workspace / "wireframes" / "login.md").exists()
    assert (temp_workspace / "wireframes" / "dashboard.md").exists()

    # Verify design system exists
    assert (temp_workspace / "reports" / "design_system.md").exists()

    # Verify accessibility checklist exists
    assert (temp_workspace / "reports" / "accessibility_checklist.md").exists()

    # Verify content
    design_system = (temp_workspace / "reports" / "design_system.md").read_text()
    assert "Colors" in design_system
    assert "Typography" in design_system
    assert "WCAG" in design_system or "accessibility" in design_system.lower()


def test_qa_generates_validation_report(temp_workspace):
    """Test that QA agent generates validation report."""
    # First create acceptance criteria (QA depends on it)
    product_manager.run(project_root=temp_workspace)

    # Run QA
    result = qa.run(project_root=temp_workspace)

    assert result["success"]
    assert len(result["artifacts"]) >= 1

    # Verify QA report exists
    qa_report_path = temp_workspace / "reports" / "qa_validation_report.md"
    assert qa_report_path.exists()

    # Verify content structure
    qa_content = qa_report_path.read_text()
    assert "QA Validation Report" in qa_content
    assert "PASS" in qa_content or "FAIL" in qa_content
    assert "Summary" in qa_content

    # Verify pass rate is tracked
    assert "pass_rate" in result or "Pass Rate" in qa_content


def test_product_trinity_end_to_end(temp_workspace):
    """Test complete product trinity workflow."""
    # Step 1: PM generates requirements
    pm_result = product_manager.run(project_root=temp_workspace)
    assert pm_result["success"]

    # Step 2: UX creates designs
    ux_result = ux_designer.run(project_root=temp_workspace)
    assert ux_result["success"]

    # Step 3: QA validates (we skip Developer for this smoke test)
    qa_result = qa.run(project_root=temp_workspace)
    assert qa_result["success"]

    # Verify all artifacts present
    expected_artifacts = [
        "reports/PRD.md",
        "reports/user_stories.md",
        "reports/acceptance_criteria.md",
        "wireframes/login.md",
        "wireframes/dashboard.md",
        "reports/design_system.md",
        "reports/qa_validation_report.md",
    ]

    for artifact in expected_artifacts:
        assert (temp_workspace / artifact).exists(), f"Missing artifact: {artifact}"


def test_qa_pass_fail_tracking(temp_workspace):
    """Test that QA tracks pass/fail metrics."""
    product_manager.run(project_root=temp_workspace)
    result = qa.run(project_root=temp_workspace)

    # Verify pass/fail metrics in result
    assert "pass_rate" in result
    assert "total_criteria" in result
    assert "passed" in result
    assert "failed" in result

    assert result["pass_rate"] > 0
    assert result["total_criteria"] > 0
    assert result["passed"] > 0


def test_artifacts_have_meaningful_content(temp_workspace):
    """Test that generated artifacts have actual content, not just templates."""
    product_manager.run(project_root=temp_workspace)

    # Check PRD has sections
    prd = (temp_workspace / "reports" / "PRD.md").read_text()
    assert len(prd) > 100  # Not just a stub
    assert "Vision" in prd
    assert "Goals" in prd
    assert "Success Metrics" in prd

    # Check user stories follow format
    stories = (temp_workspace / "reports" / "user_stories.md").read_text()
    assert "As a" in stories  # User story format
    assert "I want" in stories
    assert "So that" in stories

    # Check acceptance criteria use Given/When/Then
    criteria = (temp_workspace / "reports" / "acceptance_criteria.md").read_text()
    assert "Given" in criteria
    assert "When" in criteria
    assert "Then" in criteria
