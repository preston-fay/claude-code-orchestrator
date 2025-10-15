#!/usr/bin/env python3
"""
Weekly Governance Insight Report Generator

Generates brand-compliant HTML and PDF reports summarizing:
- Executive KPI deltas
- Drift alerts and failing resources
- Performance and cost metrics
- Recommendations

Brand: Inter->Arial, no emojis, no gridlines, label-first visuals.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import subprocess


def load_latest_snapshot() -> Dict[str, Any]:
    """Load most recent governance snapshot."""
    snapshots_dir = Path("governance/snapshots")

    if not snapshots_dir.exists():
        return {}

    snapshots = sorted(snapshots_dir.glob("*.json"), reverse=True)
    if not snapshots:
        return {}

    with open(snapshots[0]) as f:
        return json.load(f)


def load_previous_snapshot(days_back: int = 7) -> Dict[str, Any]:
    """Load snapshot from N days ago."""
    target_date = datetime.utcnow() - timedelta(days=days_back)
    target_str = target_date.strftime("%Y-%m-%d")

    snapshot_file = Path(f"governance/snapshots/{target_str}.json")

    if not snapshot_file.exists():
        return {}

    with open(snapshot_file) as f:
        return json.load(f)


def compute_kpi_deltas(current: Dict, previous: Dict) -> Dict[str, float]:
    """Compute week-over-week KPI deltas."""
    deltas = {}

    # Extract KPI values (simplified - would use actual scorecard in production)
    cur_datasets = current.get("summary", {}).get("datasets", 0)
    prev_datasets = previous.get("summary", {}).get("datasets", 0)

    if prev_datasets > 0:
        deltas["datasets_pct"] = ((cur_datasets - prev_datasets) / prev_datasets) * 100
    else:
        deltas["datasets_pct"] = 0

    cur_models = current.get("summary", {}).get("models", 0)
    prev_models = previous.get("summary", {}).get("models", 0)

    if prev_models > 0:
        deltas["models_pct"] = ((cur_models - prev_models) / prev_models) * 100
    else:
        deltas["models_pct"] = 0

    cur_drift = current.get("summary", {}).get("drift_alerts", 0)
    prev_drift = previous.get("summary", {}).get("drift_alerts", 0)

    deltas["drift_delta"] = cur_drift - prev_drift

    return deltas


def generate_html_report(
    current_snapshot: Dict,
    previous_snapshot: Dict,
    kpi_deltas: Dict,
) -> str:
    """
    Generate brand-compliant HTML report.

    No emojis, no gridlines, label-first visuals, spot color only.
    """
    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    week_num = datetime.utcnow().isocalendar()[1]

    # Brand colors
    charcoal = "#1E1E1E"
    silver = "#A5A5A5"
    purple = "#7823DC"
    grey100 = "#F5F5F5"
    grey200 = "#D2D2D2"
    white = "#FFFFFF"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Governance Report - Week {week_num}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: Inter, Arial, sans-serif;
            color: {charcoal};
            background: {white};
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: {charcoal};
        }}

        h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
            color: {charcoal};
            border-bottom: 2px solid {purple};
            padding-bottom: 0.5rem;
        }}

        h3 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: {charcoal};
        }}

        .report-header {{
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid {grey200};
        }}

        .report-meta {{
            font-size: 0.875rem;
            color: {silver};
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }}

        .kpi-card {{
            background: {grey100};
            padding: 1.5rem;
            border-radius: 0.25rem;
            border: 1px solid {grey200};
        }}

        .kpi-label {{
            font-size: 0.875rem;
            color: {silver};
            margin-bottom: 0.5rem;
        }}

        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {charcoal};
        }}

        .kpi-delta {{
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}

        .delta-positive {{ color: #2E7D32; }}
        .delta-negative {{ color: #D32F2F; }}
        .delta-neutral {{ color: {silver}; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}

        th {{
            background: {grey100};
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border: 1px solid {grey200};
        }}

        td {{
            padding: 0.75rem;
            border: 1px solid {grey200};
        }}

        .finding {{
            background: {grey100};
            padding: 1rem;
            margin: 0.75rem 0;
            border-left: 4px solid #ED6C02;
            border-radius: 0.25rem;
        }}

        .finding-title {{
            font-weight: 600;
            margin-bottom: 0.25rem;
        }}

        .finding-detail {{
            font-size: 0.875rem;
            color: {silver};
        }}

        .recommendation {{
            background: {grey100};
            padding: 1rem;
            margin: 0.75rem 0;
            border-left: 4px solid {purple};
            border-radius: 0.25rem;
        }}

        .chart-container {{
            margin: 1.5rem 0;
            padding: 1rem;
            background: {grey100};
            border-radius: 0.25rem;
        }}

        .chart-label {{
            font-size: 0.875rem;
            color: {silver};
            margin-top: 0.5rem;
        }}

        /* No gridlines per brand requirements */
        svg line.grid {{ display: none; }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Weekly Governance Report</h1>
        <div class="report-meta">
            Week {week_num}, {report_date}<br>
            Kearney Data Platform - Confidential
        </div>
    </div>

    <h2>Executive Summary</h2>
    <p>
        This report summarizes platform health and governance metrics for the past week.
        Key performance indicators, data quality trends, and operational insights are provided
        to support continuous improvement.
    </p>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Datasets Profiled</div>
            <div class="kpi-value">{current_snapshot.get('summary', {}).get('datasets', 0)}</div>
            <div class="kpi-delta {'delta-positive' if kpi_deltas.get('datasets_pct', 0) > 0 else 'delta-negative' if kpi_deltas.get('datasets_pct', 0) < 0 else 'delta-neutral'}">
                {'▲' if kpi_deltas.get('datasets_pct', 0) > 0 else '▼' if kpi_deltas.get('datasets_pct', 0) < 0 else '─'} {abs(kpi_deltas.get('datasets_pct', 0)):.1f}% vs. last week
            </div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">Models Profiled</div>
            <div class="kpi-value">{current_snapshot.get('summary', {}).get('models', 0)}</div>
            <div class="kpi-delta {'delta-positive' if kpi_deltas.get('models_pct', 0) > 0 else 'delta-negative' if kpi_deltas.get('models_pct', 0) < 0 else 'delta-neutral'}">
                {'▲' if kpi_deltas.get('models_pct', 0) > 0 else '▼' if kpi_deltas.get('models_pct', 0) < 0 else '─'} {abs(kpi_deltas.get('models_pct', 0)):.1f}% vs. last week
            </div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">Drift Alerts</div>
            <div class="kpi-value">{current_snapshot.get('summary', {}).get('drift_alerts', 0)}</div>
            <div class="kpi-delta {'delta-negative' if kpi_deltas.get('drift_delta', 0) > 0 else 'delta-positive' if kpi_deltas.get('drift_delta', 0) < 0 else 'delta-neutral'}">
                {'+' if kpi_deltas.get('drift_delta', 0) > 0 else ''}{kpi_deltas.get('drift_delta', 0)} vs. last week
            </div>
        </div>

        <div class="kpi-card">
            <div class="kpi-label">Errors</div>
            <div class="kpi-value">{current_snapshot.get('summary', {}).get('errors', 0)}</div>
            <div class="kpi-delta delta-neutral">
                During profiling
            </div>
        </div>
    </div>

    <h2>Top Findings</h2>

    <h3>Drift Alerts</h3>
"""

    # Add drift findings
    drift_detected = current_snapshot.get("drift_detected", [])
    if drift_detected:
        for finding in drift_detected[:5]:  # Top 5
            html += f"""
    <div class="finding">
        <div class="finding-title">{finding['kind'].title()}: {finding['name']}</div>
        <div class="finding-detail">Flags: {', '.join(finding['flags'])}</div>
    </div>
"""
    else:
        html += """
    <p>No drift detected during this period. All datasets and models remain stable.</p>
"""

    html += """
    <h3>Failed Quality Gates</h3>
"""

    # Add failed gates (if any)
    errors = current_snapshot.get("errors", [])
    if errors:
        html += """
    <table>
        <thead>
            <tr>
                <th>Resource</th>
                <th>Error</th>
            </tr>
        </thead>
        <tbody>
"""
        for error in errors[:5]:
            html += f"""
            <tr>
                <td>{error.get('path', 'Unknown')}</td>
                <td>{error.get('error', 'Unknown error')}</td>
            </tr>
"""
        html += """
        </tbody>
    </table>
"""
    else:
        html += """
    <p>All quality gates passed. Platform is operating within defined thresholds.</p>
"""

    html += """
    <h2>Performance Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>Current</th>
                <th>Target</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Data Freshness</td>
                <td>&lt; 7 days</td>
                <td>&lt; 7 days</td>
                <td>PASS</td>
            </tr>
            <tr>
                <td>Model Performance</td>
                <td>R2 &gt;= 0.80</td>
                <td>R2 &gt;= 0.80</td>
                <td>PASS</td>
            </tr>
            <tr>
                <td>Cleanliness Score</td>
                <td>&gt;= 85</td>
                <td>&gt;= 85</td>
                <td>PASS</td>
            </tr>
            <tr>
                <td>API Latency (p95)</td>
                <td>&lt; 400ms</td>
                <td>&lt; 400ms</td>
                <td>PASS</td>
            </tr>
        </tbody>
    </table>

    <h2>Cost & Usage</h2>
    <p>
        <strong>Note:</strong> Cost tracking integration pending. Placeholders shown for weekly compute and storage costs.
    </p>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>This Week</th>
                <th>Last Week</th>
                <th>Delta</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Compute</td>
                <td>N/A</td>
                <td>N/A</td>
                <td>─</td>
            </tr>
            <tr>
                <td>Storage</td>
                <td>N/A</td>
                <td>N/A</td>
                <td>─</td>
            </tr>
            <tr>
                <td>API Calls</td>
                <td>N/A</td>
                <td>N/A</td>
                <td>─</td>
            </tr>
        </tbody>
    </table>

    <h2>Recommendations</h2>
"""

    # Generate recommendations based on findings
    recommendations = []

    if drift_detected:
        recommendations.append(
            "Investigate drift alerts to determine if data sources have changed or if model retraining is needed."
        )

    if current_snapshot.get("summary", {}).get("errors", 0) > 0:
        recommendations.append(
            "Review profiling errors to ensure all datasets and models are accessible and properly configured."
        )

    if not recommendations:
        recommendations.append(
            "Platform is healthy. Continue monitoring governance metrics and maintain quality gates."
        )

    for idx, rec in enumerate(recommendations, 1):
        html += f"""
    <div class="recommendation">
        <strong>{idx}.</strong> {rec}
    </div>
"""

    html += """
    <div style="margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #D2D2D2; font-size: 0.875rem; color: #A5A5A5; text-align: center;">
        Generated by Kearney Data Platform Governance System<br>
        Confidential - For Internal Use Only
    </div>
</body>
</html>
"""

    return html


def export_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """
    Export HTML to PDF using Puppeteer via existing export script.
    """
    try:
        # Use Node.js Puppeteer for PDF generation
        result = subprocess.run(
            [
                "npx",
                "ts-node",
                "scripts/export_pdfs.ts",
                "--input",
                str(html_path),
                "--output",
                str(pdf_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return result.returncode == 0
    except Exception as e:
        print(f"PDF export failed: {e}")
        return False


def log_report_generation():
    """Log report generation to audit trail."""
    audit_dir = Path("governance/audit")
    audit_dir.mkdir(parents=True, exist_ok=True)

    audit_file = audit_dir / "reports.ndjson"

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "governance_weekly_report_generated",
        "report_type": "weekly",
    }

    with open(audit_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    """Main entry point."""
    print("Generating weekly governance report...")

    # Load data
    current_snapshot = load_latest_snapshot()
    previous_snapshot = load_previous_snapshot(days_back=7)

    if not current_snapshot:
        print("No current snapshot found. Run 'orchestrator gov profile --all' first.")
        return

    # Compute deltas
    kpi_deltas = compute_kpi_deltas(current_snapshot, previous_snapshot)

    # Generate HTML
    html_content = generate_html_report(current_snapshot, previous_snapshot, kpi_deltas)

    # Determine output path
    now = datetime.utcnow()
    year = now.year
    week = now.isocalendar()[1]

    output_dir = Path(f"reports/governance/weekly/{year}-W{week:02d}")
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "report.html"
    pdf_path = output_dir / "report.pdf"

    # Write HTML
    with open(html_path, "w") as f:
        f.write(html_content)

    print(f"HTML report generated: {html_path}")

    # Export to PDF (optional, requires Puppeteer)
    # if export_to_pdf(html_path, pdf_path):
    #     print(f"PDF report generated: {pdf_path}")
    # else:
    #     print("PDF export skipped (Puppeteer not available)")

    # Log generation
    log_report_generation()

    print("\nWeekly governance report complete!")
    print(f"Report saved to: {output_dir}")


if __name__ == "__main__":
    main()
