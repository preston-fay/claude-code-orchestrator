"""
Metrics Aggregator

Aggregates metrics from all collectors into summary views:
- Weekly and monthly rollups
- Trend analysis (week-over-week, month-over-month)
- Anomaly detection (statistical outliers)
- Cross-metric correlations

Inputs:
- .claude/metrics/dora/*.json
- .claude/metrics/github/*.json
- .claude/metrics/contributions/*.json
- .claude/metrics/ai_review/*.json

Outputs:
- .claude/metrics/aggregated/weekly_summary.json
- .claude/metrics/aggregated/monthly_summary.json
- .claude/metrics/aggregated/trends.json
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from collections import defaultdict
import logging
import statistics

logger = logging.getLogger(__name__)


@dataclass
class WeeklySummary:
    """Weekly metrics summary"""

    week_id: str
    week_start: str
    week_end: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    trends: Dict[str, float] = field(default_factory=dict)


@dataclass
class MonthlySummary:
    """Monthly metrics summary"""

    month_id: str
    month_start: str
    month_end: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    trends: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric"""

    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # up, down, stable
    is_anomaly: bool = False


class MetricsAggregator:
    """Aggregate and analyze metrics from all collectors"""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize metrics aggregator.

        Args:
            project_root: Root directory for metrics (default: current directory)
        """
        if project_root:
            self.metrics_dir = Path(project_root) / ".claude" / "metrics"
        else:
            self.metrics_dir = Path.cwd() / ".claude" / "metrics"

        self.output_dir = self.metrics_dir / "aggregated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized metrics aggregator with base: {self.metrics_dir}")

    def _load_json(self, filepath: Path) -> Optional[Dict]:
        """
        Load JSON file safely.

        Args:
            filepath: Path to JSON file

        Returns:
            Parsed JSON dict or None if error
        """
        try:
            if not filepath.exists():
                logger.debug(f"File not found: {filepath}")
                return None

            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {filepath}: {e}")
            return None

    def _calculate_trend(
        self, current: float, previous: float, threshold: float = 10.0
    ) -> TrendAnalysis:
        """
        Calculate trend between two values.

        Args:
            current: Current value
            previous: Previous value
            threshold: Percentage threshold for anomaly detection

        Returns:
            TrendAnalysis object
        """
        if previous == 0:
            change_pct = 100.0 if current > 0 else 0.0
        else:
            change_pct = ((current - previous) / previous) * 100

        # Determine trend direction
        if abs(change_pct) < 5:
            direction = "stable"
        elif change_pct > 0:
            direction = "up"
        else:
            direction = "down"

        # Detect anomaly
        is_anomaly = abs(change_pct) > threshold

        return TrendAnalysis(
            metric_name="",
            current_value=current,
            previous_value=previous,
            change_percentage=round(change_pct, 2),
            trend_direction=direction,
            is_anomaly=is_anomaly,
        )

    def _detect_statistical_anomaly(
        self, values: List[float], current: float, std_threshold: float = 2.0
    ) -> bool:
        """
        Detect statistical anomaly using standard deviation.

        Args:
            values: Historical values
            current: Current value
            std_threshold: Number of standard deviations for anomaly

        Returns:
            True if current value is an anomaly
        """
        if len(values) < 3:
            return False

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)

            if stdev == 0:
                return False

            z_score = abs((current - mean) / stdev)
            return z_score > std_threshold

        except Exception as e:
            logger.warning(f"Could not calculate statistical anomaly: {e}")
            return False

    def aggregate_weekly(self, weeks_back: int = 12) -> List[WeeklySummary]:
        """
        Aggregate metrics by week.

        Args:
            weeks_back: Number of weeks to aggregate

        Returns:
            List of WeeklySummary objects
        """
        logger.info(f"Aggregating weekly metrics (last {weeks_back} weeks)")

        weekly_summaries = []

        # Generate week ranges
        end_date = datetime.now()
        for i in range(weeks_back):
            week_end = end_date - timedelta(days=i * 7)
            week_start = week_end - timedelta(days=6)
            week_id = week_start.strftime("%Y-W%U")

            # Load metrics for this week
            metrics = {
                "dora": self._aggregate_dora_for_week(week_start, week_end),
                "github": self._aggregate_github_for_week(week_start, week_end),
                "contributions": self._aggregate_contributions_for_week(week_start, week_end),
                "ai_review": self._aggregate_ai_review_for_week(week_start, week_end),
            }

            # Calculate trends (week-over-week)
            trends = {}
            if i > 0 and weekly_summaries:
                prev_summary = weekly_summaries[-1]
                trends = self._calculate_weekly_trends(metrics, prev_summary.metrics)

            summary = WeeklySummary(
                week_id=week_id,
                week_start=week_start.strftime("%Y-%m-%d"),
                week_end=week_end.strftime("%Y-%m-%d"),
                metrics=metrics,
                trends=trends,
            )

            weekly_summaries.append(summary)

        # Save to JSON
        output_file = self.output_dir / "weekly_summary.json"
        with open(output_file, "w") as f:
            json.dump([asdict(s) for s in weekly_summaries], f, indent=2)

        logger.info(f"Aggregated {len(weekly_summaries)} weeks")
        return weekly_summaries

    def aggregate_monthly(self, months_back: int = 6) -> List[MonthlySummary]:
        """
        Aggregate metrics by month.

        Args:
            months_back: Number of months to aggregate

        Returns:
            List of MonthlySummary objects
        """
        logger.info(f"Aggregating monthly metrics (last {months_back} months)")

        monthly_summaries = []

        # Generate month ranges
        end_date = datetime.now()
        for i in range(months_back):
            # Calculate month boundaries
            month_end = datetime(end_date.year, end_date.month, 1) - timedelta(days=i * 30)
            month_start = datetime(month_end.year, month_end.month, 1)
            month_id = month_start.strftime("%Y-%m")

            # Load metrics for this month
            metrics = {
                "dora": self._aggregate_dora_for_month(month_start, month_end),
                "github": self._aggregate_github_for_month(month_start, month_end),
                "contributions": self._aggregate_contributions_for_month(month_start, month_end),
                "ai_review": self._aggregate_ai_review_for_month(month_start, month_end),
            }

            # Calculate trends (month-over-month)
            trends = {}
            if i > 0 and monthly_summaries:
                prev_summary = monthly_summaries[-1]
                trends = self._calculate_monthly_trends(metrics, prev_summary.metrics)

            summary = MonthlySummary(
                month_id=month_id,
                month_start=month_start.strftime("%Y-%m-%d"),
                month_end=month_end.strftime("%Y-%m-%d"),
                metrics=metrics,
                trends=trends,
            )

            monthly_summaries.append(summary)

        # Save to JSON
        output_file = self.output_dir / "monthly_summary.json"
        with open(output_file, "w") as f:
            json.dump([asdict(s) for s in monthly_summaries], f, indent=2)

        logger.info(f"Aggregated {len(monthly_summaries)} months")
        return monthly_summaries

    def _aggregate_dora_for_week(self, week_start: datetime, week_end: datetime) -> Dict:
        """Aggregate DORA metrics for a week"""
        # Load DORA metrics files
        deployments = self._load_json(self.metrics_dir / "dora" / "deployments.json")
        lead_time = self._load_json(self.metrics_dir / "dora" / "lead_time.json")
        mttr = self._load_json(self.metrics_dir / "dora" / "mttr.json")
        cfr = self._load_json(self.metrics_dir / "dora" / "change_failure_rate.json")

        summary = {}

        if deployments:
            summary["deployment_frequency"] = deployments.get("summary", {}).get(
                "deploys_per_week", 0
            )

        if lead_time:
            summary["lead_time_hours"] = lead_time.get("summary", {}).get(
                "median_lead_time_hours", 0
            )

        if mttr:
            summary["mttr_hours"] = mttr.get("summary", {}).get("median_resolution_time_hours", 0)

        if cfr:
            summary["change_failure_rate"] = cfr.get("summary", {}).get("failure_rate", 0)

        return summary

    def _aggregate_github_for_week(self, week_start: datetime, week_end: datetime) -> Dict:
        """Aggregate GitHub metrics for a week"""
        prs = self._load_json(self.metrics_dir / "github" / "pull_requests.json")
        conflicts = self._load_json(self.metrics_dir / "github" / "conflicts.json")
        velocity = self._load_json(self.metrics_dir / "github" / "velocity.json")

        summary = {}

        if prs:
            summary["pr_cycle_time_hours"] = prs.get("summary", {}).get(
                "median_cycle_time_hours", 0
            )
            summary["merge_rate"] = prs.get("summary", {}).get("merge_rate", 0)

        if conflicts:
            summary["conflict_rate"] = conflicts.get("summary", {}).get("conflict_rate", 0)

        if velocity:
            summary["features_per_week"] = velocity.get("summary", {}).get(
                "avg_features_per_week", 0
            )

        return summary

    def _aggregate_contributions_for_week(self, week_start: datetime, week_end: datetime) -> Dict:
        """Aggregate contribution metrics for a week"""
        contrib = self._load_json(self.metrics_dir / "contributions" / "attribution.json")

        summary = {}

        if contrib:
            summary["human_percentage"] = contrib.get("summary", {}).get("human_percentage", 0)
            summary["ai_percentage"] = contrib.get("summary", {}).get("ai_percentage", 0)
            summary["collaborative_percentage"] = contrib.get("summary", {}).get(
                "collaborative_percentage", 0
            )

        return summary

    def _aggregate_ai_review_for_week(self, week_start: datetime, week_end: datetime) -> Dict:
        """Aggregate AI review impact for a week"""
        impact = self._load_json(self.metrics_dir / "ai_review" / "impact.json")

        summary = {}

        if impact:
            summary["review_coverage"] = impact.get("summary", {}).get("review_coverage", 0)
            summary["avg_suggestions_per_pr"] = impact.get("summary", {}).get(
                "avg_suggestions_per_pr", 0
            )
            summary["avg_acceptance_rate"] = impact.get("summary", {}).get("avg_acceptance_rate", 0)

        return summary

    def _aggregate_dora_for_month(self, month_start: datetime, month_end: datetime) -> Dict:
        """Aggregate DORA metrics for a month"""
        return self._aggregate_dora_for_week(month_start, month_end)

    def _aggregate_github_for_month(self, month_start: datetime, month_end: datetime) -> Dict:
        """Aggregate GitHub metrics for a month"""
        return self._aggregate_github_for_week(month_start, month_end)

    def _aggregate_contributions_for_month(
        self, month_start: datetime, month_end: datetime
    ) -> Dict:
        """Aggregate contribution metrics for a month"""
        return self._aggregate_contributions_for_week(month_start, month_end)

    def _aggregate_ai_review_for_month(self, month_start: datetime, month_end: datetime) -> Dict:
        """Aggregate AI review impact for a month"""
        return self._aggregate_ai_review_for_week(month_start, month_end)

    def _calculate_weekly_trends(self, current: Dict, previous: Dict) -> Dict:
        """Calculate week-over-week trends"""
        trends = {}

        for category in current:
            for metric_name, value in current[category].items():
                if isinstance(value, (int, float)):
                    prev_value = previous.get(category, {}).get(metric_name, 0)
                    trend = self._calculate_trend(value, prev_value)
                    trends[f"{category}.{metric_name}"] = {
                        "change_percentage": trend.change_percentage,
                        "direction": trend.trend_direction,
                        "is_anomaly": trend.is_anomaly,
                    }

        return trends

    def _calculate_monthly_trends(self, current: Dict, previous: Dict) -> Dict:
        """Calculate month-over-month trends"""
        return self._calculate_weekly_trends(current, previous)

    def analyze_trends(self, weeks_back: int = 12) -> Dict:
        """
        Analyze trends across all metrics.

        Args:
            weeks_back: Number of weeks to analyze

        Returns:
            Trend analysis dictionary
        """
        logger.info(f"Analyzing trends (last {weeks_back} weeks)")

        # Load weekly summaries
        weekly_file = self.output_dir / "weekly_summary.json"
        if not weekly_file.exists():
            logger.warning("No weekly summaries found. Run aggregate_weekly() first.")
            return {}

        with open(weekly_file, "r") as f:
            weekly_data = json.load(f)

        # Collect metric values over time
        metric_history = defaultdict(list)

        for week in weekly_data[-weeks_back:]:
            for category, metrics in week["metrics"].items():
                for metric_name, value in metrics.items():
                    if isinstance(value, (int, float)):
                        metric_history[f"{category}.{metric_name}"].append(value)

        # Analyze each metric
        trends = {}

        for metric_path, values in metric_history.items():
            if len(values) < 2:
                continue

            current = values[-1]
            previous = values[-2]

            # Calculate trend
            trend = self._calculate_trend(current, previous)

            # Detect statistical anomaly
            is_stat_anomaly = self._detect_statistical_anomaly(values[:-1], current)

            trends[metric_path] = {
                "current_value": current,
                "previous_value": previous,
                "change_percentage": trend.change_percentage,
                "direction": trend.trend_direction,
                "is_anomaly": trend.is_anomaly or is_stat_anomaly,
                "historical_values": values,
            }

        # Save to JSON
        output_file = self.output_dir / "trends.json"
        with open(output_file, "w") as f:
            json.dump(trends, f, indent=2)

        logger.info(f"Analyzed {len(trends)} metric trends")
        return trends

    def aggregate_all(self, weeks_back: int = 12, months_back: int = 6) -> Dict:
        """
        Run all aggregation tasks.

        Args:
            weeks_back: Number of weeks to aggregate
            months_back: Number of months to aggregate

        Returns:
            Dictionary with all aggregation results
        """
        logger.info("=" * 60)
        logger.info("Starting metrics aggregation")
        logger.info("=" * 60)

        weekly = self.aggregate_weekly(weeks_back)
        monthly = self.aggregate_monthly(months_back)
        trends = self.analyze_trends(weeks_back)

        logger.info("=" * 60)
        logger.info("Metrics aggregation complete")
        logger.info("=" * 60)

        return {
            "weekly_summaries": len(weekly),
            "monthly_summaries": len(monthly),
            "trends_analyzed": len(trends),
        }


def main():
    """CLI entry point for metrics aggregation"""
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate and analyze metrics")
    parser.add_argument(
        "--weeks", type=int, default=12, help="Number of weeks to aggregate (default: 12)"
    )
    parser.add_argument(
        "--months", type=int, default=6, help="Number of months to aggregate (default: 6)"
    )
    parser.add_argument("--output", type=Path, help="Metrics directory (default: .claude/metrics/)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run aggregation
    try:
        aggregator = MetricsAggregator(
            project_root=args.output.parent.parent if args.output else None
        )

        aggregator.aggregate_all(weeks_back=args.weeks, months_back=args.months)

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise


if __name__ == "__main__":
    main()
