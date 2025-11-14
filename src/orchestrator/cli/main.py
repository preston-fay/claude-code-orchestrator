"""Unified orchestrator CLI - main app and top-level commands."""

from pathlib import Path
from typing import Optional
import sys

try:
    import typer
    from rich.console import Console
except ImportError:
    print("Warning: Required dependencies not installed. Run: pip install -e .")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

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

# Add registry command group
try:
    from src.orchestrator.registry import app as registry_app
    app.add_typer(registry_app, name="registry")
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import registry CLI: {e}[/yellow]")

# Add governance command group
try:
    from src.orchestrator.governance import app as gov_app
    app.add_typer(gov_app, name="gov")
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import governance CLI: {e}[/yellow]")

# Add bootstrap command
try:
    from src.orchestrator.commands.bootstrap import main as bootstrap_main
    app.command(name="bootstrap")(bootstrap_main)
except ImportError as e:
    console.print(f"[yellow]Warning: Could not import bootstrap command: {e}[/yellow]")

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

# Import run and release command groups (defined in separate modules)
from .commands_run import run_app
from .commands_release import release_app

# Add run and release command groups to main app
app.add_typer(run_app, name="run")
app.add_typer(release_app, name="release")


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


if __name__ == "__main__":
    app()
