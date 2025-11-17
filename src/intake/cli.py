"""Intake CLI commands."""

from pathlib import Path
from typing import Optional
import shutil
from datetime import datetime

try:
    import typer
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
except ImportError:
    print("Warning: Required dependencies not installed. Run: pip install -e .")
    import sys
    sys.exit(1)

# Import from orchestrator package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.intake_loader import (
    load_intake_yaml,
    validate_intake,
    get_template_path,
    list_templates,
)

app = typer.Typer(name="intake", help="Project intake commands")
console = Console()


@app.command()
def new(
    project_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Project type (webapp, analytics, ml, etc.)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for intake file"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Interactive wizard mode"
    ),
):
    """
    Create a new project intake configuration.

    This command helps you create a project intake YAML file either by:
    1. Using a starter template (if --type is provided)
    2. Interactive wizard (default)

    NOTE: This command does NOT start the project orchestration.
    It only creates the intake configuration file.
    """
    console.print("[bold blue]📋 New Project Intake[/bold blue]\n")

    # List available templates
    templates = list_templates()

    if not project_type and interactive:
        console.print("Available project types:")
        for i, tmpl in enumerate(templates, 1):
            console.print(f"  {i}. {tmpl}")
        console.print()

        project_type = Prompt.ask(
            "Select project type",
            choices=templates,
            default="webapp"
        )

    if not project_type:
        console.print("[red]Error: --type required in non-interactive mode[/red]")
        raise typer.Exit(1)

    if project_type not in templates:
        console.print(f"[red]Error: Unknown project type '{project_type}'[/red]")
        console.print(f"Available types: {', '.join(templates)}")
        raise typer.Exit(1)

    # Load template
    template_path = get_template_path(project_type)
    console.print(f"📄 Loading template: [cyan]{template_path.name}[/cyan]")

    config = load_intake_yaml(template_path)

    # Determine output path
    if not output:
        if interactive:
            default_name = config.get("project.name", "my-project")
            project_name = Prompt.ask(
                "Project name (kebab-case)",
                default=default_name
            )
            output = Path(f"intake/{project_name}.intake.yaml")
        else:
            output = Path(f"intake/{config.get('project.name')}.intake.yaml")

    output = Path(output)

    # Create intake directory if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists
    if output.exists():
        if interactive:
            overwrite = Confirm.ask(
                f"File {output} already exists. Overwrite?",
                default=False
            )
            if not overwrite:
                console.print("[yellow]Aborted.[/yellow]")
                raise typer.Exit(0)
        else:
            console.print(f"[red]Error: {output} already exists. Use --overwrite to replace.[/red]")
            raise typer.Exit(1)

    # Copy template to output
    shutil.copy(template_path, output)

    console.print(f"\n✅ Created intake file: [green]{output}[/green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit the intake file: {output}")
    console.print(f"  2. Validate: [cyan]orchestrator intake validate {output}[/cyan]")
    console.print(f"  3. Render config: [cyan]orchestrator intake render {output}[/cyan]")
    console.print("\n[dim]NOTE: This does not start the project. Use 'orchestrator run' to begin.[/dim]")


@app.command()
def validate(
    intake_file: Path = typer.Argument(..., help="Path to intake YAML file"),
):
    """Validate an intake configuration file."""
    console.print(f"[bold blue]🔍 Validating intake file:[/bold blue] {intake_file}\n")

    if not intake_file.exists():
        console.print(f"[red]Error: File not found: {intake_file}[/red]")
        raise typer.Exit(1)

    valid, error = validate_intake(intake_file)

    if valid:
        console.print("[green]✅ Validation passed[/green]")

        # Show summary
        config = load_intake_yaml(intake_file)
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Project: {config.get('project.name')}")
        console.print(f"  Type: {config.get('project.type')}")
        console.print(f"  Description: {config.get('project.description', 'N/A')}")

        # Show enabled agents
        agents = config.get('orchestration.enabled_agents', [])
        if agents:
            console.print(f"  Enabled agents: {', '.join(agents)}")

    else:
        console.print("[red]❌ Validation failed[/red]")
        console.print(f"\n[red]{error}[/red]")
        raise typer.Exit(1)


@app.command()
def clarify(
    intake_file: Path = typer.Argument(..., help="Path to intake YAML file"),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter by severity (critical, high, medium, low)",
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category (requirements, data, technical, security, etc.)",
    ),
):
    """Analyze intake and generate clarifying questions.

    This command identifies underspecified or ambiguous areas in your intake
    configuration and generates clarifying questions to improve specification quality.

    Run this BEFORE starting the orchestrator workflow to catch issues early.

    Example:
        orchestrator intake clarify intake/my-project.yaml
        orchestrator intake clarify intake/my-project.yaml --severity critical
    """
    console.print(f"[bold blue]🔍 Analyzing intake file:[/bold blue] {intake_file}\n")

    if not intake_file.exists():
        console.print(f"[red]Error: File not found: {intake_file}[/red]")
        raise typer.Exit(1)

    # Load intake
    try:
        import yaml
        with open(intake_file) as f:
            intake_data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error loading intake: {e}[/red]")
        raise typer.Exit(1)

    # Import clarifier
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.orchestrator.intake.clarifier import clarify_intake

    # Analyze and get questions
    questions = clarify_intake(intake_data)

    # Filter by severity if requested
    if severity:
        questions = [q for q in questions if q.severity == severity.lower()]

    # Filter by category if requested
    if category:
        questions = [q for q in questions if q.category == category.lower()]

    if not questions:
        console.print("[green]✅ No clarifications needed![/green]")
        console.print("\nYour intake is well-specified and ready for orchestration.")
        console.print("\n💡 Next step: orchestrator run start --intake", intake_file)
        return

    # Display questions
    console.print(f"[yellow]Found {len(questions)} clarification{'s' if len(questions) != 1 else ''}:[/yellow]\n")

    for i, q in enumerate(questions, 1):
        severity_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "cyan",
        }
        color = severity_colors.get(q.severity, "white")

        console.print(f"[bold {color}]#{i} [{q.severity.upper()}] {q.category}[/bold {color}]")
        console.print(f"[bold]❓ {q.question}[/bold]")
        console.print(f"   Field: [cyan]{q.field}[/cyan]")
        console.print(f"   Reason: {q.reason}")

        if q.examples:
            console.print("   Examples:")
            for ex in q.examples[:3]:  # Show max 3 examples
                console.print(f"     • {ex}")

        console.print()  # Blank line between questions

    # Summary
    console.print("[bold]Summary:[/bold]")
    by_severity = {}
    for q in questions:
        by_severity[q.severity] = by_severity.get(q.severity, 0) + 1

    for sev in ["critical", "high", "medium", "low"]:
        if sev in by_severity:
            color = severity_colors.get(sev, "white")
            console.print(f"  [{color}]{sev.capitalize()}: {by_severity[sev]}[/{color}]")

    console.print("\n💡 Tips:")
    console.print("  - Address critical/high severity questions before starting orchestrator")
    console.print("  - Update your intake file with clarified information")
    console.print("  - Run 'orchestrator intake validate' after updates")
    console.print("  - Run this command again to check for remaining issues")


@app.command()
def render(
    intake_file: Path = typer.Argument(..., help="Path to intake YAML file"),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files without asking"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without making changes"
    ),
):
    """
    Render intake configuration to project files.

    This updates:
    - .claude/config.yaml (orchestration settings)
    - CLAUDE.md (mission, phases, approval gates)
    - docs/requirements.md (project requirements)

    Safety: Creates backups before modifying files.
    """
    console.print(f"[bold blue]🎨 Rendering intake config:[/bold blue] {intake_file}\n")

    if not intake_file.exists():
        console.print(f"[red]Error: File not found: {intake_file}[/red]")
        raise typer.Exit(1)

    # Validate first
    valid, error = validate_intake(intake_file)
    if not valid:
        console.print(f"[red]Validation failed: {error}[/red]")
        raise typer.Exit(1)

    config = load_intake_yaml(intake_file)

    console.print("✅ Intake file is valid\n")

    if dry_run:
        console.print("[yellow]DRY RUN - No files will be modified[/yellow]\n")

    # Files to render
    files_to_update = [
        ".claude/config.yaml",
        "CLAUDE.md",
        "docs/requirements.md",
    ]

    console.print("[bold]Files that will be updated:[/bold]")
    for f in files_to_update:
        exists = Path(f).exists()
        status = "exists" if exists else "new"
        console.print(f"  - {f} ({status})")

    if not dry_run and not overwrite:
        proceed = Confirm.ask("\nProceed with rendering?", default=True)
        if not proceed:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    # Create backups
    if not dry_run:
        backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"\n📦 Creating backups in: [cyan]{backup_dir}[/cyan]")
        for f in files_to_update:
            path = Path(f)
            if path.exists():
                backup_path = backup_dir / f
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(path, backup_path)
                console.print(f"  ✓ Backed up: {f}")

    # TODO: Actual rendering logic would go here
    # For now, just show what would be rendered
    console.print("\n[yellow]⚠️  Rendering not yet implemented[/yellow]")
    console.print("[dim]This command will merge intake config into project files.[/dim]")

    if not dry_run:
        console.print(f"\n💾 Backups saved to: [green]{backup_dir}[/green]")


@app.command()
def templates():
    """List available starter templates."""
    console.print("[bold blue]📚 Available Starter Templates[/bold blue]\n")

    templates_list = list_templates()

    if not templates_list:
        console.print("[yellow]No templates found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Type", style="green")
    table.add_column("Path")

    for tmpl in templates_list:
        path = get_template_path(tmpl)
        table.add_row(tmpl, str(path))

    console.print(table)

    console.print("\n[bold]Usage:[/bold]")
    console.print("  orchestrator intake new --type <type>")


if __name__ == "__main__":
    app()
