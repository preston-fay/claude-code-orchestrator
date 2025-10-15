"""Unified orchestrator CLI - composes intake and data command groups."""

from pathlib import Path
from typing import Optional, List
import sys

try:
    import typer
    from rich.console import Console
except ImportError:
    print("Warning: Required dependencies not installed. Run: pip install -e .")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import command groups
from src.intake.cli import app as intake_app
from src.orchestrator.nl_triggers import route_nl_command, describe_triggers

# Create main app
app = typer.Typer(
    name="orchestrator",
    help="Claude Code Orchestrator - Unified CLI for project orchestration",
    add_completion=False,
)
console = Console()

# Add intake command group
app.add_typer(intake_app, name="intake")

# Add style command group
try:
    from src.orchestrator.style import app as style_app
    app.add_typer(style_app, name="style")
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import style CLI: {e}[/yellow]")

# Add data command group (import commands from existing src/cli.py)
try:
    from src.cli import app as data_cli_app
    # Create a sub-app for data commands
    data_app = typer.Typer(name="data", help="Data pipeline commands")

    # Import individual commands from src.cli
    from src.cli import ingest, transform, train, evaluate, status as data_status

    # Register data commands
    data_app.command(name="ingest")(ingest)
    data_app.command(name="transform")(transform)
    data_app.command(name="train")(train)
    data_app.command(name="evaluate")(evaluate)
    data_app.command(name="status")(data_status)

    # Add data group to main app
    app.add_typer(data_app, name="data")

except ImportError as e:
    console.print(f"[yellow]Warning: Could not import data CLI: {e}[/yellow]")


@app.command()
def status():
    """Show orchestrator status and current workflow state."""
    from src.orchestrator.state import get_state

    console.print("[bold blue]📊 Orchestrator Status[/bold blue]\n")

    state = get_state()
    full_state = state.get_full_state()

    status_emoji = {
        "idle": "⚪",
        "running": "🟢",
        "completed": "✅",
        "aborted": "🔴",
    }

    current_status = full_state.get("status", "idle")
    emoji = status_emoji.get(current_status, "❓")

    console.print(f"Status: {emoji} [bold]{current_status.upper()}[/bold]")

    if full_state.get("current_project"):
        console.print(f"Project: [cyan]{full_state['current_project']}[/cyan]")

    if full_state.get("current_phase"):
        console.print(f"Phase: [yellow]{full_state['current_phase']}[/yellow]")

    if full_state.get("completed_phases"):
        console.print(f"\nCompleted phases:")
        for phase in full_state["completed_phases"]:
            console.print(f"  ✓ {phase}")

    if full_state.get("started_at"):
        console.print(f"\nStarted: {full_state['started_at']}")

    if full_state.get("updated_at"):
        console.print(f"Updated: {full_state['updated_at']}")


@app.command()
def triggers():
    """Show available natural language triggers."""
    console.print(describe_triggers())


@app.command()
def version():
    """Show orchestrator version."""
    from src.orchestrator import __version__
    console.print(f"Claude Code Orchestrator v{__version__}")


@app.command()
def quickstart(
    type: str = typer.Option(..., "--type", help="Project type (webapp, analytics, ml, library, service)"),
    name: str = typer.Option(..., "--name", help="Project name"),
):
    """
    Quickstart a new project workflow.

    Combines intake generation and planning phase execution into one command.
    Generates intake YAML, starts run, executes planning phase, and pauses at consensus.

    Example:
        orchestrator quickstart --type webapp --name my-app
    """
    from src.intake.generator import generate_intake
    from src.orchestrator.runloop import Orchestrator
    import tempfile

    console.print("[bold]🚀 Quickstart: New Project Workflow[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        # Step 1: Generate intake
        console.print(f"[bold]Step 1:[/bold] Generating intake for {type} project: {name}")

        # Create intake YAML in temp location
        intake_data = {
            "project": {
                "name": name,
                "type": type,
                "description": f"New {type} project: {name}",
                "directory": f"./{name}",
            },
            "requirements": {
                "functional": [
                    f"Implement {type} application with best practices",
                    "Include testing framework",
                    "Add comprehensive documentation",
                ],
                "technical": [
                    f"Follow {type} architecture patterns",
                    "Ensure code quality and maintainability",
                    "Include CI/CD configuration",
                ],
            },
            "constraints": {
                "timeline": "Standard development timeline",
                "budget": "N/A",
                "technical": [
                    "Use industry-standard tools and frameworks",
                    "Follow security best practices",
                ],
            },
        }

        import yaml
        intake_path = Path(tempfile.gettempdir()) / f"intake_{name}.yaml"
        with open(intake_path, "w") as f:
            yaml.dump(intake_data, f, default_flow_style=False, sort_keys=False)

        console.print(f"  ✓ Intake generated: [link]{intake_path}[/link]")
        console.print()

        # Step 2: Start orchestrator run
        console.print("[bold]Step 2:[/bold] Starting orchestrator run")

        orch = Orchestrator()
        orch.start_run(intake_path=intake_path, from_phase=None)

        console.print(f"  ✓ Run started: {orch.state.run_id}")
        console.print()

        # Step 3: Execute planning phase
        console.print("[bold]Step 3:[/bold] Executing planning phase")

        outcome = orch.next_phase()

        if outcome.success:
            console.print(f"  ✓ Planning phase completed")
        else:
            console.print(f"  ⚠️  Planning phase completed with issues")

        console.print()

        # Step 4: Show consensus status
        if outcome.awaiting_consensus:
            console.print("[bold]Step 4:[/bold] Awaiting Consensus")
            console.print()
            console.print("[yellow]📋 Planning phase requires review before proceeding[/yellow]")
            console.print()
            console.print(f"Review: [link].claude/consensus/REQUEST.md[/link]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Review the consensus request")
            console.print("  2. Run: [cyan]orchestrator run approve[/cyan]")
            console.print("  3. Run: [cyan]orchestrator run next[/cyan] to continue workflow")
        else:
            console.print("[green]✓ Quickstart complete![/green]")
            console.print()
            console.print("Run [cyan]orchestrator run next[/cyan] to proceed")

        console.print()
        console.print("━" * 60)
        console.print("[dim]Use 'orchestrator run status' to check progress[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Quickstart failed: {e}[/red]")
        raise


# Run command group
run_app = typer.Typer(name="run", help="Run orchestration workflows and hygiene checks")
app.add_typer(run_app, name="run")


@run_app.command(name="repo-hygiene")
def repo_hygiene(
    apply: bool = typer.Option(
        False, "--apply", help="Apply approved cleanup actions (requires Consensus)"
    ),
    large_file_mb: Optional[int] = typer.Option(
        None, "--large-file-mb", help="Override large file threshold (MB)"
    ),
):
    """
    Run repository hygiene scan (detect orphans, large files, dead code, notebook outputs).

    By default, runs in dry-run mode and generates reports without making changes.
    Use --apply to execute approved cleanup actions after Consensus review.
    """
    from pathlib import Path
    from src.orchestrator.state import is_busy
    from src.steward.config import HygieneConfig
    from src.steward.scanner import scan_large_files, scan_orphans
    from src.steward.dead_code import analyze_dead_code
    from src.steward.notebooks import check_notebooks
    from src.steward.glue import aggregate_reports

    # Check busy state
    if is_busy():
        console.print(
            "[yellow]⚠️  Orchestrator is currently running a workflow.[/yellow]"
        )
        console.print(
            "[dim]Please finish the current workflow or run: orchestrator run --abort[/dim]"
        )
        return

    console.print("[bold]🧹 Repository Hygiene Scan[/bold]")
    console.print("━" * 60)
    console.print()

    root = Path.cwd()

    # Load config
    config = HygieneConfig()
    if large_file_mb:
        config.config["large_file_mb"] = large_file_mb

    try:
        # Step 1: Run scanners
        console.print("📦 Scanning for large files...")
        large_files = scan_large_files(root, config)
        console.print(f"   Found {len(large_files)} large files")

        console.print("🗑️  Scanning for orphaned files...")
        orphans = scan_orphans(root, config)
        console.print(f"   Found {len(orphans)} potential orphans")

        console.print("🔍 Analyzing dead code...")
        dead_code_results = analyze_dead_code(root, config)
        console.print(
            f"   Found {len(dead_code_results['functions'])} unused functions, "
            f"{len(dead_code_results['imports'])} unused imports"
        )

        console.print("📓 Checking Jupyter notebooks...")
        notebooks = check_notebooks(root, config, clear_outputs=apply)
        whitelisted_count = sum(1 for nb in notebooks if nb["whitelisted"])
        needs_cleanup = len(notebooks) - whitelisted_count
        console.print(f"   Found {len(notebooks)} notebooks with outputs")
        console.print(f"   - {whitelisted_count} whitelisted (OK)")
        console.print(f"   - {needs_cleanup} need cleanup")

        # Step 2: Aggregate reports
        console.print()
        console.print("📊 Aggregating reports...")
        stats = aggregate_reports(root, config)

        # Step 3: Show results
        console.print()
        console.print("[bold green]✓ Scan complete[/bold green]")
        console.print()

        # Display cleanliness score
        score_data = stats.get("cleanliness_score", {})
        if score_data:
            score = score_data["score"]
            grade = score_data["grade"]

            if score >= 95:
                score_color = "green"
            elif score >= 85:
                score_color = "yellow"
            else:
                score_color = "red"

            console.print(f"[bold]Cleanliness Score:[/bold] [{score_color}]{score}/100 (Grade: {grade})[/{score_color}]")
            console.print()

        console.print("[bold]Summary:[/bold]")
        console.print(
            f"  - {stats['orphans']['count']} orphaned files "
            f"({stats['orphans']['total_size_mb']:.2f} MB)"
        )
        console.print(
            f"  - {stats['large_files']['count']} large binaries "
            f"({stats['large_files']['total_size_mb']:.2f} MB)"
        )
        console.print(
            f"  - {stats['dead_code']['functions']} unused functions, "
            f"{stats['dead_code']['imports']} unused imports"
        )
        console.print(f"  - {needs_cleanup} notebooks need output clearing")

        console.print()
        console.print("[bold]Reports generated:[/bold]")
        console.print("  - [link]reports/repo_hygiene_report.md[/link]")
        console.print("  - [link]reports/PR_PLAN.md[/link]")
        console.print("  - [link]reports/dead_code.md[/link]")
        console.print("  - [link]reports/large_files.csv[/link]")
        console.print("  - [link]reports/orphans.csv[/link]")
        console.print("  - [link]reports/hygiene_summary.json[/link]")

        # Check quality gates
        if stats['orphans']['count'] >= config.max_orphans_warn:
            console.print()
            console.print(f"[yellow]⚠️  Warning: {stats['orphans']['count']} orphans exceeds threshold ({config.max_orphans_warn})[/yellow]")

        if score < config.min_cleanliness_score:
            console.print()
            console.print(f"[red]❌ Cleanliness score {score} below minimum ({config.min_cleanliness_score})[/red]")

        if not apply:
            console.print()
            console.print("[yellow]⚠️  Dry-run mode: no changes applied.[/yellow]")
            console.print("[dim]Review reports/PR_PLAN.md for proposed actions.[/dim]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Review reports manually")
            console.print("  2. Run: [cyan]orchestrator run repo-hygiene --apply[/cyan]")
            console.print("     (will route to Consensus for approval)")
        else:
            # Check if apply is blocked by safety thresholds
            import json
            summary_path = root / "reports" / "hygiene_summary.json"
            if summary_path.exists():
                with open(summary_path) as f:
                    summary = json.load(f)

            # Read PR plan to check for BLOCKED status
            pr_plan_path = root / "reports" / "PR_PLAN.md"
            if pr_plan_path.exists():
                with open(pr_plan_path) as f:
                    pr_plan_content = f.read()
                    if "APPLY BLOCKED" in pr_plan_content:
                        console.print()
                        console.print("[red bold]⚠️  APPLY BLOCKED - Safety thresholds exceeded[/red bold]")
                        console.print("[dim]See reports/PR_PLAN.md for details[/dim]")
                        console.print()
                        console.print("The cleanup is too large for automatic application.")
                        console.print("Split into smaller batches or adjust thresholds in configs/hygiene.yaml")
                        return

            console.print()
            console.print(
                "[bold green]✓ Cleanup actions executed (approved items only)[/bold green]"
            )
            console.print(
                "[dim]Review the generated PR plan and create a pull request.[/dim]"
            )

    except Exception as e:
        console.print(f"[red]✗ Error during hygiene scan: {e}[/red]")
        raise


@run_app.command(name="start")
def run_start(
    intake: Optional[Path] = typer.Option(
        None, "--intake", help="Path to intake YAML file"
    ),
    from_phase: Optional[str] = typer.Option(
        None, "--from", help="Start from specific phase (must be enabled)"
    ),
):
    """
    Initialize a new orchestrator run.

    Starts a new workflow execution, optionally loading project configuration
    from an intake YAML file. Can start from a specific phase for testing.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]🚀 Starting Orchestrator Run[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        # Check if already running
        if orch.state.status.value not in ("idle", "completed", "aborted"):
            console.print(
                f"[yellow]⚠️  Run already active (status: {orch.state.status.value})[/yellow]"
            )
            console.print(f"   Run ID: {orch.state.run_id}")
            console.print()
            console.print("Use [cyan]orchestrator run abort[/cyan] to stop current run")
            return

        orch.start_run(intake_path=intake, from_phase=from_phase)

        console.print(f"[green]✓ Run initialized: {orch.state.run_id}[/green]")
        console.print(f"  Current phase: [yellow]{orch.state.current_phase}[/yellow]")

        if intake:
            console.print(f"  Intake loaded: [cyan]{intake}[/cyan]")

        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  • Run [cyan]orchestrator run next[/cyan] to execute current phase")
        console.print("  • Run [cyan]orchestrator run status[/cyan] to view state")

    except Exception as e:
        console.print(f"[red]✗ Error starting run: {e}[/red]")
        raise


@run_app.command(name="next")
def run_next(
    parallel: bool = typer.Option(
        False, "--parallel", help="Force parallel execution (only for parallel-enabled phases)"
    ),
    max_workers: Optional[int] = typer.Option(
        None, "--max-workers", help="Maximum parallel workers (capped by config limit)"
    ),
    timeout: Optional[int] = typer.Option(
        None, "--timeout", help="Timeout in seconds (overrides config)"
    ),
):
    """
    Execute the next phase in the workflow.

    Runs the current phase and advances to the next one. If a phase requires
    consensus, execution will pause and you'll need to approve/reject before continuing.

    Options:
        --parallel: Attempt parallel execution (only works for phases with parallel: true)
        --max-workers: Cap concurrent agents (limited by config max_parallel_agents)
        --timeout: Override timeout in seconds
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]⏭️  Executing Next Phase[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if orch.state.status.value == "idle":
            console.print("[yellow]⚠️  No active run[/yellow]")
            console.print("Start a run first with: [cyan]orchestrator run start[/cyan]")
            return

        console.print(f"Current phase: [yellow]{orch.state.current_phase}[/yellow]")
        console.print()

        # Pass overrides to orchestrator
        outcome = orch.next_phase(
            force_parallel=parallel,
            max_workers=max_workers,
            timeout_override=timeout
        )

        console.print(f"[green]✓ Phase {outcome.phase_name} executed[/green]")
        console.print()

        # Show agent outcomes
        console.print("[bold]Agent Results:[/bold]")
        for agent_outcome in outcome.agent_outcomes:
            status = "✅" if agent_outcome.success else "❌"
            console.print(f"  {status} {agent_outcome.agent_name}")
            if agent_outcome.notes:
                console.print(f"     {agent_outcome.notes[:100]}")

        console.print()

        # Show validation results
        if outcome.validation:
            val_emoji = {
                "pass": "✅",
                "partial": "⚠️",
                "fail": "❌",
            }
            emoji = val_emoji.get(outcome.validation.status.value, "❓")
            console.print(f"[bold]Validation:[/bold] {emoji} {outcome.validation.status.value.upper()}")
            console.print(f"  Found: {len(outcome.validation.found)} file(s)")
            console.print(f"  Missing: {len(outcome.validation.missing)} pattern(s)")
            console.print()

        # Check if consensus required
        if outcome.awaiting_consensus:
            console.print("[yellow bold]⏸️  Consensus Required[/yellow bold]")
            console.print()
            console.print(f"Phase [yellow]{outcome.phase_name}[/yellow] requires approval before proceeding.")
            console.print()
            console.print("Review: [link].claude/consensus/REQUEST.md[/link]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  • [green]orchestrator run approve[/green] - Approve and continue")
            console.print("  • [red]orchestrator run reject --reason \"...\"[/red] - Reject for revision")
        elif orch.state.status.value == "completed":
            console.print("[green bold]🎉 Run Completed Successfully![/green bold]")
            console.print()
            console.print(f"Completed phases: {len(orch.state.completed_phases)}")
        else:
            console.print(f"[bold]Next phase:[/bold] [yellow]{orch.state.current_phase}[/yellow]")
            console.print()
            console.print("Run [cyan]orchestrator run next[/cyan] to continue")

    except Exception as e:
        console.print(f"[red]✗ Error executing phase: {e}[/red]")
        raise


@run_app.command(name="status")
def run_status():
    """
    Show current run status and detailed state.

    Displays comprehensive information about the active run including:
    - Run ID and status
    - Current and completed phases
    - Checkpoint validation results
    - Repository cleanliness score (if available)
    """
    from src.orchestrator.runloop import Orchestrator
    import json

    try:
        orch = Orchestrator()
        status = orch.get_status()

        console.print("[bold]📊 Run Status[/bold]")
        console.print("━" * 60)
        console.print()

        # Status with emoji
        status_emoji = {
            "idle": "⚪",
            "running": "🟢",
            "awaiting_consensus": "⏸️",
            "needs_revision": "⚠️",
            "aborted": "🔴",
            "completed": "✅",
        }
        emoji = status_emoji.get(status["status"], "❓")
        console.print(f"Status: {emoji} [bold]{status['status'].upper()}[/bold]")

        if status.get("run_id"):
            console.print(f"Run ID: [cyan]{status['run_id']}[/cyan]")

        if status.get("current_phase"):
            console.print(f"Current Phase: [yellow]{status['current_phase']}[/yellow]")

        if status.get("completed_phases"):
            console.print(f"\n[bold]Completed Phases:[/bold]")
            for phase in status["completed_phases"]:
                artifacts = status.get("phase_artifacts", {}).get(phase, [])
                console.print(f"  ✓ {phase} ({len(artifacts)} artifacts)")

        if status.get("awaiting_consensus"):
            console.print(f"\n[yellow bold]⏸️  Awaiting Consensus[/yellow bold]")
            console.print(f"Phase: {status.get('consensus_phase')}")
            console.print("Review: [link].claude/consensus/REQUEST.md[/link]")

        # Checkpoints summary
        if status.get("checkpoints", {}).get("by_phase"):
            console.print(f"\n[bold]Checkpoint Validations:[/bold]")
            for phase, info in status["checkpoints"]["by_phase"].items():
                status_emoji_val = {"pass": "✅", "partial": "⚠️", "fail": "❌"}
                emoji_val = status_emoji_val.get(info["status"], "❓")
                console.print(f"  {emoji_val} {phase}: {info['status']}")

        # Cleanliness score
        if status.get("cleanliness_score") is not None:
            score = status["cleanliness_score"]
            grade = status.get("cleanliness_grade", "")

            if score >= 95:
                score_color = "green"
            elif score >= 85:
                score_color = "yellow"
            else:
                score_color = "red"

            console.print(f"\n[bold]Cleanliness Score:[/bold] [{score_color}]{score}/100 (Grade: {grade})[/{score_color}]")

        # Timestamps
        if status.get("created_at"):
            console.print(f"\n[dim]Created: {status['created_at']}[/dim]")
        if status.get("updated_at"):
            console.print(f"[dim]Updated: {status['updated_at']}[/dim]")

        # JSON output option
        console.print()
        console.print("[dim]Full JSON: orchestrator run status --json[/dim]")

    except Exception as e:
        console.print(f"[red]✗ Error getting status: {e}[/red]")
        raise


@run_app.command(name="approve")
def run_approve():
    """
    Approve consensus and proceed to next phase.

    Approves the current consensus request and advances the workflow
    to the next phase. Only works when status is 'awaiting_consensus'.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]✅ Approving Consensus[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if not orch.state.awaiting_consensus:
            console.print("[yellow]⚠️  No consensus awaiting approval[/yellow]")
            console.print(f"Current status: {orch.state.status.value}")
            return

        phase = orch.state.consensus_phase
        console.print(f"Approving phase: [yellow]{phase}[/yellow]")

        orch.approve_consensus()

        console.print()
        console.print(f"[green]✓ Consensus approved for {phase}[/green]")

        if orch.state.status.value == "completed":
            console.print()
            console.print("[green bold]🎉 Run Completed![/green bold]")
        else:
            console.print(f"Next phase: [yellow]{orch.state.current_phase}[/yellow]")
            console.print()
            console.print("Run [cyan]orchestrator run next[/cyan] to continue")

    except Exception as e:
        console.print(f"[red]✗ Error approving consensus: {e}[/red]")
        raise


@run_app.command(name="reject")
def run_reject(
    reason: str = typer.Option(
        ..., "--reason", help="Reason for rejection"
    ),
):
    """
    Reject consensus and mark phase for revision.

    Rejects the current consensus request and marks the run as needing
    revision. You must provide a reason for the rejection.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]❌ Rejecting Consensus[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if not orch.state.awaiting_consensus:
            console.print("[yellow]⚠️  No consensus awaiting decision[/yellow]")
            console.print(f"Current status: {orch.state.status.value}")
            return

        phase = orch.state.consensus_phase
        console.print(f"Rejecting phase: [yellow]{phase}[/yellow]")
        console.print(f"Reason: {reason}")

        orch.reject_consensus(reason)

        console.print()
        console.print(f"[red]✗ Consensus rejected for {phase}[/red]")
        console.print()
        console.print("Run status set to: [yellow]NEEDS_REVISION[/yellow]")
        console.print()
        console.print("After revisions, run [cyan]orchestrator run resume[/cyan] to continue")

    except Exception as e:
        console.print(f"[red]✗ Error rejecting consensus: {e}[/red]")
        raise


@run_app.command(name="abort")
def run_abort():
    """
    Abort the current run safely.

    Stops the current workflow execution while preserving all artifacts
    and logs. The run can be resumed later if needed.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]🛑 Aborting Run[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if orch.state.status.value == "idle":
            console.print("[yellow]⚠️  No active run to abort[/yellow]")
            return

        run_id = orch.state.run_id
        console.print(f"Aborting run: [cyan]{run_id}[/cyan]")

        orch.abort_run()

        console.print()
        console.print("[red]✓ Run aborted[/red]")
        console.print()
        console.print("All artifacts and logs preserved.")
        console.print("To resume: [cyan]orchestrator run resume[/cyan]")

    except Exception as e:
        console.print(f"[red]✗ Error aborting run: {e}[/red]")
        raise


@run_app.command(name="resume")
def run_resume():
    """
    Resume an aborted or paused run.

    Resumes a previously aborted run or a run that needs revision.
    Changes status back to 'running'.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]▶️  Resuming Run[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if orch.state.status.value not in ("aborted", "needs_revision"):
            console.print(f"[yellow]⚠️  Cannot resume from status: {orch.state.status.value}[/yellow]")
            return

        console.print(f"Resuming run: [cyan]{orch.state.run_id}[/cyan]")
        console.print(f"Current phase: [yellow]{orch.state.current_phase}[/yellow]")

        orch.resume_run()

        console.print()
        console.print("[green]✓ Run resumed[/green]")
        console.print()
        console.print("Run [cyan]orchestrator run next[/cyan] to continue")

    except Exception as e:
        console.print(f"[red]✗ Error resuming run: {e}[/red]")
        raise


@run_app.command(name="jump")
def run_jump(
    phase: str = typer.Argument(..., help="Target phase name"),
):
    """
    Jump to a specific phase (admin/debug mode).

    ⚠️  WARNING: This is an advanced command for debugging and surgery.
    Jumping phases can skip required validations and break workflow integrity.

    Only use when you know exactly what you're doing.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold red]⚠️  ADMIN MODE: Phase Jump[/bold red]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        console.print(f"[yellow]⚠️  Jumping to phase: {phase}[/yellow]")
        console.print()
        console.print("[red]This may skip required validations![/red]")

        orch.jump_to_phase(phase)

        console.print()
        console.print(f"[green]✓ Jumped to phase: {phase}[/green]")
        console.print()
        console.print("Run [cyan]orchestrator run next[/cyan] to execute")

    except Exception as e:
        console.print(f"[red]✗ Error jumping to phase: {e}[/red]")
        raise


@run_app.command(name="replay")
def run_replay(
    phase: str = typer.Argument(..., help="Phase to replay"),
):
    """
    Re-run a completed phase.

    Executes a phase again, writing a new validation report and appending
    to the run log. Useful for re-validating after manual changes.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]🔄 Replaying Phase[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        console.print(f"Replaying phase: [yellow]{phase}[/yellow]")

        outcome = orch.run_phase(phase)

        console.print()
        console.print(f"[green]✓ Phase replayed: {phase}[/green]")
        console.print(f"Success: {outcome.success}")

        if outcome.validation:
            console.print(f"Validation: {outcome.validation.status.value}")

    except Exception as e:
        console.print(f"[red]✗ Error replaying phase: {e}[/red]")
        raise


@run_app.command(name="log")
def run_log(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
):
    """
    Show tail of current run log.

    Displays the most recent log entries from the active run.
    Useful for debugging and monitoring workflow execution.
    """
    from src.orchestrator.runloop import Orchestrator

    try:
        orch = Orchestrator()

        if not orch.state.run_id:
            console.print("[yellow]⚠️  No active run[/yellow]")
            return

        console.print(f"[bold]📋 Run Log: {orch.state.run_id}[/bold]")
        console.print("━" * 60)
        console.print()

        log_tail = orch.get_log_tail(lines=lines)
        console.print(log_tail)

    except Exception as e:
        console.print(f"[red]✗ Error reading log: {e}[/red]")
        raise


@run_app.command(name="metrics")
def run_metrics():
    """
    Display metrics for the current run.

    Shows a compact table of:
    - Phase durations
    - Agent runtimes and retries
    - Last exit codes
    - Latest cleanliness score
    """
    from src.orchestrator.runloop import Orchestrator
    from src.orchestrator.metrics import MetricsTracker
    from rich.table import Table
    import json

    try:
        orch = Orchestrator()

        if not orch.state.run_id:
            console.print("[yellow]⚠️  No active run[/yellow]")
            return

        metrics_dir = orch.project_root / ".claude" / "metrics"
        metrics_file = metrics_dir / f"run_{orch.state.run_id}.json"

        if not metrics_file.exists():
            console.print("[yellow]⚠️  No metrics file found[/yellow]")
            console.print(f"Expected: {metrics_file}")
            return

        # Load metrics
        with open(metrics_file, "r") as f:
            metrics = json.load(f)

        console.print(f"[bold]📊 Metrics for Run: {orch.state.run_id}[/bold]")
        console.print("━" * 60)
        console.print()

        # Phase summary table
        phase_table = Table(title="Phase Summary")
        phase_table.add_column("Phase", style="cyan")
        phase_table.add_column("Duration (s)", style="yellow")
        phase_table.add_column("Agents", style="green")
        phase_table.add_column("Status", style="bold")

        for phase_name, phase_data in metrics.get("phases", {}).items():
            duration = phase_data.get("duration_s", 0.0)
            agents_count = len(phase_data.get("agents", []))
            status = "✅" if phase_data.get("success", False) else "❌"
            phase_table.add_row(
                phase_name,
                f"{duration:.2f}",
                str(agents_count),
                status
            )

        console.print(phase_table)
        console.print()

        # Agent details table
        agent_table = Table(title="Agent Executions")
        agent_table.add_column("Phase", style="cyan")
        agent_table.add_column("Agent", style="magenta")
        agent_table.add_column("Duration (s)", style="yellow")
        agent_table.add_column("Retries", style="red")
        agent_table.add_column("Exit Code", style="white")

        for phase_name, phase_data in metrics.get("phases", {}).items():
            for agent_data in phase_data.get("agents", []):
                agent_table.add_row(
                    phase_name,
                    agent_data.get("agent_name", "unknown"),
                    f"{agent_data.get('duration_s', 0.0):.2f}",
                    str(agent_data.get("retry_count", 0)),
                    str(agent_data.get("exit_code", "N/A"))
                )

        console.print(agent_table)
        console.print()

        # Cleanliness score
        summary_file = orch.project_root / "reports" / "hygiene_summary.json"
        if summary_file.exists():
            with open(summary_file, "r") as f:
                hygiene = json.load(f)
                score = hygiene.get("cleanliness_score", 0)
                grade = hygiene.get("grade", "N/A")

                score_color = "green" if score >= 95 else "yellow" if score >= 85 else "red"
                console.print(
                    f"[bold]Cleanliness Score:[/bold] [{score_color}]{score}/100 (Grade: {grade})[/{score_color}]"
                )
                console.print()

        # File paths
        console.print("[bold]Metrics Files:[/bold]")
        console.print(f"  JSON: [link]{metrics_file}[/link]")

        prom_file = metrics_dir / "metrics.prom"
        if prom_file.exists():
            console.print(f"  Prometheus: [link]{prom_file}[/link]")

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error loading metrics: {e}[/red]")
        raise


@run_app.command(name="retry")
def run_retry(
    phase: str = typer.Option(..., "--phase", help="Phase to retry"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Specific agent to retry (optional)"),
):
    """
    Retry a failed phase or agent.

    Re-invokes the last failed execution for the specified phase, preserving
    the retry policy. If --agent is specified, only that agent is retried.
    """
    from src.orchestrator.runloop import Orchestrator

    console.print("[bold]🔄 Retrying Failed Execution[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        if agent:
            console.print(f"Retrying agent: [yellow]{agent}[/yellow] in phase: [yellow]{phase}[/yellow]")
            console.print()

            # Retry single agent
            outcome = orch.invoke_agent(agent, phase)

            status = "✅" if outcome.success else "❌"
            console.print(f"{status} Agent: {agent}")
            console.print(f"Exit code: {outcome.exit_code}")
            if outcome.notes:
                console.print(f"Notes: {outcome.notes}")

        else:
            console.print(f"Retrying phase: [yellow]{phase}[/yellow]")
            console.print()

            # Retry entire phase
            outcome = orch.run_phase(phase)

            console.print(f"[green]✓ Phase retried: {phase}[/green]")
            console.print(f"Success: {outcome.success}")
            console.print(f"Agents: {len(outcome.agent_outcomes)}")

            if outcome.validation:
                console.print(f"Validation: {outcome.validation.status.value}")

        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error retrying: {e}[/red]")
        raise


@run_app.command(name="rollback")
def run_rollback(
    phase: str = typer.Option(..., "--phase", help="Phase to roll back to"),
):
    """
    Roll back to a previous phase (non-destructive).

    Creates a ROLLBACK_<timestamp>.md advisory document and resets the
    workflow cursor to the specified phase. Does not modify git or files.
    """
    from src.orchestrator.runloop import Orchestrator
    from datetime import datetime

    console.print("[bold]⏪ Rolling Back to Phase[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        orch = Orchestrator()

        console.print(f"[yellow]⚠️  Rolling back to phase: {phase}[/yellow]")
        console.print()
        console.print("[dim]This is non-destructive and creates an advisory document[/dim]")
        console.print()

        # Validate phase exists
        phases = orch.config.get("workflow", {}).get("phases", {})
        if phase not in phases:
            console.print(f"[red]✗ Phase not found: {phase}[/red]")
            return

        # Create rollback advisory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rollback_file = orch.project_root / ".claude" / f"ROLLBACK_{timestamp}.md"

        rollback_content = f"""# Rollback Advisory

**Timestamp:** {datetime.now().isoformat()}
**Run ID:** {orch.state.run_id}
**From Phase:** {orch.state.current_phase}
**To Phase:** {phase}

## Advisory

The workflow has been rolled back to phase: **{phase}**

### Manual Steps Required

1. Review any artifacts created after phase `{phase}`
2. Consider reverting code changes if needed:
   ```bash
   git log --oneline --since="<timestamp>"
   git revert <commit-hash>
   ```
3. Clean up any generated files if necessary

### Completed Phases Before Rollback

{chr(10).join(f"- {p}" for p in orch.state.completed_phases)}

### Next Steps

1. Review this advisory
2. Run: `orchestrator run next` to re-execute from phase `{phase}`

---

This rollback is **non-destructive** and does not automatically modify git or files.
"""

        rollback_file.write_text(rollback_content)

        # Reset state
        previous_phase = orch._get_previous_phase(phase)
        if previous_phase:
            orch.state.current_phase = previous_phase
        else:
            orch.state.current_phase = phase

        # Remove phases after rollback point from completed list
        phase_order = list(phases.keys())
        rollback_idx = phase_order.index(phase)
        orch.state.completed_phases = [
            p for p in orch.state.completed_phases if phase_order.index(p) < rollback_idx
        ]

        orch._save_state()

        console.print(f"[green]✓ Rolled back to phase: {phase}[/green]")
        console.print()
        console.print(f"Advisory created: [link]{rollback_file}[/link]")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Review the rollback advisory")
        console.print("  2. Run: [cyan]orchestrator run next[/cyan]")
        console.print()

    except Exception as e:
        console.print(f"[red]✗ Error during rollback: {e}[/red]")
        raise


# Release command group
release_app = typer.Typer(name="release", help="Release management: versioning, changelog, gates, GitHub releases")
app.add_typer(release_app, name="release")


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


if __name__ == "__main__":
    app()
