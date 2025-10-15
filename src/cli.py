"""CLI for Claude Code Orchestrator data pipelines."""

import json
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.progress import track
    import pandas as pd
    import numpy as np
except ImportError:
    # Graceful degradation if dependencies not installed
    print("Warning: Required dependencies not installed. Run: pip install -e .")
    import sys
    sys.exit(1)

app = typer.Typer(
    name="orchestrator",
    help="Claude Code Orchestrator - Data pipeline commands",
    add_completion=False,
)
console = Console()


def get_paths():
    """Get standard data paths."""
    base = Path(__file__).parent.parent
    return {
        "data_dir": base / "data",
        "external": base / "data" / "external" / "sample",
        "raw": base / "data" / "raw",
        "interim": base / "data" / "interim",
        "processed": base / "data" / "processed",
        "models": base / "models",
    }


@app.command()
def ingest(
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Source data file (default: sample)"
    ),
    output_name: str = typer.Option(
        "ingested_data.csv", "--output", "-o", help="Output filename"
    ),
):
    """Ingest data from external source to raw."""
    console.print("[bold blue]🔄 Starting data ingestion...[/bold blue]")

    paths = get_paths()
    paths["raw"].mkdir(parents=True, exist_ok=True)

    try:
        # If no source, create sample data
        if source is None:
            console.print("No source specified, creating sample dataset...")
            np.random.seed(42)
            df = pd.DataFrame({
                'id': range(1, 101),
                'feature_a': np.random.randn(100),
                'feature_b': np.random.randint(0, 10, 100),
                'feature_c': np.random.choice(['A', 'B', 'C'], 100),
                'target': np.random.randint(0, 2, 100)
            })
        else:
            source_path = Path(source)
            if not source_path.exists():
                console.print(f"[red]Error: Source file not found: {source}[/red]")
                raise typer.Exit(1)
            df = pd.read_csv(source_path)

        # Save to raw
        output_path = paths["raw"] / output_name
        df.to_csv(output_path, index=False)

        console.print(f"✅ Ingested {len(df)} rows to [green]{output_path}[/green]")
        console.print(f"   Columns: {list(df.columns)}")
        console.print(f"   Shape: {df.shape}")

    except Exception as e:
        console.print(f"[red]❌ Ingestion failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def transform(
    input_file: str = typer.Option(
        "ingested_data.csv", "--input", "-i", help="Input filename from raw/"
    ),
    output_name: str = typer.Option(
        "transformed_data.csv", "--output", "-o", help="Output filename"
    ),
):
    """Transform raw data to interim and processed."""
    console.print("[bold blue]🔄 Starting data transformation...[/bold blue]")

    paths = get_paths()
    paths["interim"].mkdir(parents=True, exist_ok=True)
    paths["processed"].mkdir(parents=True, exist_ok=True)

    try:
        # Read from raw
        input_path = paths["raw"] / input_file
        if not input_path.exists():
            console.print(f"[red]Error: Input file not found: {input_path}[/red]")
            raise typer.Exit(1)

        df = pd.read_csv(input_path)
        console.print(f"📥 Loaded {len(df)} rows from raw/")

        # Interim: Basic cleaning
        console.print("🧹 Cleaning data...")
        df_interim = df.copy()
        df_interim = df_interim.dropna()  # Remove nulls
        df_interim = df_interim.drop_duplicates()  # Remove duplicates

        interim_path = paths["interim"] / output_name
        df_interim.to_csv(interim_path, index=False)
        console.print(f"   Saved interim: {len(df_interim)} rows to [yellow]{interim_path}[/yellow]")

        # Processed: Feature engineering
        console.print("⚙️  Engineering features...")
        df_processed = df_interim.copy()

        # Example transformations
        if 'feature_a' in df_processed.columns:
            df_processed['feature_a_squared'] = df_processed['feature_a'] ** 2
        if 'feature_b' in df_processed.columns:
            df_processed['feature_b_norm'] = (
                df_processed['feature_b'] - df_processed['feature_b'].mean()
            ) / df_processed['feature_b'].std()
        if 'feature_c' in df_processed.columns:
            df_processed = pd.get_dummies(df_processed, columns=['feature_c'], prefix='cat')

        processed_path = paths["processed"] / output_name
        df_processed.to_csv(processed_path, index=False)
        console.print(f"   Saved processed: {len(df_processed)} rows, {len(df_processed.columns)} features to [green]{processed_path}[/green]")

        console.print("✅ Transformation complete")

    except Exception as e:
        console.print(f"[red]❌ Transformation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def train(
    input_file: str = typer.Option(
        "transformed_data.csv", "--input", "-i", help="Input filename from processed/"
    ),
    model_name: str = typer.Option(
        "demo_model", "--model", "-m", help="Model name"
    ),
):
    """Train a model on processed data."""
    console.print("[bold blue]🤖 Starting model training...[/bold blue]")

    paths = get_paths()
    paths["models"].mkdir(parents=True, exist_ok=True)

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        import pickle

        # Read processed data
        input_path = paths["processed"] / input_file
        if not input_path.exists():
            console.print(f"[red]Error: Input file not found: {input_path}[/red]")
            raise typer.Exit(1)

        df = pd.read_csv(input_path)
        console.print(f"📥 Loaded {len(df)} rows from processed/")

        # Prepare features and target
        if 'target' not in df.columns:
            console.print("[red]Error: 'target' column not found in data[/red]")
            raise typer.Exit(1)

        X = df.drop('target', axis=1)
        y = df['target']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        console.print(f"📊 Train: {len(X_train)} rows, Test: {len(X_test)} rows")

        # Train model
        console.print("🎯 Training RandomForest model...")
        model = RandomForestClassifier(n_estimators=10, random_state=42)

        for _ in track(range(10), description="Training..."):
            pass  # Simulate training progress

        model.fit(X_train, y_train)

        # Save model
        model_path = paths["models"] / f"{model_name}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        # Save metadata
        metadata = {
            "model_name": model_name,
            "model_type": "RandomForestClassifier",
            "n_features": len(X.columns),
            "feature_names": list(X.columns),
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
        metadata_path = paths["models"] / f"{model_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        console.print(f"✅ Model saved to [green]{model_path}[/green]")
        console.print(f"   Metadata: [green]{metadata_path}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Training failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def evaluate(
    model_name: str = typer.Option(
        "demo_model", "--model", "-m", help="Model name to evaluate"
    ),
    input_file: str = typer.Option(
        "transformed_data.csv", "--input", "-i", help="Input filename from processed/"
    ),
):
    """Evaluate a trained model."""
    console.print("[bold blue]📊 Starting model evaluation...[/bold blue]")

    paths = get_paths()

    try:
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split
        import pickle

        # Load model
        model_path = paths["models"] / f"{model_name}.pkl"
        if not model_path.exists():
            console.print(f"[red]Error: Model not found: {model_path}[/red]")
            raise typer.Exit(1)

        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        console.print(f"📥 Loaded model from {model_path}")

        # Load data
        input_path = paths["processed"] / input_file
        df = pd.read_csv(input_path)

        X = df.drop('target', axis=1)
        y = df['target']

        # Split same as training
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Evaluate
        console.print("🎯 Evaluating model...")
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Save metrics
        metrics = {
            "model_name": model_name,
            "accuracy": float(accuracy),
            "n_test_samples": len(y_test),
        }
        metrics_path = paths["models"] / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        console.print(f"\n✅ Evaluation complete:")
        console.print(f"   Accuracy: [green]{accuracy:.2%}[/green]")
        console.print(f"   Metrics saved: [green]{metrics_path}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Evaluation failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show status of data pipeline artifacts."""
    console.print("[bold blue]📊 Pipeline Status[/bold blue]\n")

    paths = get_paths()

    # Check each directory
    for name, path in paths.items():
        if path.exists():
            if path.is_dir():
                files = list(path.glob("*"))
                csv_files = list(path.glob("*.csv"))
                pkl_files = list(path.glob("*.pkl"))
                console.print(f"[green]✓[/green] {name:12} : {len(files)} files", end="")
                if csv_files:
                    console.print(f" ({len(csv_files)} CSV)", end="")
                if pkl_files:
                    console.print(f" ({len(pkl_files)} models)", end="")
                console.print()
            else:
                console.print(f"[yellow]?[/yellow] {name:12} : (not a directory)")
        else:
            console.print(f"[red]✗[/red] {name:12} : (not found)")

    # Check for key artifacts
    console.print("\n[bold]Key Artifacts:[/bold]")

    if (paths["models"] / "metrics.json").exists():
        with open(paths["models"] / "metrics.json") as f:
            metrics = json.load(f)
        console.print(f"  Model metrics: accuracy = [green]{metrics.get('accuracy', 0):.2%}[/green]")
    else:
        console.print("  [yellow]No model metrics found[/yellow]")


if __name__ == "__main__":
    app()
