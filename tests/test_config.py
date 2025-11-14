"""Tests for common.config module.

Tests configuration loading with file, environment, and CLI overrides.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.common.config import (
    AppConfig,
    ConfigLoader,
    emit_deprecation_once,
    load_config,
)


class TestAppConfig:
    """Test AppConfig Pydantic model."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = AppConfig()

        assert config.app.name == "orchestrator"
        assert config.app.environment == "dev"
        assert config.paths.workspace == ".work"
        assert config.paths.reports == "reports"
        assert config.logging.level == "INFO"
        assert config.logging.json_format is False
        assert config.governance.require_security_scan is False
        assert config.runtime.max_parallel_agents == 2
        assert config.runtime.auto_advance is False

    def test_custom_values(self):
        """Test setting custom values."""
        config = AppConfig(
            app={"name": "custom-orchestrator", "environment": "prod"},
            logging={"level": "DEBUG", "json": True},
            runtime={"max_parallel_agents": 4},
        )

        assert config.app.name == "custom-orchestrator"
        assert config.app.environment == "prod"
        assert config.logging.level == "DEBUG"
        assert config.logging.json_format is True
        assert config.runtime.max_parallel_agents == 4


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_from_default_file(self, tmp_path, monkeypatch):
        """Test loading from default config file."""
        # Create a temporary config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "default.yaml"

        config_data = {
            "app": {"name": "test-app", "environment": "staging"},
            "logging": {"level": "DEBUG"},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Change to tmp directory so default path resolves correctly
        monkeypatch.chdir(tmp_path)

        loader = ConfigLoader()
        config = loader.load()

        assert config.app.name == "test-app"
        assert config.app.environment == "staging"
        assert config.logging.level == "DEBUG"

    def test_load_from_explicit_path(self, tmp_path):
        """Test loading from explicit config path."""
        config_file = tmp_path / "custom.yaml"

        config_data = {
            "app": {"name": "explicit-app"},
            "runtime": {"max_parallel_agents": 8},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader()
        config = loader.load(path=config_file)

        assert config.app.name == "explicit-app"
        assert config.runtime.max_parallel_agents == 8

    def test_env_var_overrides(self, tmp_path, monkeypatch):
        """Test environment variable overrides."""
        config_file = tmp_path / "test.yaml"

        config_data = {
            "app": {"name": "base-app"},
            "logging": {"level": "INFO"},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Set environment variables
        monkeypatch.setenv("ORCH_LOGGING__LEVEL", "DEBUG")
        monkeypatch.setenv("ORCH_RUNTIME__MAX_PARALLEL_AGENTS", "4")
        monkeypatch.setenv("ORCH_CLI__COLOR", "false")

        loader = ConfigLoader()
        config = loader.load(path=config_file)

        assert config.app.name == "base-app"  # Not overridden
        assert config.logging.level == "DEBUG"  # Overridden by env
        assert config.runtime.max_parallel_agents == 4  # Overridden by env
        assert config.cli.color is False  # Overridden by env (bool coercion)

    def test_cli_overrides(self, tmp_path):
        """Test CLI programmatic overrides."""
        config_file = tmp_path / "test.yaml"

        config_data = {
            "app": {"name": "base-app"},
            "logging": {"level": "INFO"},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        cli_overrides = {
            "logging": {"level": "ERROR", "json": True},
            "runtime": {"auto_advance": True},
        }

        loader = ConfigLoader()
        config = loader.load(path=config_file, cli_overrides=cli_overrides)

        assert config.app.name == "base-app"
        assert config.logging.level == "ERROR"  # CLI override
        assert config.logging.json_format is True  # CLI override
        assert config.runtime.auto_advance is True  # CLI override

    def test_layered_overrides(self, tmp_path, monkeypatch):
        """Test that overrides are applied in correct order: file -> env -> CLI."""
        config_file = tmp_path / "test.yaml"

        config_data = {
            "logging": {"level": "INFO", "json": False},
            "runtime": {"max_parallel_agents": 2},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Env overrides file
        monkeypatch.setenv("ORCH_LOGGING__LEVEL", "WARNING")

        # CLI overrides env
        cli_overrides = {"logging": {"level": "ERROR"}}

        loader = ConfigLoader()
        config = loader.load(path=config_file, cli_overrides=cli_overrides)

        # CLI should win
        assert config.logging.level == "ERROR"
        assert config.runtime.max_parallel_agents == 2

    def test_env_var_from_orch_config(self, tmp_path, monkeypatch):
        """Test loading config file path from ORCH_CONFIG env var."""
        config_file = tmp_path / "from-env.yaml"

        config_data = {"app": {"name": "env-loaded-app"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setenv("ORCH_CONFIG", str(config_file))

        loader = ConfigLoader()
        config = loader.load()

        assert config.app.name == "env-loaded-app"

    def test_missing_config_file_uses_defaults(self):
        """Test that missing config file uses model defaults."""
        loader = ConfigLoader()
        config = loader.load(path="/nonexistent/config.yaml")

        # Should use Pydantic defaults
        assert config.app.name == "orchestrator"
        assert config.logging.level == "INFO"

    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config raises RuntimeError."""
        config_file = tmp_path / "invalid.yaml"

        # Invalid: max_parallel_agents must be int
        config_data = {"runtime": {"max_parallel_agents": "not-a-number"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        loader = ConfigLoader()

        with pytest.raises(RuntimeError, match="Invalid configuration"):
            loader.load(path=config_file)

    def test_deep_merge(self):
        """Test deep merge utility."""
        base = {
            "a": {"b": 1, "c": 2},
            "d": 3,
        }

        override = {
            "a": {"c": 99, "e": 4},
            "f": 5,
        }

        result = ConfigLoader._deep_merge(base, override)

        assert result == {
            "a": {"b": 1, "c": 99, "e": 4},
            "d": 3,
            "f": 5,
        }

    def test_coerce_boolean(self):
        """Test boolean coercion from env vars."""
        assert ConfigLoader._coerce("true") is True
        assert ConfigLoader._coerce("True") is True
        assert ConfigLoader._coerce("TRUE") is True
        assert ConfigLoader._coerce("false") is False
        assert ConfigLoader._coerce("False") is False
        assert ConfigLoader._coerce("not-a-bool") == "not-a-bool"

    def test_coerce_integer(self):
        """Test integer coercion from env vars."""
        assert ConfigLoader._coerce("123") == 123
        assert ConfigLoader._coerce("0") == 0
        assert ConfigLoader._coerce("not-an-int") == "not-an-int"

    def test_custom_env_prefix(self, tmp_path, monkeypatch):
        """Test using custom environment variable prefix."""
        config_file = tmp_path / "test.yaml"

        config_data = {"logging": {"level": "INFO"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        monkeypatch.setenv("CUSTOM_LOGGING__LEVEL", "DEBUG")

        loader = ConfigLoader(env_prefix="CUSTOM_")
        config = loader.load(path=config_file)

        assert config.logging.level == "DEBUG"


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_load_config_convenience(self, tmp_path):
        """Test load_config convenience function."""
        config_file = tmp_path / "test.yaml"

        config_data = {"app": {"name": "convenience-test"}}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(path=config_file)

        assert isinstance(config, AppConfig)
        assert config.app.name == "convenience-test"

    def test_emit_deprecation_warning(self):
        """Test deprecation warning emission."""
        with pytest.warns(DeprecationWarning, match="old_module.*new_module"):
            emit_deprecation_once("old_module", "new_module")


class TestIntegration:
    """Integration tests for real-world scenarios."""

    def test_production_like_config(self, tmp_path, monkeypatch):
        """Test a production-like configuration scenario."""
        # Base config file
        config_file = tmp_path / "prod.yaml"

        config_data = {
            "app": {"name": "production-orchestrator", "environment": "prod"},
            "logging": {"level": "WARNING", "json": True, "file": "/var/log/orch.log"},
            "governance": {
                "require_security_scan": True,
                "performance_slas": {"latency_p95_ms": 200},
            },
            "runtime": {"max_parallel_agents": 8, "auto_advance": True},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Environment overrides (e.g., from k8s secrets)
        monkeypatch.setenv("ORCH_LOGGING__LEVEL", "ERROR")
        monkeypatch.setenv("ORCH_RUNTIME__MAX_PARALLEL_AGENTS", "16")

        # CLI overrides (e.g., from command-line flags)
        cli_overrides = {"cli": {"progress_bars": False}}

        config = load_config(path=config_file, cli_overrides=cli_overrides)

        # Verify layering
        assert config.app.environment == "prod"  # From file
        assert config.logging.level == "ERROR"  # Env override
        assert config.runtime.max_parallel_agents == 16  # Env override
        assert config.cli.progress_bars is False  # CLI override
        assert config.governance.require_security_scan is True  # From file


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config_file(self, tmp_path):
        """Test loading empty config file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = load_config(path=config_file)

        # Should use defaults
        assert config.app.name == "orchestrator"

    def test_null_config_file(self, tmp_path):
        """Test loading config file with null content."""
        config_file = tmp_path / "null.yaml"
        config_file.write_text("null")

        config = load_config(path=config_file)

        # Should use defaults
        assert config.app.name == "orchestrator"

    def test_nested_env_vars(self, tmp_path, monkeypatch):
        """Test deeply nested environment variable overrides."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("app:\n  name: base")

        monkeypatch.setenv(
            "ORCH_GOVERNANCE__PERFORMANCE_SLAS__LATENCY_P95_MS", "500"
        )

        config = load_config(path=config_file)

        assert config.governance.performance_slas.latency_p95_ms == 500
