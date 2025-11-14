"""Tests for Skills Engine prerequisite validation."""

import pytest
from src.orchestrator.skills import SkillsEngine, SkillRef


@pytest.fixture
def engine():
    """Create SkillsEngine instance."""
    return SkillsEngine()


def test_validate_prereqs_all_available(engine):
    """Test validation when all prerequisites are available."""
    # Create a skill with available prereqs (standard library modules)
    skill = SkillRef(
        name="test_skill",
        keywords=["test"],
        requires=["os", "sys", "pathlib"],  # Standard library modules
        snippets={},
    )

    available, missing = engine.validate_prereqs([skill])

    assert len(available) == 1
    assert available[0].name == "test_skill"
    assert len(missing) == 0


def test_validate_prereqs_missing(engine):
    """Test validation when prerequisites are missing."""
    # Create a skill with missing prereqs
    skill = SkillRef(
        name="test_skill_missing",
        keywords=["test"],
        requires=["nonexistent_module_12345", "another_fake_module_67890"],
        snippets={},
    )

    available, missing = engine.validate_prereqs([skill])

    assert len(available) == 0
    assert len(missing) == 2

    # Check that missing prereqs have proper structure
    assert all(m.skill_name == "test_skill_missing" for m in missing)
    assert any("nonexistent_module_12345" in m.module_path for m in missing)
    assert all(m.hint != "" for m in missing)


def test_validate_prereqs_hint_generation(engine):
    """Test that helpful hints are generated for missing prereqs."""
    skill = SkillRef(
        name="test_skill",
        keywords=["test"],
        requires=["orchestrator.mcp.data.load_csv", "numpy"],
        snippets={},
    )

    _, missing = engine.validate_prereqs([skill])

    # Should have hints
    assert all(m.hint != "" for m in missing)

    # MCP module should have specific hint
    mcp_missing = [m for m in missing if "orchestrator.mcp" in m.module_path]
    if mcp_missing:
        assert "MCP" in mcp_missing[0].hint or "mcp" in mcp_missing[0].hint.lower()

    # Non-MCP module should suggest pip install
    non_mcp_missing = [m for m in missing if "orchestrator.mcp" not in m.module_path]
    if non_mcp_missing:
        assert "pip install" in non_mcp_missing[0].hint


def test_validate_prereqs_partial(engine):
    """Test validation with mix of available and missing prereqs."""
    skill1 = SkillRef(
        name="available_skill",
        keywords=["test"],
        requires=["os", "sys"],  # Available
        snippets={},
    )

    skill2 = SkillRef(
        name="missing_skill",
        keywords=["test"],
        requires=["fake_module_xyz"],  # Missing
        snippets={},
    )

    available, missing = engine.validate_prereqs([skill1, skill2])

    assert len(available) == 1
    assert available[0].name == "available_skill"
    assert len(missing) == 1
    assert missing[0].skill_name == "missing_skill"


def test_check_module_available_stdlib(engine):
    """Test that standard library modules are detected as available."""
    assert engine._check_module_available("os")
    assert engine._check_module_available("sys")
    assert engine._check_module_available("pathlib")
    assert engine._check_module_available("json")


def test_check_module_available_missing(engine):
    """Test that nonexistent modules are detected as missing."""
    assert not engine._check_module_available("nonexistent_module_12345")
    assert not engine._check_module_available("fake.module.path")


def test_summarize_telemetry(engine):
    """Test telemetry summary generation."""
    skill1 = SkillRef(name="skill1", keywords=[], requires=["os"], snippets={})
    skill2 = SkillRef(name="skill2", keywords=[], requires=["fake_mod"], snippets={})

    matched = [skill1, skill2]
    available, missing = engine.validate_prereqs(matched)

    summary = engine.summarize(matched, available, missing)

    assert summary["match_count"] == 2
    assert summary["available_count"] == 1
    assert summary["missing_count"] == 1
    assert "skill1" in summary["skills_matched"]
    assert "skill2" in summary["skills_matched"]
    assert "skill1" in summary["skills_available"]
    assert "skill2" in summary["skills_missing_prereqs"]
    assert len(summary["missing_modules"]) == 1


def test_get_match_result_convenience(engine):
    """Test convenience method for matching and validating."""
    result = engine.get_match_result("forecast time series seasonal")

    assert result.matched is not None
    assert result.available is not None
    assert result.missing_prereqs is not None

    # Should have matched time_series_analytics
    skill_names = [s.name for s in result.matched]
    assert "time_series_analytics" in skill_names


def test_missing_prereq_structure(engine):
    """Test that MissingPrereq has all required fields."""
    skill = SkillRef(
        name="test",
        keywords=[],
        requires=["nonexistent_mod"],
        snippets={},
    )

    _, missing = engine.validate_prereqs([skill])

    assert len(missing) == 1
    m = missing[0]

    # Verify all fields present
    assert m.module_path == "nonexistent_mod"
    assert m.skill_name == "test"
    assert m.hint != ""
    assert isinstance(m.hint, str)
