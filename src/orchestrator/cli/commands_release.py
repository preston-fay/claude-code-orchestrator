"""Release management commands."""

from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console

console = Console()

# Release command group
release_app = typer.Typer(name="release", help="Release management: versioning, changelog, gates, GitHub releases")

@release_app.command(name="prepare")
def release_prepare(
    bump: Optional[str] = typer.Option(
        None, "--bump", help="Version bump type: major, minor, patch (auto-detect if omitted)"
    ),
    prerelease: Optional[str] = typer.Option(
        None, "--prerelease", help="Prerelease identifier (e.g., alpha.1, beta.2, rc.1)"
    ),
    skip_gates: Optional[List[str]] = typer.Option(
        None, "--skip-gate", help="Gate to skip (can be repeated)"
    ),
):
    """
    Prepare release: version bump, changelog, quality gates.

    Analyzes commits since last release, determines version bump,
    runs quality gates, generates changelog and release notes.

    Does not modify files or create tags - use 'release cut' after reviewing.
    """
    from src.orchestrator.release import prepare_release
    from src.orchestrator.version import BumpType
    from rich.table import Table

    console.print("[bold]🚀 Preparing Release[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        # Parse bump type
        bump_type = None
        if bump:
            try:
                bump_type = BumpType(bump.lower())
            except ValueError:
                console.print(f"[red]✗ Invalid bump type: {bump}[/red]")
                console.print("Valid options: major, minor, patch")
                return

        # Prepare release
        plan = prepare_release(
            project_root=Path.cwd(),
            bump_type=bump_type,
            prerelease=prerelease,
            skip_gates=skip_gates,
        )

        # Show version bump
        console.print("[bold]Version:[/bold]")
        console.print(f"  Current: {plan.current_version}")
        console.print(f"  New: [cyan]{plan.new_version}[/cyan] ({plan.bump_type.value} bump)")
        console.print()

        # Show commits
        console.print(f"[bold]Commits:[/bold] {len(plan.commits)} since last release")
        if plan.commits:
            for commit in plan.commits[:5]:
                scope = f"({commit.scope})" if commit.scope else ""
                console.print(f"  • {commit.type}{scope}: {commit.description[:60]}")
            if len(plan.commits) > 5:
                console.print(f"  ... and {len(plan.commits) - 5} more")
        console.print()

        # Show quality gates
        console.print(f"[bold]Quality Gates:[/bold] {plan.gates_report.summary}")
        console.print()

        gate_table = Table()
        gate_table.add_column("Gate", style="cyan")
        gate_table.add_column("Status", style="bold")
        gate_table.add_column("Message")

        for gate in plan.gates_report.gates:
            status_emoji = {
                "pass": "✅",
                "warn": "⚠️",
                "fail": "❌",
                "skip": "⏭️",
            }.get(gate.status.value, "❓")

            gate_table.add_row(
                gate.gate_name,
                f"{status_emoji} {gate.status.value.upper()}",
                gate.message,
            )

        console.print(gate_table)
        console.print()

        # Show assets
        if plan.assets:
            console.print(f"[bold]Release Assets:[/bold] {len(plan.assets)} file(s)")
            for asset in plan.assets[:5]:
                console.print(f"  • {asset.name}")
            if len(plan.assets) > 5:
                console.print(f"  ... and {len(plan.assets) - 5} more")
            console.print()

        # Decision
        if plan.ready_to_release:
            console.print("[green bold]✓ Ready to Release[/green bold]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Review changelog preview above")
            console.print("  2. Run: [cyan]orchestrator release cut[/cyan]")
        else:
            console.print("[red bold]✗ Not Ready - Fix Gate Failures[/red bold]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Fix failed quality gates")
            console.print("  2. Re-run: [cyan]orchestrator release prepare[/cyan]")
            console.print("  3. Or force with: [yellow]orchestrator release cut --force[/yellow] (not recommended)")

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Release preparation failed: {e}[/red]")
        raise


@release_app.command(name="cut")
def release_cut(
    force: bool = typer.Option(
        False, "--force", help="Force release even if gates failed (NOT RECOMMENDED)"
    ),
    no_push: bool = typer.Option(
        False, "--no-push", help="Don't push tag to remote"
    ),
    no_github: bool = typer.Option(
        False, "--no-github", help="Don't create GitHub release"
    ),
    draft: bool = typer.Option(
        False, "--draft", help="Create GitHub release as draft"
    ),
    bump: Optional[str] = typer.Option(
        None, "--bump", help="Version bump type (run prepare first for safety)"
    ),
):
    """
    Execute release: version bump, tag, push, GitHub release.

    IMPORTANT: Run 'release prepare' first to preview changes!

    This command:
    1. Updates version file
    2. Updates CHANGELOG.md
    3. Commits changes
    4. Creates git tag
    5. Pushes to remote (unless --no-push)
    6. Creates GitHub release with assets (unless --no-github)
    """
    from src.orchestrator.release import prepare_release, cut_release
    from src.orchestrator.version import BumpType

    console.print("[bold]✂️  Cutting Release[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        # Prepare release (same as prepare command)
        bump_type = None
        if bump:
            try:
                bump_type = BumpType(bump.lower())
            except ValueError:
                console.print(f"[red]✗ Invalid bump type: {bump}[/red]")
                return

        console.print("[dim]Preparing release plan...[/dim]")
        plan = prepare_release(
            project_root=Path.cwd(),
            bump_type=bump_type,
        )

        console.print(f"Version: {plan.current_version} → [cyan]{plan.new_version}[/cyan]")
        console.print(f"Commits: {len(plan.commits)}")
        console.print(f"Gates: {plan.gates_report.summary}")
        console.print()

        # Check if ready
        if not plan.ready_to_release and not force:
            console.print("[red bold]✗ Cannot release: quality gates failed[/red bold]")
            console.print()
            console.print("Fix issues and try again, or use --force to override (not recommended)")
            return

        if force and not plan.ready_to_release:
            console.print("[yellow]⚠️  Forcing release despite gate failures (--force)[/yellow]")
            console.print()

        # Confirm
        if not force:
            confirm = typer.confirm(f"Create release {plan.new_version}?")
            if not confirm:
                console.print("[yellow]Release cancelled[/yellow]")
                return

        console.print()
        console.print("[dim]Executing release...[/dim]")

        # Execute release
        cut_release(
            project_root=Path.cwd(),
            plan=plan,
            push=not no_push,
            create_gh_release=not no_github,
            draft=draft,
        )

        console.print()
        console.print("[green bold]✓ Release Complete![/green bold]")
        console.print()
        console.print(f"  Version: [cyan]{plan.new_version}[/cyan]")
        console.print(f"  Tag: v{plan.new_version}")

        if not no_push:
            console.print(f"  Pushed: ✓")

        if not no_github:
            console.print(f"  GitHub Release: ✓")

        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print(f"  • Verify: [cyan]orchestrator release verify[/cyan]")
        console.print(f"  • View on GitHub: [cyan]gh release view v{plan.new_version}[/cyan]")

    except Exception as e:
        console.print(f"[red]✗ Release failed: {e}[/red]")
        raise


@release_app.command(name="verify")
def release_verify(
    version: Optional[str] = typer.Argument(None, help="Version to verify (default: current)"),
):
    """
    Verify release was successful.

    Checks:
    - Version file updated
    - Git tag exists locally
    - Tag pushed to remote
    - GitHub release created
    """
    from src.orchestrator.release import verify_release
    from src.orchestrator.version import Version, get_current_version
    from rich.table import Table

    console.print("[bold]🔍 Verifying Release[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        # Parse version
        version_obj = None
        if version:
            version_obj = Version.parse(version)
        else:
            version_obj = get_current_version(Path.cwd())

        console.print(f"Verifying: [cyan]{version_obj}[/cyan]")
        console.print()

        # Run verification
        success = verify_release(Path.cwd(), version_obj)

        if success:
            console.print("[green bold]✓ Release Verified Successfully[/green bold]")
        else:
            console.print("[yellow]⚠️  Some verification checks failed[/yellow]")
            console.print()
            console.print("This may be expected if you didn't push or create GitHub release")

    except Exception as e:
        console.print(f"[red]✗ Verification failed: {e}[/red]")
        raise


@release_app.command(name="rollback")
def release_rollback(
    version: str = typer.Argument(..., help="Version to rollback (e.g., 1.2.3)"),
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
):
    """
    Rollback release: delete tag and GitHub release.

    DESTRUCTIVE: Cannot be undone easily!

    This will:
    - Delete local git tag
    - Delete remote git tag
    - Delete GitHub release

    Does NOT revert the version bump commit - use git revert for that.
    """
    from src.orchestrator.release import rollback_release
    from src.orchestrator.version import Version

    console.print("[bold]⏪ Rolling Back Release[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        version_obj = Version.parse(version)

        console.print(f"[yellow]⚠️  Rolling back: {version_obj}[/yellow]")
        console.print()
        console.print("This will:")
        console.print("  • Delete local tag")
        console.print("  • Delete remote tag")
        console.print("  • Delete GitHub release")
        console.print()

        if not confirm:
            confirmed = typer.confirm("Are you sure?")
            if not confirmed:
                console.print("[yellow]Rollback cancelled[/yellow]")
                return

        rollback_release(Path.cwd(), version_obj)

        console.print()
        console.print("[green]✓ Release rolled back[/green]")
        console.print()
        console.print("[bold]To revert version bump commit:[/bold]")
        console.print("  git revert HEAD")

    except Exception as e:
        console.print(f"[red]✗ Rollback failed: {e}[/red]")
        raise

