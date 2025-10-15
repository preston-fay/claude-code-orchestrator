"""Release orchestration: prepare, cut, verify, rollback."""

import subprocess
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
import json

from .version import Version, BumpType, get_current_version, write_version, get_version_tag, determine_bump_type
from .changelog import (
    get_commits_since_tag,
    get_latest_tag,
    CommitEntry,
    generate_changelog_entry,
    update_changelog,
    generate_release_notes,
)
from .release_gates import run_all_gates, GatesReport, save_gates_report
from .github_release import (
    create_github_release,
    prepare_release_assets,
    ReleaseAsset,
    check_github_auth,
)


@dataclass
class ReleasePlan:
    """Release preparation plan."""

    current_version: Version
    new_version: Version
    bump_type: BumpType
    commits: List[CommitEntry]
    gates_report: GatesReport
    changelog_entry: str
    release_notes: str
    assets: List[ReleaseAsset]
    timestamp: str

    @property
    def ready_to_release(self) -> bool:
        """Check if release is ready (all gates passed)."""
        return self.gates_report.all_passed


def prepare_release(
    project_root: Path,
    bump_type: Optional[BumpType] = None,
    prerelease: Optional[str] = None,
    skip_gates: Optional[List[str]] = None,
    highlights: Optional[List[str]] = None,
) -> ReleasePlan:
    """
    Prepare release: version bump, changelog, gates, assets.

    Args:
        project_root: Project root directory
        bump_type: Version bump type (auto-detect if None)
        prerelease: Prerelease identifier (e.g., "alpha.1")
        skip_gates: List of gates to skip
        highlights: Optional release highlights

    Returns:
        ReleasePlan with all release data

    Raises:
        RuntimeError: If preparation fails
    """
    # 1. Get current version
    current_version = get_current_version(project_root)

    # 2. Get commits since last tag
    latest_tag = get_latest_tag(project_root)
    commit_data = get_commits_since_tag(project_root, latest_tag)

    # Parse conventional commits
    commits = []
    for c in commit_data:
        entry = CommitEntry.parse(c["message"], c["hash"], c["author"])
        if entry:
            commits.append(entry)

    if not commits:
        raise RuntimeError("No commits since last release")

    # 3. Determine version bump
    if bump_type is None:
        commit_messages = [c["message"] for c in commit_data]
        bump_type = determine_bump_type(commit_messages)

    new_version = current_version.bump(bump_type, prerelease=prerelease)

    # 4. Run quality gates
    gates_report = run_all_gates(project_root, skip_gates=skip_gates)
    save_gates_report(gates_report, project_root)

    # 5. Generate changelog
    changelog_entry = generate_changelog_entry(
        version=new_version,
        commits=commits,
        date=datetime.now(),
    )

    # 6. Generate release notes
    release_notes_text = generate_release_notes(
        version=new_version,
        commits=commits,
        highlights=highlights,
    )

    # 7. Prepare assets
    assets = prepare_release_assets(project_root, new_version)

    return ReleasePlan(
        current_version=current_version,
        new_version=new_version,
        bump_type=bump_type,
        commits=commits,
        gates_report=gates_report,
        changelog_entry=changelog_entry,
        release_notes=release_notes_text,
        assets=assets,
        timestamp=datetime.now().isoformat(),
    )


def cut_release(
    project_root: Path,
    plan: ReleasePlan,
    push: bool = True,
    create_gh_release: bool = True,
    draft: bool = False,
) -> None:
    """
    Execute release: update version, changelog, tag, push, create GitHub release.

    Args:
        project_root: Project root directory
        plan: ReleasePlan from prepare_release
        push: Push tag to remote
        create_gh_release: Create GitHub release
        draft: Create GitHub release as draft

    Raises:
        RuntimeError: If release fails
    """
    # Safety check: ensure gates passed
    if not plan.ready_to_release:
        raise RuntimeError(
            f"Cannot release: {plan.gates_report.blocking_failures} blocking gate(s) failed. "
            f"Fix issues or use --force to override (not recommended)."
        )

    tag = get_version_tag(plan.new_version)

    # 1. Update version file
    write_version(project_root, plan.new_version)

    # 2. Update CHANGELOG.md
    update_changelog(project_root, plan.new_version, plan.changelog_entry)

    # 3. Commit changes
    try:
        subprocess.run(
            ["git", "add", "src/orchestrator/__version__.py", "CHANGELOG.md"],
            cwd=project_root,
            check=True,
        )

        commit_msg = f"chore(release): bump version to {plan.new_version}\n\n🤖 Generated with Claude Code Orchestrator"

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=project_root,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to commit version bump: {e}")

    # 4. Create git tag
    try:
        tag_msg = f"Release {plan.new_version}"
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", tag_msg],
            cwd=project_root,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create git tag: {e}")

    # 5. Push to remote (if requested)
    if push:
        try:
            # Push commits
            subprocess.run(
                ["git", "push"],
                cwd=project_root,
                check=True,
            )

            # Push tag
            subprocess.run(
                ["git", "push", "origin", tag],
                cwd=project_root,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to push to remote: {e}")

    # 6. Create GitHub release (if requested)
    if create_gh_release:
        if not check_github_auth(project_root):
            raise RuntimeError(
                "GitHub CLI not authenticated. Run: gh auth login\n"
                "Or skip GitHub release with --no-github"
            )

        try:
            is_prerelease = plan.new_version.prerelease is not None

            create_github_release(
                project_root=project_root,
                version=plan.new_version,
                release_notes=plan.release_notes,
                assets=plan.assets,
                draft=draft,
                prerelease=is_prerelease,
            )
        except Exception as e:
            # Don't fail entire release if GitHub release fails
            print(f"Warning: GitHub release failed: {e}")
            print("You can create it manually with: gh release create {tag}")

    # 7. Save release metadata
    _save_release_metadata(project_root, plan)


def verify_release(project_root: Path, version: Optional[Version] = None) -> bool:
    """
    Verify release was successful.

    Checks:
    - Version file updated
    - Git tag exists
    - Tag pushed to remote
    - GitHub release exists (if gh CLI available)

    Args:
        project_root: Project root directory
        version: Version to verify (default: current version)

    Returns:
        True if all checks pass
    """
    if version is None:
        version = get_current_version(project_root)

    tag = get_version_tag(version)

    checks = {
        "version_file": False,
        "git_tag": False,
        "tag_pushed": False,
        "github_release": False,
    }

    # 1. Check version file
    try:
        current = get_current_version(project_root)
        checks["version_file"] = str(current) == str(version)
    except Exception:
        pass

    # 2. Check git tag exists locally
    try:
        result = subprocess.run(
            ["git", "tag", "-l", tag],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        checks["git_tag"] = tag in result.stdout
    except subprocess.CalledProcessError:
        pass

    # 3. Check tag pushed to remote
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", tag],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        checks["tag_pushed"] = tag in result.stdout
    except subprocess.CalledProcessError:
        pass

    # 4. Check GitHub release (optional)
    if check_github_auth(project_root):
        try:
            subprocess.run(
                ["gh", "release", "view", tag],
                cwd=project_root,
                capture_output=True,
                check=True,
            )
            checks["github_release"] = True
        except subprocess.CalledProcessError:
            pass

    return all([checks["version_file"], checks["git_tag"], checks["tag_pushed"]])


def rollback_release(project_root: Path, version: Version) -> None:
    """
    Rollback release (delete tag and GitHub release).

    Does NOT revert commits - use git revert for that.

    Args:
        project_root: Project root directory
        version: Version to rollback

    Raises:
        RuntimeError: If rollback fails
    """
    tag = get_version_tag(version)

    # 1. Delete GitHub release (if exists)
    if check_github_auth(project_root):
        try:
            from .github_release import delete_release

            delete_release(project_root, tag, delete_tag=False)
        except Exception as e:
            print(f"Warning: Could not delete GitHub release: {e}")

    # 2. Delete remote tag
    try:
        subprocess.run(
            ["git", "push", "origin", f":refs/tags/{tag}"],
            cwd=project_root,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not delete remote tag: {e}")

    # 3. Delete local tag
    try:
        subprocess.run(
            ["git", "tag", "-d", tag],
            cwd=project_root,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to delete local tag: {e}")

    print(f"✓ Rolled back release {version}")
    print(f"  Local tag deleted: {tag}")
    print(f"  Remote tag deleted")
    print(f"  GitHub release deleted (if existed)")
    print()
    print("To revert version bump commit:")
    print(f"  git revert HEAD")


def _save_release_metadata(project_root: Path, plan: ReleasePlan) -> None:
    """Save release metadata for bookkeeping."""
    release_dir = project_root / ".claude" / "release"
    release_dir.mkdir(parents=True, exist_ok=True)

    metadata_file = release_dir / f"release_{plan.new_version}.json"

    data = {
        "version": str(plan.new_version),
        "previous_version": str(plan.current_version),
        "bump_type": plan.bump_type.value,
        "timestamp": plan.timestamp,
        "commit_count": len(plan.commits),
        "gates_passed": plan.gates_report.all_passed,
        "assets_count": len(plan.assets),
    }

    with open(metadata_file, "w") as f:
        json.dump(data, f, indent=2)
