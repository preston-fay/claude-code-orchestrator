#!/usr/bin/env python3
"""Generate SVG badge for repository cleanliness score."""

import json
from pathlib import Path
from typing import Tuple


def load_score(summary_path: Path) -> Tuple[float, str]:
    """Load current cleanliness score and grade."""
    if not summary_path.exists():
        raise FileNotFoundError(f"Hygiene summary not found: {summary_path}")

    with open(summary_path) as f:
        data = json.load(f)
        return data["cleanliness_score"], data["grade"]


def get_color(score: float) -> str:
    """Determine badge color based on score."""
    if score >= 95:
        return "#4CAF50"  # Green (A+)
    elif score >= 90:
        return "#8BC34A"  # Light Green (A)
    elif score >= 85:
        return "#FFC107"  # Amber (B+)
    elif score >= 80:
        return "#FF9800"  # Orange (B)
    elif score >= 75:
        return "#FF5722"  # Deep Orange (C+)
    else:
        return "#F44336"  # Red (D-F)


def generate_badge_svg(score: float, grade: str, color: str) -> str:
    """Generate SVG badge (Shields.io style)."""
    label = "cleanliness"
    message = f"{score:.0f}/100 ({grade})"

    # Calculate widths (approximate, monospace)
    label_width = len(label) * 7 + 10
    message_width = len(message) * 7 + 10
    total_width = label_width + message_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="a">
    <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#a)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{message_width}v20H{label_width}z"/>
    <path fill="url(#b)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width // 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width // 2}" y="14">{label}</text>
    <text x="{label_width + message_width // 2}" y="15" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_width + message_width // 2}" y="14">{message}</text>
  </g>
</svg>'''
    return svg


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    summary_path = root / "reports" / "hygiene_summary.json"
    output_path = root / "docs" / "badges" / "cleanliness.svg"

    score, grade = load_score(summary_path)
    color = get_color(score)
    svg = generate_badge_svg(score, grade, color)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(svg)

    print(f"✅ Generated badge: {output_path}")
    print(f"   Score: {score}/100 (Grade: {grade}, Color: {color})")


if __name__ == "__main__":
    main()
