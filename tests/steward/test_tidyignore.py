"""Test .tidyignore whitelist behavior."""

import pytest
from pathlib import Path

from src.steward.scanner import is_whitelisted


class TestTidyIgnore:
    """Test whitelist pattern matching."""

    def test_exact_path_match(self):
        """Test exact path whitelisting."""
        patterns = ["data/external/sample.csv"]
        path = Path("data/external/sample.csv")

        assert is_whitelisted(path, patterns)

    def test_glob_pattern_match(self):
        """Test glob pattern whitelisting."""
        patterns = ["data/external/**"]
        path = Path("data/external/subfolder/file.csv")

        assert is_whitelisted(path, patterns)

    def test_wildcard_extension(self):
        """Test wildcard extension matching."""
        patterns = ["docs/**/*.png"]
        path = Path("docs/images/diagram.png")

        assert is_whitelisted(path, patterns)

    def test_non_matching_pattern(self):
        """Test that non-matching patterns return False."""
        patterns = ["data/external/**"]
        path = Path("data/raw/file.csv")

        assert not is_whitelisted(path, patterns)

    def test_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = [
            "data/external/**",
            "docs/**",
            "models/**/*.pkl",
        ]

        assert is_whitelisted(Path("data/external/sample.csv"), patterns)
        assert is_whitelisted(Path("docs/readme.md"), patterns)
        assert is_whitelisted(Path("models/trained/model.pkl"), patterns)
        assert not is_whitelisted(Path("src/utils.py"), patterns)

    def test_readme_whitelisting(self):
        """Test that README files can be whitelisted."""
        patterns = ["*.md"]

        assert is_whitelisted(Path("README.md"), patterns)
        assert is_whitelisted(Path("CHANGELOG.md"), patterns)
