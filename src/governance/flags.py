"""
Feature flags system for safe rollouts and rollbacks.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

FLAGS_FILE = Path("configs/flags.yaml")
FLAGS_OVERRIDE_ENV = "FEATURE_FLAGS"


def load_flags() -> Dict[str, bool]:
    """
    Load feature flags from config and environment.

    Returns:
        Dictionary of flag names to boolean values
    """
    flags = {}

    # Load from YAML config if exists
    if FLAGS_FILE.exists():
        import yaml

        with open(FLAGS_FILE) as f:
            config = yaml.safe_load(f) or {}
            flags.update(config.get("flags", {}))

    # Override from environment
    env_flags = os.getenv(FLAGS_OVERRIDE_ENV)
    if env_flags:
        try:
            env_dict = json.loads(env_flags)
            flags.update(env_dict)
        except json.JSONDecodeError:
            pass

    return flags


def is_enabled(key: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        key: Flag key (e.g., "ui.experimental_map")

    Returns:
        True if enabled, False otherwise
    """
    flags = load_flags()
    return flags.get(key, False)


def get_all_flags() -> Dict[str, bool]:
    """
    Get all feature flags.

    Returns:
        Dictionary of all flags
    """
    return load_flags()


def set_flag(key: str, enabled: bool = True) -> None:
    """
    Set a feature flag and log the change.

    Args:
        key: Flag key
        enabled: Whether to enable the flag
    """
    import yaml

    # Load current flags
    FLAGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if FLAGS_FILE.exists():
        with open(FLAGS_FILE) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    if "flags" not in config:
        config["flags"] = {}

    # Update flag
    config["flags"][key] = enabled

    # Save
    with open(FLAGS_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Log to audit
    _log_flag_change(key, enabled)


def unset_flag(key: str) -> None:
    """
    Remove a feature flag.

    Args:
        key: Flag key
    """
    import yaml

    if not FLAGS_FILE.exists():
        return

    with open(FLAGS_FILE) as f:
        config = yaml.safe_load(f) or {}

    if "flags" in config and key in config["flags"]:
        del config["flags"][key]

        with open(FLAGS_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        _log_flag_change(key, None)


def _log_flag_change(key: str, value: bool | None) -> None:
    """
    Log feature flag change to audit log.

    Args:
        key: Flag key
        value: New value (None for deletion)
    """
    audit_dir = Path("governance/audit")
    audit_dir.mkdir(parents=True, exist_ok=True)

    audit_file = audit_dir / "flags.ndjson"

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "flag_change",
        "flag": key,
        "value": value,
        "action": "set" if value is not None else "unset",
    }

    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
