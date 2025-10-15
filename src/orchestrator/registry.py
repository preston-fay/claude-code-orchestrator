"""
Registry management commands for orchestrator CLI.

Provides commands for:
- Publishing models with metrics
- Registering datasets with schema info
- Fetching entries by name/version
- Listing with filters
- Verifying integrity
"""

import typer
from pathlib import Path
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional
import json

from src.registry.manager import RegistryManager

app = typer.Typer(help="Model registry and dataset catalog management")
console = Console()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent


@app.command("model-publish")
def publish_model(
    path: str = typer.Option(..., "--path", help="Path to model artifact (e.g., models/forecast_v1.pkl)"),
    name: Optional[str] = typer.Option(None, "--name", help="Model name (defaults to filename without extension)"),
    version: str = typer.Option(..., "--version", help="Semantic version (e.g., 1.0.0)"),
    metrics: Optional[str] = typer.Option(None, "--metrics", help="Path to metrics JSON file"),
    client: Optional[str] = typer.Option(None, "--client", help="Client slug"),
    cleanliness: Optional[int] = typer.Option(None, "--cleanliness", help="Cleanliness score (0-100)"),
    release: Optional[str] = typer.Option(None, "--release", help="Release tag (e.g., v1.0.0)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Release notes"),
):
    """
    Publish a model to the registry.

    Computes SHA256 hash, links to current release, and adds to manifest.

    Example:
        orchestrator registry model-publish --path models/forecast_v1.pkl --version 1.0.0 --metrics models/metrics.json --client acme-corp
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        # Resolve paths
        artifact_path = Path(path)
        if not artifact_path.is_absolute():
            artifact_path = PROJECT_ROOT / artifact_path

        if not artifact_path.exists():
            console.print(f"[red]Error: Artifact not found: {path}[/red]", file=sys.stderr)
            raise typer.Exit(1)

        # Load metrics if provided
        metrics_dict = None
        if metrics:
            metrics_path = Path(metrics)
            if not metrics_path.is_absolute():
                metrics_path = PROJECT_ROOT / metrics_path

            if not metrics_path.exists():
                console.print(f"[red]Error: Metrics file not found: {metrics}[/red]", file=sys.stderr)
                raise typer.Exit(1)

            with open(metrics_path, "r") as f:
                metrics_dict = json.load(f)

        # Default name from filename
        if not name:
            name = artifact_path.stem

        # Make path relative to project root
        relative_path = str(artifact_path.relative_to(PROJECT_ROOT))

        console.print(f"[cyan]Publishing model: {name} v{version}[/cyan]")
        console.print(f"Artifact: {relative_path}")

        # Publish
        entry = manager.publish_model(
            name=name,
            version=version,
            artifacts=[relative_path],
            metrics=metrics_dict,
            cleanliness_score=cleanliness,
            release_tag=release,
            client=client,
            notes=notes,
        )

        console.print(f"[green]✓ Model published successfully[/green]")
        console.print(f"ID: {entry.id}")
        console.print(f"SHA256: {entry.sha256[:16]}...")

        if metrics_dict:
            console.print("\nMetrics:")
            for key, value in metrics_dict.items():
                console.print(f"  {key}: {value}")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("dataset-register")
def register_dataset(
    path: str = typer.Option(..., "--path", help="Path to dataset (e.g., data/processed/sales.parquet)"),
    name: Optional[str] = typer.Option(None, "--name", help="Dataset name (defaults to filename without extension)"),
    version: str = typer.Option(..., "--version", help="Semantic version (e.g., 1.0.0)"),
    rows: int = typer.Option(..., "--rows", help="Number of rows in dataset"),
    client: Optional[str] = typer.Option(None, "--client", help="Client slug"),
    cleanliness: Optional[int] = typer.Option(None, "--cleanliness", help="Cleanliness score (0-100)"),
    release: Optional[str] = typer.Option(None, "--release", help="Release tag (e.g., v1.0.0)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Dataset description"),
):
    """
    Register a dataset in the catalog.

    Computes SHA256 hash and schema hash, adds to manifest.

    Example:
        orchestrator registry dataset-register --path data/processed/sales.parquet --version 1.0.0 --rows 3200000 --client acme-corp
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        # Resolve paths
        artifact_path = Path(path)
        if not artifact_path.is_absolute():
            artifact_path = PROJECT_ROOT / artifact_path

        if not artifact_path.exists():
            console.print(f"[red]Error: Artifact not found: {path}[/red]", file=sys.stderr)
            raise typer.Exit(1)

        # Default name from filename
        if not name:
            name = artifact_path.stem

        # Make path relative to project root
        relative_path = str(artifact_path.relative_to(PROJECT_ROOT))

        console.print(f"[cyan]Registering dataset: {name} v{version}[/cyan]")
        console.print(f"Artifact: {relative_path}")
        console.print(f"Rows: {rows:,}")

        # Register
        entry = manager.register_dataset(
            name=name,
            version=version,
            artifacts=[relative_path],
            row_count=rows,
            cleanliness_score=cleanliness,
            release_tag=release,
            client=client,
            notes=notes,
        )

        console.print(f"[green]✓ Dataset registered successfully[/green]")
        console.print(f"ID: {entry.id}")
        console.print(f"SHA256: {entry.sha256[:16]}...")
        console.print(f"Schema hash: {entry.schema_hash[:16]}...")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("fetch")
def fetch_entry(
    name: str = typer.Option(..., "--name", help="Model or dataset name"),
    version: Optional[str] = typer.Option(None, "--version", help="Version (latest if not specified)"),
    type: str = typer.Option("model", "--type", help="Entry type (model or dataset)"),
):
    """
    Fetch model or dataset metadata by name and version.

    Example:
        orchestrator registry fetch --name forecast_v1 --version 1.0.0 --type model
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        if type == "model":
            entry = manager.get_model(name, version)
            if not entry:
                console.print(f"[red]Model not found: {name} v{version or 'latest'}[/red]", file=sys.stderr)
                raise typer.Exit(1)

            console.print(f"[cyan]Model: {entry.name} v{entry.version}[/cyan]")
            console.print(f"ID: {entry.id}")
            console.print(f"Created: {entry.created_at}")
            console.print(f"SHA256: {entry.sha256}")
            console.print(f"\nArtifacts:")
            for artifact in entry.artifacts:
                full_path = PROJECT_ROOT / artifact
                exists = " (exists)" if full_path.exists() else " (NOT FOUND)"
                console.print(f"  {artifact}{exists}")

            if entry.metrics:
                console.print(f"\nMetrics:")
                for key, value in entry.metrics.items():
                    console.print(f"  {key}: {value}")

            if entry.cleanliness_score is not None:
                console.print(f"\nCleanliness Score: {entry.cleanliness_score}/100")

            if entry.release_tag:
                console.print(f"Release: {entry.release_tag}")

            if entry.client:
                console.print(f"Client: {entry.client}")

        elif type == "dataset":
            entry = manager.get_dataset(name, version)
            if not entry:
                console.print(f"[red]Dataset not found: {name} v{version or 'latest'}[/red]", file=sys.stderr)
                raise typer.Exit(1)

            console.print(f"[cyan]Dataset: {entry.name} v{entry.version}[/cyan]")
            console.print(f"ID: {entry.id}")
            console.print(f"Created: {entry.created_at}")
            console.print(f"SHA256: {entry.sha256}")
            console.print(f"Schema hash: {entry.schema_hash}")
            console.print(f"Rows: {entry.row_count:,}")
            console.print(f"\nArtifacts:")
            for artifact in entry.artifacts:
                full_path = PROJECT_ROOT / artifact
                exists = " (exists)" if full_path.exists() else " (NOT FOUND)"
                console.print(f"  {artifact}{exists}")

            if entry.cleanliness_score is not None:
                console.print(f"\nCleanliness Score: {entry.cleanliness_score}/100")

            if entry.release_tag:
                console.print(f"Release: {entry.release_tag}")

            if entry.client:
                console.print(f"Client: {entry.client}")

        else:
            console.print(f"[red]Invalid type: {type}. Must be 'model' or 'dataset'[/red]", file=sys.stderr)
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("list")
def list_entries(
    type: str = typer.Option("model", "--type", help="Entry type (model or dataset)"),
    client: Optional[str] = typer.Option(None, "--client", help="Filter by client slug"),
    release: Optional[str] = typer.Option(None, "--release", help="Filter by release tag"),
):
    """
    List models or datasets with optional filters.

    Example:
        orchestrator registry list --type model --client acme-corp
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        if type == "model":
            models = manager.list_models(client=client, release_tag=release)

            if not models:
                console.print("[yellow]No models found[/yellow]")
                return

            table = Table(title=f"Models ({len(models)})")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Client", style="dim")
            table.add_column("Cleanliness", justify="right")
            table.add_column("Release", style="dim")
            table.add_column("Created", style="dim")

            for model in sorted(models, key=lambda m: (m.name, m.version)):
                cleanliness = f"{model.cleanliness_score}/100" if model.cleanliness_score is not None else "-"
                table.add_row(
                    model.name,
                    model.version,
                    model.client or "-",
                    cleanliness,
                    model.release_tag or "-",
                    model.created_at[:10],  # Date only
                )

            console.print(table)

        elif type == "dataset":
            datasets = manager.list_datasets(client=client, release_tag=release)

            if not datasets:
                console.print("[yellow]No datasets found[/yellow]")
                return

            table = Table(title=f"Datasets ({len(datasets)})")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Rows", justify="right")
            table.add_column("Client", style="dim")
            table.add_column("Cleanliness", justify="right")
            table.add_column("Release", style="dim")
            table.add_column("Created", style="dim")

            for dataset in sorted(datasets, key=lambda d: (d.name, d.version)):
                cleanliness = f"{dataset.cleanliness_score}/100" if dataset.cleanliness_score is not None else "-"
                table.add_row(
                    dataset.name,
                    dataset.version,
                    f"{dataset.row_count:,}",
                    dataset.client or "-",
                    cleanliness,
                    dataset.release_tag or "-",
                    dataset.created_at[:10],
                )

            console.print(table)

        else:
            console.print(f"[red]Invalid type: {type}. Must be 'model' or 'dataset'[/red]", file=sys.stderr)
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("verify")
def verify_integrity():
    """
    Verify integrity of registry and catalog.

    Checks that all artifacts exist and SHA256 hashes match.
    Returns non-zero exit code if any errors found.

    Example:
        orchestrator registry verify
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        console.print("[cyan]Verifying registry integrity...[/cyan]")
        results = manager.verify_integrity()

        console.print(f"Models checked: {results['models_checked']}")
        console.print(f"Datasets checked: {results['datasets_checked']}")

        if results["errors"]:
            console.print(f"\n[red]Errors found ({len(results['errors'])}):[/red]")
            for error in results["errors"]:
                console.print(f"  - {error}")

        if results["warnings"]:
            console.print(f"\n[yellow]Warnings ({len(results['warnings'])}):[/yellow]")
            for warning in results["warnings"]:
                console.print(f"  - {warning}")

        if results["valid"]:
            console.print(f"\n[green]✓ All integrity checks passed[/green]")
        else:
            console.print(f"\n[red]✗ Integrity verification failed[/red]", file=sys.stderr)
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


@app.command("stats")
def show_stats():
    """
    Show aggregate registry statistics.

    Displays model/dataset counts by client and average cleanliness scores.

    Example:
        orchestrator registry stats
    """
    try:
        manager = RegistryManager(PROJECT_ROOT)

        stats = manager.get_stats()

        console.print("[cyan]Registry Statistics[/cyan]\n")

        console.print(f"Total Models: {stats['models_total']}")
        console.print(f"Total Datasets: {stats['datasets_total']}")

        if stats["avg_model_cleanliness"] is not None:
            console.print(f"Avg Model Cleanliness: {stats['avg_model_cleanliness']:.1f}/100")

        if stats["avg_dataset_cleanliness"] is not None:
            console.print(f"Avg Dataset Cleanliness: {stats['avg_dataset_cleanliness']:.1f}/100")

        if stats["models_by_client"]:
            console.print("\nModels by Client:")
            for client, count in sorted(stats["models_by_client"].items()):
                console.print(f"  {client}: {count}")

        if stats["datasets_by_client"]:
            console.print("\nDatasets by Client:")
            for client, count in sorted(stats["datasets_by_client"].items()):
                console.print(f"  {client}: {count}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
