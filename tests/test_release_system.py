"""Tests for release system: versioning, changelog, gates."""

import pytest
from pathlib import Path
from src.orchestrator.version import Version, BumpType, determine_bump_type
from src.orchestrator.changelog import CommitEntry, group_commits, generate_changelog_entry
from src.orchestrator.release_gates import GateStatus, GateResult


class TestVersion:
    """Test semantic versioning."""

    def test_version_parse(self):
        """Test version string parsing."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease is None

    def test_version_parse_prerelease(self):
        """Test parsing with prerelease."""
        v = Version.parse("2.0.0-alpha.1")
        assert v.major == 2
        assert v.minor == 0
        assert v.patch == 0
        assert v.prerelease == "alpha.1"

    def test_version_str(self):
        """Test version to string."""
        v = Version(1, 2, 3)
        assert str(v) == "1.2.3"

        v_pre = Version(2, 0, 0, prerelease="beta.2")
        assert str(v_pre) == "2.0.0-beta.2"

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 4)
        v3 = Version(2, 0, 0)

        assert v1 < v2
        assert v2 < v3
        assert not v3 < v1

    def test_version_bump_major(self):
        """Test major version bump."""
        v = Version(1, 2, 3)
        v_new = v.bump(BumpType.MAJOR)

        assert v_new.major == 2
        assert v_new.minor == 0
        assert v_new.patch == 0

    def test_version_bump_minor(self):
        """Test minor version bump."""
        v = Version(1, 2, 3)
        v_new = v.bump(BumpType.MINOR)

        assert v_new.major == 1
        assert v_new.minor == 3
        assert v_new.patch == 0

    def test_version_bump_patch(self):
        """Test patch version bump."""
        v = Version(1, 2, 3)
        v_new = v.bump(BumpType.PATCH)

        assert v_new.major == 1
        assert v_new.minor == 2
        assert v_new.patch == 4

    def test_determine_bump_type_breaking(self):
        """Test bump type determination with breaking change."""
        commits = [
            "feat!: breaking API change",
            "fix: minor bug",
        ]
        assert determine_bump_type(commits) == BumpType.MAJOR

    def test_determine_bump_type_feature(self):
        """Test bump type determination with features."""
        commits = [
            "feat: add new command",
            "fix: resolve issue",
            "docs: update readme",
        ]
        assert determine_bump_type(commits) == BumpType.MINOR

    def test_determine_bump_type_fix(self):
        """Test bump type determination with only fixes."""
        commits = [
            "fix: resolve bug",
            "docs: typo",
        ]
        assert determine_bump_type(commits) == BumpType.PATCH


class TestChangelog:
    """Test changelog generation."""

    def test_commit_entry_parse(self):
        """Test conventional commit parsing."""
        entry = CommitEntry.parse("feat: add new feature")

        assert entry is not None
        assert entry.type == "feat"
        assert entry.scope is None
        assert entry.description == "add new feature"
        assert entry.breaking is False

    def test_commit_entry_parse_with_scope(self):
        """Test parsing with scope."""
        entry = CommitEntry.parse("fix(auth): resolve login bug")

        assert entry is not None
        assert entry.type == "fix"
        assert entry.scope == "auth"
        assert entry.description == "resolve login bug"

    def test_commit_entry_parse_breaking(self):
        """Test parsing breaking change."""
        entry = CommitEntry.parse("feat!: breaking change")

        assert entry is not None
        assert entry.type == "feat"
        assert entry.breaking is True

    def test_commit_entry_invalid(self):
        """Test invalid commit format."""
        entry = CommitEntry.parse("random commit message")
        assert entry is None

    def test_group_commits(self):
        """Test grouping commits by type."""
        commits = [
            CommitEntry("feat", None, "feature 1"),
            CommitEntry("feat", None, "feature 2"),
            CommitEntry("fix", None, "bug fix"),
            CommitEntry("docs", None, "documentation"),
        ]

        sections = group_commits(commits)

        assert "feat" in sections
        assert "fix" in sections
        assert "docs" in sections

        assert len(sections["feat"].commits) == 2
        assert len(sections["fix"].commits) == 1

    def test_generate_changelog_entry(self):
        """Test changelog entry generation."""
        commits = [
            CommitEntry("feat", "cli", "add new command", hash="abc1234"),
            CommitEntry("fix", None, "resolve bug", hash="def5678"),
        ]

        version = Version(1, 2, 0)
        entry = generate_changelog_entry(version, commits)

        assert "## [1.2.0]" in entry
        assert "### ✨ Features" in entry
        assert "### 🐛 Bug Fixes" in entry
        assert "**cli**: add new command" in entry
        assert "resolve bug" in entry


class TestReleaseGates:
    """Test quality gates."""

    def test_gate_result_passed(self):
        """Test gate result with pass/warn/skip."""
        pass_gate = GateResult("tests", GateStatus.PASS, "All tests passed", blocking=True)
        assert pass_gate.passed is True

        warn_gate = GateResult("hygiene", GateStatus.WARN, "Score below target", blocking=False)
        assert warn_gate.passed is True

        skip_gate = GateResult("security", GateStatus.SKIP, "Tool not installed", blocking=False)
        assert skip_gate.passed is True

    def test_gate_result_failed(self):
        """Test gate result with fail."""
        fail_gate = GateResult("tests", GateStatus.FAIL, "Tests failed", blocking=True)
        assert fail_gate.passed is False

    def test_gates_report_blocking_failures(self):
        """Test gates report with blocking failures."""
        from src.orchestrator.release_gates import GatesReport

        gates = [
            GateResult("tests", GateStatus.PASS, "OK", blocking=True),
            GateResult("hygiene", GateStatus.FAIL, "Failed", blocking=True),
            GateResult("security", GateStatus.WARN, "Warning", blocking=False),
        ]

        report = GatesReport(gates=gates, timestamp="2025-01-14T12:00:00", blocking_failures=1, warnings=1)

        assert report.all_passed is False
        assert report.blocking_failures == 1
        assert report.warnings == 1

    def test_gates_report_all_passed(self):
        """Test gates report with all passing."""
        from src.orchestrator.release_gates import GatesReport

        gates = [
            GateResult("tests", GateStatus.PASS, "OK", blocking=True),
            GateResult("hygiene", GateStatus.PASS, "OK", blocking=True),
        ]

        report = GatesReport(gates=gates, timestamp="2025-01-14T12:00:00", blocking_failures=0, warnings=0)

        assert report.all_passed is True
        assert "✅" in report.summary
