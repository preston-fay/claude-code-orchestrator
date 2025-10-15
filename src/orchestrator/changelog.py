"""Conventional commits changelog generator."""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from .version import Version


@dataclass
class CommitEntry:
    """Parsed conventional commit."""

    type: str  # feat, fix, docs, etc.
    scope: Optional[str]  # (scope) part
    description: str  # Main message
    body: Optional[str] = None
    breaking: bool = False
    hash: str = ""
    author: str = ""

    @classmethod
    def parse(cls, commit_msg: str, commit_hash: str = "", author: str = "") -> Optional["CommitEntry"]:
        """
        Parse conventional commit message.

        Format: <type>[optional scope][!]: <description>

        Examples:
        - feat: add new feature
        - fix(auth): resolve login bug
        - feat!: breaking change
        - fix(api)!: breaking API change
        """
        # Pattern: type(scope)!: description
        pattern = r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$"

        match = re.match(pattern, commit_msg.strip(), re.IGNORECASE)
        if not match:
            return None

        # Check for BREAKING CHANGE in body
        has_breaking = match.group("breaking") is not None

        return cls(
            type=match.group("type").lower(),
            scope=match.group("scope"),
            description=match.group("description").strip(),
            breaking=has_breaking,
            hash=commit_hash,
            author=author,
        )


@dataclass
class ChangelogSection:
    """Grouped commits by type."""

    title: str
    emoji: str
    commits: List[CommitEntry] = field(default_factory=list)


def get_commits_since_tag(project_root: Path, since_tag: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get git commits since specified tag.

    Args:
        project_root: Project root directory
        since_tag: Git tag to start from (None = all commits)

    Returns:
        List of commit dicts with hash, author, message
    """
    try:
        # Format: hash|author|message
        git_cmd = ["git", "log", "--pretty=format:%H|%an|%s"]

        if since_tag:
            git_cmd.append(f"{since_tag}..HEAD")

        result = subprocess.run(
            git_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append({"hash": parts[0], "author": parts[1], "message": parts[2]})

        return commits

    except subprocess.CalledProcessError:
        return []


def get_latest_tag(project_root: Path) -> Optional[str]:
    """
    Get latest git tag.

    Args:
        project_root: Project root directory

    Returns:
        Latest tag or None
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def group_commits(commits: List[CommitEntry]) -> Dict[str, ChangelogSection]:
    """
    Group commits by type into changelog sections.

    Args:
        commits: List of parsed commits

    Returns:
        Dict of type -> ChangelogSection
    """
    # Define section metadata
    section_config = {
        "feat": ChangelogSection("Features", "✨"),
        "fix": ChangelogSection("Bug Fixes", "🐛"),
        "perf": ChangelogSection("Performance", "⚡"),
        "docs": ChangelogSection("Documentation", "📚"),
        "style": ChangelogSection("Styling", "💄"),
        "refactor": ChangelogSection("Refactoring", "♻️"),
        "test": ChangelogSection("Tests", "✅"),
        "build": ChangelogSection("Build System", "🔧"),
        "ci": ChangelogSection("CI/CD", "👷"),
        "chore": ChangelogSection("Chores", "🔨"),
    }

    sections = defaultdict(lambda: ChangelogSection("Other", "📦"))

    for commit in commits:
        if commit.type in section_config:
            section = section_config[commit.type]
        else:
            section = sections["other"]

        section.commits.append(commit)

    # Merge with predefined sections
    result = {}
    for commit_type, section in section_config.items():
        if section.commits:
            result[commit_type] = section

    if sections["other"].commits:
        result["other"] = sections["other"]

    return result


def generate_changelog_entry(
    version: Version,
    commits: List[CommitEntry],
    date: Optional[datetime] = None,
    compare_url: Optional[str] = None,
) -> str:
    """
    Generate changelog entry for version.

    Args:
        version: Version being released
        commits: List of parsed commits
        date: Release date (default: today)
        compare_url: GitHub compare URL

    Returns:
        Markdown changelog entry
    """
    if date is None:
        date = datetime.now()

    lines = []

    # Header
    lines.append(f"## [{version}] - {date.strftime('%Y-%m-%d')}")
    lines.append("")

    if compare_url:
        lines.append(f"[Compare changes]({compare_url})")
        lines.append("")

    # Group commits
    sections = group_commits(commits)

    # Breaking changes first
    breaking = [c for c in commits if c.breaking]
    if breaking:
        lines.append("### ⚠️ BREAKING CHANGES")
        lines.append("")
        for commit in breaking:
            scope = f"**{commit.scope}**: " if commit.scope else ""
            lines.append(f"- {scope}{commit.description} ({commit.hash[:7]})")
        lines.append("")

    # Regular sections in priority order
    priority_order = ["feat", "fix", "perf", "docs", "refactor", "test", "build", "ci", "chore", "style"]

    for commit_type in priority_order:
        if commit_type in sections:
            section = sections[commit_type]
            lines.append(f"### {section.emoji} {section.title}")
            lines.append("")

            for commit in section.commits:
                scope = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope}{commit.description} ({commit.hash[:7]})")

            lines.append("")

    # Other section
    if "other" in sections:
        section = sections["other"]
        lines.append(f"### {section.emoji} {section.title}")
        lines.append("")
        for commit in section.commits:
            lines.append(f"- {commit.description} ({commit.hash[:7]})")
        lines.append("")

    return "\n".join(lines)


def update_changelog(
    project_root: Path,
    version: Version,
    changelog_entry: str,
) -> None:
    """
    Update CHANGELOG.md with new entry.

    Creates file if it doesn't exist. Prepends new entry after header.

    Args:
        project_root: Project root directory
        version: Version being released
        changelog_entry: Markdown entry to add
    """
    changelog_path = project_root / "CHANGELOG.md"

    if not changelog_path.exists():
        # Create new changelog
        content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{changelog_entry}
"""
    else:
        # Read existing changelog
        existing = changelog_path.read_text()

        # Find where to insert (after header)
        lines = existing.split("\n")
        insert_idx = 0

        # Skip header and intro paragraphs
        for i, line in enumerate(lines):
            if line.startswith("## "):  # First version entry
                insert_idx = i
                break
            elif i > 10:  # Safety: don't scan entire file
                insert_idx = len(lines)
                break

        if insert_idx == 0:
            insert_idx = len(lines)

        # Insert new entry
        lines.insert(insert_idx, changelog_entry)
        content = "\n".join(lines)

    changelog_path.write_text(content)


def generate_release_notes(
    version: Version,
    commits: List[CommitEntry],
    highlights: Optional[List[str]] = None,
) -> str:
    """
    Generate GitHub release notes.

    Similar to changelog but more user-friendly format.

    Args:
        version: Version being released
        commits: List of parsed commits
        highlights: Optional highlights/summary

    Returns:
        Markdown release notes
    """
    lines = []

    lines.append(f"# Release {version}")
    lines.append("")

    # Highlights section
    if highlights:
        lines.append("## 🎉 Highlights")
        lines.append("")
        for highlight in highlights:
            lines.append(f"- {highlight}")
        lines.append("")

    # Generate sections
    sections = group_commits(commits)

    # Breaking changes
    breaking = [c for c in commits if c.breaking]
    if breaking:
        lines.append("## ⚠️ Breaking Changes")
        lines.append("")
        for commit in breaking:
            scope = f"**{commit.scope}**: " if commit.scope else ""
            lines.append(f"- {scope}{commit.description}")
        lines.append("")

    # Features
    if "feat" in sections:
        lines.append("## ✨ New Features")
        lines.append("")
        for commit in sections["feat"].commits:
            scope = f"**{commit.scope}**: " if commit.scope else ""
            lines.append(f"- {scope}{commit.description}")
        lines.append("")

    # Bug fixes
    if "fix" in sections:
        lines.append("## 🐛 Bug Fixes")
        lines.append("")
        for commit in sections["fix"].commits:
            scope = f"**{commit.scope}**: " if commit.scope else ""
            lines.append(f"- {scope}{commit.description}")
        lines.append("")

    # Other improvements
    other_types = [t for t in sections.keys() if t not in ("feat", "fix")]
    if other_types:
        lines.append("## 🔧 Other Changes")
        lines.append("")
        for commit_type in other_types:
            section = sections[commit_type]
            for commit in section.commits:
                scope = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope}{commit.description}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("**Full Changelog**: See [CHANGELOG.md](./CHANGELOG.md)")

    return "\n".join(lines)
