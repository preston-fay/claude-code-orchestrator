"""Repository scanner for orphaned files and large binaries."""

import csv
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import os

from .config import HygieneConfig


def is_whitelisted(file_path: Path, whitelist_globs: List[str]) -> bool:
    """Check if file matches any whitelist pattern."""
    path_str = str(file_path)
    for pattern in whitelist_globs:
        if fnmatch.fnmatch(path_str, pattern):
            return True
    return False


def is_gitignored(file_path: Path, root: Path) -> bool:
    """Check if file is in .gitignore (simple check)."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return False

    with open(gitignore_path, "r") as f:
        patterns = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    rel_path = str(file_path.relative_to(root))
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
            rel_path, f"**/{pattern}"
        ):
            return True
    return False


def is_tidyignored(file_path: Path, root: Path) -> bool:
    """Check if file is in .tidyignore."""
    tidyignore_path = root / ".tidyignore"
    if not tidyignore_path.exists():
        return False

    with open(tidyignore_path, "r") as f:
        patterns = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    rel_path = str(file_path.relative_to(root))
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
            rel_path, f"**/{pattern}"
        ):
            return True
    return False


def find_references(file_path: Path, root: Path, search_exts: List[str]) -> int:
    """Count references to file in codebase."""
    filename = file_path.name
    count = 0

    for ext in search_exts:
        for search_file in root.rglob(f"*{ext}"):
            if search_file == file_path:
                continue
            try:
                with open(search_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if filename in content or str(file_path.relative_to(root)) in content:
                        count += 1
            except Exception:
                continue

    return count


def scan_large_files(
    root: Path,
    config: HygieneConfig,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """Scan for large binary files exceeding threshold."""
    if output_path is None:
        output_path = root / "reports" / "large_files.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    large_files = []
    threshold_bytes = config.large_file_mb * 1024 * 1024

    # Walk repository
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip .git directory
        if ".git" in file_path.parts:
            continue

        # Check if binary
        if file_path.suffix.lower() not in config.binary_exts:
            continue

        # Check size
        size_bytes = file_path.stat().st_size
        if size_bytes < threshold_bytes:
            continue

        # Check if whitelisted
        rel_path = file_path.relative_to(root)
        whitelisted = (
            is_whitelisted(rel_path, config.whitelist_globs)
            or is_tidyignored(file_path, root)
        )

        large_files.append(
            {
                "path": str(rel_path),
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "type": file_path.suffix,
                "whitelisted": whitelisted,
                "recommendation": "KEEP" if whitelisted else "REVIEW",
            }
        )

    # Sort by size descending
    large_files.sort(key=lambda x: x["size_mb"], reverse=True)

    # Write CSV
    if large_files:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["path", "size_mb", "type", "whitelisted", "recommendation"]
            )
            writer.writeheader()
            writer.writerows(large_files)

    return large_files


def scan_orphans(
    root: Path,
    config: HygieneConfig,
    output_path: Optional[Path] = None,
) -> List[Dict]:
    """Scan for orphaned files (not referenced in codebase)."""
    if output_path is None:
        output_path = root / "reports" / "orphans.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    orphans = []
    min_age = timedelta(days=config.orphan_min_age_days)
    now = datetime.now()

    # Get reference extensions
    ref_exts = config.get("orphan_detection.reference_extensions", [".py", ".md"])

    # Walk repository
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        # Skip .git, .claude, venv, etc.
        if any(
            part.startswith(".")
            for part in file_path.parts
            if part not in [".", ".."]
        ):
            continue

        # Skip Python cache, build artifacts
        if any(
            part in ["__pycache__", "node_modules", "venv", ".venv", "dist", "build"]
            for part in file_path.parts
        ):
            continue

        # Check age
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if now - mtime < min_age:
            continue

        # Check if whitelisted
        rel_path = file_path.relative_to(root)
        if is_whitelisted(rel_path, config.whitelist_globs):
            continue
        if is_tidyignored(file_path, root):
            continue

        # Check if protected pattern
        protected_patterns = config.get(
            "orphan_detection.protected_patterns", ["example", "template"]
        )
        if any(pattern in file_path.name.lower() for pattern in protected_patterns):
            continue

        # Find references
        ref_count = find_references(file_path, root, ref_exts)

        if ref_count == 0:
            orphans.append(
                {
                    "path": str(rel_path),
                    "last_modified": mtime.strftime("%Y-%m-%d"),
                    "references_found": ref_count,
                    "recommendation": "REVIEW",
                }
            )

    # Write CSV
    if orphans:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["path", "last_modified", "references_found", "recommendation"],
            )
            writer.writeheader()
            writer.writerows(orphans)

    return orphans


def main():
    """CLI entry point for scanner."""
    import sys

    root = Path.cwd()
    config = HygieneConfig()

    print("🔍 Scanning repository for hygiene issues...")
    print()

    # Scan large files
    print("📦 Scanning for large files...")
    large_files = scan_large_files(root, config)
    print(f"   Found {len(large_files)} large files")

    # Scan orphans
    print("🗑️  Scanning for orphaned files...")
    orphans = scan_orphans(root, config)
    print(f"   Found {len(orphans)} potential orphans")

    print()
    print("✓ Scan complete")
    print(f"  - reports/large_files.csv")
    print(f"  - reports/orphans.csv")


if __name__ == "__main__":
    main()
