"""Demo end-to-end data pipeline: ingest → transform → train → evaluate."""

import json
from pathlib import Path
from typing import Dict, Any
import sys

# Allow imports from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def get_project_paths() -> Dict[str, Path]:
    """Get standard project paths."""
    base = Path(__file__).parent.parent.parent
    return {
        "base": base,
        "data": base / "data",
        "raw": base / "data" / "raw",
        "interim": base / "data" / "interim",
        "processed": base / "data" / "processed",
        "external": base / "data" / "external" / "sample",
        "models": base / "models",
    }


def run_demo_pipeline(verbose: bool = True) -> Dict[str, Any]:
    """
    Execute the demo pipeline end-to-end.

    Steps:
        1. Ingest: Load sample data to raw/
        2. Transform: Clean and engineer features to processed/
        3. Train: Train RandomForest model
        4. Evaluate: Compute metrics and save

    Args:
        verbose: Whether to print progress messages

    Returns:
        Dictionary with pipeline results and artifact paths
    """
    try:
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, classification_report
        import pickle
    except ImportError as e:
        raise ImportError(
            f"Required dependency not installed: {e}. "
            "Run: pip install pandas numpy scikit-learn"
        )

    paths = get_project_paths()
    results = {
        "status": "running",
        "steps": [],
        "artifacts": {},
        "errors": []
    }

    # Ensure directories exist
    for path in [paths["raw"], paths["interim"], paths["processed"], paths["models"]]:
        path.mkdir(parents=True, exist_ok=True)

    try:
        # STEP 1: Ingest
        if verbose:
            print("📥 Step 1/4: Ingesting data...")

        # Create sample data (or load from external)
        np.random.seed(42)
        df_raw = pd.DataFrame({
            'id': range(1, 101),
            'feature_a': np.random.randn(100),
            'feature_b': np.random.randint(0, 10, 100),
            'feature_c': np.random.choice(['A', 'B', 'C'], 100),
            'target': np.random.randint(0, 2, 100)
        })

        raw_path = paths["raw"] / "demo_data.csv"
        df_raw.to_csv(raw_path, index=False)

        results["steps"].append({
            "step": "ingest",
            "status": "success",
            "rows": len(df_raw),
            "path": str(raw_path)
        })
        results["artifacts"]["raw_data"] = str(raw_path)

        if verbose:
            print(f"   ✓ Ingested {len(df_raw)} rows to {raw_path.name}")

        # STEP 2: Transform
        if verbose:
            print("⚙️  Step 2/4: Transforming data...")

        # Clean (interim)
        df_interim = df_raw.copy()
        df_interim = df_interim.dropna()
        df_interim = df_interim.drop_duplicates()

        interim_path = paths["interim"] / "demo_cleaned.csv"
        df_interim.to_csv(interim_path, index=False)

        # Feature engineering (processed)
        df_processed = df_interim.copy()
        df_processed['feature_a_squared'] = df_processed['feature_a'] ** 2
        df_processed['feature_b_norm'] = (
            (df_processed['feature_b'] - df_processed['feature_b'].mean()) /
            df_processed['feature_b'].std()
        )
        df_processed = pd.get_dummies(df_processed, columns=['feature_c'], prefix='cat')

        processed_path = paths["processed"] / "demo_features.csv"
        df_processed.to_csv(processed_path, index=False)

        results["steps"].append({
            "step": "transform",
            "status": "success",
            "rows_in": len(df_raw),
            "rows_out": len(df_processed),
            "features": len(df_processed.columns),
            "path": str(processed_path)
        })
        results["artifacts"]["processed_data"] = str(processed_path)

        if verbose:
            print(f"   ✓ Transformed to {len(df_processed)} rows, {len(df_processed.columns)} features")

        # STEP 3: Train
        if verbose:
            print("🤖 Step 3/4: Training model...")

        X = df_processed.drop('target', axis=1)
        y = df_processed['target']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestClassifier(n_estimators=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        model_path = paths["models"] / "demo_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        # Save metadata
        metadata = {
            "model_name": "demo_model",
            "model_type": "RandomForestClassifier",
            "n_estimators": 10,
            "n_features": len(X.columns),
            "feature_names": list(X.columns),
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
        metadata_path = paths["models"] / "demo_model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        results["steps"].append({
            "step": "train",
            "status": "success",
            "model_type": "RandomForestClassifier",
            "n_train": len(X_train),
            "n_test": len(X_test),
            "path": str(model_path)
        })
        results["artifacts"]["model"] = str(model_path)
        results["artifacts"]["model_metadata"] = str(metadata_path)

        if verbose:
            print(f"   ✓ Trained model on {len(X_train)} samples")

        # STEP 4: Evaluate
        if verbose:
            print("📊 Step 4/4: Evaluating model...")

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        metrics = {
            "accuracy": float(accuracy),
            "n_test_samples": len(y_test),
            "n_correct": int((y_test == y_pred).sum()),
            "n_incorrect": int((y_test != y_pred).sum()),
        }

        metrics_path = paths["models"] / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)

        results["steps"].append({
            "step": "evaluate",
            "status": "success",
            "accuracy": accuracy,
            "n_test": len(y_test),
            "path": str(metrics_path)
        })
        results["artifacts"]["metrics"] = str(metrics_path)
        results["metrics"] = metrics

        if verbose:
            print(f"   ✓ Accuracy: {accuracy:.2%}")

        # Mark pipeline as successful
        results["status"] = "success"

        if verbose:
            print("\n✅ Pipeline completed successfully!")
            print(f"\n📁 Artifacts:")
            for name, path in results["artifacts"].items():
                print(f"   - {name}: {path}")

    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(str(e))
        if verbose:
            print(f"\n❌ Pipeline failed: {e}")
        raise

    return results


if __name__ == "__main__":
    # Run pipeline when executed directly
    results = run_demo_pipeline(verbose=True)

    if results["status"] == "success":
        print(f"\n✅ Final accuracy: {results['metrics']['accuracy']:.2%}")
    else:
        print(f"\n❌ Pipeline failed with errors: {results['errors']}")
        sys.exit(1)
