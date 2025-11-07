"""
GitHub Collaboration Metrics Collector

Collects collaboration metrics from GitHub API:
- PR Cycle Time: Time from PR open to merge
- Merge Conflicts: Frequency and resolution time
- Feature Velocity: Features/bugs completed per sprint

Requires GITHUB_TOKEN environment variable for API access.
"""

import os
import json
import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
import logging

try:
    from github import Github, GithubException
    from github.PullRequest import PullRequest

    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    logging.warning("PyGithub not installed. Run: pip install PyGithub")

logger = logging.getLogger(__name__)


@dataclass
class PRMetrics:
    """Metrics for a single pull request"""

    pr_number: int
    title: str
    opened_at: str
    merged_at: Optional[str]
    closed_at: Optional[str]
    cycle_time_hours: Optional[float]
    commits: int
    files_changed: int
    additions: int
    deletions: int
    author: str
    state: str  # open, closed, merged


@dataclass
class PRCycleTimeMetrics:
    """PR cycle time metrics"""

    metric: str = "pr_cycle_time"
    period: str = ""
    collection_timestamp: str = ""
    pull_requests: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


@dataclass
class ConflictMetrics:
    """Merge conflict metrics"""

    metric: str = "merge_conflicts"
    period: str = ""
    collection_timestamp: str = ""
    conflicts: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


@dataclass
class VelocityMetrics:
    """Feature velocity metrics"""

    metric: str = "feature_velocity"
    period: str = ""
    collection_timestamp: str = ""
    sprints: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


class GitHubMetricsCollector:
    """Collect GitHub collaboration metrics via API"""

    def __init__(
        self,
        repo_name: str,
        token: Optional[str] = None,
        days_back: int = 90,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize GitHub metrics collector.

        Args:
            repo_name: Repository name in format 'owner/repo'
            token: GitHub API token (default: GITHUB_TOKEN env var)
            days_back: Number of days of history to analyze (default: 90)
            project_root: Root directory for output (default: current directory)
        """
        if not GITHUB_AVAILABLE:
            raise ImportError("PyGithub required. Install with: pip install PyGithub")

        self.repo_name = repo_name
        self.days_back = days_back
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN environment variable or pass token parameter."
            )

        # Initialize GitHub client
        self.github = Github(self.token)
        self.repo = self.github.get_repo(repo_name)

        # Setup output directory
        if project_root:
            self.output_dir = Path(project_root) / ".claude" / "metrics" / "github"
        else:
            self.output_dir = Path.cwd() / ".claude" / "metrics" / "github"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized GitHub metrics collector for {repo_name}")

        # Log rate limit info (safely handle API version differences)
        try:
            rate_limit = self.github.get_rate_limit()
            if hasattr(rate_limit, "core"):
                logger.info(f"API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")
            else:
                logger.info(f"API rate limit: {rate_limit.rate.remaining}/{rate_limit.rate.limit}")
        except Exception as e:
            logger.debug(f"Could not fetch rate limit: {e}")

    def _get_pr_cycle_time(self, pr: PullRequest) -> Optional[float]:
        """
        Calculate PR cycle time in hours.

        Args:
            pr: GitHub PullRequest object

        Returns:
            Cycle time in hours, or None if PR not merged
        """
        if not pr.merged:
            return None

        if pr.merged_at and pr.created_at:
            cycle_time = (pr.merged_at - pr.created_at).total_seconds() / 3600
            return round(cycle_time, 2)

        return None

    def _detect_conflict(self, pr: PullRequest) -> Optional[Dict]:
        """
        Detect if PR had merge conflicts.

        Heuristic: Look for force pushes or synchronize events after review.

        Args:
            pr: GitHub PullRequest object

        Returns:
            Conflict metadata or None
        """
        try:
            # Check timeline events for conflict indicators
            events = list(pr.get_issue_events())

            # Look for head_ref_force_pushed events (conflict resolution indicator)
            force_pushes = [e for e in events if e.event == "head_ref_force_pushed"]

            if force_pushes:
                # Conflict detected - calculate resolution time
                first_force = force_pushes[0]
                detected_at = first_force.created_at

                # Find when PR was updated after conflict
                if pr.merged_at:
                    resolved_at = pr.merged_at
                elif pr.closed_at:
                    resolved_at = pr.closed_at
                else:
                    resolved_at = datetime.now()

                resolution_time_hours = (resolved_at - detected_at).total_seconds() / 3600

                return {
                    "pr_number": pr.number,
                    "detected_at": detected_at.isoformat(),
                    "resolved_at": resolved_at.isoformat(),
                    "resolution_time_hours": round(resolution_time_hours, 2),
                    "force_pushes": len(force_pushes),
                }

        except Exception as e:
            logger.warning(f"Error detecting conflicts for PR #{pr.number}: {e}")

        return None

    async def collect_pr_data(self) -> PRCycleTimeMetrics:
        """
        Collect PR cycle time and metadata.

        Returns:
            PRCycleTimeMetrics object
        """
        logger.info(f"Collecting PR data (last {self.days_back} days)")

        since_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)

        # Get closed PRs (merged and closed)
        prs = self.repo.get_pulls(state="closed", sort="updated", direction="desc")

        pr_metrics = []
        total_prs = 0
        merged_prs = 0

        for pr in prs:
            # Filter by date
            if pr.updated_at < since_date:
                break

            total_prs += 1

            # Calculate cycle time
            cycle_time = self._get_pr_cycle_time(pr)
            if cycle_time is not None:
                merged_prs += 1

            # Extract PR metadata
            pr_data = PRMetrics(
                pr_number=pr.number,
                title=pr.title,
                opened_at=pr.created_at.isoformat(),
                merged_at=pr.merged_at.isoformat() if pr.merged_at else None,
                closed_at=pr.closed_at.isoformat() if pr.closed_at else None,
                cycle_time_hours=cycle_time,
                commits=pr.commits,
                files_changed=pr.changed_files,
                additions=pr.additions,
                deletions=pr.deletions,
                author=pr.user.login if pr.user else "unknown",
                state="merged" if pr.merged else "closed",
            )

            pr_metrics.append(asdict(pr_data))

            # Rate limit check
            if total_prs % 10 == 0:
                try:
                    rate_limit = self.github.get_rate_limit()
                    remaining = (
                        rate_limit.core.remaining
                        if hasattr(rate_limit, "core")
                        else rate_limit.rate.remaining
                    )
                    if remaining < 100:
                        logger.warning(f"API rate limit low: {remaining} remaining")
                except Exception:
                    pass  # Continue if rate limit check fails

        # Calculate summary statistics
        cycle_times = [
            pm["cycle_time_hours"] for pm in pr_metrics if pm["cycle_time_hours"] is not None
        ]

        if cycle_times:
            median_cycle_time = sorted(cycle_times)[len(cycle_times) // 2]
            merge_rate = (merged_prs / total_prs) * 100 if total_prs > 0 else 0
        else:
            median_cycle_time = 0
            merge_rate = 0

        # Build period string
        start_date = since_date.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        period = f"{start_date}/{end_date}"

        metrics = PRCycleTimeMetrics(
            period=period,
            collection_timestamp=datetime.now().isoformat(),
            pull_requests=pr_metrics,
            summary={
                "total_prs": total_prs,
                "merged_prs": merged_prs,
                "median_cycle_time_hours": round(median_cycle_time, 2),
                "merge_rate": round(merge_rate, 2),
            },
        )

        # Save to JSON
        output_file = self.output_dir / "pull_requests.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(f"Collected {total_prs} PRs, median cycle time: {median_cycle_time:.1f}h")
        return metrics

    async def detect_conflicts(self) -> ConflictMetrics:
        """
        Detect and track merge conflicts.

        Returns:
            ConflictMetrics object
        """
        logger.info(f"Detecting merge conflicts (last {self.days_back} days)")

        since_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)

        # Get closed PRs to analyze
        prs = self.repo.get_pulls(state="closed", sort="updated", direction="desc")

        conflicts = []
        total_prs_analyzed = 0

        for pr in prs:
            if pr.updated_at < since_date:
                break

            total_prs_analyzed += 1

            # Detect conflict
            conflict = self._detect_conflict(pr)
            if conflict:
                conflicts.append(conflict)

            # Rate limit management
            if total_prs_analyzed % 10 == 0:
                try:
                    rate_limit = self.github.get_rate_limit()
                    remaining = (
                        rate_limit.core.remaining
                        if hasattr(rate_limit, "core")
                        else rate_limit.rate.remaining
                    )
                    if remaining < 100:
                        logger.warning(f"API rate limit low: {remaining} remaining")
                        break
                except Exception:
                    pass  # Continue if rate limit check fails

        # Calculate summary statistics
        if conflicts:
            resolution_times = [c["resolution_time_hours"] for c in conflicts]
            median_resolution = sorted(resolution_times)[len(resolution_times) // 2]
            conflict_rate = (
                (len(conflicts) / total_prs_analyzed) * 100 if total_prs_analyzed > 0 else 0
            )
        else:
            median_resolution = 0
            conflict_rate = 0

        # Build period string
        start_date = since_date.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        period = f"{start_date}/{end_date}"

        metrics = ConflictMetrics(
            period=period,
            collection_timestamp=datetime.now().isoformat(),
            conflicts=conflicts,
            summary={
                "total_conflicts": len(conflicts),
                "total_prs_analyzed": total_prs_analyzed,
                "median_resolution_time_hours": round(median_resolution, 2),
                "conflict_rate": round(conflict_rate, 2),
            },
        )

        # Save to JSON
        output_file = self.output_dir / "conflicts.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(f"Detected {len(conflicts)} conflicts ({conflict_rate:.1f}% rate)")
        return metrics

    def calculate_velocity(self) -> VelocityMetrics:
        """
        Calculate feature velocity from commit messages.

        Uses conventional commit types: feat:, fix:, chore:

        Returns:
            VelocityMetrics object
        """
        logger.info(f"Calculating feature velocity (last {self.days_back} days)")

        since_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)

        # Get commits
        commits = self.repo.get_commits(since=since_date)

        # Group by week
        weekly_velocity = {}

        for commit in commits:
            commit_date = commit.commit.author.date
            week_key = commit_date.strftime("%Y-W%U")  # ISO week format

            if week_key not in weekly_velocity:
                weekly_velocity[week_key] = {
                    "week_id": week_key,
                    "start_date": (commit_date - timedelta(days=commit_date.weekday())).strftime(
                        "%Y-%m-%d"
                    ),
                    "features": 0,
                    "bugs": 0,
                    "chores": 0,
                    "total_commits": 0,
                }

            # Parse commit message
            message = commit.commit.message.lower()

            if message.startswith("feat:") or message.startswith("feature:"):
                weekly_velocity[week_key]["features"] += 1
            elif message.startswith("fix:") or message.startswith("bugfix:"):
                weekly_velocity[week_key]["bugs"] += 1
            elif message.startswith("chore:"):
                weekly_velocity[week_key]["chores"] += 1

            weekly_velocity[week_key]["total_commits"] += 1

        # Convert to list and sort
        sprints = sorted(weekly_velocity.values(), key=lambda x: x["week_id"], reverse=True)

        # Calculate averages
        if sprints:
            avg_features = sum(s["features"] for s in sprints) / len(sprints)
            avg_bugs = sum(s["bugs"] for s in sprints) / len(sprints)
        else:
            avg_features = 0
            avg_bugs = 0

        # Build period string
        start_date = since_date.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        period = f"{start_date}/{end_date}"

        metrics = VelocityMetrics(
            period=period,
            collection_timestamp=datetime.now().isoformat(),
            sprints=sprints,
            summary={
                "total_weeks": len(sprints),
                "avg_features_per_week": round(avg_features, 2),
                "avg_bugs_per_week": round(avg_bugs, 2),
            },
        )

        # Save to JSON
        output_file = self.output_dir / "velocity.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(
            f"Calculated velocity: {avg_features:.1f} features/week, {avg_bugs:.1f} bugs/week"
        )
        return metrics

    async def collect_all(self) -> Dict:
        """
        Collect all GitHub metrics.

        Returns:
            Dictionary with all metrics
        """
        logger.info("=" * 60)
        logger.info("Collecting GitHub Collaboration Metrics")
        logger.info("=" * 60)

        pr_metrics = await self.collect_pr_data()
        conflict_metrics = await self.detect_conflicts()
        velocity_metrics = self.calculate_velocity()

        logger.info("=" * 60)
        logger.info("GitHub Metrics Collection Complete")
        logger.info("=" * 60)

        # Check API rate limit status
        try:
            rate_limit = self.github.get_rate_limit()
            if hasattr(rate_limit, "core"):
                logger.info(
                    f"API rate limit remaining: {rate_limit.core.remaining}/{rate_limit.core.limit}"
                )
            else:
                logger.info(
                    f"API rate limit remaining: {rate_limit.rate.remaining}/{rate_limit.rate.limit}"
                )
        except Exception as e:
            logger.debug(f"Could not fetch final rate limit: {e}")

        return {
            "pr_cycle_time": asdict(pr_metrics),
            "conflicts": asdict(conflict_metrics),
            "velocity": asdict(velocity_metrics),
        }


async def main():
    """CLI entry point for GitHub metrics collection"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect GitHub collaboration metrics")
    parser.add_argument(
        "--repo", type=str, required=True, help="Repository name in format owner/repo"
    )
    parser.add_argument(
        "--token", type=str, help="GitHub API token (default: GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--days", type=int, default=90, help="Number of days of history to analyze (default: 90)"
    )
    parser.add_argument(
        "--output", type=Path, help="Output directory (default: .claude/metrics/github/)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run collection
    try:
        collector = GitHubMetricsCollector(
            repo_name=args.repo,
            token=args.token,
            days_back=args.days,
            project_root=args.output.parent.parent.parent if args.output else None,
        )

        await collector.collect_all()

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
