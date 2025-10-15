"""Aggregate hygiene reports and generate PR plan."""

import csv
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .config import HygieneConfig
from .score import compute_cleanliness_score


def aggregate_reports(
    root: Path,
    config: HygieneConfig,
    hygiene_output: Optional[Path] = None,
    pr_plan_output: Optional[Path] = None,
) -> Dict:
    """Aggregate all hygiene reports into summary and PR plan."""
    if hygiene_output is None:
        hygiene_output = root / "reports" / "repo_hygiene_report.md"
    if pr_plan_output is None:
        pr_plan_output = root / "reports" / "PR_PLAN.md"

    hygiene_output.parent.mkdir(parents=True, exist_ok=True)

    # Read reports
    large_files = _read_large_files_csv(root / "reports" / "large_files.csv")
    orphans = _read_orphans_csv(root / "reports" / "orphans.csv")
    dead_code_stats = _parse_dead_code_md(root / "reports" / "dead_code.md")
    notebook_stats = _parse_notebook_md(root / "reports" / "notebook_sanitizer.md")

    # Calculate statistics
    stats = {
        "orphans": {
            "count": len(orphans),
            "total_size_mb": sum(
                _estimate_file_size(root / o["path"]) for o in orphans
            ),
        },
        "large_files": {
            "count": len([f for f in large_files if not f.get("whitelisted", False)]),
            "total_size_mb": sum(
                f["size_mb"]
                for f in large_files
                if not f.get("whitelisted", False)
            ),
            "whitelisted_count": len(
                [f for f in large_files if f.get("whitelisted", False)]
            ),
        },
        "dead_code": dead_code_stats,
        "notebooks": notebook_stats,
        "secrets": {"findings": 0},  # Placeholder for secrets scan results
    }

    # Compute cleanliness score
    score_data = compute_cleanliness_score(stats, config)
    stats["cleanliness_score"] = score_data

    # Generate JSON summary
    _generate_json_summary(root / "reports" / "hygiene_summary.json", stats, config)

    # Generate hygiene report
    _generate_hygiene_report(hygiene_output, stats)

    # Generate PR plan with safety checks
    apply_safety = check_apply_safety(large_files, orphans, config)
    _generate_pr_plan(pr_plan_output, large_files, orphans, stats, apply_safety)

    return stats


def _read_large_files_csv(path: Path) -> List[Dict]:
    """Read large files CSV."""
    if not path.exists():
        return []

    large_files = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["size_mb"] = float(row["size_mb"])
            row["whitelisted"] = row["whitelisted"].lower() == "true"
            large_files.append(row)
    return large_files


def _read_orphans_csv(path: Path) -> List[Dict]:
    """Read orphans CSV."""
    if not path.exists():
        return []

    orphans = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["references_found"] = int(row["references_found"])
            orphans.append(row)
    return orphans


def _parse_dead_code_md(path: Path) -> Dict:
    """Parse dead code markdown report for statistics."""
    if not path.exists():
        return {"functions": 0, "classes": 0, "imports": 0}

    with open(path, "r") as f:
        content = f.read()

    stats = {"functions": 0, "classes": 0, "imports": 0}

    for line in content.split("\n"):
        if line.startswith("- **Unused functions**:"):
            stats["functions"] = int(line.split(":")[1].strip())
        elif line.startswith("- **Unused classes**:"):
            stats["classes"] = int(line.split(":")[1].strip())
        elif line.startswith("- **Unused imports**:"):
            stats["imports"] = int(line.split(":")[1].strip())

    return stats


def _parse_notebook_md(path: Path) -> Dict:
    """Parse notebook markdown report for statistics."""
    if not path.exists():
        return {"with_outputs": 0, "whitelisted": 0, "needs_cleanup": 0}

    with open(path, "r") as f:
        content = f.read()

    stats = {"with_outputs": 0, "whitelisted": 0, "needs_cleanup": 0}

    for line in content.split("\n"):
        if line.startswith("- **Notebooks with outputs**:"):
            stats["with_outputs"] = int(line.split(":")[1].strip())
        elif line.startswith("- **Whitelisted**:"):
            stats["whitelisted"] = int(line.split(":")[1].strip())
        elif line.startswith("- **Requiring cleanup**:"):
            stats["needs_cleanup"] = int(line.split(":")[1].strip())

    return stats


def _estimate_file_size(path: Path) -> float:
    """Estimate file size in MB."""
    try:
        return path.stat().st_size / (1024 * 1024)
    except FileNotFoundError:
        return 0.0


def _generate_json_summary(output: Path, stats: Dict, config: HygieneConfig) -> None:
    """Generate machine-readable JSON summary."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "cleanliness_score": stats["cleanliness_score"]["score"],
        "grade": stats["cleanliness_score"]["grade"],
        "stats": {
            "orphans": stats["orphans"]["count"],
            "large_files": stats["large_files"]["count"],
            "dead_code_functions": stats["dead_code"]["functions"],
            "dead_code_classes": stats["dead_code"]["classes"],
            "dead_code_imports": stats["dead_code"]["imports"],
            "notebooks_with_outputs": stats["notebooks"]["with_outputs"],
            "notebooks_needs_cleanup": stats["notebooks"]["needs_cleanup"],
            "secrets_findings": stats["secrets"]["findings"],
        },
        "thresholds": {
            "max_orphans_warn": config.max_orphans_warn,
            "max_orphans_block": config.max_orphans_block,
            "min_cleanliness_score": config.min_cleanliness_score,
        },
        "quality_gates": {
            "orphans_warn": stats["orphans"]["count"] >= config.max_orphans_warn,
            "orphans_block": stats["orphans"]["count"] >= config.max_orphans_block,
            "score_pass": stats["cleanliness_score"]["score"] >= config.min_cleanliness_score,
        },
    }

    with open(output, "w") as f:
        json.dump(summary, f, indent=2)


def check_apply_safety(
    large_files: List[Dict],
    orphans: List[Dict],
    config: HygieneConfig,
) -> Tuple[bool, List[str]]:
    """
    Check if apply operation is safe based on thresholds.

    Returns: (is_safe, blocked_reasons)
    """
    blocked_reasons = []

    # Count proposed deletions
    deletion_count = len(orphans) + len([f for f in large_files if not f.get("whitelisted", False)])

    if deletion_count > config.max_apply_deletions:
        blocked_reasons.append(
            f"Too many deletions: {deletion_count} > {config.max_apply_deletions} max"
        )

    # Estimate bytes to be removed
    bytes_to_remove = sum(_estimate_file_size(Path(o["path"])) for o in orphans) * 1024 * 1024
    bytes_to_remove += sum(f["size_mb"] * 1024 * 1024 for f in large_files if not f.get("whitelisted", False))

    if bytes_to_remove > config.max_apply_bytes_removed:
        mb_to_remove = bytes_to_remove / (1024 * 1024)
        max_mb = config.max_apply_bytes_removed / (1024 * 1024)
        blocked_reasons.append(
            f"Too much data to remove: {mb_to_remove:.1f}MB > {max_mb:.1f}MB max"
        )

    is_safe = len(blocked_reasons) == 0
    return is_safe, blocked_reasons


def _generate_hygiene_report(output: Path, stats: Dict) -> None:
    """Generate executive hygiene summary report."""
    with open(output, "w") as f:
        f.write("# Repository Hygiene Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Cleanliness score
        score_data = stats.get("cleanliness_score", {})
        if score_data:
            f.write("## Cleanliness Score\n\n")
            f.write(f"**Score:** {score_data['score']}/100 (Grade: {score_data['grade']})\n\n")
            f.write("**Breakdown:**\n")
            for component, score in score_data.get("breakdown", {}).items():
                f.write(f"- {component.replace('_', ' ').title()}: {score}/100\n")
            f.write("\n")

        # Summary section
        f.write("## Summary\n\n")
        f.write(
            f"- **Orphaned files**: {stats['orphans']['count']} "
            f"({stats['orphans']['total_size_mb']:.2f} MB)\n"
        )
        f.write(
            f"- **Large binaries**: {stats['large_files']['count']} files "
            f"({stats['large_files']['total_size_mb']:.2f} MB)\n"
        )
        f.write(
            f"  - Whitelisted: {stats['large_files']['whitelisted_count']} files (OK)\n"
        )
        f.write(
            f"- **Dead code**: {stats['dead_code']['functions']} functions, "
            f"{stats['dead_code']['classes']} classes, "
            f"{stats['dead_code']['imports']} imports\n"
        )
        f.write(
            f"- **Notebook outputs**: {stats['notebooks']['with_outputs']} notebooks\n"
        )
        f.write(f"  - Whitelisted: {stats['notebooks']['whitelisted']} (OK)\n")
        f.write(f"  - Need cleanup: {stats['notebooks']['needs_cleanup']}\n\n")

        # Severity breakdown
        critical = stats["orphans"]["count"] + stats["large_files"]["count"]
        warning = stats["dead_code"]["functions"] + stats["notebooks"]["needs_cleanup"]
        info = stats["dead_code"]["imports"]

        f.write("## Severity Breakdown\n\n")
        f.write(f"- **Critical**: {critical} (orphans + large files)\n")
        f.write(f"- **Warning**: {warning} (dead code + notebook outputs)\n")
        f.write(f"- **Info**: {info} (unused imports)\n\n")

        # Details
        f.write("## Detailed Reports\n\n")
        f.write("- [Large Files](large_files.csv)\n")
        f.write("- [Orphaned Files](orphans.csv)\n")
        f.write("- [Dead Code Analysis](dead_code.md)\n")
        f.write("- [Notebook Hygiene](notebook_sanitizer.md)\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if critical > 0:
            f.write(
                "1. **Review proposed cleanup actions** in [PR_PLAN.md](PR_PLAN.md)\n"
            )
            f.write("2. **Approve safe actions** by checking boxes\n")
            f.write(
                "3. **Reject risky actions** or provide feedback on specific items\n"
            )
        else:
            f.write("✓ Repository is in good shape. No critical issues found.\n")

        if stats["notebooks"]["needs_cleanup"] > 0:
            f.write(
                f"\n4. **Clear notebook outputs** for {stats['notebooks']['needs_cleanup']} notebooks\n"
            )

        if stats["dead_code"]["imports"] > 10:
            f.write("\n5. **Clean up unused imports** to improve code readability\n")


def _generate_pr_plan(
    output: Path,
    large_files: List[Dict],
    orphans: List[Dict],
    stats: Dict,
    apply_safety: Tuple[bool, List[str]],
) -> None:
    """Generate actionable PR cleanup plan."""
    is_safe, blocked_reasons = apply_safety

    with open(output, "w") as f:
        f.write("# Cleanup Plan for Approval\n\n")
        f.write(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        # Safety status
        if not is_safe:
            f.write("## ⚠️ APPLY BLOCKED - Safety Thresholds Exceeded\n\n")
            f.write("This cleanup cannot be applied automatically due to:\n\n")
            for reason in blocked_reasons:
                f.write(f"- {reason}\n")
            f.write("\n**Action Required:** Split cleanup into smaller batches or increase thresholds in `configs/hygiene.yaml`.\n\n")
            f.write("---\n\n")

        f.write(
            "Check the box next to each action you approve. "
            "Actions marked SAFE can be executed immediately. "
            "Actions marked NEEDS_REVIEW require careful consideration.\n\n"
        )

        action_num = 1

        # Safe actions: Orphaned files
        if orphans:
            f.write("## Safe Actions (Low Risk)\n\n")
            for orphan in orphans[:10]:  # Limit to first 10
                f.write(f"- [ ] **{action_num}.** Remove orphaned file: `{orphan['path']}`\n")
                f.write(f"      - **Command:** `git rm {orphan['path']}`\n")
                f.write(
                    f"      - **Reason:** No references found, last modified {orphan['last_modified']}\n"
                )
                f.write("      - **Risk:** SAFE\n\n")
                action_num += 1

            if len(orphans) > 10:
                f.write(
                    f"... and {len(orphans) - 10} more orphaned files "
                    f"(see [orphans.csv](orphans.csv))\n\n"
                )

        # Needs review: Large binaries
        if large_files:
            non_whitelisted = [
                f for f in large_files if not f.get("whitelisted", False)
            ]
            if non_whitelisted:
                f.write("## Needs Review (Medium Risk)\n\n")
                for lf in non_whitelisted[:5]:  # Limit to first 5
                    f.write(
                        f"- [ ] **{action_num}.** Delete large binary: `{lf['path']}` ({lf['size_mb']} MB)\n"
                    )
                    f.write(f"      - **Command:** `git rm {lf['path']}`\n")
                    f.write(
                        f"      - **Reason:** Exceeds {lf['size_mb']}MB threshold, not in whitelist\n"
                    )
                    f.write("      - **Risk:** NEEDS_REVIEW\n\n")
                    action_num += 1

                if len(non_whitelisted) > 5:
                    f.write(
                        f"... and {len(non_whitelisted) - 5} more large files "
                        f"(see [large_files.csv](large_files.csv))\n\n"
                    )

        # Info: Dead code cleanup
        if stats["dead_code"]["imports"] > 0 or stats["dead_code"]["functions"] > 0:
            f.write("## Informational (Manual Review)\n\n")
            f.write(
                "These items require manual code inspection. "
                "See [dead_code.md](dead_code.md) for details.\n\n"
            )
            f.write(
                f"- [ ] **{action_num}.** Remove {stats['dead_code']['imports']} unused imports\n"
            )
            f.write("      - **Risk:** MANUAL_REVIEW\n\n")
            action_num += 1

            if stats["dead_code"]["functions"] > 0:
                f.write(
                    f"- [ ] **{action_num}.** Remove {stats['dead_code']['functions']} unused functions\n"
                )
                f.write("      - **Risk:** MANUAL_REVIEW\n\n")
                action_num += 1

        if action_num == 1:
            f.write("## No Actions Required\n\n")
            f.write("✓ Repository hygiene is excellent. No cleanup needed.\n")


def main():
    """CLI entry point for report aggregation."""
    root = Path.cwd()
    config = HygieneConfig()

    print("📊 Aggregating hygiene reports...")
    stats = aggregate_reports(root, config)

    print()
    print("Summary:")
    print(f"  - {stats['orphans']['count']} orphaned files")
    print(f"  - {stats['large_files']['count']} large files")
    print(f"  - {stats['dead_code']['functions']} unused functions")
    print(f"  - {stats['notebooks']['needs_cleanup']} notebooks need cleanup")
    print()
    print("✓ Reports generated:")
    print("  - reports/repo_hygiene_report.md")
    print("  - reports/PR_PLAN.md")


if __name__ == "__main__":
    main()
