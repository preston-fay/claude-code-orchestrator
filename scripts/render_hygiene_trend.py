#!/usr/bin/env python3
"""Render hygiene trend chart from CSV history."""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def load_trend_data(trend_path: Path) -> List[Dict]:
    """Load trend data from CSV."""
    if not trend_path.exists():
        raise FileNotFoundError(f"Trend CSV not found: {trend_path}")

    with open(trend_path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def render_chart(trend_data: List[Dict], output_path: Path) -> None:
    """Render line chart of cleanliness score over time."""
    if not trend_data:
        print("⚠️  No trend data to render")
        return

    # Parse data
    dates = [datetime.fromisoformat(row["timestamp"]) for row in trend_data]
    scores = [float(row["score"]) for row in trend_data]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot score line
    ax.plot(dates, scores, marker="o", linewidth=2, markersize=8, color="#4CAF50")

    # Add horizontal reference lines
    ax.axhline(y=95, color="green", linestyle="--", linewidth=1, alpha=0.5, label="A+ (95)")
    ax.axhline(y=85, color="orange", linestyle="--", linewidth=1, alpha=0.5, label="Min CI Pass (85)")
    ax.axhline(y=75, color="red", linestyle="--", linewidth=1, alpha=0.5, label="Warning (75)")

    # Formatting
    ax.set_title("Repository Cleanliness Score Over Time", fontsize=16, fontweight="bold")
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Cleanliness Score", fontsize=12)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45, ha="right")

    # Annotate latest score
    if dates:
        latest_date = dates[-1]
        latest_score = scores[-1]
        ax.annotate(
            f"{latest_score:.1f}",
            xy=(latest_date, latest_score),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=12,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="gray"),
        )

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✅ Rendered trend chart to {output_path}")


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    trend_path = root / "reports" / "hygiene_trend.csv"
    output_path = root / "docs" / "hygiene_trend.png"

    trend_data = load_trend_data(trend_path)
    render_chart(trend_data, output_path)


if __name__ == "__main__":
    main()
