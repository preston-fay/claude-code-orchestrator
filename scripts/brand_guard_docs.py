#!/usr/bin/env python3
"""
Brand compliance checker for documentation.

Ensures all documentation adheres to Kearney brand guidelines:
- No emojis
- No gridlines mention (checks for grid-related keywords)
- Proper terminology
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

DOCS_DIR = Path(__file__).parent.parent / "site" / "docs"

# Emoji pattern (matches most emoji ranges)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]+"
)

# Terms that might indicate gridlines
GRIDLINE_KEYWORDS = [
    "gridline",
    "grid-line",
    "grid line",
    "chart grid",
    "axis grid",
]

# Forbidden terms
FORBIDDEN_TERMS = {
    "awesome": "Use 'excellent' or 'outstanding' instead",
    "cool": "Use professional terminology",
    "nice": "Use specific descriptive language",
}


def check_emojis(content: str, filepath: Path) -> List[Tuple[int, str]]:
    """Check for emoji usage in content."""
    violations = []
    for i, line in enumerate(content.split("\n"), 1):
        matches = EMOJI_PATTERN.findall(line)
        if matches:
            violations.append((i, f"Emoji found: {matches}"))
    return violations


def check_gridlines(content: str, filepath: Path) -> List[Tuple[int, str]]:
    """Check for gridline mentions."""
    violations = []
    content_lower = content.lower()

    for keyword in GRIDLINE_KEYWORDS:
        if keyword in content_lower:
            # Find line numbers
            for i, line in enumerate(content.split("\n"), 1):
                if keyword in line.lower():
                    # Allow if it's in the context of "no gridlines"
                    if "no gridline" not in line.lower() and "without gridline" not in line.lower():
                        violations.append(
                            (i, f"Gridline mention found: '{keyword}' (ensure it's in 'no gridlines' context)")
                        )
    return violations


def check_forbidden_terms(content: str, filepath: Path) -> List[Tuple[int, str]]:
    """Check for informal or forbidden terminology."""
    violations = []
    content_lower = content.lower()

    for term, suggestion in FORBIDDEN_TERMS.items():
        if re.search(rf"\b{term}\b", content_lower):
            for i, line in enumerate(content.split("\n"), 1):
                if re.search(rf"\b{term}\b", line.lower()):
                    violations.append((i, f"Informal term '{term}' found. {suggestion}"))
    return violations


def check_file(filepath: Path) -> Tuple[Path, List[Tuple[int, str]]]:
    """Check a single file for brand violations."""
    try:
        content = filepath.read_text()
    except Exception as e:
        return filepath, [(0, f"Error reading file: {e}")]

    all_violations = []

    # Run all checks
    all_violations.extend(check_emojis(content, filepath))
    all_violations.extend(check_gridlines(content, filepath))
    all_violations.extend(check_forbidden_terms(content, filepath))

    return filepath, all_violations


def main():
    """Main entry point."""
    print("Running brand compliance checks...")
    print(f"Checking directory: {DOCS_DIR}")

    if not DOCS_DIR.exists():
        print(f"Error: Documentation directory not found: {DOCS_DIR}")
        sys.exit(1)

    # Find all markdown files
    md_files = list(DOCS_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files")

    # Check each file
    all_results = []
    for filepath in md_files:
        result = check_file(filepath)
        if result[1]:  # Has violations
            all_results.append(result)

    # Report results
    if not all_results:
        print("\n✓ All checks passed! Documentation is brand-compliant.")
        sys.exit(0)

    print(f"\n✗ Found brand violations in {len(all_results)} file(s):\n")

    total_violations = 0
    for filepath, violations in all_results:
        rel_path = filepath.relative_to(DOCS_DIR.parent.parent)
        print(f"\n{rel_path}:")
        for line_num, message in violations:
            print(f"  Line {line_num}: {message}")
            total_violations += 1

    print(f"\nTotal violations: {total_violations}")
    print("\nBrand Guidelines:")
    print("- No emojis allowed in documentation")
    print("- No gridlines in charts/visualizations")
    print("- Use professional terminology")
    print("- Inter font with Arial fallback")

    sys.exit(1)


if __name__ == "__main__":
    main()
