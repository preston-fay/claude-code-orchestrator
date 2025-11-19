#!/usr/bin/env python3
"""Validate KDS color compliance.

Scans all KDS files for hex colors and fails if non-approved colors are found.
This enforces the Kearney brand palette: white + slate + purple accent.
"""

import re
import sys
from pathlib import Path
from typing import Set, List, Tuple

# Approved Kearney palette (case-insensitive)
APPROVED_COLORS = {
    # Dark & White
    "#1E1E1E", "#FFFFFF", "#000000",
    # Greys
    "#F5F5F5", "#FAFAFA", "#E6E6E6", "#D2D2D2", "#C8C8C8", "#B9B9B9",
    "#A5A5A5", "#8C8C8C", "#787878", "#5F5F5F", "#4B4B4B",
    "#323232", "#2D2D2D", "#1A1A1A",
    # Purples (primary)
    "#7823DC", "#9150E1", "#AF7DEB", "#C8A5F0", "#E6D2FA",
    # Purples (secondary)
    "#8737E1", "#A064E6", "#B991EB", "#D7BEF5",
    # Light purple tints (for backgrounds)
    "#F4EDFF",  # Very light purple for insight boxes
}

# Files to scan
SCAN_PATTERNS = [
    "design_system/**/*.json",
    "design_system/**/*.ts",
    "design_system/**/*.js",
    "design_system/**/*.css",
    "apps/web/src/**/*.tsx",
    "apps/web/src/**/*.ts",
    "apps/web/src/**/*.css",
    "apps/web/tailwind.config.js",
    "src/dashboard/**/*.js",
    "src/dashboard/**/*.css",
    "src/server/**/*.css",
    "site/src/**/*.css",
]

# Files/paths to ignore
IGNORE_PATTERNS = [
    "*/node_modules/*",
    "*/dist/*",
    "*/build/*",
    "*/__pycache__/*",
    "*/htmlcov/*",
    "*/coverage/*",
    "*/.cache/*",
    "clients/*/governance.yaml",  # Client examples OK
    "clients/example-client/*",   # Example client OK
]

HEX_COLOR_PATTERN = re.compile(r'#[0-9A-Fa-f]{6}\b')


def should_ignore(file_path: Path, root: Path) -> bool:
    """Check if file should be ignored."""
    rel_path = str(file_path.relative_to(root))
    return any(
        pattern.replace("*/", "").replace("*", "") in rel_path
        for pattern in IGNORE_PATTERNS
    )


def scan_file(file_path: Path) -> List[Tuple[int, str]]:
    """Scan a file for hex colors and return violations."""
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments in CSS/JS/TS files
                if line.strip().startswith('//') or line.strip().startswith('/*'):
                    continue

                for match in HEX_COLOR_PATTERN.finditer(line):
                    color = match.group().upper()
                    if color not in APPROVED_COLORS:
                        violations.append((line_num, color, line.strip()))
    except (UnicodeDecodeError, PermissionError):
        pass  # Skip binary files or files we can't read
    return violations


def validate_colors() -> int:
    """Validate all KDS files for color compliance."""
    root = Path(__file__).parent.parent
    violations_found = False
    total_files_scanned = 0
    files_with_violations = 0

    print("🎨 Validating KDS Color Compliance...")
    print(f"   Approved palette: {len(APPROVED_COLORS)} colors")
    print(f"   Brand principle: white + slate + purple accent")
    print(f"   Forbidden: green, red, orange, blue\n")

    for pattern in SCAN_PATTERNS:
        for file_path in root.glob(pattern):
            # Check ignore patterns
            if should_ignore(file_path, root):
                continue

            total_files_scanned += 1
            violations = scan_file(file_path)

            if violations:
                violations_found = True
                files_with_violations += 1
                rel_path = file_path.relative_to(root)
                print(f"❌ {rel_path}")
                for line_num, color, line_content in violations:
                    print(f"   Line {line_num}: {color}")
                    # Show context (truncate if too long)
                    context = line_content[:80] + "..." if len(line_content) > 80 else line_content
                    print(f"   Context: {context}")
                print()

    print(f"\n📊 Scan Summary:")
    print(f"   Files scanned: {total_files_scanned}")
    print(f"   Files with violations: {files_with_violations}")

    if violations_found:
        print("\n❌ KDS color validation FAILED")
        print("\nApproved Kearney palette:")
        print("  - Dark & White: #1E1E1E, #FFFFFF, #000000")
        print("  - Greys: #F5F5F5 → #1A1A1A (11 shades)")
        print("  - Purples: #7823DC, #9150E1, #AF7DEB, #C8A5F0, #E6D2FA")
        print("  - Alt purples: #8737E1, #A064E6, #B991EB, #D7BEF5")
        print("\nSee docs/kds_color_audit.md for complete palette and usage guidelines.")
        return 1
    else:
        print("\n✅ All colors comply with Kearney brand palette")
        print("   NO green, red, orange, or blue detected")
        print("   Brand principle verified: white + slate + purple accent")
        return 0


if __name__ == "__main__":
    sys.exit(validate_colors())
