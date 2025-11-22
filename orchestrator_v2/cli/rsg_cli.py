"""
Rich-enhanced RSG CLI for Orchestrator v2.

Provides a beautiful command-line interface for Ready/Set/Go operations
using Typer and Rich for professional output formatting.
"""

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="rsg",
    help="Ready/Set/Go workflow commands",
    no_args_is_help=True,
)
console = Console()

# API base URL - configurable
API_BASE_URL = "http://127.0.0.1:8000"


# -----------------------------------------------------------------------------
# Utility Functions (Pretty Printers)
# -----------------------------------------------------------------------------

def render_stage_banner(stage: str) -> None:
    """Render a colorized stage banner."""
    colors = {
        "not_started": "grey39",
        "ready": "bright_blue",
        "set": "bright_yellow",
        "go": "bright_green",
        "complete": "bright_magenta",
    }
    color = colors.get(stage.lower(), "white")
    console.print(
        Panel(
            f"[bold white]RSG Stage:[/] [bold {color}]{stage.upper()}[/]",
            expand=False,
        )
    )


def print_ready_status(status: dict) -> None:
    """Print Ready stage status as a Rich table."""
    table = Table(title="READY STATUS", title_style="bold blue")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Stage", status.get("stage", "unknown"))
    table.add_row(
        "Completed",
        "[green]Yes[/]" if status.get("completed") else "[yellow]No[/]"
    )
    table.add_row("Current Phase", status.get("current_phase") or "—")
    table.add_row(
        "Completed Phases",
        ", ".join(status.get("completed_phases", [])) or "—"
    )
    table.add_row(
        "Governance Passed",
        "[green]Yes[/]" if status.get("governance_passed") else "[yellow]Pending[/]"
    )

    console.print(table)

    # Print messages if any
    messages = status.get("messages", [])
    if messages:
        console.print("\n[bold]Messages:[/]")
        for msg in messages:
            console.print(f"  • {msg}")


def print_set_status(status: dict) -> None:
    """Print Set stage status as a Rich table."""
    table = Table(title="SET STATUS", title_style="bold yellow")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Stage", status.get("stage", "unknown"))
    table.add_row(
        "Completed",
        "[green]Yes[/]" if status.get("completed") else "[yellow]No[/]"
    )
    table.add_row("Current Phase", status.get("current_phase") or "—")
    table.add_row(
        "Completed Phases",
        ", ".join(status.get("completed_phases", [])) or "—"
    )
    table.add_row("Artifacts Count", str(status.get("artifacts_count", 0)))
    table.add_row(
        "Data Ready",
        "[green]Yes[/]" if status.get("data_ready") else "[yellow]No[/]"
    )

    console.print(table)

    messages = status.get("messages", [])
    if messages:
        console.print("\n[bold]Messages:[/]")
        for msg in messages:
            console.print(f"  • {msg}")


def print_go_status(status: dict) -> None:
    """Print Go stage status as a Rich table."""
    table = Table(title="GO STATUS", title_style="bold green")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Stage", status.get("stage", "unknown"))
    table.add_row(
        "Completed",
        "[green]Yes[/]" if status.get("completed") else "[yellow]No[/]"
    )
    table.add_row("Current Phase", status.get("current_phase") or "—")
    table.add_row(
        "Completed Phases",
        ", ".join(status.get("completed_phases", [])) or "—"
    )
    table.add_row("Checkpoints Count", str(status.get("checkpoints_count", 0)))
    table.add_row(
        "Governance Blocked",
        "[red]Yes[/]" if status.get("governance_blocked") else "[green]No[/]"
    )

    console.print(table)

    messages = status.get("messages", [])
    if messages:
        console.print("\n[bold]Messages:[/]")
        for msg in messages:
            console.print(f"  • {msg}")


def print_rsg_overview(overview: dict) -> None:
    """Print complete RSG overview with all stages."""
    # Header panel
    stage = overview.get("stage", "unknown")
    render_stage_banner(stage)

    console.print(f"\n[bold]Project:[/] {overview.get('project_name', 'Unknown')}")
    console.print(f"[bold]Project ID:[/] {overview.get('project_id', 'Unknown')}\n")

    # Ready status
    ready = overview.get("ready", {})
    ready_table = Table(title="READY", title_style="bold blue", expand=False)
    ready_table.add_column("Status", style="cyan", width=12)
    ready_table.add_column("Value", style="white")
    ready_table.add_row(
        "Completed",
        "[green]✓[/]" if ready.get("completed") else "[yellow]○[/]"
    )
    ready_table.add_row(
        "Phases",
        ", ".join(ready.get("completed_phases", [])) or "—"
    )
    console.print(ready_table)

    # Set status
    set_data = overview.get("set", {})
    set_table = Table(title="SET", title_style="bold yellow", expand=False)
    set_table.add_column("Status", style="cyan", width=12)
    set_table.add_column("Value", style="white")
    set_table.add_row(
        "Completed",
        "[green]✓[/]" if set_data.get("completed") else "[yellow]○[/]"
    )
    set_table.add_row(
        "Phases",
        ", ".join(set_data.get("completed_phases", [])) or "—"
    )
    set_table.add_row("Artifacts", str(set_data.get("artifacts_count", 0)))
    console.print(set_table)

    # Go status
    go = overview.get("go", {})
    go_table = Table(title="GO", title_style="bold green", expand=False)
    go_table.add_column("Status", style="cyan", width=12)
    go_table.add_column("Value", style="white")
    go_table.add_row(
        "Completed",
        "[green]✓[/]" if go.get("completed") else "[yellow]○[/]"
    )
    go_table.add_row(
        "Phases",
        ", ".join(go.get("completed_phases", [])) or "—"
    )
    go_table.add_row("Checkpoints", str(go.get("checkpoints_count", 0)))
    console.print(go_table)


def handle_error(response: httpx.Response) -> None:
    """Handle API error responses."""
    if response.status_code == 404:
        console.print("[red]Error:[/] Project not found")
    elif response.status_code == 400:
        detail = response.json().get("detail", "Bad request")
        console.print(f"[red]Error:[/] {detail}")
    else:
        console.print(f"[red]Error:[/] {response.status_code} - {response.text}")
    raise typer.Exit(1)


# -----------------------------------------------------------------------------
# CLI Commands
# -----------------------------------------------------------------------------

@app.command("init")
def rsg_init(
    project_name: str = typer.Argument(..., help="Name for the new project"),
    client: str = typer.Option("kearney-default", help="Client identifier"),
    git_url: str = typer.Option(None, help="Git URL to clone"),
):
    """Initialize a new project with workspace."""
    console.print(Panel("[bold]Initializing Project[/]", expand=False))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating project...", total=None)

        try:
            with httpx.Client() as client_http:
                response = client_http.post(
                    f"{API_BASE_URL}/projects",
                    json={
                        "project_name": project_name,
                        "client": client,
                        "metadata": {"git_url": git_url} if git_url else {},
                    },
                    timeout=30.0,
                )

            if response.status_code != 201:
                handle_error(response)

            project = response.json()
            progress.update(task, completed=True)

        except httpx.ConnectError:
            console.print("[red]Error:[/] Cannot connect to API server")
            console.print("Make sure the server is running: python scripts/run_api_server.py")
            raise typer.Exit(1)

    # Success output
    console.print("\n[green]✓[/] Project created successfully!\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Project ID", project["project_id"])
    table.add_row("Project Name", project["project_name"])
    table.add_row("Client", project["client"])
    table.add_row("Current Phase", project["current_phase"])

    console.print(table)
    console.print("\n[dim]Next: Run 'orchestrator rsg ready-start <project_id>' to begin[/]")


@app.command("ready-start")
def ready_start(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Start the Ready stage (PLANNING + ARCHITECTURE)."""
    console.print(Panel("[bold blue]Starting READY Stage[/]", expand=False))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running READY phases...", total=None)

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{API_BASE_URL}/rsg/{project_id}/ready/start",
                    timeout=60.0,
                )

            if response.status_code != 200:
                handle_error(response)

            status = response.json()
            progress.update(task, completed=True)

        except httpx.ConnectError:
            console.print("[red]Error:[/] Cannot connect to API server")
            raise typer.Exit(1)

    console.print()
    render_stage_banner(status["stage"])
    console.print()
    print_ready_status(status)


@app.command("ready-status")
def ready_status(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Get Ready stage status."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{API_BASE_URL}/rsg/{project_id}/ready/status",
                timeout=10.0,
            )

        if response.status_code != 200:
            handle_error(response)

        status = response.json()

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to API server")
        raise typer.Exit(1)

    render_stage_banner(status["stage"])
    console.print()
    print_ready_status(status)


@app.command("set-start")
def set_start(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Start the Set stage (DATA + early DEVELOPMENT)."""
    console.print(Panel("[bold yellow]Starting SET Stage[/]", expand=False))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running SET phases...", total=None)

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{API_BASE_URL}/rsg/{project_id}/set/start",
                    timeout=60.0,
                )

            if response.status_code != 200:
                handle_error(response)

            status = response.json()
            progress.update(task, completed=True)

        except httpx.ConnectError:
            console.print("[red]Error:[/] Cannot connect to API server")
            raise typer.Exit(1)

    console.print()
    render_stage_banner(status["stage"])
    console.print()
    print_set_status(status)


@app.command("set-status")
def set_status(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Get Set stage status."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{API_BASE_URL}/rsg/{project_id}/set/status",
                timeout=10.0,
            )

        if response.status_code != 200:
            handle_error(response)

        status = response.json()

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to API server")
        raise typer.Exit(1)

    render_stage_banner(status["stage"])
    console.print()
    print_set_status(status)


@app.command("go-start")
def go_start(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Start the Go stage (DEVELOPMENT + QA + DOCUMENTATION)."""
    console.print(Panel("[bold green]Starting GO Stage[/]", expand=False))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running GO phases...", total=None)

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{API_BASE_URL}/rsg/{project_id}/go/start",
                    timeout=120.0,
                )

            if response.status_code != 200:
                handle_error(response)

            status = response.json()
            progress.update(task, completed=True)

        except httpx.ConnectError:
            console.print("[red]Error:[/] Cannot connect to API server")
            raise typer.Exit(1)

    console.print()
    render_stage_banner(status["stage"])
    console.print()
    print_go_status(status)


@app.command("go-status")
def go_status(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Get Go stage status."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{API_BASE_URL}/rsg/{project_id}/go/status",
                timeout=10.0,
            )

        if response.status_code != 200:
            handle_error(response)

        status = response.json()

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to API server")
        raise typer.Exit(1)

    render_stage_banner(status["stage"])
    console.print()
    print_go_status(status)


@app.command("overview")
def overview(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Get complete RSG overview for a project."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{API_BASE_URL}/rsg/{project_id}/overview",
                timeout=10.0,
            )

        if response.status_code != 200:
            handle_error(response)

        overview_data = response.json()

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to API server")
        raise typer.Exit(1)

    print_rsg_overview(overview_data)


@app.command("list")
def list_projects():
    """List all projects."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{API_BASE_URL}/projects",
                timeout=10.0,
            )

        if response.status_code != 200:
            console.print(f"[red]Error:[/] {response.status_code}")
            raise typer.Exit(1)

        projects = response.json()

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to API server")
        raise typer.Exit(1)

    if not projects:
        console.print("[yellow]No projects found[/]")
        console.print("\n[dim]Create one with: orchestrator rsg init <project_name>[/]")
        return

    table = Table(title="Projects", title_style="bold")
    table.add_column("Project ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Phase", style="yellow")
    table.add_column("Status", style="green")

    for project in projects:
        table.add_row(
            project["project_id"][:8] + "...",
            project["project_name"],
            project["current_phase"],
            project["status"],
        )

    console.print(table)


def main():
    """Main entry point for RSG CLI."""
    app()


if __name__ == "__main__":
    main()
