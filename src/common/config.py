"""Canonical configuration loading for the orchestrator.

This module provides a unified configuration system with:
- Pydantic-based validation
- Layered configuration (file → env → CLI overrides)
- Type-safe access to settings
- Environment-based overrides (ORCH_* env vars)

Example:
    >>> from common.config import load_config
    >>> config = load_config()
    >>> print(config.app.name)
    'orchestrator'
    >>> print(config.logging.level)
    'INFO'

    # With overrides
    >>> config = load_config(cli_overrides={"logging": {"level": "DEBUG"}})
    >>> print(config.logging.level)
    'DEBUG'
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


# ---------- Pydantic Models ----------


class PerformanceSLAs(BaseModel):
    """Performance service level agreements."""

    latency_p95_ms: int = Field(
        default=0, description="95th percentile latency threshold in ms (0 = disabled)"
    )


class Governance(BaseModel):
    """Governance and quality gate settings."""

    require_security_scan: bool = Field(
        default=False, description="Whether security scanning is mandatory"
    )
    performance_slas: PerformanceSLAs = Field(default_factory=PerformanceSLAs)


class LoggingCfg(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level (DEBUG|INFO|WARNING|ERROR)")
    json_format: bool = Field(
        default=False, description="Output logs as JSON", alias="json"
    )
    file: Optional[str] = Field(default=None, description="Log file path (null = stdout)")


class Paths(BaseModel):
    """File system paths used by the orchestrator."""

    workspace: str = Field(default=".work", description="Working directory for temp files")
    reports: str = Field(default="reports", description="Output directory for reports")
    data_processed: str = Field(
        default="data/processed", description="Processed data storage path"
    )


class Runtime(BaseModel):
    """Runtime execution settings."""

    max_parallel_agents: int = Field(
        default=2, description="Maximum number of agents to run concurrently"
    )
    auto_advance: bool = Field(
        default=False, description="Automatically advance through workflow phases"
    )


class Secrets(BaseModel):
    """Secrets management configuration."""

    provider: str = Field(
        default="env", description="Secrets provider (env|none|vault)"
    )
    env_prefix: str = Field(
        default="ORCH_", description="Prefix for environment variable secrets"
    )


class CLI(BaseModel):
    """CLI interface settings."""

    color: bool = Field(default=True, description="Enable colored output")
    progress_bars: bool = Field(default=True, description="Show progress bars")


class App(BaseModel):
    """Application metadata."""

    name: str = Field(default="orchestrator", description="Application name")
    environment: str = Field(
        default="dev", description="Deployment environment (dev|staging|prod)"
    )


class AppConfig(BaseModel):
    """Root configuration model for the orchestrator.

    This is the canonical configuration object used throughout the application.
    All settings are validated on load and provide type-safe access.

    Attributes:
        app: Application metadata (name, environment)
        paths: File system paths
        logging: Logging configuration
        governance: Quality gates and governance rules
        runtime: Execution settings
        secrets: Secrets management config
        cli: CLI interface settings
    """

    app: App = Field(default_factory=App)
    paths: Paths = Field(default_factory=Paths)
    logging: LoggingCfg = Field(default_factory=LoggingCfg)
    governance: Governance = Field(default_factory=Governance)
    runtime: Runtime = Field(default_factory=Runtime)
    secrets: Secrets = Field(default_factory=Secrets)
    cli: CLI = Field(default_factory=CLI)


# ---------- Configuration Loader ----------


class ConfigLoader:
    """Canonical configuration loader with layered overrides.

    Configuration is loaded in the following order (later overrides earlier):
      1. Base file (explicit path, ORCH_CONFIG env var, or config/default.yaml)
      2. Environment variables (ORCH_LOGGING__LEVEL=DEBUG → logging.level)
      3. CLI overrides (programmatic dict overrides)

    Args:
        env_prefix: Prefix for environment variable overrides (default: "ORCH_")

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load()
        >>> print(config.app.name)
        'orchestrator'

        >>> # With environment override
        >>> os.environ["ORCH_LOGGING__LEVEL"] = "DEBUG"
        >>> config = loader.load()
        >>> print(config.logging.level)
        'DEBUG'
    """

    def __init__(self, env_prefix: str = "ORCH_") -> None:
        """Initialize the config loader.

        Args:
            env_prefix: Prefix for environment variable overrides
        """
        self.env_prefix = env_prefix

    def load(
        self,
        path: Optional[str | Path] = None,
        cli_overrides: Optional[dict[str, Any]] = None,
    ) -> AppConfig:
        """Load configuration with layered overrides.

        Args:
            path: Explicit config file path (optional)
            cli_overrides: Programmatic overrides as nested dict (optional)

        Returns:
            Validated AppConfig instance

        Raises:
            RuntimeError: If configuration is invalid

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load(
            ...     path="config/prod.yaml",
            ...     cli_overrides={"runtime": {"max_parallel_agents": 4}}
            ... )
        """
        cfg_dict: dict[str, Any] = {}

        # Layer 1: Base file
        file_path = self._resolve_file(path)
        if file_path and Path(file_path).exists():
            with open(file_path, encoding="utf-8") as f:
                cfg_dict = yaml.safe_load(f) or {}

        # Layer 2: Environment variable overlay
        env_overlay = self._env_overlay()
        cfg_dict = self._deep_merge(cfg_dict, env_overlay)

        # Layer 3: CLI overrides
        if cli_overrides:
            cfg_dict = self._deep_merge(cfg_dict, cli_overrides)

        # Validate and return
        try:
            return AppConfig.model_validate(cfg_dict)
        except ValidationError as e:
            raise RuntimeError(f"Invalid configuration: {e}") from e

    def _resolve_file(self, explicit: Optional[str | Path]) -> str:
        """Resolve which config file to load.

        Args:
            explicit: Explicitly provided path

        Returns:
            Path to config file (may not exist)
        """
        if explicit:
            return str(explicit)
        env_path = os.getenv(f"{self.env_prefix}CONFIG")
        if env_path:
            return env_path
        return "config/default.yaml"

    def _env_overlay(self) -> dict[str, Any]:
        """Convert environment variables to nested config dict.

        Environment variables like ORCH_LOGGING__LEVEL=DEBUG are converted
        to {"logging": {"level": "DEBUG"}}.

        Returns:
            Nested dict of environment variable overrides
        """
        prefix = self.env_prefix
        overlay: dict[str, Any] = {}

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Skip ORCH_CONFIG which is the file pointer
            if key == f"{prefix}CONFIG":
                continue

            # Convert LOGGING__LEVEL to ["logging", "level"]
            path = key[len(prefix) :].lower().split("__")
            cur = overlay
            for part in path[:-1]:
                cur = cur.setdefault(part, {})
            cur[path[-1]] = self._coerce(value)

        return overlay

    @staticmethod
    def _coerce(value: str) -> Any:
        """Coerce string environment variable to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Coerced value (bool, int, or str)
        """
        vl = value.lower()

        # Boolean coercion
        if vl in {"true", "false"}:
            return vl == "true"

        # Integer coercion
        if vl.isdigit():
            try:
                return int(vl)
            except ValueError:
                pass

        return value

    @staticmethod
    def _deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries (b overrides a).

        Args:
            a: Base dictionary
            b: Override dictionary

        Returns:
            Merged dictionary
        """
        out = dict(a)
        for k, v in b.items():
            if k in out and isinstance(out[k], dict) and isinstance(v, dict):
                out[k] = ConfigLoader._deep_merge(out[k], v)
            else:
                out[k] = v
        return out


# ---------- Backward-Compatible API ----------

_loader_singleton = ConfigLoader()


def load_config(
    path: Optional[str | Path] = None,
    cli_overrides: Optional[dict[str, Any]] = None,
) -> AppConfig:
    """Load configuration using the singleton loader.

    This is the primary API for loading configuration. It uses a singleton
    ConfigLoader instance for convenience.

    Args:
        path: Optional config file path
        cli_overrides: Optional programmatic overrides

    Returns:
        Validated AppConfig instance

    Example:
        >>> from common.config import load_config
        >>> config = load_config()
        >>> print(config.app.environment)
        'dev'
    """
    return _loader_singleton.load(path=path, cli_overrides=cli_overrides)


# ---------- Deprecation Utilities ----------


def emit_deprecation_once(old_module: str, new_module: str) -> None:
    """Emit deprecation warning for old config loading patterns.

    Args:
        old_module: Old module path (e.g., "orchestrator.config")
        new_module: New module path (e.g., "common.config")
    """
    warnings.warn(
        f"`{old_module}.load_config` is deprecated; use `{new_module}.load_config`.",
        DeprecationWarning,
        stacklevel=2,
    )
