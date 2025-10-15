"""
Governance CLI commands.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..governance.profiling import profile_dataset, profile_model, persist_profile
from ..governance.runner import run_nightly, rebuild_snapshot, load_latest_profile

app = typer.Typer(help="Governance and quality management commands")
console = Console()


@app.command()
def profile(
    dataset: Optional[str] = typer.Option(None, help="Profile specific dataset"),
    model: Optional[str] = typer.Option(None, help="Profile specific model"),
    all: bool = typer.Option(False, "--all", help="Profile all datasets and models"),
):
    """
    Profile datasets and models for quality metrics.
    """
    if not any([dataset, model, all]):
        console.print("[yellow]Specify --dataset, --model, or --all[/yellow]")
        raise typer.Exit(1)

    if all:
        console.print("[bold]Running full governance profiling...[/bold]\n")

        with console.status("Profiling resources..."):
            summary = run_nightly()

        # Display summary table
        table = Table(title="Profiling Summary", show_header=False, border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Datasets Profiled", str(summary["datasets_profiled"]))
        table.add_row("Models Profiled", str(summary["models_profiled"]))
        table.add_row("Drift Detected", str(len(summary["drift_detected"])))
        table.add_row("Errors", str(len(summary["errors"])))

        console.print(table)

        # Show drift alerts
        if summary["drift_detected"]:
            console.print("\n[yellow]Drift Alerts:[/yellow]")
            for alert in summary["drift_detected"]:
                flags = ", ".join(alert["flags"])
                console.print(f"  - {alert['kind']}: {alert['name']} ({flags})")

        # Show errors
        if summary["errors"]:
            console.print("\n[red]Errors:[/red]")
            for error in summary["errors"][:5]:
                console.print(f"  - {error['path']}: {error['error']}")

    elif dataset:
        # Profile specific dataset
        dataset_path = Path("datasets") / f"{dataset}.csv"
        if not dataset_path.exists():
            dataset_path = Path("datasets") / f"{dataset}.parquet"

        if not dataset_path.exists():
            console.print(f"[red]Dataset not found: {dataset}[/red]")
            raise typer.Exit(1)

        console.print(f"[bold]Profiling dataset: {dataset}[/bold]\n")

        with console.status("Computing statistics..."):
            stats = profile_dataset(dataset_path)

        # Display stats table
        table = Table(title=f"Dataset Profile: {dataset}", border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Rows", f"{stats['rows']:,}")
        table.add_row("Columns", str(stats["columns"]))
        table.add_row("Size", f"{stats['size_bytes'] / 1024:.1f} KB")
        table.add_row("Duplicates", f"{stats['duplicate_rows']:,} ({stats['duplicate_pct']:.1f}%)")
        table.add_row("Modified", stats["modified_at"])
        table.add_row("Hash", stats["content_hash"])

        console.print(table)

        # Column stats
        console.print("\n[bold]Column Statistics:[/bold]\n")
        col_table = Table(border_style="dim")
        col_table.add_column("Column", style="cyan")
        col_table.add_column("Type", style="yellow")
        col_table.add_column("Nulls", style="white")
        col_table.add_column("Details", style="white")

        for col, col_stats in stats["columns_detail"].items():
            null_info = f"{col_stats['null_count']:,} ({col_stats['null_pct']:.1f}%)"

            details = []
            if "mean" in col_stats:
                details.append(f"mean={col_stats['mean']:.2f}")
            if "unique_count" in col_stats:
                details.append(f"unique={col_stats['unique_count']}")

            col_table.add_row(col, col_stats["type"], null_info, ", ".join(details))

        console.print(col_table)

        # Persist
        persist_profile("dataset", dataset, "latest", stats)
        console.print(f"\n[green]Profile saved to governance/profiles/datasets.ndjson[/green]")

    elif model:
        # Profile specific model
        model_path = Path("models") / f"{model}.pkl"

        if not model_path.exists():
            console.print(f"[red]Model not found: {model}[/red]")
            raise typer.Exit(1)

        console.print(f"[bold]Profiling model: {model}[/bold]\n")

        # Look for metrics
        metrics_path = model_path.parent / f"{model}_metrics.json"
        if not metrics_path.exists():
            metrics_path = None

        with console.status("Computing statistics..."):
            stats = profile_model(model_path, metrics_path)

        # Display stats table
        table = Table(title=f"Model Profile: {model}", border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Size", f"{stats['size_bytes'] / 1024:.1f} KB")
        table.add_row("Modified", stats["modified_at"])
        table.add_row("SHA256", stats["sha256"][:16] + "...")

        if stats["metrics"]:
            table.add_row("", "")
            table.add_row("[bold]Performance Metrics[/bold]", "")
            for metric, value in stats["metrics"].items():
                if value is not None:
                    table.add_row(f"  {metric}", f"{value:.4f}" if isinstance(value, float) else str(value))

        console.print(table)

        # Persist
        persist_profile("model", model, "latest", stats)
        console.print(f"\n[green]Profile saved to governance/profiles/models.ndjson[/green]")


@app.command()
def snapshot(
    date: Optional[str] = typer.Option(None, help="Rebuild snapshot for date (YYYY-MM-DD)"),
):
    """
    Create or rebuild governance snapshot.
    """
    if date:
        console.print(f"[bold]Rebuilding snapshot for {date}...[/bold]\n")

        try:
            snapshot = rebuild_snapshot(date)

            table = Table(title=f"Snapshot: {date}", show_header=False, border_style="dim")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Datasets", str(snapshot["summary"]["datasets"]))
            table.add_row("Models", str(snapshot["summary"]["models"]))
            table.add_row("Drift Alerts", str(snapshot["summary"]["drift_alerts"]))
            table.add_row("Errors", str(snapshot["summary"]["errors"]))

            console.print(table)
            console.print(f"\n[green]Snapshot saved to governance/snapshots/{date}.json[/green]")

        except Exception as e:
            console.print(f"[red]Error rebuilding snapshot: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Show latest snapshot
        snapshots_dir = Path("governance/snapshots")
        if not snapshots_dir.exists():
            console.print("[yellow]No snapshots found. Run 'orchestrator gov profile --all' first.[/yellow]")
            raise typer.Exit(1)

        snapshots = sorted(snapshots_dir.glob("*.json"), reverse=True)
        if not snapshots:
            console.print("[yellow]No snapshots found.[/yellow]")
            raise typer.Exit(1)

        latest = snapshots[0]
        with open(latest) as f:
            snapshot = json.load(f)

        table = Table(title=f"Latest Snapshot: {snapshot['date']}", show_header=False, border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Datasets", str(snapshot["summary"]["datasets"]))
        table.add_row("Models", str(snapshot["summary"]["models"]))
        table.add_row("Drift Alerts", str(snapshot["summary"]["drift_alerts"]))
        table.add_row("Errors", str(snapshot["summary"]["errors"]))

        console.print(table)

        if snapshot.get("drift_detected"):
            console.print("\n[yellow]Drift Alerts:[/yellow]")
            for alert in snapshot["drift_detected"]:
                flags = ", ".join(alert["flags"])
                console.print(f"  - {alert['kind']}: {alert['name']} ({flags})")


@app.command()
def flags(
    action: str = typer.Argument(..., help="Action: list, set, unset"),
    name: Optional[str] = typer.Argument(None, help="Flag name"),
    value: Optional[str] = typer.Argument(None, help="Flag value (on/off)"),
):
    """
    Manage feature flags.
    """
    from ..governance.flags import get_all_flags, set_flag, unset_flag, is_enabled

    if action == "list":
        flags_dict = get_all_flags()

        table = Table(title="Feature Flags", border_style="dim")
        table.add_column("Flag", style="cyan")
        table.add_column("Enabled", style="white")
        table.add_column("Category", style="yellow")

        for flag_name, enabled in sorted(flags_dict.items()):
            category = flag_name.split(".")[0] if "." in flag_name else "general"
            status = "[green]ON[/green]" if enabled else "[dim]OFF[/dim]"
            table.add_row(flag_name, status, category)

        console.print(table)

    elif action == "set":
        if not name:
            console.print("[red]Flag name required[/red]")
            raise typer.Exit(1)

        enabled = value != "off" if value else True
        set_flag(name, enabled)

        status = "enabled" if enabled else "disabled"
        console.print(f"[green]Flag '{name}' {status}[/green]")

    elif action == "unset":
        if not name:
            console.print("[red]Flag name required[/red]")
            raise typer.Exit(1)

        unset_flag(name)
        console.print(f"[green]Flag '{name}' removed[/green]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: list, set, unset")
        raise typer.Exit(1)
