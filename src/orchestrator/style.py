"""
Client theme management commands for orchestrator CLI.

Provides commands for:
- Listing available client themes
- Applying client themes (merge + regenerate tokens)
- Validating client themes against schema
- Creating new client themes from template
"""

import typer
from pathlib import Path
import json
import subprocess
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional

app = typer.Typer(help="Client theme management")
console = Console()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLIENTS_DIR = PROJECT_ROOT / "clients"
SCHEMA_PATH = CLIENTS_DIR / ".schema" / "theme.schema.json"
MERGE_SCRIPT = PROJECT_ROOT / "scripts" / "merge_theme.py"


@app.command("list")
def list_themes():
    """List all available client themes."""
    try:
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

        themes = []
        for client_dir in CLIENTS_DIR.iterdir():
            if client_dir.is_dir() and not client_dir.name.startswith("."):
                theme_file = client_dir / "theme.json"
                if theme_file.exists():
                    with open(theme_file, "r") as f:
                        theme_data = json.load(f)
                    themes.append(
                        {
                            "slug": client_dir.name,
                            "name": theme_data.get("client", {}).get("name", client_dir.name),
                            "path": str(theme_file.relative_to(PROJECT_ROOT)),
                        }
                    )

        if not themes:
            console.print("[yellow]No client themes found[/yellow]")
            console.print(f"Create themes in: {CLIENTS_DIR.relative_to(PROJECT_ROOT)}")
            return

        # Display table
        table = Table(title="Client Themes")
        table.add_column("Slug", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Path", style="dim")

        for theme in sorted(themes, key=lambda x: x["slug"]):
            table.add_row(theme["slug"], theme["name"], theme["path"])

        console.print(table)
        console.print(f"\nTotal: {len(themes)} client theme(s)")

    except Exception as e:
        console.print(f"[red]Error listing themes: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("apply")
def apply_theme(
    client: str = typer.Option(..., "--client", "-c", help="Client slug to apply"),
    output: str = typer.Option(
        "design_system/.generated", "--output", "-o", help="Output directory for generated tokens"
    ),
):
    """
    Apply client theme by merging with base tokens and regenerating files.

    This command:
    1. Validates the client theme against schema
    2. Merges base tokens with client overrides
    3. Generates CSS, TypeScript, and JSON token files
    """
    theme_path = CLIENTS_DIR / client / "theme.json"

    if not theme_path.exists():
        console.print(f"[red]Theme not found for client: {client}[/red]", file=sys.stderr)
        console.print(f"Expected path: {theme_path.relative_to(PROJECT_ROOT)}")
        raise typer.Exit(1)

    console.print(f"[cyan]Applying theme for client: {client}[/cyan]")
    console.print(f"Theme file: {theme_path.relative_to(PROJECT_ROOT)}")

    # Run merge script
    try:
        result = subprocess.run(
            [sys.executable, str(MERGE_SCRIPT), "--client", client, "--output", output],
            capture_output=True,
            text=True,
            check=True,
        )

        console.print(result.stdout)
        console.print(f"[green]✓ Theme applied successfully for client: {client}[/green]")

    except subprocess.CalledProcessError as e:
        console.print("[red]Theme application failed:[/red]", file=sys.stderr)
        console.print(e.stderr, file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error applying theme: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("validate")
def validate_theme(
    client: str = typer.Option(..., "--client", "-c", help="Client slug to validate"),
):
    """
    Validate client theme against JSON schema.

    Checks:
    - JSON syntax is valid
    - Required fields are present
    - Color values are valid hex codes
    - Font families include fallbacks
    - Design constraints are enforced (no emojis, no gridlines, etc.)
    """
    theme_path = CLIENTS_DIR / client / "theme.json"

    if not theme_path.exists():
        console.print(f"[red]Theme not found for client: {client}[/red]", file=sys.stderr)
        console.print(f"Expected path: {theme_path.relative_to(PROJECT_ROOT)}")
        raise typer.Exit(1)

    console.print(f"[cyan]Validating theme for client: {client}[/cyan]")
    console.print(f"Theme file: {theme_path.relative_to(PROJECT_ROOT)}")

    # Run merge script in validate-only mode
    try:
        result = subprocess.run(
            [sys.executable, str(MERGE_SCRIPT), "--client", client, "--validate-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        console.print(result.stdout)
        console.print(f"[green]✓ Theme is valid for client: {client}[/green]")

    except subprocess.CalledProcessError as e:
        console.print("[red]Theme validation failed:[/red]", file=sys.stderr)
        console.print(e.stderr, file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error validating theme: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("create")
def create_theme(
    client: str = typer.Option(..., "--client", "-c", help="Client slug for new theme"),
    name: str = typer.Option(..., "--name", "-n", help="Client display name"),
    template: Optional[str] = typer.Option(None, "--from", help="Copy from existing client theme"),
):
    """
    Create a new client theme from template.

    If --from is specified, copies an existing theme as a starting point.
    Otherwise, creates a minimal theme with Kearney defaults.
    """
    client_dir = CLIENTS_DIR / client
    theme_path = client_dir / "theme.json"

    if theme_path.exists():
        console.print(f"[red]Theme already exists for client: {client}[/red]", file=sys.stderr)
        console.print(f"Path: {theme_path.relative_to(PROJECT_ROOT)}")
        raise typer.Exit(1)

    console.print(f"[cyan]Creating theme for client: {client}[/cyan]")

    # Load template
    if template:
        template_path = CLIENTS_DIR / template / "theme.json"
        if not template_path.exists():
            console.print(f"[red]Template theme not found: {template}[/red]", file=sys.stderr)
            raise typer.Exit(1)

        console.print(f"Copying from template: {template}")
        with open(template_path, "r") as f:
            theme_data = json.load(f)

        # Update client info
        theme_data["client"]["slug"] = client
        theme_data["client"]["name"] = name
    else:
        # Create minimal theme
        console.print("Creating minimal theme with Kearney defaults")
        theme_data = {
            "client": {"slug": client, "name": name},
            "colors": {
                "light": {"primary": "#7823DC", "emphasis": "#E63946"},
                "dark": {"primary": "#A855F7", "emphasis": "#EF476F"},
            },
            "typography": {"fontFamilyPrimary": "Inter, Arial, sans-serif"},
            "constraints": {"allowEmojis": False, "allowGridlines": False, "labelFirst": True},
        }

    # Create directory and save theme
    client_dir.mkdir(parents=True, exist_ok=True)
    with open(theme_path, "w") as f:
        json.dump(theme_data, f, indent=2)

    console.print(f"[green]✓ Theme created: {theme_path.relative_to(PROJECT_ROOT)}[/green]")
    console.print("\nNext steps:")
    console.print(f"  1. Edit theme: {theme_path.relative_to(PROJECT_ROOT)}")
    console.print(f"  2. Validate: orchestrator style validate --client {client}")
    console.print(f"  3. Apply: orchestrator style apply --client {client}")


@app.command("schema")
def show_schema():
    """Display the theme JSON schema."""
    if not SCHEMA_PATH.exists():
        console.print(f"[red]Schema not found: {SCHEMA_PATH}[/red]", file=sys.stderr)
        raise typer.Exit(1)

    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    console.print_json(data=schema)


if __name__ == "__main__":
    app()
