"""Jupyter notebook hygiene checker and sanitizer."""

import json
from pathlib import Path
from typing import List, Dict, Optional

from .config import HygieneConfig


def check_notebooks(
    root: Path,
    config: HygieneConfig,
    output_path: Optional[Path] = None,
    clear_outputs: bool = False,
) -> List[Dict]:
    """Check notebooks for outputs and optionally clear them."""
    if output_path is None:
        output_path = root / "reports" / "notebook_sanitizer.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    notebooks_with_outputs = []
    notebooks_cleared = []

    # Find all notebooks
    for nb_path in root.rglob("*.ipynb"):
        # Skip .ipynb_checkpoints
        if ".ipynb_checkpoints" in nb_path.parts:
            continue

        # Skip hidden directories
        if any(part.startswith(".") for part in nb_path.parts if part != "."):
            continue

        rel_path = nb_path.relative_to(root)

        # Check if whitelisted
        whitelisted = any(
            rel_path.match(pattern) for pattern in config.whitelist_globs
        )

        try:
            with open(nb_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)

            # Check for outputs
            has_outputs = False
            cells_with_outputs = 0

            for cell in notebook.get("cells", []):
                if cell.get("cell_type") == "code":
                    outputs = cell.get("outputs", [])
                    execution_count = cell.get("execution_count")

                    if outputs or execution_count:
                        has_outputs = True
                        cells_with_outputs += 1

            if has_outputs:
                notebooks_with_outputs.append(
                    {
                        "path": str(rel_path),
                        "cells_with_outputs": cells_with_outputs,
                        "whitelisted": whitelisted,
                        "recommendation": "KEEP"
                        if whitelisted
                        else "CLEAR_OUTPUTS",
                    }
                )

                # Clear outputs if requested and not whitelisted
                if clear_outputs and not whitelisted:
                    _clear_notebook_outputs(notebook)
                    with open(nb_path, "w", encoding="utf-8") as f:
                        json.dump(notebook, f, indent=1, ensure_ascii=False)
                        f.write("\n")  # Add trailing newline
                    notebooks_cleared.append(str(rel_path))

        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # Skip invalid notebooks
            continue

    # Generate report
    with open(output_path, "w") as f:
        f.write("# Notebook Hygiene Report\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Notebooks with outputs**: {len(notebooks_with_outputs)}\n")
        f.write(
            f"- **Whitelisted**: {sum(1 for nb in notebooks_with_outputs if nb['whitelisted'])}\n"
        )
        f.write(
            f"- **Requiring cleanup**: {sum(1 for nb in notebooks_with_outputs if not nb['whitelisted'])}\n"
        )

        if clear_outputs:
            f.write(f"- **Cleared**: {len(notebooks_cleared)}\n")

        f.write("\n")

        if notebooks_with_outputs:
            f.write("## Notebooks with Outputs\n\n")
            f.write("| Path | Cells with Outputs | Whitelisted | Recommendation |\n")
            f.write("|------|-------------------|-------------|----------------|\n")

            for nb in notebooks_with_outputs:
                f.write(
                    f"| {nb['path']} | {nb['cells_with_outputs']} | "
                    f"{'✓' if nb['whitelisted'] else '✗'} | {nb['recommendation']} |\n"
                )

            f.write("\n")

        if notebooks_cleared:
            f.write("## Notebooks Cleared\n\n")
            for path in notebooks_cleared:
                f.write(f"- {path}\n")
            f.write("\n")

        if not notebooks_with_outputs:
            f.write("✓ All notebooks are clean (no outputs detected).\n")

        f.write("\n## Configuration\n\n")
        f.write(f"- **Clear outputs on apply**: {config.notebook_clear_outputs}\n")
        f.write(
            f"- **Whitelisted directories**: {', '.join(config.whitelist_globs[:3])}...\n"
        )

    return notebooks_with_outputs


def _clear_notebook_outputs(notebook: Dict) -> None:
    """Clear all outputs from notebook cells."""
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None


def main():
    """CLI entry point for notebook checker."""
    import sys

    root = Path.cwd()
    config = HygieneConfig()

    # Check if --apply flag is present
    clear_outputs = "--apply" in sys.argv or config.notebook_clear_outputs

    print("📓 Checking Jupyter notebooks...")
    notebooks = check_notebooks(root, config, clear_outputs=clear_outputs)

    whitelisted_count = sum(1 for nb in notebooks if nb["whitelisted"])
    needs_cleanup = len(notebooks) - whitelisted_count

    print(f"   Found {len(notebooks)} notebooks with outputs")
    print(f"   - {whitelisted_count} whitelisted (OK)")
    print(f"   - {needs_cleanup} need cleanup")

    if clear_outputs and needs_cleanup > 0:
        print(f"   ✓ Cleared outputs from {needs_cleanup} notebooks")

    print()
    print("✓ Notebook check complete")
    print("  - reports/notebook_sanitizer.md")


if __name__ == "__main__":
    main()
