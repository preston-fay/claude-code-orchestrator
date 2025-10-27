"""Bootstrap command - Initialize new projects with orchestrator framework."""

from pathlib import Path
from typing import Optional, Dict, Any
import shutil
import yaml
import subprocess
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

console = Console()


class BootstrapError(Exception):
    """Bootstrap operation failed."""
    pass


def load_template(template_name: str, templates_dir: Path) -> Dict[str, Any]:
    """Load project template configuration."""
    template_path = templates_dir / "project-types" / f"{template_name}.yaml"

    if not template_path.exists():
        available = [
            f.stem for f in (templates_dir / "project-types").glob("*.yaml")
        ]
        raise BootstrapError(
            f"Template '{template_name}' not found.\n"
            f"Available templates: {', '.join(available)}"
        )

    with open(template_path) as f:
        return yaml.safe_load(f)


def load_client_governance(client_name: str, orchestrator_root: Path) -> Optional[Dict[str, Any]]:
    """Load client-specific governance configuration."""
    gov_path = orchestrator_root / "clients" / client_name / "governance.yaml"

    if not gov_path.exists():
        console.print(f"[yellow]Warning: Client governance not found: {gov_path}[/yellow]")
        return None

    with open(gov_path) as f:
        return yaml.safe_load(f)


def create_directory_structure(output_dir: Path, directories: list, dry_run: bool = False):
    """Create project directory structure."""
    for dir_path in directories:
        full_path = output_dir / dir_path

        if dry_run:
            console.print(f"  [dim]Would create: {dir_path}/[/dim]")
        else:
            full_path.mkdir(parents=True, exist_ok=True)


def copy_orchestrator_files(
    orchestrator_root: Path,
    output_dir: Path,
    files_to_copy: list,
    dry_run: bool = False
):
    """Copy framework files from orchestrator to new project."""
    for file_spec in files_to_copy:
        source = orchestrator_root / file_spec["source"]
        dest = output_dir / file_spec["destination"]
        recursive = file_spec.get("recursive", False)
        optional = file_spec.get("optional", False)

        if not source.exists():
            if optional:
                console.print(f"  [dim]Skipping optional: {file_spec['source']}[/dim]")
                continue
            else:
                raise BootstrapError(f"Source file not found: {source}")

        if dry_run:
            console.print(f"  [dim]Would copy: {file_spec['source']} → {file_spec['destination']}[/dim]")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)

            if source.is_dir() and recursive:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)


def generate_config_files(
    output_dir: Path,
    config_files: list,
    placeholders: Dict[str, str],
    dry_run: bool = False
):
    """Generate configuration files with placeholder substitution."""
    for config_spec in config_files:
        file_path = output_dir / config_spec["name"]
        content = config_spec["content"]

        # Replace placeholders
        for key, value in placeholders.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        if dry_run:
            console.print(f"  [dim]Would create: {config_spec['name']}[/dim]")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)


def generate_intake_yaml(
    output_dir: Path,
    template: Dict[str, Any],
    placeholders: Dict[str, str],
    dry_run: bool = False
):
    """Generate intake.yaml from template."""
    intake_template = template.get("intake_template", {})

    # Replace placeholders in intake template
    intake_str = yaml.dump(intake_template, default_flow_style=False, sort_keys=False)
    for key, value in placeholders.items():
        intake_str = intake_str.replace(f"{{{{{key}}}}}", str(value))

    intake_data = yaml.safe_load(intake_str)

    intake_path = output_dir / "intake.yaml"

    if dry_run:
        console.print(f"  [dim]Would create: intake.yaml[/dim]")
    else:
        with open(intake_path, "w") as f:
            yaml.dump(intake_data, f, default_flow_style=False, sort_keys=False)


def initialize_git_repo(output_dir: Path, dry_run: bool = False):
    """Initialize git repository if not already initialized."""
    git_dir = output_dir / ".git"

    if git_dir.exists():
        console.print("  [dim]Git repository already exists[/dim]")
        return

    if dry_run:
        console.print("  [dim]Would initialize git repository[/dim]")
    else:
        try:
            subprocess.run(
                ["git", "init"],
                cwd=output_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "add", "."],
                cwd=output_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "Initial commit (orchestrator bootstrap)"],
                cwd=output_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[yellow]Warning: Git initialization failed: {e}[/yellow]")


def run_validations(output_dir: Path, validations: list):
    """Run post-bootstrap validation checks."""
    console.print("\n[bold]Running validations...[/bold]")

    all_passed = True

    for validation in validations:
        check_type = validation["check"]
        path = validation["path"]
        message = validation.get("message", "")

        if check_type == "directory_exists":
            exists = (output_dir / path).is_dir()
        elif check_type == "file_exists":
            exists = (output_dir / path).is_file()
        else:
            console.print(f"[yellow]Unknown check type: {check_type}[/yellow]")
            continue

        if exists:
            console.print(f"  [green]✓[/green] {message}")
        else:
            console.print(f"  [red]✗[/red] {message}")
            all_passed = False

    return all_passed


def bootstrap(
    template: str,
    output: Path,
    client: Optional[str] = None,
    project_name: Optional[str] = None,
    project_description: Optional[str] = None,
    dry_run: bool = False,
):
    """
    Bootstrap a new project with orchestrator framework.

    Args:
        template: Project template name (analytics, ml-model, webapp, supply-chain)
        output: Target directory for new project
        client: Optional client name for governance customization
        project_name: Project name (defaults to output directory name)
        project_description: Project description
        dry_run: Preview actions without making changes
    """
    # Find orchestrator root (where templates are)
    orchestrator_root = Path(__file__).parent.parent.parent.parent
    templates_dir = orchestrator_root / "templates"

    if not templates_dir.exists():
        raise BootstrapError(f"Templates directory not found: {templates_dir}")

    # Load template
    console.print(f"[bold]Loading template: {template}[/bold]")
    template_config = load_template(template, templates_dir)

    # Load client governance if specified
    client_governance = None
    if client:
        console.print(f"[bold]Loading client governance: {client}[/bold]")
        client_governance = load_client_governance(client, orchestrator_root)

    # Prepare placeholders
    placeholders = {
        "PROJECT_NAME": project_name or output.name,
        "PROJECT_DESCRIPTION": project_description or template_config["description"],
        "PROJECT_SLUG": (project_name or output.name).lower().replace(" ", "-"),
        "TIMESTAMP": datetime.now().isoformat(),
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "TEMPLATE_TYPE": template,
    }

    # Add client-specific placeholders
    if client_governance:
        placeholders["CLIENT_NAME"] = client_governance.get("client_name", client)

    console.print()
    console.print(f"[bold cyan]Bootstrapping project: {placeholders['PROJECT_NAME']}[/bold cyan]")
    console.print(f"[dim]Template: {template}[/dim]")
    console.print(f"[dim]Output: {output}[/dim]")
    if client:
        console.print(f"[dim]Client: {client}[/dim]")
    if dry_run:
        console.print(f"[yellow]DRY RUN MODE (no changes will be made)[/yellow]")
    console.print()

    # Create output directory
    if not dry_run:
        output.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # Step 1: Create directory structure
        task = progress.add_task("Creating directory structure...", total=1)
        create_directory_structure(
            output,
            template_config.get("directory_structure", []),
            dry_run
        )
        progress.update(task, completed=1)

        # Step 2: Copy orchestrator files
        task = progress.add_task("Copying orchestrator files...", total=1)
        copy_orchestrator_files(
            orchestrator_root,
            output,
            template_config.get("copy_files", []),
            dry_run
        )
        progress.update(task, completed=1)

        # Step 3: Generate configuration files
        task = progress.add_task("Generating configuration files...", total=1)
        generate_config_files(
            output,
            template_config.get("config_files", []),
            placeholders,
            dry_run
        )
        progress.update(task, completed=1)

        # Step 4: Generate intake.yaml
        task = progress.add_task("Generating intake.yaml...", total=1)
        generate_intake_yaml(
            output,
            template_config,
            placeholders,
            dry_run
        )
        progress.update(task, completed=1)

        # Step 5: Initialize git
        if not dry_run:
            task = progress.add_task("Initializing git repository...", total=1)
            initialize_git_repo(output, dry_run)
            progress.update(task, completed=1)

    console.print()

    # Run validations
    if not dry_run:
        validations = template_config.get("validations", [])
        if validations:
            all_passed = run_validations(output, validations)

            if not all_passed:
                console.print("\n[yellow]Some validations failed. Review and fix before proceeding.[/yellow]")

    # Show next steps
    console.print("\n[bold green]✓ Bootstrap complete![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")

    next_steps = template_config.get("next_steps", [])
    for i, step in enumerate(next_steps, 1):
        console.print(f"  {i}. {step}")

    if dry_run:
        console.print("\n[yellow]This was a dry run. Run without --dry-run to create the project.[/yellow]")

    console.print()
    console.print(f"[dim]Project directory: {output.absolute()}[/dim]")


# CLI command (will be registered in cli.py)
def main(
    template: str = typer.Argument(..., help="Template name (analytics, ml-model, webapp, supply-chain)"),
    output: Path = typer.Option(..., "--output", "-o", help="Output directory for new project"),
    client: Optional[str] = typer.Option(None, "--client", "-c", help="Client name for governance customization"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without making changes"),
):
    """
    Bootstrap a new project with orchestrator framework.

    Examples:
        # Create analytics project
        orchestrator bootstrap analytics --output ~/projects/customer-churn

        # Create ML model project with client governance
        orchestrator bootstrap ml-model --output ~/projects/forecast --client acme-corp

        # Preview without creating files
        orchestrator bootstrap webapp --output ~/projects/dashboard --dry-run
    """
    try:
        bootstrap(
            template=template,
            output=output,
            client=client,
            project_name=name,
            project_description=description,
            dry_run=dry_run,
        )
    except BootstrapError as e:
        console.print(f"[red]✗ Bootstrap failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error: {e}[/red]")
        raise


if __name__ == "__main__":
    typer.run(main)
