"""Configuration loader for hygiene settings."""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


DEFAULT_CONFIG = {
    "large_file_mb": 1,
    "binary_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz"],
    "notebook_clear_outputs": False,
    "whitelist_globs": [
        "data/external/**",
        "docs/**",
        ".github/**",
        "models/**",
        "data/processed/**",
    ],
    "dead_code": {
        "min_confidence": 60,
        "exclude_patterns": ["__init__\\.py$", "test_.*\\.py$"],
        "exclude_names": ["__all__", "__version__", "main", "cli", "app"],
        "ignore_unused_imports": ["__init__.py"],
    },
    "orphan_detection": {
        "min_age_days": 30,
        "reference_extensions": [".py", ".md", ".yaml", ".yml", ".toml", ".json"],
        "protected_patterns": ["example", "template", "fixture", "sample"],
    },
    "reports": {
        "include_metadata": True,
        "include_sizes": True,
        "include_timestamps": True,
        "csv_sort_by": "size",
        "csv_sort_descending": True,
    },
}


class HygieneConfig:
    """Hygiene configuration with defaults."""

    def __init__(self, config_path: Optional[Path] = None):
        """Load configuration from file or use defaults."""
        self.config = DEFAULT_CONFIG.copy()

        if config_path is None:
            config_path = Path("configs/hygiene.yaml")

        if config_path.exists():
            with open(config_path, "r") as f:
                user_config = yaml.safe_load(f) or {}
                self._deep_merge(self.config, user_config)

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    @property
    def large_file_mb(self) -> float:
        """Get large file threshold in MB."""
        return self.config["large_file_mb"]

    @property
    def binary_exts(self) -> List[str]:
        """Get list of binary file extensions."""
        return self.config["binary_exts"]

    @property
    def notebook_clear_outputs(self) -> bool:
        """Whether to clear notebook outputs on --apply."""
        return self.config["notebook_clear_outputs"]

    @property
    def whitelist_globs(self) -> List[str]:
        """Get whitelist glob patterns."""
        return self.config["whitelist_globs"]

    @property
    def dead_code_min_confidence(self) -> int:
        """Minimum confidence for dead code reporting."""
        return self.config["dead_code"]["min_confidence"]

    @property
    def orphan_min_age_days(self) -> int:
        """Minimum age in days for orphan detection."""
        return self.config["orphan_detection"]["min_age_days"]

    # Safety thresholds
    @property
    def max_apply_deletions(self) -> int:
        """Maximum deletions allowed in --apply mode."""
        return self.get("safety.max_apply_deletions", 50)

    @property
    def max_apply_renames(self) -> int:
        """Maximum renames allowed in --apply mode."""
        return self.get("safety.max_apply_renames", 50)

    @property
    def max_apply_bytes_removed(self) -> int:
        """Maximum bytes that can be removed in --apply mode."""
        return self.get("safety.max_apply_bytes_removed", 10485760)

    # Quality gates
    @property
    def max_orphans_warn(self) -> int:
        """Orphan count threshold for warnings."""
        return self.get("quality.max_orphans_warn", 10)

    @property
    def max_orphans_block(self) -> int:
        """Orphan count threshold for blocking CI."""
        return self.get("quality.max_orphans_block", 50)

    @property
    def min_cleanliness_score(self) -> int:
        """Minimum cleanliness score to pass CI."""
        return self.get("quality.min_cleanliness_score", 85)

    @property
    def score_weights(self) -> Dict[str, int]:
        """Score weights for cleanliness calculation."""
        return self.get("quality.score_weights", {
            "no_orphans": 30,
            "no_large_files": 25,
            "no_dead_code": 20,
            "no_notebook_outputs": 15,
            "no_secrets": 10,
        })

    # Links
    @property
    def check_doc_links(self) -> bool:
        """Whether to check documentation links."""
        return self.get("links.check_doc_links", True)

    @property
    def doc_dirs(self) -> List[str]:
        """Directories to scan for documentation."""
        return self.get("links.doc_dirs", ["docs", "README.md"])

    # Security
    @property
    def run_secret_scan(self) -> bool:
        """Whether to run secret scanning."""
        return self.get("security.run_secret_scan", True)

    @property
    def run_license_header_check(self) -> bool:
        """Whether to check license headers."""
        return self.get("security.run_license_header_check", True)

    @property
    def spdx_id(self) -> str:
        """Expected SPDX license identifier."""
        return self.get("security.spdx_id", "Apache-2.0")


def load_config(config_path: Optional[Path] = None) -> HygieneConfig:
    """Load hygiene configuration."""
    return HygieneConfig(config_path)
