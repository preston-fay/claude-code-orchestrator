"""Cleanliness score computation."""

from typing import Dict
from .config import HygieneConfig


def compute_cleanliness_score(
    stats: Dict,
    config: HygieneConfig,
) -> Dict:
    """
    Compute repository cleanliness score (0-100).

    Score is weighted combination of:
    - no_orphans: 30% (perfect if 0 orphans)
    - no_large_files: 25% (perfect if 0 non-whitelisted large files)
    - no_dead_code: 20% (perfect if 0 dead functions/classes)
    - no_notebook_outputs: 15% (perfect if all notebooks clean)
    - no_secrets: 10% (perfect if 0 secrets found)

    Returns dict with score, grade, and breakdown.
    """
    weights = config.score_weights

    # Calculate component scores (0-1)
    orphan_score = _score_orphans(stats.get("orphans", {}).get("count", 0))
    large_file_score = _score_large_files(stats.get("large_files", {}).get("count", 0))
    dead_code_score = _score_dead_code(stats.get("dead_code", {}))
    notebook_score = _score_notebooks(stats.get("notebooks", {}).get("needs_cleanup", 0))
    secrets_score = _score_secrets(stats.get("secrets", {}).get("findings", 0))

    # Weighted total
    total_score = (
        orphan_score * weights["no_orphans"] +
        large_file_score * weights["no_large_files"] +
        dead_code_score * weights["no_dead_code"] +
        notebook_score * weights["no_notebook_outputs"] +
        secrets_score * weights["no_secrets"]
    )

    # Grade assignment
    if total_score >= 95:
        grade = "A+"
    elif total_score >= 90:
        grade = "A"
    elif total_score >= 85:
        grade = "B+"
    elif total_score >= 80:
        grade = "B"
    elif total_score >= 75:
        grade = "C+"
    elif total_score >= 70:
        grade = "C"
    elif total_score >= 60:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": round(total_score, 1),
        "grade": grade,
        "breakdown": {
            "orphans": round(orphan_score * 100, 1),
            "large_files": round(large_file_score * 100, 1),
            "dead_code": round(dead_code_score * 100, 1),
            "notebooks": round(notebook_score * 100, 1),
            "secrets": round(secrets_score * 100, 1),
        },
        "weights": weights,
    }


def _score_orphans(count: int) -> float:
    """Score orphan files (0 is perfect)."""
    if count == 0:
        return 1.0
    elif count <= 5:
        return 0.8
    elif count <= 10:
        return 0.6
    elif count <= 20:
        return 0.4
    elif count <= 50:
        return 0.2
    else:
        return 0.0


def _score_large_files(count: int) -> float:
    """Score non-whitelisted large files (0 is perfect)."""
    if count == 0:
        return 1.0
    elif count <= 3:
        return 0.7
    elif count <= 5:
        return 0.5
    elif count <= 10:
        return 0.3
    else:
        return 0.0


def _score_dead_code(dead_code_stats: Dict) -> float:
    """Score dead code findings."""
    functions = dead_code_stats.get("functions", 0)
    classes = dead_code_stats.get("classes", 0)
    imports = dead_code_stats.get("imports", 0)

    # Weight functions/classes more than imports
    total = functions * 3 + classes * 3 + imports

    if total == 0:
        return 1.0
    elif total <= 10:
        return 0.8
    elif total <= 20:
        return 0.6
    elif total <= 50:
        return 0.4
    else:
        return 0.2


def _score_notebooks(needs_cleanup: int) -> float:
    """Score notebook hygiene."""
    if needs_cleanup == 0:
        return 1.0
    elif needs_cleanup <= 2:
        return 0.7
    elif needs_cleanup <= 5:
        return 0.5
    elif needs_cleanup <= 10:
        return 0.3
    else:
        return 0.0


def _score_secrets(findings: int) -> float:
    """Score secrets scanning (any finding is critical)."""
    if findings == 0:
        return 1.0
    else:
        return 0.0  # Any secret finding is a critical failure
