"""Checkpoint validation command for in-session guided execution."""

import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
except ImportError:
    print("Warning: Required dependencies not installed. Run: pip install -e .")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.orchestrator.runloop import Orchestrator
from src.orchestrator.checkpoints import validate_artifacts

console = Console()


def main(
    force: bool = typer.Option(
        False, "--force", help="Force advance to next phase even if artifacts missing (not recommended)"
    ),
):
    """
    Validate checkpoint and advance workflow state.

    Used in in-session guided execution mode after Claude Code completes work.
    Validates that required artifacts exist and advances state to next phase.

    Workflow:
        1. User runs: orchestrator run next
        2. Orchestrator prints agent instructions and pauses (exit_code=2)
        3. Claude Code executes work in current session
        4. User runs: orchestrator run checkpoint ← YOU ARE HERE
        5. Validates artifacts and advances to next phase
    """
    console.print("[bold]✅ Checkpoint Validation[/bold]")
    console.print("━" * 60)
    console.print()

    try:
        # Load orchestrator state
        orch = Orchestrator()

        if orch.state.status.value == "idle":
            console.print("[yellow]⚠️  No active run[/yellow]")
            console.print("Start a run first with: [cyan]orchestrator run start[/cyan]")
            return

        current_phase = orch.state.current_phase
        console.print(f"Current phase: [yellow]{current_phase}[/yellow]")
        console.print()

        # Get phase configuration
        phases = orch.config.get("workflow", {}).get("phases", {})
        if current_phase not in phases:
            console.print(f"[red]✗ Phase not found in config: {current_phase}[/red]")
            return

        phase_config = phases[current_phase]
        agents = phase_config.get("agents", [])

        if not agents:
            console.print(f"[red]✗ No agents configured for phase: {current_phase}[/red]")
            return

        # For in-session mode, we assume one agent per phase for simplicity
        # Get required artifacts from the first agent's config
        agent_name = agents[0]
        subagents = orch.config.get("subagents", {})
        agent_config = subagents.get(agent_name, {})
        required_artifacts = agent_config.get("checkpoint_artifacts", [])

        if not required_artifacts:
            console.print(f"[yellow]⚠️  No checkpoint artifacts defined for agent: {agent_name}[/yellow]")
            console.print("[dim]Advancing to next phase without validation[/dim]")
            console.print()
        else:
            console.print(f"[bold]Validating artifacts for agent:[/bold] {agent_name}")
            console.print()

            # Validate artifacts
            validation = validate_artifacts(
                artifacts_required=required_artifacts,
                project_root=orch.project_root,
                phase_name=current_phase,
            )

            # Show validation results
            status_emoji = {
                "pass": "✅",
                "partial": "⚠️",
                "fail": "❌",
            }
            emoji = status_emoji.get(validation.status.value, "❓")
            console.print(f"[bold]Validation:[/bold] {emoji} {validation.status.value.upper()}")
            console.print(f"  Required: {len(validation.required)} pattern(s)")
            console.print(f"  Found: {len(validation.found)} file(s)")
            console.print(f"  Missing: {len(validation.missing)} pattern(s)")
            console.print()

            if validation.found:
                console.print("[bold]Found artifacts:[/bold]")
                for artifact in sorted(validation.found):
                    console.print(f"  ✅ {artifact}")
                console.print()

            if validation.missing:
                console.print("[bold yellow]Missing artifacts:[/bold yellow]")
                for pattern in validation.missing:
                    console.print(f"  ❌ {pattern}")
                console.print()

            # Check if validation passed
            if validation.status.value == "fail" and not force:
                console.print("[red bold]✗ Checkpoint Validation Failed[/red bold]")
                console.print()
                console.print("Required artifacts are missing. Please complete the work before running checkpoint.")
                console.print()
                console.print("[bold]Options:[/bold]")
                console.print("  1. Complete the missing artifacts")
                console.print("  2. Run [cyan]orchestrator run checkpoint --force[/cyan] to advance anyway (not recommended)")
                console.print()
                console.print(f"Validation report: [link]{validation.validation_report_path}[/link]")
                return

            if validation.status.value == "partial" and not force:
                console.print("[yellow bold]⚠️  Partial Validation[/yellow bold]")
                console.print()
                console.print("Some artifacts are missing. Consider completing them before proceeding.")
                console.print()

                # Ask for confirmation
                if not typer.confirm("Proceed to next phase anyway?"):
                    console.print("[yellow]Checkpoint cancelled[/yellow]")
                    console.print()
                    console.print("Complete missing artifacts and run [cyan]orchestrator run checkpoint[/cyan] again")
                    return

            if force and validation.status.value != "pass":
                console.print("[yellow]⚠️  Forcing checkpoint despite validation issues (--force)[/yellow]")
                console.print()

            console.print(f"Validation report: [link]{validation.validation_report_path}[/link]")
            console.print()

        # Mark phase as complete and advance state
        console.print("[dim]Advancing workflow state...[/dim]")

        # Add current phase to completed phases if not already there
        if current_phase not in orch.state.completed_phases:
            orch.state.completed_phases.append(current_phase)

        # Get next phase
        phase_order = list(phases.keys())
        current_idx = phase_order.index(current_phase)

        if current_idx + 1 < len(phase_order):
            next_phase = phase_order[current_idx + 1]
            orch.state.current_phase = next_phase
            orch._save_state()

            console.print(f"[green]✓ Phase {current_phase} marked complete[/green]")
            console.print()
            console.print(f"[bold]Next phase:[/bold] [yellow]{next_phase}[/yellow]")
            console.print()
            console.print("Run [cyan]orchestrator run next[/cyan] to continue")
        else:
            # Workflow complete
            orch.state.complete_workflow()
            console.print(f"[green]✓ Phase {current_phase} marked complete[/green]")
            console.print()
            console.print("[green bold]🎉 Workflow Completed![/green bold]")
            console.print()
            console.print(f"Completed phases: {len(orch.state.completed_phases)}")

    except Exception as e:
        console.print(f"[red]✗ Checkpoint validation failed: {e}[/red]")
        raise


if __name__ == "__main__":
    typer.run(main)
