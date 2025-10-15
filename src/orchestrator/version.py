"""Semantic versioning management for orchestrator releases."""

import re
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class BumpType(str, Enum):
    """Semantic version bump types."""

    MAJOR = "major"  # Breaking changes: X.0.0
    MINOR = "minor"  # New features: 0.X.0
    PATCH = "patch"  # Bug fixes: 0.0.X


@dataclass
class Version:
    """Semantic version representation."""

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None  # e.g., "alpha.1", "beta.2", "rc.1"
    build: Optional[str] = None  # e.g., "20250114"

    def __str__(self) -> str:
        """Return version string in semver format."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "Version") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major.minor.patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)

        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # No prerelease > has prerelease
        if self.prerelease is None and other.prerelease is not None:
            return False
        if self.prerelease is not None and other.prerelease is None:
            return True

        # Compare prereleases lexicographically
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease

        return False

    @classmethod
    def parse(cls, version_string: str) -> "Version":
        """
        Parse semantic version string.

        Supports formats:
        - 1.2.3
        - 1.2.3-alpha.1
        - 1.2.3+build.123
        - 1.2.3-beta.2+build.456
        """
        # Semver regex
        pattern = r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<prerelease>[0-9A-Za-z\-.]+))?(?:\+(?P<build>[0-9A-Za-z\-.]+))?$"

        match = re.match(pattern, version_string)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")

        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            prerelease=match.group("prerelease"),
            build=match.group("build"),
        )

    def bump(self, bump_type: BumpType, prerelease: Optional[str] = None) -> "Version":
        """
        Create new version with specified bump.

        Args:
            bump_type: Type of version bump (major/minor/patch)
            prerelease: Optional prerelease identifier

        Returns:
            New Version instance
        """
        if bump_type == BumpType.MAJOR:
            return Version(self.major + 1, 0, 0, prerelease=prerelease)
        elif bump_type == BumpType.MINOR:
            return Version(self.major, self.minor + 1, 0, prerelease=prerelease)
        elif bump_type == BumpType.PATCH:
            return Version(self.major, self.minor, self.patch + 1, prerelease=prerelease)
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")


def get_current_version(project_root: Path) -> Version:
    """
    Read current version from __version__.py.

    Args:
        project_root: Project root directory

    Returns:
        Current Version

    Raises:
        FileNotFoundError: If version file not found
        ValueError: If version string invalid
    """
    version_file = project_root / "src" / "orchestrator" / "__version__.py"

    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")

    content = version_file.read_text()

    # Extract version string from __version__ = "X.Y.Z"
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError(f"Could not find __version__ in {version_file}")

    version_string = match.group(1)
    return Version.parse(version_string)


def write_version(project_root: Path, version: Version) -> None:
    """
    Write version to __version__.py.

    Args:
        project_root: Project root directory
        version: Version to write
    """
    version_file = project_root / "src" / "orchestrator" / "__version__.py"

    content = f'''"""Orchestrator version."""

__version__ = "{version}"
'''

    version_file.write_text(content)


def determine_bump_type(commits: list[str]) -> BumpType:
    """
    Determine bump type from conventional commits.

    Analyzes commit messages following conventional commits spec:
    - BREAKING CHANGE: or !: → major
    - feat: → minor
    - fix: → patch
    - Other types (docs, chore, etc.) → patch

    Args:
        commits: List of commit messages

    Returns:
        Recommended BumpType
    """
    has_breaking = False
    has_feature = False
    has_fix = False

    for commit in commits:
        commit_lower = commit.lower()

        # Check for breaking changes
        if "breaking change:" in commit_lower or re.search(r"^[a-z]+!:", commit_lower):
            has_breaking = True
            break  # Breaking takes precedence

        # Check for features
        if commit_lower.startswith("feat:") or commit_lower.startswith("feat("):
            has_feature = True

        # Check for fixes
        if commit_lower.startswith("fix:") or commit_lower.startswith("fix("):
            has_fix = True

    if has_breaking:
        return BumpType.MAJOR
    elif has_feature:
        return BumpType.MINOR
    elif has_fix:
        return BumpType.PATCH
    else:
        # Default to patch for other changes
        return BumpType.PATCH


def get_version_tag(version: Version) -> str:
    """
    Get git tag name for version.

    Args:
        version: Version to tag

    Returns:
        Tag name (e.g., "v1.2.3")
    """
    return f"v{version}"


def validate_version_file(project_root: Path) -> bool:
    """
    Validate that version file exists and is parseable.

    Args:
        project_root: Project root directory

    Returns:
        True if valid, False otherwise
    """
    try:
        get_current_version(project_root)
        return True
    except (FileNotFoundError, ValueError):
        return False
