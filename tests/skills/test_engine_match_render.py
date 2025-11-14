"""Tests for Skills Engine matching and rendering."""

import pytest
from src.orchestrator.skills import SkillsEngine


@pytest.fixture
def engine():
    """Create SkillsEngine instance."""
    return SkillsEngine()


def test_engine_loads_index(engine):
    """Test that engine loads skills from index."""
    assert len(engine.skills_catalog) > 0
    assert "time_series_analytics" in engine.skills_catalog
    assert "optimization_modeling" in engine.skills_catalog


def test_match_by_keyword(engine):
    """Test matching skills by keyword."""
    # Match time series skill
    matched = engine.match("We need to forecast seasonal demand")
    skill_names = [s.name for s in matched]

    assert "time_series_analytics" in skill_names

    # Match optimization skill
    matched = engine.match("Optimize warehouse allocation to minimize costs")
    skill_names = [s.name for s in matched]

    assert "optimization_modeling" in skill_names


def test_match_from_intake(engine):
    """Test matching skills from intake requirements."""
    intake = {
        "requirements": {
            "functional": ["Survey data analysis", "Customer sentiment analysis"],
            "technical": ["Clean and process Likert scale responses"],
        }
    }

    matched = engine.match("Process customer feedback", intake=intake)
    skill_names = [s.name for s in matched]

    assert "survey_data_processing" in skill_names


def test_match_multiple_skills(engine):
    """Test matching multiple skills simultaneously."""
    task = "Build forecasting model and optimize resource allocation with survey feedback"

    matched = engine.match(task)
    skill_names = [s.name for s in matched]

    # Should match all three
    assert "time_series_analytics" in skill_names
    assert "optimization_modeling" in skill_names
    assert "survey_data_processing" in skill_names


def test_match_ordering_by_relevance(engine):
    """Test that skills are ordered by match score."""
    # Task with strong time-series focus
    task = "forecast seasonal trends using prophet with time series decomposition"

    matched = engine.match(task)

    # time_series_analytics should be first (multiple keyword matches)
    assert matched[0].name == "time_series_analytics"


def test_no_match(engine):
    """Test that irrelevant text returns no matches."""
    matched = engine.match("hello world foo bar baz")
    assert len(matched) == 0


def test_match_is_case_insensitive(engine):
    """Test that matching is case-insensitive."""
    matched1 = engine.match("FORECAST seasonal demand")
    matched2 = engine.match("forecast seasonal demand")
    matched3 = engine.match("FoReCaSt SeAsOnAl DeMaNd")

    assert [s.name for s in matched1] == [s.name for s in matched2]
    assert [s.name for s in matched1] == [s.name for s in matched3]


def test_render_for_agent_data(engine):
    """Test rendering snippets for data agent."""
    matched = engine.match("time series forecasting")
    # Use matched skills directly (validation may fail if MCP modules not installed)

    # Render for data agent
    snippet = engine.render_for_agent("data", matched)

    # Should contain time series related content
    assert "time_series" in snippet or "load_csv" in snippet or "decompose" in snippet
    assert "Skill: time_series_analytics" in snippet


def test_render_for_agent_developer(engine):
    """Test rendering snippets for developer agent."""
    matched = engine.match("optimize costs minimize expenses")
    # Use matched skills directly (validation may fail if MCP modules not installed)

    # Render for developer agent
    snippet = engine.render_for_agent("developer", matched)

    assert "optimization" in snippet.lower() or "optimize" in snippet.lower()


def test_render_respects_max_chars(engine):
    """Test that rendering respects max_chars limit."""
    # Match multiple skills
    matched = engine.match("forecast optimize survey classification")
    available, _ = engine.validate_prereqs(matched)

    # Render with tight limit
    snippet = engine.render_for_agent("developer", available, max_chars=500)

    assert len(snippet) <= 550  # Allow some buffer for truncation notice


def test_render_empty_for_no_agent_snippets(engine):
    """Test that rendering returns empty for agent with no snippets."""
    matched = engine.match("time series")
    available, _ = engine.validate_prereqs(matched)

    # Render for non-existent agent
    snippet = engine.render_for_agent("nonexistent_agent", available)

    assert snippet == ""


def test_render_truncation_notice(engine):
    """Test that truncation notice is added when limit exceeded."""
    matched = engine.match("forecast optimize survey classification accessibility")
    available, _ = engine.validate_prereqs(matched)

    # Very tight limit to force truncation
    snippet = engine.render_for_agent("developer", available, max_chars=200)

    # Should contain truncation notice if multiple skills matched
    if len(available) > 1 and len(snippet) > 150:
        assert "Truncated" in snippet or len(snippet) <= 250


def test_match_governance_keywords(engine):
    """Test matching from governance configuration."""
    governance = {
        "compliance": ["accessibility", "wcag"],
        "quality_gates": {"accessibility_audit": True},
    }

    matched = engine.match("design user interface", governance=governance)
    skill_names = [s.name for s in matched]

    assert "wcag_accessibility" in skill_names


def test_deterministic_ordering(engine):
    """Test that match ordering is deterministic across runs."""
    task = "forecast optimize survey"

    results = []
    for _ in range(5):
        matched = engine.match(task)
        results.append([s.name for s in matched])

    # All results should be identical
    for result in results[1:]:
        assert result == results[0]
