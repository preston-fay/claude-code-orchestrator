#!/usr/bin/env python3
"""
Generate Weekly Metrics Report

Reads aggregated metrics and generates a markdown report with:
- Executive summary
- DORA metrics with trends
- AI contribution analysis
- AI review impact
- GitHub collaboration (if available)
- Anomalies and recommendations
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_weekly_summary() -> Optional[Dict]:
    """Load the most recent weekly summary"""
    summary_path = Path(".claude/metrics/aggregated/weekly_summary.json")

    if not summary_path.exists():
        print(f"Warning: Weekly summary not found at {summary_path}")
        return None

    try:
        with open(summary_path, "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error loading weekly summary: {e}")
        return None


def format_change(current: float, previous: float, invert: bool = False) -> str:
    """
    Format change percentage with + or - sign

    Args:
        current: Current value
        previous: Previous value
        invert: If True, negative change is good (e.g., for failure rate)

    Returns:
        Formatted string like "+15.2%" or "-5.0%"
    """
    if previous == 0:
        return "N/A"

    change = ((current - previous) / previous) * 100

    if abs(change) < 0.1:
        return "→ 0.0%"

    sign = "+" if change > 0 else ""
    return f"{sign}{change:.1f}%"


def get_change_icon(current: float, previous: float, invert: bool = False) -> str:
    """
    Get icon for change direction

    Args:
        current: Current value
        previous: Previous value
        invert: If True, down is good (e.g., for failure rate, MTTR)

    Returns:
        Arrow icon: ↑ ↓ or →
    """
    if previous == 0 or abs(current - previous) < 0.01:
        return "→"

    if current > previous:
        return "↑" if not invert else "↓"
    else:
        return "↓" if not invert else "↑"


def get_dora_rating(value: float, metric: str) -> str:
    """
    Get DORA rating based on value and metric type

    Returns: Elite, High, Medium, or Low
    """
    ratings = {
        "deployment_frequency": [
            (7, "Elite"),  # Multiple deploys per day
            (1, "High"),  # Once per week
            (0.25, "Medium"),  # Once per month
            (0, "Low"),  # Less than monthly
        ],
        "lead_time": [
            (24, "Elite"),  # Less than 1 day
            (168, "High"),  # Less than 1 week
            (720, "Medium"),  # Less than 1 month
            (float("inf"), "Low"),
        ],
        "mttr": [
            (1, "Elite"),  # Less than 1 hour
            (24, "High"),  # Less than 1 day
            (168, "Medium"),  # Less than 1 week
            (float("inf"), "Low"),
        ],
        "change_failure_rate": [
            (15, "Elite"),  # 0-15%
            (30, "High"),  # 15-30%
            (45, "Medium"),  # 30-45%
            (100, "Low"),  # 45%+
        ],
    }

    if metric not in ratings:
        return "Unknown"

    thresholds = ratings[metric]

    # For deployment frequency (higher is better)
    if metric == "deployment_frequency":
        for threshold, rating in thresholds:
            if value >= threshold:
                return rating
        return "Low"

    # For other metrics (lower is better)
    for threshold, rating in thresholds:
        if value <= threshold:
            return rating

    return "Low"


def detect_anomalies(data: Dict) -> List[Dict]:
    """
    Detect statistical anomalies in metrics

    Returns list of anomalies with severity
    """
    anomalies = []

    # Check for marked anomalies in aggregated data
    if "anomalies" in data:
        for anomaly in data.get("anomalies", []):
            anomalies.append(
                {
                    "metric": anomaly.get("metric", "Unknown"),
                    "description": anomaly.get("description", ""),
                    "severity": anomaly.get("severity", "Medium"),
                    "value": anomaly.get("value", 0),
                }
            )

    return anomalies


def generate_recommendations(current_week: Dict, previous_week: Optional[Dict]) -> List[str]:
    """
    Generate automated recommendations based on trends
    """
    recommendations = []

    if not previous_week:
        return ["Collect more data to enable trend analysis and recommendations"]

    # DORA recommendations
    dora_current = current_week.get("dora", {})
    dora_previous = previous_week.get("dora", {})

    # Deployment frequency declining
    deploy_freq_current = dora_current.get("deploys_per_week", 0)
    deploy_freq_previous = dora_previous.get("deploys_per_week", 0)
    if deploy_freq_previous > 0 and deploy_freq_current < deploy_freq_previous * 0.8:
        recommendations.append(
            "Deployment frequency has declined by >20%. Consider reviewing deployment processes and CI/CD pipeline."
        )

    # Lead time increasing
    lead_time_current = dora_current.get("median_lead_time_hours", 0)
    lead_time_previous = dora_previous.get("median_lead_time_hours", 0)
    if lead_time_previous > 0 and lead_time_current > lead_time_previous * 1.5:
        recommendations.append(
            "Lead time has increased significantly. Review PR review processes and identify bottlenecks."
        )

    # Failure rate increasing
    failure_rate_current = dora_current.get("failure_rate", 0)
    failure_rate_previous = dora_previous.get("failure_rate", 0)
    if failure_rate_current > failure_rate_previous + 5:
        recommendations.append(
            "Change failure rate has increased. Consider improving test coverage and code review rigor."
        )

    # AI contribution recommendations
    collab_current = current_week.get("contributions", {}).get("collaborative_percentage", 0)
    collab_previous = previous_week.get("contributions", {}).get("collaborative_percentage", 0)
    if collab_current > collab_previous + 10:
        recommendations.append(
            "Collaborative AI work is increasing. Consider sharing best practices across the team."
        )

    if not recommendations:
        recommendations.append("Metrics are stable. Continue current practices.")

    return recommendations


def generate_report(data: Dict) -> str:
    """Generate markdown report from weekly summary data"""

    if not data or "weeks" not in data or len(data["weeks"]) == 0:
        return "# Weekly Metrics Report\n\nNo data available for report generation."

    # Get current and previous week
    weeks = sorted(data["weeks"], key=lambda w: w.get("week_start", ""), reverse=True)
    current_week = weeks[0]
    previous_week = weeks[1] if len(weeks) > 1 else None

    # Extract date range
    week_start = current_week.get("week_start", "Unknown")
    week_end = current_week.get("week_end", "Unknown")

    # Build report
    lines = []
    lines.append("# Weekly Metrics Report")
    lines.append(f"**Week of {week_start} - {week_end}**")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    dora = current_week.get("dora", {})
    overall_rating = dora.get("overall_rating", "Unknown")
    lines.append(f"- **Overall DORA Rating:** {overall_rating}")

    # Key achievement (biggest improvement)
    lines.append(f"- **Deployment Frequency:** {dora.get('deploys_per_week', 0):.1f} deploys/week")

    contrib = current_week.get("contributions", {})
    lines.append(
        f"- **AI Collaboration:** {contrib.get('collaborative_percentage', 0):.1f}% of commits are collaborative"
    )
    lines.append("")

    # DORA Metrics
    lines.append("## DORA Metrics")
    lines.append("")

    # Deployment Frequency
    lines.append("### Deployment Frequency")
    deploy_freq_current = dora.get("deploys_per_week", 0)
    deploy_freq_previous = (
        previous_week.get("dora", {}).get("deploys_per_week", 0) if previous_week else 0
    )
    lines.append(f"- **Current:** {deploy_freq_current:.1f} deploys/week")
    if previous_week:
        lines.append(f"- **Previous:** {deploy_freq_previous:.1f} deploys/week")
        change = format_change(deploy_freq_current, deploy_freq_previous)
        icon = get_change_icon(deploy_freq_current, deploy_freq_previous)
        lines.append(f"- **Change:** {change} {icon}")
    rating = get_dora_rating(deploy_freq_current, "deployment_frequency")
    lines.append(f"- **Rating:** {rating}")
    lines.append("")

    # Lead Time
    lines.append("### Lead Time for Changes")
    lead_time_current = dora.get("median_lead_time_hours", 0)
    lead_time_previous = (
        previous_week.get("dora", {}).get("median_lead_time_hours", 0) if previous_week else 0
    )
    lines.append(f"- **Current:** {lead_time_current:.1f} hours")
    if previous_week:
        lines.append(f"- **Previous:** {lead_time_previous:.1f} hours")
        change = format_change(lead_time_current, lead_time_previous, invert=True)
        icon = get_change_icon(lead_time_current, lead_time_previous, invert=True)
        lines.append(f"- **Change:** {change} {icon}")
    rating = get_dora_rating(lead_time_current, "lead_time")
    lines.append(f"- **Rating:** {rating}")
    lines.append("")

    # MTTR
    lines.append("### Mean Time to Recovery")
    mttr_current = dora.get("median_resolution_time_hours", 0)
    mttr_previous = (
        previous_week.get("dora", {}).get("median_resolution_time_hours", 0) if previous_week else 0
    )
    if mttr_current == 0:
        lines.append("- **Current:** No incidents (Elite)")
    else:
        lines.append(f"- **Current:** {mttr_current:.1f} hours")
        if previous_week and mttr_previous > 0:
            lines.append(f"- **Previous:** {mttr_previous:.1f} hours")
            change = format_change(mttr_current, mttr_previous, invert=True)
            icon = get_change_icon(mttr_current, mttr_previous, invert=True)
            lines.append(f"- **Change:** {change} {icon}")
        rating = get_dora_rating(mttr_current, "mttr")
        lines.append(f"- **Rating:** {rating}")
    lines.append("")

    # Change Failure Rate
    lines.append("### Change Failure Rate")
    failure_rate_current = dora.get("failure_rate", 0)
    failure_rate_previous = (
        previous_week.get("dora", {}).get("failure_rate", 0) if previous_week else 0
    )
    lines.append(f"- **Current:** {failure_rate_current:.1f}%")
    if previous_week:
        lines.append(f"- **Previous:** {failure_rate_previous:.1f}%")
        change = format_change(failure_rate_current, failure_rate_previous, invert=True)
        icon = get_change_icon(failure_rate_current, failure_rate_previous, invert=True)
        lines.append(f"- **Change:** {change} {icon}")
    rating = get_dora_rating(failure_rate_current, "change_failure_rate")
    lines.append(f"- **Rating:** {rating}")
    lines.append("")

    # AI Contribution Metrics
    lines.append("## AI Contribution Metrics")
    lines.append("")

    lines.append("### Collaborative Work")
    collab_current = contrib.get("collaborative_percentage", 0)
    collab_previous = (
        previous_week.get("contributions", {}).get("collaborative_percentage", 0)
        if previous_week
        else 0
    )
    lines.append(f"- **Current:** {collab_current:.1f}%")
    if previous_week:
        lines.append(f"- **Previous:** {collab_previous:.1f}%")
        change = format_change(collab_current, collab_previous)
        icon = get_change_icon(collab_current, collab_previous)
        lines.append(f"- **Change:** {change} {icon}")
    lines.append("")

    lines.append("### Lines of Code")
    lines.append(
        f"- **Human:** {contrib.get('human_lines_added', 0)} lines ({contrib.get('human_percentage', 0):.1f}%)"
    )
    lines.append(
        f"- **AI:** {contrib.get('ai_lines_added', 0)} lines ({contrib.get('ai_percentage', 0):.1f}%)"
    )
    lines.append(
        f"- **Collaborative:** {contrib.get('collaborative_lines_added', 0)} lines ({collab_current:.1f}%)"
    )
    lines.append("")

    # AI Review Impact
    review = current_week.get("ai_review", {})
    if review:
        lines.append("## AI Review Impact")
        lines.append("")

        lines.append("### Review Coverage")
        coverage_current = review.get("review_coverage", 0)
        coverage_previous = (
            previous_week.get("ai_review", {}).get("review_coverage", 0) if previous_week else 0
        )
        lines.append(f"- **Current:** {coverage_current:.1f}%")
        if previous_week:
            lines.append(f"- **Previous:** {coverage_previous:.1f}%")
            change = format_change(coverage_current, coverage_previous)
            icon = get_change_icon(coverage_current, coverage_previous)
            lines.append(f"- **Change:** {change} {icon}")
        lines.append("")

        lines.append("### Suggestion Acceptance Rate")
        acceptance_current = review.get("avg_acceptance_rate", 0)
        acceptance_previous = (
            previous_week.get("ai_review", {}).get("avg_acceptance_rate", 0) if previous_week else 0
        )
        lines.append(f"- **Current:** {acceptance_current:.1f}%")
        if previous_week:
            lines.append(f"- **Previous:** {acceptance_previous:.1f}%")
            change = format_change(acceptance_current, acceptance_previous)
            icon = get_change_icon(acceptance_current, acceptance_previous)
            lines.append(f"- **Change:** {change} {icon}")
        lines.append("")

    # GitHub Collaboration (if available)
    github = current_week.get("github", {})
    if github and github.get("total_prs", 0) > 0:
        lines.append("## GitHub Collaboration")
        lines.append("")

        lines.append("### PR Cycle Time")
        cycle_time_current = github.get("median_cycle_time_hours", 0)
        cycle_time_previous = (
            previous_week.get("github", {}).get("median_cycle_time_hours", 0)
            if previous_week
            else 0
        )
        lines.append(f"- **Current:** {cycle_time_current:.1f} hours")
        if previous_week and cycle_time_previous > 0:
            lines.append(f"- **Previous:** {cycle_time_previous:.1f} hours")
            change = format_change(cycle_time_current, cycle_time_previous, invert=True)
            icon = get_change_icon(cycle_time_current, cycle_time_previous, invert=True)
            lines.append(f"- **Change:** {change} {icon}")
        lines.append("")

        lines.append("### Feature Velocity")
        lines.append(f"- **Features:** {github.get('features_completed', 0)} completed")
        lines.append(f"- **Bugs:** {github.get('bugs_fixed', 0)} fixed")
        lines.append(
            f"- **Total:** {github.get('features_completed', 0) + github.get('bugs_fixed', 0)} items"
        )
        lines.append("")

    # Anomalies
    anomalies = detect_anomalies(current_week)
    if anomalies:
        lines.append("## Anomalies Detected")
        lines.append("")
        for anomaly in anomalies:
            severity = anomaly.get("severity", "Medium")
            metric = anomaly.get("metric", "Unknown")
            description = anomaly.get("description", "")
            lines.append(f"- **{metric}:** {description} (Severity: {severity})")
        lines.append("")

    # Recommendations
    recommendations = generate_recommendations(current_week, previous_week)
    lines.append("## Recommendations")
    lines.append("")
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append("")

    # Resources
    lines.append("## Resources")
    lines.append("- [View Full Dashboard](../../src/dashboard/index.html)")
    lines.append("- [Metrics Collection Workflow](../../.github/workflows/metrics-collection.yml)")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*This report was automatically generated by the Metrics Dashboard system.*")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"*Report generated on: {timestamp}*")

    return "\n".join(lines)


def main():
    """Main entry point"""
    print("Generating weekly metrics report...")

    # Load data
    data = load_weekly_summary()

    if not data:
        print("ERROR: Could not load weekly summary data")
        # Create a placeholder report
        report = "# Weekly Metrics Report\n\n**Data not available**\n\nPlease run metrics collection workflow first."
    else:
        # Generate report
        report = generate_report(data)

    # Ensure reports directory exists
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Write report
    report_path = reports_dir / "weekly_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    print(f"Report generated: {report_path}")
    print(f"Report length: {len(report)} characters")


if __name__ == "__main__":
    main()
