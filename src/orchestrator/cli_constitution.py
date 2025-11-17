"""CLI commands for constitution management."""

import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

from .constitution import (
    ConstitutionConfig,
    ConstitutionError,
    generate_constitution,
    validate_constitution,
)

app = typer.Typer(help="Constitution management commands")


@app.command(name="generate")
def constitution_generate(
    intake: Optional[Path] = typer.Option(
        None,
        "--intake",
        "-i",
        help="Path to intake.yaml (auto-detects if not provided)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for constitution (default: .claude/constitution.md)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing constitution without prompting",
    ),
):
    """Generate a project constitution from intake configuration.

    The constitution establishes fundamental principles, standards, and guardrails
    that govern all project decisions and deliverables.

    Example:
        orchestrator constitution generate --intake intake/my-project.yaml
    """
    # Auto-detect intake file if not provided
    if intake is None:
        intake = _find_intake_file()
        if intake is None:
            typer.secho(
                "❌ No intake file found. Please specify --intake or create intake/*.yaml",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
        typer.secho(f"📄 Using intake file: {intake}", fg=typer.colors.BLUE)

    # Load intake
    try:
        with open(intake) as f:
            intake_data = yaml.safe_load(f)
    except Exception as e:
        typer.secho(f"❌ Failed to load intake file: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Set default output path
    if output is None:
        output = Path(".claude/constitution.md")

    # Check if constitution already exists
    if output.exists() and not force:
        typer.secho(f"⚠️  Constitution already exists at {output}", fg=typer.colors.YELLOW)
        overwrite = typer.confirm("Do you want to overwrite it?")
        if not overwrite:
            typer.secho("❌ Aborted", fg=typer.colors.RED)
            raise typer.Exit(1)

    # Generate constitution
    try:
        config = ConstitutionConfig.from_intake(intake_data)
        constitution = generate_constitution(config, output)

        typer.secho(f"✅ Constitution generated successfully!", fg=typer.colors.GREEN)
        typer.secho(f"📄 Saved to: {output}", fg=typer.colors.BLUE)
        typer.secho(
            f"\n💡 Tip: Review and customize the constitution, then commit it to version control.",
            fg=typer.colors.CYAN,
        )
        typer.secho(
            f"💡 Run 'orchestrator constitution validate' to check for completeness.",
            fg=typer.colors.CYAN,
        )

    except Exception as e:
        typer.secho(f"❌ Failed to generate constitution: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command(name="validate")
def constitution_validate(
    constitution: Optional[Path] = typer.Option(
        None,
        "--constitution",
        "-c",
        help="Path to constitution.md (default: .claude/constitution.md)",
    ),
):
    """Validate that constitution exists and is well-formed.

    Example:
        orchestrator constitution validate
    """
    if constitution is None:
        constitution = Path(".claude/constitution.md")

    try:
        is_valid = validate_constitution(constitution)
        if is_valid:
            typer.secho(f"✅ Constitution is valid: {constitution}", fg=typer.colors.GREEN)
            typer.secho(
                f"💡 Constitution will be enforced during orchestrator execution.",
                fg=typer.colors.CYAN,
            )
    except ConstitutionError as e:
        typer.secho(f"❌ Constitution validation failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command(name="check")
def constitution_check(
    constitution: Optional[Path] = typer.Option(
        None,
        "--constitution",
        "-c",
        help="Path to constitution.md (default: .claude/constitution.md)",
    ),
):
    """Check if a constitution exists.

    Example:
        orchestrator constitution check
    """
    if constitution is None:
        constitution = Path(".claude/constitution.md")

    if constitution.exists():
        typer.secho(f"✅ Constitution found: {constitution}", fg=typer.colors.GREEN)

        # Show basic stats
        content = constitution.read_text()
        lines = len(content.split("\n"))
        words = len(content.split())

        typer.secho(f"📊 Stats: {lines} lines, {words} words", fg=typer.colors.BLUE)
    else:
        typer.secho(f"❌ No constitution found at {constitution}", fg=typer.colors.RED)
        typer.secho(
            f"\n💡 Generate one with: orchestrator constitution generate",
            fg=typer.colors.CYAN,
        )
        raise typer.Exit(1)


def _find_intake_file() -> Optional[Path]:
    """Auto-detect intake file in intake/ directory."""
    intake_dir = Path("intake")
    if not intake_dir.exists():
        return None

    # Look for *.intake.yaml files
    intake_files = list(intake_dir.glob("*.intake.yaml"))
    if not intake_files:
        # Try *.yaml files
        intake_files = list(intake_dir.glob("*.yaml"))

    if not intake_files:
        return None

    # If multiple files, pick the most recently modified
    if len(intake_files) > 1:
        typer.secho(
            f"⚠️  Found {len(intake_files)} intake files, using most recent",
            fg=typer.colors.YELLOW,
        )

    return max(intake_files, key=lambda p: p.stat().st_mtime)


def main():
    """Entry point for constitution CLI."""
    app()


if __name__ == "__main__":
    main()
