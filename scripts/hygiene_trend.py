#!/usr/bin/env python3
"""Append current hygiene stats to trend CSV for historical tracking."""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_current_stats(summary_path: Path) -> Dict:
    """Load current hygiene stats from JSON summary."""
    if not summary_path.exists():
        raise FileNotFoundError(f"Hygiene summary not found: {summary_path}")

    with open(summary_path) as f:
        return json.load(f)


def append_to_trend(trend_path: Path, stats: Dict) -> None:
    """Append current stats to trend CSV."""
    trend_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare row
    row = {
        "date": stats["timestamp"][:10],  # YYYY-MM-DD
        "timestamp": stats["timestamp"],
        "score": stats["cleanliness_score"],
        "grade": stats["grade"],
        "orphans": stats["stats"]["orphans"],
        "large_files": stats["stats"]["large_files"],
        "dead_code_functions": stats["stats"]["dead_code_functions"],
        "dead_code_classes": stats["stats"]["dead_code_classes"],
        "dead_code_imports": stats["stats"]["dead_code_imports"],
        "notebooks_to_fix": stats["stats"]["notebooks_needs_cleanup"],
        "secrets_findings": stats["stats"]["secrets_findings"],
    }

    # Read existing rows to check for duplicates
    existing_rows: List[Dict] = []
    if trend_path.exists():
        with open(trend_path, newline="") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)

    # Deduplicate: skip if exact timestamp exists
    if any(r["timestamp"] == row["timestamp"] for r in existing_rows):
        print(f"Skipping duplicate entry for {row['timestamp']}")
        return

    # Append new row
    file_exists = trend_path.exists()
    with open(trend_path, "a", newline="") as f:
        fieldnames = [
            "date",
            "timestamp",
            "score",
            "grade",
            "orphans",
            "large_files",
            "dead_code_functions",
            "dead_code_classes",
            "dead_code_imports",
            "notebooks_to_fix",
            "secrets_findings",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    print(f"✅ Appended hygiene stats to {trend_path}")
    print(f"   Score: {row['score']}/100 (Grade: {row['grade']})")


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    summary_path = root / "reports" / "hygiene_summary.json"
    trend_path = root / "reports" / "hygiene_trend.csv"

    stats = load_current_stats(summary_path)
    append_to_trend(trend_path, stats)


if __name__ == "__main__":
    main()
