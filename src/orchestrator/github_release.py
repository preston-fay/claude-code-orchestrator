"""GitHub Releases integration with artifacts and release notes."""

import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .version import Version


@dataclass
class ReleaseAsset:
    """GitHub release asset (artifact)."""

    path: Path
    name: str
    label: Optional[str] = None


def create_github_release(
    project_root: Path,
    version: Version,
    release_notes: str,
    assets: Optional[List[ReleaseAsset]] = None,
    draft: bool = False,
    prerelease: bool = False,
) -> Dict[str, Any]:
    """
    Create GitHub release using gh CLI.

    Args:
        project_root: Project root directory
        version: Version being released
        release_notes: Markdown release notes
        assets: List of assets to upload
        draft: Create as draft
        prerelease: Mark as prerelease

    Returns:
        Release data from GitHub API

    Raises:
        RuntimeError: If gh CLI not available or release fails
    """
    tag = f"v{version}"

    # Check if gh CLI is available
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise RuntimeError(
            "gh CLI not found. Install from: https://cli.github.com/\n"
            "Or use: brew install gh"
        )

    # Build gh release create command
    cmd = [
        "gh",
        "release",
        "create",
        tag,
        "--title",
        f"Release {version}",
        "--notes",
        release_notes,
    ]

    if draft:
        cmd.append("--draft")

    if prerelease:
        cmd.append("--prerelease")

    # Add assets
    if assets:
        for asset in assets:
            if not asset.path.exists():
                raise FileNotFoundError(f"Asset not found: {asset.path}")

            cmd.append(str(asset.path))

            # Add asset label if provided
            if asset.label:
                cmd.extend(["--notes", f"Attachment: {asset.label}"])

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse release URL from output
        release_url = result.stdout.strip()

        # Get release details
        release_data = get_release(project_root, tag)

        return release_data

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Failed to create GitHub release: {error_msg}")


def get_release(project_root: Path, tag: str) -> Dict[str, Any]:
    """
    Get GitHub release details.

    Args:
        project_root: Project root directory
        tag: Release tag

    Returns:
        Release data from GitHub API
    """
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--json", "url,name,tagName,createdAt,assets"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get release {tag}: {e.stderr}")


def delete_release(project_root: Path, tag: str, delete_tag: bool = False) -> None:
    """
    Delete GitHub release.

    Args:
        project_root: Project root directory
        tag: Release tag
        delete_tag: Also delete git tag

    Raises:
        RuntimeError: If deletion fails
    """
    cmd = ["gh", "release", "delete", tag, "--yes"]

    if delete_tag:
        cmd.append("--cleanup-tag")

    try:
        subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to delete release {tag}: {e.stderr}")


def list_releases(project_root: Path, limit: int = 10) -> List[Dict[str, Any]]:
    """
    List GitHub releases.

    Args:
        project_root: Project root directory
        limit: Maximum number of releases to fetch

    Returns:
        List of release data
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "release",
                "list",
                "--limit",
                str(limit),
                "--json",
                "tagName,name,createdAt,isPrerelease,isDraft",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to list releases: {e.stderr}")


def prepare_release_assets(project_root: Path, version: Version) -> List[ReleaseAsset]:
    """
    Prepare release assets for upload.

    Collects:
    - Package wheels from dist/
    - Latest gates report
    - Artifact bundles for latest run

    Args:
        project_root: Project root directory
        version: Version being released

    Returns:
        List of ReleaseAsset objects
    """
    assets = []

    # 1. Package distributions
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        for wheel in dist_dir.glob("*.whl"):
            # Only include wheels for this version
            if str(version).replace(".", "_") in wheel.name:
                assets.append(
                    ReleaseAsset(
                        path=wheel,
                        name=wheel.name,
                        label=f"Python wheel for {version}",
                    )
                )

        for tarball in dist_dir.glob("*.tar.gz"):
            if str(version) in tarball.name:
                assets.append(
                    ReleaseAsset(
                        path=tarball,
                        name=tarball.name,
                        label=f"Source distribution for {version}",
                    )
                )

    # 2. Latest quality gates report
    gates_dir = project_root / ".claude" / "release"
    if gates_dir.exists():
        gate_reports = sorted(gates_dir.glob("gates_report_*.json"), key=lambda p: p.stat().st_mtime)
        if gate_reports:
            latest_gates = gate_reports[-1]
            assets.append(
                ReleaseAsset(
                    path=latest_gates,
                    name="quality_gates_report.json",
                    label="Pre-release quality gates report",
                )
            )

    # 3. CHANGELOG.md
    changelog = project_root / "CHANGELOG.md"
    if changelog.exists():
        assets.append(
            ReleaseAsset(
                path=changelog,
                name="CHANGELOG.md",
                label="Full project changelog",
            )
        )

    return assets


def check_github_auth(project_root: Path) -> bool:
    """
    Check if gh CLI is authenticated.

    Args:
        project_root: Project root directory

    Returns:
        True if authenticated
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_repo_info(project_root: Path) -> Dict[str, str]:
    """
    Get GitHub repository info.

    Args:
        project_root: Project root directory

    Returns:
        Dict with owner and repo name
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "owner,name"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        return {
            "owner": data["owner"]["login"],
            "repo": data["name"],
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return {}
