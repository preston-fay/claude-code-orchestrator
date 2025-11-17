"""Tests for constitution management."""

import pytest
from pathlib import Path
import yaml

from src.orchestrator.constitution import (
    ConstitutionConfig,
    ConstitutionError,
    generate_constitution,
    validate_constitution,
)
from src.orchestrator.constitution.validator import (
    check_code_against_constitution,
    ConstitutionViolation,
)


class TestConstitutionConfig:
    """Test ConstitutionConfig creation and defaults."""

    def test_create_basic_config(self):
        """Test creating a basic constitution config."""
        config = ConstitutionConfig(
            project_name="test-project",
            project_type="ml",
            mission_statement="Build an ML model",
        )

        assert config.project_name == "test-project"
        assert config.project_type == "ml"
        assert config.mission_statement == "Build an ML model"
        assert config.version == "1.0.0"
        assert config.raise_compliance is True

    def test_from_intake_basic(self):
        """Test creating config from intake YAML."""
        intake = {
            "project": {
                "name": "my-ml-project",
                "type": "ml",
                "description": "An ML project",
            },
            "goals": {
                "primary": ["Develop ML model"],
                "success_criteria": ["Accuracy > 85%"],
            },
        }

        config = ConstitutionConfig.from_intake(intake)

        assert config.project_name == "my-ml-project"
        assert config.project_type == "ml"
        assert "Develop ML model" in config.mission_statement
        assert len(config.code_quality_mandatory) > 0  # Has defaults

    def test_from_intake_with_constitution_section(self):
        """Test creating config from intake with constitution section."""
        intake = {
            "project": {
                "name": "test-project",
                "type": "webapp",
            },
            "goals": {
                "primary": ["Build webapp"],
            },
            "constitution": {
                "code_quality": ["All functions must have docstrings", "Test coverage ≥ 90%"],
                "forbidden": ["No inline SQL", "No global variables"],
            },
        }

        config = ConstitutionConfig.from_intake(intake)

        assert "All functions must have docstrings" in config.code_quality_mandatory
        assert len(config.forbidden_practices) == 2
        assert config.forbidden_practices[0]["practice"] == "No inline SQL"

    def test_ml_defaults(self):
        """Test ML-specific defaults are added."""
        config = ConstitutionConfig(
            project_name="ml-test",
            project_type="ml",
            mission_statement="Build ML model",
        )
        config._add_defaults_by_type()

        assert len(config.data_quality) > 0
        assert len(config.forbidden_practices) > 0
        assert any("data leakage" in p["reason"].lower() for p in config.forbidden_practices)

    def test_webapp_defaults(self):
        """Test webapp-specific defaults are added."""
        config = ConstitutionConfig(
            project_name="webapp-test",
            project_type="webapp",
            mission_statement="Build webapp",
        )
        config._add_defaults_by_type()

        assert len(config.ux_performance) > 0
        assert len(config.ux_accessibility) > 0
        assert any("WCAG" in perf for perf in config.ux_accessibility)


class TestConstitutionGeneration:
    """Test constitution document generation."""

    def test_generate_constitution_basic(self, tmp_path):
        """Test generating a constitution document."""
        config = ConstitutionConfig(
            project_name="test-project",
            project_type="ml",
            mission_statement="Build an ML model",
        )
        config._add_defaults_by_type()
        config._add_kearney_defaults()

        output_path = tmp_path / "constitution.md"
        md = generate_constitution(config, output_path)

        assert output_path.exists()
        assert "# Project Constitution: test-project" in md
        assert "## 🎯 Core Principles" in md
        assert "## 📐 Code Quality Standards" in md
        assert "## 🔒 Security & Privacy" in md
        assert "Build an ML model" in md

    def test_generate_constitution_with_kearney_standards(self, tmp_path):
        """Test that Kearney standards are included."""
        config = ConstitutionConfig(
            project_name="kearney-project",
            project_type="analytics",
            mission_statement="Analytics project",
        )
        config._add_kearney_defaults()

        output_path = tmp_path / "constitution.md"
        md = generate_constitution(config, output_path)

        assert "## 🎓 Kearney Standards" in md
        assert "RAISE Framework" in md
        assert "Kearney" in md
        assert "#7823DC" in md  # Kearney purple

    def test_generate_constitution_with_forbidden_practices(self, tmp_path):
        """Test constitution with forbidden practices."""
        config = ConstitutionConfig(
            project_name="test",
            project_type="ml",
            mission_statement="Test",
            forbidden_practices=[
                {"practice": "Using pickle", "reason": "Security risk"},
                {"practice": "Global variables", "reason": "Poor design"},
            ],
        )

        output_path = tmp_path / "constitution.md"
        md = generate_constitution(config, output_path)

        assert "## 🚫 Forbidden Practices" in md
        assert "Using pickle" in md
        assert "Security risk" in md


class TestConstitutionValidation:
    """Test constitution validation."""

    def test_validate_constitution_missing(self, tmp_path):
        """Test validation fails when constitution doesn't exist."""
        constitution_path = tmp_path / "constitution.md"

        with pytest.raises(ConstitutionError, match="Constitution not found"):
            validate_constitution(constitution_path)

    def test_validate_constitution_incomplete(self, tmp_path):
        """Test validation fails for incomplete constitution."""
        constitution_path = tmp_path / "constitution.md"
        constitution_path.write_text("# Short document")

        with pytest.raises(ConstitutionError, match="missing required sections"):
            validate_constitution(constitution_path)

    def test_validate_constitution_missing_sections(self, tmp_path):
        """Test validation fails for missing required sections."""
        constitution_path = tmp_path / "constitution.md"
        constitution_path.write_text(
            "# Project Constitution: Test\n\n" + "Some content but missing required sections." * 50
        )

        with pytest.raises(ConstitutionError, match="missing required sections"):
            validate_constitution(constitution_path)

    def test_validate_constitution_valid(self, tmp_path):
        """Test validation passes for valid constitution."""
        config = ConstitutionConfig(
            project_name="test",
            project_type="ml",
            mission_statement="Test project",
        )
        config._add_defaults_by_type()

        constitution_path = tmp_path / "constitution.md"
        generate_constitution(config, constitution_path)

        assert validate_constitution(constitution_path) is True


class TestCodeViolationDetection:
    """Test detecting code violations against constitution."""

    def test_detect_hardcoded_credentials(self, tmp_path):
        """Test detection of hardcoded credentials."""
        # Create constitution
        constitution_path = tmp_path / "constitution.md"
        constitution_path.write_text(
            """# Project Constitution: Test

## 📐 Code Quality Standards
- No hardcoded credentials

## 🔒 Security & Privacy
- Use secrets manager
"""
        )

        # Create code with hardcoded credential
        code_file = tmp_path / "test.py"
        code_file.write_text(
            """
def connect():
    password = "mysecretpassword123"
    return connect_to_db(password)
"""
        )

        violations = check_code_against_constitution([code_file], constitution_path)

        assert len(violations) > 0
        assert any("hardcoded credentials" in v.rule.lower() for v in violations)
        assert any(v.severity == "critical" for v in violations)

    def test_detect_missing_docstrings(self, tmp_path):
        """Test detection of missing docstrings."""
        constitution_path = tmp_path / "constitution.md"
        constitution_path.write_text(
            """# Project Constitution: Test

## 📐 Code Quality Standards
- All functions must have docstrings

## 🔒 Security & Privacy
- Security standards
"""
        )

        # Create code with functions but no docstrings
        code_file = tmp_path / "test.py"
        code_file.write_text(
            """
def func1():
    pass

def func2():
    pass

def func3():
    pass

def func4():
    pass
"""
        )

        violations = check_code_against_constitution([code_file], constitution_path)

        # Should detect that many functions are missing docstrings
        docstring_violations = [v for v in violations if "docstring" in v.rule.lower()]
        assert len(docstring_violations) > 0

    def test_no_violations_for_good_code(self, tmp_path):
        """Test that well-written code has minimal violations."""
        constitution_path = tmp_path / "constitution.md"
        constitution_path.write_text(
            """# Project Constitution: Test

## 📐 Code Quality Standards
- Code quality standards

## 🔒 Security & Privacy
- Security standards
"""
        )

        # Create good code (uses environment variables, has docstrings)
        code_file = tmp_path / "test.py"
        code_file.write_text(
            '''
def connect():
    """Connect to database using environment variables."""
    import os
    db_config = os.getenv("DB_CONFIG")
    return connect_to_db(db_config)

def process_data(data):
    """Process input data and return results."""
    return data * 2
'''
        )

        violations = check_code_against_constitution([code_file], constitution_path)

        # Should have no violations (or very few false positives)
        # Note: Simple heuristics may flag some false positives
        assert len(violations) <= 1  # Allow for one false positive


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
