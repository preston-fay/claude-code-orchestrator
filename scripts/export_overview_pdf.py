#!/usr/bin/env python3
"""
Export the Orchestrator Overview HTML to a branded PDF using WeasyPrint.

Usage:
    python scripts/export_overview_pdf.py
"""

import os
from pathlib import Path

try:
    from weasyprint import HTML, CSS
except ImportError:
    print("WeasyPrint not installed. Install with: pip install weasyprint")
    exit(1)

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
HTML_PATH = PROJECT_DIR / "docs" / "ORCHESTRATOR_OVERVIEW.html"
OUTPUT_PATH = PROJECT_DIR / "docs" / "ORCHESTRATOR_OVERVIEW.pdf"


def main():
    print("Kearney PDF Export - Orchestrator Overview")
    print("=" * 42)
    print()

    if not HTML_PATH.exists():
        print(f"Error: HTML file not found at {HTML_PATH}")
        exit(1)

    print(f"Input:  {HTML_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    # Generate PDF
    print("Generating PDF...")

    html = HTML(filename=str(HTML_PATH))
    html.write_pdf(str(OUTPUT_PATH))

    print()
    print("=" * 42)
    print("PDF exported successfully!")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
