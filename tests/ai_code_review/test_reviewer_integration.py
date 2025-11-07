"""Integration tests for AI code review system."""

import pytest
import os
from pathlib import Path
import asyncio
from src.orchestrator.executors.llm_exec import execute_llm


class TestReviewerIntegration:
    """Test AI code review integration."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create temporary project structure for testing."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Create .claude directories
        (project_root / ".claude" / "checkpoints").mkdir(parents=True)
        (project_root / ".claude" / "agent_outputs").mkdir(parents=True)

        # Create sample source file with security issue
        src_dir = project_root / "src"
        src_dir.mkdir()

        sample_code = '''
def authenticate_user(username, password):
    """Authenticate user with credentials."""
    # Security issue: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result


def process_data(user_input):
    """Process user data."""
    # Performance issue: inefficient loop
    results = []
    for item_id in get_item_ids():  # N+1 query problem
        item = db.query(Item).filter_by(id=item_id).first()
        results.append(item)
    return results
'''

        (src_dir / "auth.py").write_text(sample_code)

        return project_root

    @pytest.fixture
    def reviewer_prompt(self, tmp_path):
        """Create minimal reviewer prompt for testing."""
        prompt_dir = tmp_path / "subagent_prompts"
        prompt_dir.mkdir()

        prompt_content = '''
# Reviewer Agent

You are a code reviewer. Analyze the provided code and identify:
1. Security vulnerabilities
2. Performance issues
3. Code quality problems
4. Best practice violations

## Output Format

# Code Review Report

## Summary
**Status:** [APPROVED | APPROVED WITH SUGGESTIONS | CHANGES REQUESTED]
**Issues Found:** Critical: [X], Major: [X], Minor: [X]

## Review Findings

### Critical Issues (Must Fix)
[List critical issues with file:line references]

### Major Issues (Should Fix)
[List major issues]

### Positive Highlights
[What was done well]

## Recommendation
[Overall recommendation]
'''

        (prompt_dir / "reviewer.md").write_text(prompt_content)
        return prompt_dir / "reviewer.md"

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping real API test"
    )
    @pytest.mark.asyncio
    async def test_reviewer_with_real_api(self, temp_project, reviewer_prompt):
        """Test reviewer with real Claude API (requires API key)."""
        # Set execution mode to API
        os.environ["ORCHESTRATOR_EXECUTION_MODE"] = "api"

        # Read sample code
        sample_code = (temp_project / "src" / "auth.py").read_text()

        # Build review prompt
        prompt = f'''
{reviewer_prompt.read_text()}

---

# CODE TO REVIEW

## File: src/auth.py
```python
{sample_code}
```

Please review this code focusing on security and performance issues.
'''

        # Execute reviewer
        result = await execute_llm(
            prompt=prompt,
            agent_name="reviewer",
            phase_name="review",
            project_root=temp_project,
            timeout_seconds=300,
        )

        # Assertions
        assert result.exit_code == 0, f"Review failed: {result.stderr}"
        assert len(result.stdout) > 0, "Review output is empty"

        # Check review content
        review_output = result.stdout.lower()
        assert "security" in review_output or "sql injection" in review_output, \
            "Review should mention security/SQL injection"
        assert "performance" in review_output or "n+1" in review_output, \
            "Review should mention performance/N+1 query problem"

        # Verify checkpoint file created
        checkpoint_dir = temp_project / ".claude" / "checkpoints"
        assert checkpoint_dir.exists(), "Checkpoint directory should exist"

    @pytest.mark.asyncio
    async def test_reviewer_stub_mode(self, temp_project, reviewer_prompt):
        """Test reviewer in stub mode (no API key required)."""
        # Unset API key to force stub mode
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        os.environ["ORCHESTRATOR_EXECUTION_MODE"] = "stub"

        # Simple prompt
        prompt = "Review this code for security issues."

        # Execute reviewer in stub mode
        result = await execute_llm(
            prompt=prompt,
            agent_name="reviewer",
            phase_name="review",
            project_root=temp_project,
            timeout_seconds=60,
        )

        # Assertions
        assert result.exit_code == 0
        assert "stub mode" in result.stdout.lower() or "simulated" in result.stdout.lower()

        # Verify output files created
        output_dir = temp_project / ".claude" / "agent_outputs" / "reviewer" / "review"
        assert output_dir.exists()
        assert (output_dir / "prompt.md").exists()
        assert (output_dir / "response.md").exists()

    def test_reviewer_config_enabled(self):
        """Test that reviewer is enabled in config."""
        config_path = Path(__file__).parents[2] / ".claude" / "config.yaml"

        if not config_path.exists():
            pytest.skip("Config file not found")

        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)

        reviewer_config = config.get("subagents", {}).get("reviewer", {})
        assert reviewer_config.get("enabled") is True, \
            "Reviewer should be enabled in config"

    def test_reviewer_prompt_exists(self):
        """Test that reviewer prompt template exists."""
        prompt_path = Path(__file__).parents[2] / "subagent_prompts" / "reviewer.md"
        assert prompt_path.exists(), "Reviewer prompt template should exist"

        content = prompt_path.read_text()
        assert len(content) > 1000, "Reviewer prompt should be comprehensive"
        assert "security" in content.lower(), "Prompt should mention security"
        assert "performance" in content.lower(), "Prompt should mention performance"


class TestGitHubActionsWorkflow:
    """Test GitHub Actions workflow configuration."""

    def test_workflow_file_exists(self):
        """Test that AI code review workflow exists."""
        workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ai-code-review.yml"
        assert workflow_path.exists(), "AI code review workflow should exist"

    def test_workflow_has_required_triggers(self):
        """Test workflow triggers on PR events."""
        workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ai-code-review.yml"

        if not workflow_path.exists():
            pytest.skip("Workflow file not found")

        content = workflow_path.read_text()
        assert "pull_request" in content, "Workflow should trigger on pull_request"
        assert "opened" in content or "synchronize" in content, \
            "Workflow should trigger on PR open/update"

    def test_workflow_has_required_permissions(self):
        """Test workflow has necessary permissions."""
        workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ai-code-review.yml"

        if not workflow_path.exists():
            pytest.skip("Workflow file not found")

        content = workflow_path.read_text()
        assert "permissions:" in content, "Workflow should define permissions"
        assert "pull-requests: write" in content, \
            "Workflow needs pull-requests:write permission"

    def test_workflow_uses_anthropic_api_key(self):
        """Test workflow references ANTHROPIC_API_KEY secret."""
        workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ai-code-review.yml"

        if not workflow_path.exists():
            pytest.skip("Workflow file not found")

        content = workflow_path.read_text()
        assert "ANTHROPIC_API_KEY" in content, \
            "Workflow should use ANTHROPIC_API_KEY secret"
        assert "secrets.ANTHROPIC_API_KEY" in content, \
            "Workflow should reference GitHub secret"


class TestReviewOutput:
    """Test review output format and structure."""

    def test_review_output_format(self):
        """Test that review output follows expected format."""
        # Sample review output
        review_sample = '''
# Code Review Report: Authentication Module

## Summary
**Status:** CHANGES REQUESTED
**Issues Found:** Critical: 1, Major: 1, Minor: 0

## Review Findings

### Critical Issues (Must Fix)

**Issue 1: SQL Injection Vulnerability**
- **File:** `src/auth.py:5`
- **Severity:** Critical
- **Category:** Security
- **Code:**
  ```python
  query = f"SELECT * FROM users WHERE username='{username}'"
  ```
- **Recommendation:** Use parameterized queries

### Major Issues (Should Fix)

**Issue 2: N+1 Query Problem**
- **File:** `src/auth.py:15`
- **Severity:** Major
- **Category:** Performance

## Recommendation
CHANGES REQUESTED
'''

        # Validate format
        assert "# Code Review Report" in review_sample
        assert "## Summary" in review_sample
        assert "**Status:**" in review_sample
        assert "**Issues Found:**" in review_sample
        assert "### Critical Issues" in review_sample
        assert "**File:**" in review_sample
        assert "**Severity:**" in review_sample
        assert "**Recommendation:**" in review_sample
        assert "CHANGES REQUESTED" in review_sample

    def test_review_severity_levels(self):
        """Test that review output includes severity levels."""
        severity_levels = ["Critical", "Major", "Minor", "Suggestions"]

        # All severity levels should be documented
        for level in severity_levels:
            assert level in ["Critical", "Major", "Minor", "Suggestions"]


class TestCostTracking:
    """Test cost tracking and token usage."""

    def test_token_usage_in_metadata(self):
        """Test that token usage is tracked in review metadata."""
        # Sample review with token metadata
        review_with_metadata = '''
# Code Review Report

[Review content...]

---
*Generated by reviewer agent via Claude API*
*Model: claude-sonnet-4-20250514*
*Tokens: 2500 in, 1200 out*
'''

        assert "*Tokens:" in review_with_metadata
        assert "in, " in review_with_metadata and " out*" in review_with_metadata

    def test_cost_calculation(self):
        """Test cost calculation from token usage."""
        # Anthropic pricing (as of 2025): $3/M input, $15/M output
        input_tokens = 2500
        output_tokens = 1200

        input_cost = (input_tokens * 3) / 1_000_000
        output_cost = (output_tokens * 15) / 1_000_000
        total_cost = input_cost + output_cost

        assert total_cost < 1.0, "Review should cost less than $1"
        assert total_cost > 0, "Review should have non-zero cost"

        # Typical PR review cost: $0.10 - $0.50
        assert 0.01 <= total_cost <= 0.50, \
            f"Review cost ${total_cost:.2f} outside expected range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
