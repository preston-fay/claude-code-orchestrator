"""Tests for intake schema validation."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.intake_loader import (
    load_intake_yaml,
    validate_intake,
    get_template_path,
    list_templates,
)


class TestIntakeSchema:
    """Test intake schema and template validation."""

    def test_list_templates(self):
        """Test that templates can be listed."""
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "webapp" in templates
        assert "analytics" in templates
        assert "ml" in templates

    def test_get_webapp_template(self):
        """Test getting webapp template path."""
        path = get_template_path("webapp")
        assert path.exists()
        assert path.name == "starter.webapp.yaml"

    def test_get_analytics_template(self):
        """Test getting analytics template path."""
        path = get_template_path("analytics")
        assert path.exists()
        assert path.name == "starter.analytics.yaml"

    def test_get_ml_template(self):
        """Test getting ml template path."""
        path = get_template_path("ml")
        assert path.exists()
        assert path.name == "starter.ml.yaml"

    def test_unknown_template_raises(self):
        """Test that unknown template type raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            get_template_path("nonexistent")

    def test_validate_webapp_template(self):
        """Test that webapp template is valid against schema."""
        path = get_template_path("webapp")
        valid, error = validate_intake(path)
        assert valid, f"Validation failed: {error}"

    def test_validate_analytics_template(self):
        """Test that analytics template is valid against schema."""
        path = get_template_path("analytics")
        valid, error = validate_intake(path)
        assert valid, f"Validation failed: {error}"

    def test_validate_ml_template(self):
        """Test that ml template is valid against schema."""
        path = get_template_path("ml")
        valid, error = validate_intake(path)
        assert valid, f"Validation failed: {error}"

    def test_load_webapp_template(self):
        """Test loading and accessing webapp template config."""
        path = get_template_path("webapp")
        config = load_intake_yaml(path)

        assert config.get("project.name") is not None
        assert config.get("project.type") == "webapp"
        assert isinstance(config.get("goals.primary"), list)
        assert len(config.get("goals.primary")) > 0

    def test_load_analytics_template(self):
        """Test loading and accessing analytics template config."""
        path = get_template_path("analytics")
        config = load_intake_yaml(path)

        assert config.get("project.type") == "analytics"
        assert config.get("analytics_ml.required") is True
        assert isinstance(config.get("data.sources"), list)

    def test_load_ml_template(self):
        """Test loading and accessing ml template config."""
        path = get_template_path("ml")
        config = load_intake_yaml(path)

        assert config.get("project.type") == "ml"
        assert config.get("analytics_ml.required") is True
        assert isinstance(config.get("analytics_ml.model_types"), list)

    def test_template_has_required_sections(self):
        """Test that templates have all required sections."""
        for template_type in list_templates():
            path = get_template_path(template_type)
            config = load_intake_yaml(path)

            # Required top-level sections
            assert "project" in config.data
            assert "goals" in config.data

            # Required nested fields
            assert config.get("project.name") is not None
            assert config.get("project.type") is not None
            assert config.get("goals.primary") is not None

    def test_nonexistent_file_validation_fails(self):
        """Test that validation fails for nonexistent file."""
        path = Path("nonexistent.yaml")
        valid, error = validate_intake(path)
        assert not valid
        assert "not found" in error.lower()

    @pytest.mark.parametrize("template_type", ["webapp", "analytics", "ml"])
    def test_all_templates_valid(self, template_type):
        """Parametrized test that all templates are valid."""
        path = get_template_path(template_type)
        valid, error = validate_intake(path)
        assert valid, f"{template_type} template validation failed: {error}"

    def test_template_orchestration_config(self):
        """Test that templates have orchestration configuration."""
        for template_type in list_templates():
            path = get_template_path(template_type)
            config = load_intake_yaml(path)

            assert "orchestration" in config.data
            enabled_agents = config.get("orchestration.enabled_agents")
            assert isinstance(enabled_agents, list)
            assert len(enabled_agents) > 0

            # All templates should enable at least architect
            assert "architect" in enabled_agents

    def test_template_testing_config(self):
        """Test that templates have testing configuration."""
        for template_type in list_templates():
            path = get_template_path(template_type)
            config = load_intake_yaml(path)

            assert "testing" in config.data
            coverage = config.get("testing.coverage_target")
            assert coverage is not None
            assert 0 <= coverage <= 100
