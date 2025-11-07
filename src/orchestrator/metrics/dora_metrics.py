"""
DORA Metrics Calculator

Calculates DevOps Research & Assessment (DORA) metrics from git history:
- Deployment Frequency: How often deployments reach production
- Lead Time for Changes: Time from commit to production
- Mean Time to Recovery (MTTR): Time to restore service after incident
- Change Failure Rate: % of deployments requiring hotfix

Based on DORA research: https://dora.dev/research/
"""

import json
import re
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class Deployment:
    """Single deployment event"""

    version: str
    timestamp: datetime
    commit_sha: str
    branch: str

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "commit_sha": self.commit_sha,
            "branch": self.branch,
        }


@dataclass
class DeploymentFrequencyMetrics:
    """Deployment frequency metrics"""

    metric: str = "deployment_frequency"
    period: str = ""
    collection_timestamp: str = ""
    deployments: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


@dataclass
class LeadTimeMetrics:
    """Lead time for changes metrics"""

    metric: str = "lead_time_for_changes"
    period: str = ""
    collection_timestamp: str = ""
    measurements: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


@dataclass
class MTTRMetrics:
    """Mean time to recovery metrics"""

    metric: str = "mean_time_to_recovery"
    period: str = ""
    collection_timestamp: str = ""
    incidents: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)


@dataclass
class ChangeFailureRateMetrics:
    """Change failure rate metrics"""

    metric: str = "change_failure_rate"
    period: str = ""
    collection_timestamp: str = ""
    summary: Dict = field(default_factory=dict)


class DORAMetricsCalculator:
    """Calculate DORA metrics from git history"""

    # DORA rating thresholds
    DORA_THRESHOLDS = {
        "deployment_frequency": {
            "elite": 1.0,  # >= 1 deploy per day
            "high": 0.14,  # >= 1 deploy per week
            "medium": 0.03,  # >= 1 deploy per month
            # low: < 1 per month
        },
        "lead_time": {
            "elite": 1,  # < 1 hour
            "high": 24,  # < 1 day
            "medium": 168,  # < 1 week
            # low: >= 1 week
        },
        "mttr": {
            "elite": 1,  # < 1 hour
            "high": 24,  # < 1 day
            "medium": 168,  # < 1 week
            # low: >= 1 week
        },
        "change_failure_rate": {
            "elite": 5,  # < 5%
            "high": 10,  # < 10%
            "medium": 15,  # < 15%
            # low: >= 15%
        },
    }

    def __init__(self, project_root: Path, days_back: int = 90):
        """
        Initialize DORA metrics calculator.

        Args:
            project_root: Root directory of git repository
            days_back: Number of days of history to analyze (default: 90)
        """
        self.project_root = Path(project_root)
        self.days_back = days_back
        self.output_dir = self.project_root / ".claude" / "metrics" / "dora"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate git repository
        if not (self.project_root / ".git").exists():
            raise ValueError(f"Not a git repository: {self.project_root}")

    def _run_git_command(self, args: List[str]) -> str:
        """
        Run git command and return output.

        Args:
            args: Git command arguments

        Returns:
            Command output as string
        """
        try:
            result = subprocess.run(
                ["git"] + args, cwd=self.project_root, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            return ""

    def _parse_semver(self, tag: str) -> Optional[Tuple[int, int, int]]:
        """
        Parse semantic version tag.

        Args:
            tag: Version tag string (e.g., 'v1.2.3')

        Returns:
            Tuple of (major, minor, patch) or None if invalid
        """
        match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", tag)
        if match:
            return tuple(map(int, match.groups()))
        return None

    def _is_hotfix(self, tag: str, prev_tag: str, time_diff: timedelta) -> bool:
        """
        Detect if a release is a hotfix.

        Criteria:
        - Patch version bump (v1.2.0 -> v1.2.1) within 48 hours
        - Tag name contains 'hotfix' or 'patch'

        Args:
            tag: Current tag
            prev_tag: Previous tag
            time_diff: Time difference between releases

        Returns:
            True if hotfix, False otherwise
        """
        # Check time window
        if time_diff > timedelta(hours=48):
            return False

        # Check tag name
        if "hotfix" in tag.lower() or "patch" in tag.lower():
            return True

        # Check if patch version bump
        curr_ver = self._parse_semver(tag)
        prev_ver = self._parse_semver(prev_tag)

        if curr_ver and prev_ver:
            # Patch bump: major.minor same, patch incremented
            if (
                curr_ver[0] == prev_ver[0]
                and curr_ver[1] == prev_ver[1]
                and curr_ver[2] == prev_ver[2] + 1
            ):
                return True

        return False

    def _calculate_dora_rating(self, metric_name: str, value: float) -> str:
        """
        Calculate DORA performance rating.

        Args:
            metric_name: Name of metric (deployment_frequency, lead_time, mttr, change_failure_rate)
            value: Metric value

        Returns:
            Rating: 'elite', 'high', 'medium', or 'low'
        """
        thresholds = self.DORA_THRESHOLDS.get(metric_name, {})

        if metric_name == "change_failure_rate":
            # Lower is better for CFR
            if value < thresholds["elite"]:
                return "elite"
            elif value < thresholds["high"]:
                return "high"
            elif value < thresholds["medium"]:
                return "medium"
            else:
                return "low"
        else:
            # For deployment_frequency: higher is better
            # For lead_time/mttr: lower is better (inverted)
            if metric_name == "deployment_frequency":
                if value >= thresholds["elite"]:
                    return "elite"
                elif value >= thresholds["high"]:
                    return "high"
                elif value >= thresholds["medium"]:
                    return "medium"
                else:
                    return "low"
            else:  # lead_time, mttr
                if value < thresholds["elite"]:
                    return "elite"
                elif value < thresholds["high"]:
                    return "high"
                elif value < thresholds["medium"]:
                    return "medium"
                else:
                    return "low"

    def collect_deployment_frequency(self) -> DeploymentFrequencyMetrics:
        """
        Collect deployment frequency metrics from git tags.

        Returns:
            DeploymentFrequencyMetrics object
        """
        logger.info(f"Collecting deployment frequency (last {self.days_back} days)")

        # Get all tags with timestamps (semver pattern only)
        since_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        git_output = self._run_git_command(
            [
                "log",
                "--tags",
                "--simplify-by-decoration",
                "--pretty=format:%ai|%H|%D",
                f"--since={since_date}",
            ]
        )

        deployments = []
        for line in git_output.split("\n"):
            if not line or "tag:" not in line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                continue

            timestamp_str, commit_sha, refs = parts

            # Extract tag name
            tag_match = re.search(r"tag:\s*(v?\d+\.\d+\.\d+[^\s,]*)", refs)
            if not tag_match:
                continue

            tag_name = tag_match.group(1)

            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str.strip()[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            # Determine branch (look for branch in refs)
            branch = "main"
            if "origin/main" in refs or "main" in refs:
                branch = "main"
            elif "origin/master" in refs or "master" in refs:
                branch = "master"

            deployment = Deployment(
                version=tag_name, timestamp=timestamp, commit_sha=commit_sha.strip(), branch=branch
            )
            deployments.append(deployment)

        # Calculate summary statistics
        total_deployments = len(deployments)

        if total_deployments > 0:
            # Calculate deploys per day/week
            days_span = min(self.days_back, (datetime.now() - deployments[-1].timestamp).days or 1)
            deploys_per_day = total_deployments / max(days_span, 1)
            deploys_per_week = deploys_per_day * 7

            rating = self._calculate_dora_rating("deployment_frequency", deploys_per_day)
        else:
            deploys_per_day = 0
            deploys_per_week = 0
            rating = "low"

        # Build period string
        start_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        period = f"{start_date}/{end_date}"

        metrics = DeploymentFrequencyMetrics(
            period=period,
            collection_timestamp=datetime.now().isoformat(),
            deployments=[d.to_dict() for d in deployments],
            summary={
                "total_deployments": total_deployments,
                "deploys_per_day": round(deploys_per_day, 2),
                "deploys_per_week": round(deploys_per_week, 2),
                "rating": rating,
            },
        )

        # Save to JSON
        output_file = self.output_dir / "deployments.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(
            f"✅ Deployment frequency: {total_deployments} deploys, {deploys_per_week:.1f}/week ({rating})"
        )
        return metrics

    def calculate_lead_time(self) -> LeadTimeMetrics:
        """
        Calculate lead time for changes (commit to deployment).

        Returns:
            LeadTimeMetrics object
        """
        logger.info(f"Calculating lead time for changes (last {self.days_back} days)")

        # Get deployments (tags)
        since_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        tags_output = self._run_git_command(
            [
                "log",
                "--tags",
                "--simplify-by-decoration",
                "--pretty=format:%ai|%H|%D",
                f"--since={since_date}",
            ]
        )

        tags = []
        for line in tags_output.split("\n"):
            if not line or "tag:" not in line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                continue

            timestamp_str, commit_sha, refs = parts
            tag_match = re.search(r"tag:\s*(v?\d+\.\d+\.\d+[^\s,]*)", refs)
            if not tag_match:
                continue

            try:
                timestamp = datetime.strptime(timestamp_str.strip()[:19], "%Y-%m-%d %H:%M:%S")
                tags.append((tag_match.group(1), timestamp, commit_sha.strip()))
            except ValueError:
                continue

        if len(tags) < 2:
            logger.warning("Need at least 2 deployments to calculate lead time")
            return LeadTimeMetrics(
                period=f"{since_date}/{datetime.now().strftime('%Y-%m-%d')}",
                collection_timestamp=datetime.now().isoformat(),
                summary={"median_lead_time_hours": 0, "p95_lead_time_hours": 0, "rating": "low"},
            )

        # For each deployment, get commits since previous deployment
        measurements = []
        for i in range(len(tags) - 1):
            curr_tag, curr_time, _ = tags[i]
            prev_tag, _, _ = tags[i + 1]

            # Get commits between tags
            commits_output = self._run_git_command(
                ["log", f"{prev_tag}..{curr_tag}", "--pretty=format:%H|%ai", "--first-parent"]
            )

            for commit_line in commits_output.split("\n"):
                if not commit_line:
                    continue

                commit_sha, commit_time_str = commit_line.split("|")
                try:
                    commit_time = datetime.strptime(
                        commit_time_str.strip()[:19], "%Y-%m-%d %H:%M:%S"
                    )
                    lead_time_hours = (curr_time - commit_time).total_seconds() / 3600

                    measurements.append(
                        {
                            "commit_sha": commit_sha,
                            "commit_time": commit_time.isoformat(),
                            "deployment_version": curr_tag,
                            "deployment_time": curr_time.isoformat(),
                            "lead_time_hours": round(lead_time_hours, 2),
                        }
                    )
                except ValueError:
                    continue

        # Calculate summary statistics
        if measurements:
            lead_times = sorted([m["lead_time_hours"] for m in measurements])
            median_lead_time = lead_times[len(lead_times) // 2]
            p95_index = int(len(lead_times) * 0.95)
            p95_lead_time = lead_times[p95_index] if p95_index < len(lead_times) else lead_times[-1]

            rating = self._calculate_dora_rating("lead_time", median_lead_time)
        else:
            median_lead_time = 0
            p95_lead_time = 0
            rating = "low"

        metrics = LeadTimeMetrics(
            period=f"{since_date}/{datetime.now().strftime('%Y-%m-%d')}",
            collection_timestamp=datetime.now().isoformat(),
            measurements=measurements,
            summary={
                "median_lead_time_hours": round(median_lead_time, 2),
                "p95_lead_time_hours": round(p95_lead_time, 2),
                "rating": rating,
            },
        )

        # Save to JSON
        output_file = self.output_dir / "lead_time.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(f"✅ Lead time: {median_lead_time:.1f}h median ({rating})")
        return metrics

    def calculate_mttr(self) -> MTTRMetrics:
        """
        Calculate Mean Time to Recovery from hotfixes.

        Returns:
            MTTRMetrics object
        """
        logger.info(f"Calculating MTTR (last {self.days_back} days)")

        # Get all tags with timestamps
        since_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        tags_output = self._run_git_command(
            [
                "log",
                "--tags",
                "--simplify-by-decoration",
                "--pretty=format:%ai|%H|%D",
                f"--since={since_date}",
            ]
        )

        tags = []
        for line in tags_output.split("\n"):
            if not line or "tag:" not in line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                continue

            timestamp_str, commit_sha, refs = parts
            tag_match = re.search(r"tag:\s*(v?\d+\.\d+\.\d+[^\s,]*)", refs)
            if not tag_match:
                continue

            try:
                timestamp = datetime.strptime(timestamp_str.strip()[:19], "%Y-%m-%d %H:%M:%S")
                tags.append((tag_match.group(1), timestamp, commit_sha.strip()))
            except ValueError:
                continue

        # Detect hotfixes
        incidents = []
        for i in range(len(tags) - 1):
            curr_tag, curr_time, curr_sha = tags[i]
            prev_tag, prev_time, _ = tags[i + 1]

            time_diff = curr_time - prev_time

            if self._is_hotfix(curr_tag, prev_tag, time_diff):
                # This is a hotfix - calculate MTTR
                mttr_hours = time_diff.total_seconds() / 3600

                # Get hotfix commits
                commits_output = self._run_git_command(
                    ["log", f"{prev_tag}..{curr_tag}", "--pretty=format:%H", "--first-parent"]
                )
                hotfix_commits = [c for c in commits_output.split("\n") if c]

                incidents.append(
                    {
                        "incident_id": curr_tag,
                        "original_release": prev_tag,
                        "detection_time": prev_time.isoformat(),
                        "resolution_time": curr_time.isoformat(),
                        "mttr_hours": round(mttr_hours, 2),
                        "hotfix_commits": hotfix_commits,
                    }
                )

        # Calculate summary statistics
        if incidents:
            mttr_values = [inc["mttr_hours"] for inc in incidents]
            median_mttr = sorted(mttr_values)[len(mttr_values) // 2]
            rating = self._calculate_dora_rating("mttr", median_mttr)
        else:
            median_mttr = 0
            rating = "elite"  # No incidents is good!

        metrics = MTTRMetrics(
            period=f"{since_date}/{datetime.now().strftime('%Y-%m-%d')}",
            collection_timestamp=datetime.now().isoformat(),
            incidents=incidents,
            summary={
                "median_mttr_hours": round(median_mttr, 2),
                "total_incidents": len(incidents),
                "rating": rating,
            },
        )

        # Save to JSON
        output_file = self.output_dir / "mttr.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(f"✅ MTTR: {median_mttr:.1f}h median, {len(incidents)} incidents ({rating})")
        return metrics

    def calculate_change_failure_rate(self) -> ChangeFailureRateMetrics:
        """
        Calculate change failure rate (% of deployments requiring hotfix).

        Returns:
            ChangeFailureRateMetrics object
        """
        logger.info(f"Calculating change failure rate (last {self.days_back} days)")

        # Get all tags
        since_date = (datetime.now() - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        tags_output = self._run_git_command(
            [
                "log",
                "--tags",
                "--simplify-by-decoration",
                "--pretty=format:%ai|%H|%D",
                f"--since={since_date}",
            ]
        )

        tags = []
        for line in tags_output.split("\n"):
            if not line or "tag:" not in line:
                continue

            parts = line.split("|")
            if len(parts) < 3:
                continue

            timestamp_str, commit_sha, refs = parts
            tag_match = re.search(r"tag:\s*(v?\d+\.\d+\.\d+[^\s,]*)", refs)
            if not tag_match:
                continue

            try:
                timestamp = datetime.strptime(timestamp_str.strip()[:19], "%Y-%m-%d %H:%M:%S")
                tags.append((tag_match.group(1), timestamp, commit_sha.strip()))
            except ValueError:
                continue

        total_deployments = len(tags)
        failed_deployments = 0

        # Count hotfixes
        for i in range(len(tags) - 1):
            curr_tag, curr_time, _ = tags[i]
            prev_tag, prev_time, _ = tags[i + 1]

            time_diff = curr_time - prev_time

            if self._is_hotfix(curr_tag, prev_tag, time_diff):
                failed_deployments += 1

        # Calculate CFR
        if total_deployments > 0:
            cfr = (failed_deployments / total_deployments) * 100
            rating = self._calculate_dora_rating("change_failure_rate", cfr)
        else:
            cfr = 0
            rating = "low"

        metrics = ChangeFailureRateMetrics(
            period=f"{since_date}/{datetime.now().strftime('%Y-%m-%d')}",
            collection_timestamp=datetime.now().isoformat(),
            summary={
                "total_deployments": total_deployments,
                "failed_deployments": failed_deployments,
                "change_failure_rate": round(cfr, 2),
                "rating": rating,
            },
        )

        # Save to JSON
        output_file = self.output_dir / "change_failure_rate.json"
        with open(output_file, "w") as f:
            json.dump(asdict(metrics), f, indent=2)

        logger.info(f"✅ Change failure rate: {cfr:.1f}% ({rating})")
        return metrics

    def collect_all(self) -> Dict:
        """
        Collect all DORA metrics.

        Returns:
            Dictionary with all metrics
        """
        logger.info("=" * 60)
        logger.info("Collecting DORA Metrics")
        logger.info("=" * 60)

        deployment_freq = self.collect_deployment_frequency()
        lead_time = self.calculate_lead_time()
        mttr = self.calculate_mttr()
        cfr = self.calculate_change_failure_rate()

        logger.info("=" * 60)
        logger.info("DORA Metrics Collection Complete")
        logger.info("=" * 60)

        return {
            "deployment_frequency": asdict(deployment_freq),
            "lead_time": asdict(lead_time),
            "mttr": asdict(mttr),
            "change_failure_rate": asdict(cfr),
        }


def main():
    """CLI entry point for DORA metrics collection"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect DORA metrics from git repository")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of git repository (default: current directory)",
    )
    parser.add_argument(
        "--days", type=int, default=90, help="Number of days of history to analyze (default: 90)"
    )
    parser.add_argument(
        "--output", type=Path, help="Output directory (default: .claude/metrics/dora/)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run collection
    calculator = DORAMetricsCalculator(args.project_root, args.days)
    if args.output:
        calculator.output_dir = args.output
        calculator.output_dir.mkdir(parents=True, exist_ok=True)

    calculator.collect_all()


if __name__ == "__main__":
    main()
