# Metrics Export Guide

How to export and use metrics data for presentations, reports, and analysis.

## Quick Reference

| Export Type | Button Location | Output Format | Use Case |
|-------------|----------------|---------------|----------|
| **CSV** | Header "Export Data" | .csv file | Excel analysis, data sharing |
| **PNG** | Per-chart "Download" | .png image | PowerPoint, reports, emails |

## CSV Export

### Basic Usage

1. Open dashboard: `src/dashboard/index.html`
2. Click **"Export Data"** button in header
3. File downloads: `metrics_export_2025-11-07.csv`
4. Open in Excel, Google Sheets, or text editor

### CSV Structure

```csv
Date,Metric Category,Metric Name,Value,Unit
2025-11-07,DORA,Total Deployments,45,count
2025-11-07,DORA,Deployment Frequency,2.5,deploys/week
2025-11-07,DORA,Median Lead Time,4.2,hours
2025-11-07,DORA,P95 Lead Time,12.8,hours
2025-11-07,DORA,Total Incidents,2,count
2025-11-07,DORA,Median Resolution Time,3.5,hours
2025-11-07,DORA,Total Failures,3,count
2025-11-07,DORA,Failure Rate,6.7,%
2025-11-07,GitHub,Total PRs,28,count
2025-11-07,GitHub,Median Cycle Time,18.4,hours
2025-11-07,GitHub,Open PRs,5,count
2025-11-07,GitHub,Merged PRs,23,count
2025-11-07,GitHub,Total Conflicts,4,count
2025-11-07,GitHub,Conflict Rate,14.3,%
2025-11-07,Contributions,Total Commits,18,count
2025-11-07,Contributions,Human Commits,33.3,%
2025-11-07,Contributions,AI Commits,5.6,%
2025-11-07,Contributions,Collaborative Commits,61.1,%
2025-11-07,AI Review,Review Coverage,78.5,%
2025-11-07,AI Review,Avg Suggestions per PR,5.2,suggestions/PR
2025-11-07,AI Review,Avg Acceptance Rate,72.3,%
2025-11-07,AI Review,Avg Response Time,0.8,hours
```

### Column Definitions

- **Date:** Timestamp of metric collection (YYYY-MM-DD)
- **Metric Category:** DORA, GitHub, Contributions, or AI Review
- **Metric Name:** Specific metric (e.g., "Deployment Frequency")
- **Value:** Numeric value
- **Unit:** Measurement unit (%, hours, count, deploys/week)

### Opening in Excel

**Method 1: Import (Recommended for UTF-8)**

1. Open Excel
2. **Data** → **Get Data** → **From File** → **From Text/CSV**
3. Select `metrics_export_*.csv`
4. File Origin: **65001: Unicode (UTF-8)**
5. Delimiter: **Comma**
6. Click **Load**

**Method 2: Double-Click (Quick)**

1. Double-click CSV file
2. Excel opens automatically
3. May need to adjust column widths

**Method 3: Drag and Drop**

1. Open blank Excel workbook
2. Drag CSV file into Excel window
3. Choose **Import**

### Opening in Google Sheets

1. Open Google Sheets: https://sheets.google.com
2. **File** → **Import**
3. **Upload** tab → **Select file**
4. Import location: **New spreadsheet**
5. Separator type: **Comma**
6. Click **Import data**

### Opening in Numbers (Mac)

1. Right-click CSV file
2. **Open With** → **Numbers**
3. Numbers auto-detects CSV format
4. Adjust column widths as needed

## PNG Export

### Basic Usage

1. Open dashboard: `src/dashboard/index.html`
2. **Hover** over any chart card
3. **"Download"** button appears in top-right corner
4. **Click** download button
5. File saves: `{metric_name}_2025-11-07.png`

### Export All Charts

To export all 14 charts:

1. Set desired theme (dark or light)
2. Hover and click download for each chart:
   - Deployment Frequency → `deployment_frequency_2025-11-07.png`
   - Lead Time → `lead_time_2025-11-07.png`
   - MTTR → `mttr_2025-11-07.png`
   - Change Failure Rate → `change_failure_rate_2025-11-07.png`
   - PR Cycle Time → `pr_cycle_time_2025-11-07.png`
   - Merge Conflicts → `merge_conflicts_2025-11-07.png`
   - Feature Velocity → `feature_velocity_2025-11-07.png`
   - Contribution Attribution → `contribution_attribution_2025-11-07.png`
   - Contribution Trend → `contribution_trend_2025-11-07.png`
   - Commit Distribution → `commit_distribution_2025-11-07.png`
   - Review Coverage → `review_coverage_2025-11-07.png`
   - Suggestions per PR → `suggestions_per_pr_2025-11-07.png`
   - Acceptance Rate → `acceptance_rate_2025-11-07.png`
   - Response Time → `response_time_2025-11-07.png`

### Chart Properties

- **Resolution:** 1200x800px (presentation-ready)
- **Format:** PNG with transparency support
- **Background:** Matches current theme
  - Dark mode: `rgba(26, 26, 26, 1)` (dark gray)
  - Light mode: `rgba(255, 255, 255, 1)` (white)
- **Quality:** High-resolution, lossless PNG
- **Size:** Typically 50-200KB per chart

## Use Cases

### PowerPoint Presentations

**Quick Insert:**
1. Export charts as PNG (use light mode for white backgrounds)
2. PowerPoint → **Insert** → **Pictures** → **This Device**
3. Select downloaded PNG files (can select multiple)
4. Click **Insert**
5. Resize and position as needed

**Slide Layouts:**

**Option 1: Single Chart per Slide**
- Full-size chart (centered)
- Title at top
- Key insights as bullet points

**Option 2: Two Charts per Slide**
- Compare related metrics
- Side-by-side layout
- Common title

**Option 3: Four Charts per Slide**
- Executive overview
- 2x2 grid layout
- Highlight trends

**Best Practices:**
- Use consistent background (dark vs light)
- Add slide titles that interpret data
- Include data source in footer: "Source: Metrics Dashboard - [Date]"
- Crop charts if needed for focus

### Word Documents / Reports

**Inserting Charts:**
1. Export charts as PNG
2. Word → **Insert** → **Pictures**
3. Select PNG files
4. Use **Tight** text wrapping
5. Add captions below charts

**Report Structure:**

```markdown
# Weekly Metrics Report

## Executive Summary
[Key findings]

## DORA Metrics
[Insert deployment_frequency.png]
**Figure 1:** Deployment frequency shows...

[Insert lead_time.png]
**Figure 2:** Lead time has...

## Recommendations
[Action items based on data]
```

**Formatting Tips:**
- Use "In Line with Text" for simple layout
- Use "Square" or "Tight" for text wrapping
- Center-align charts for professional appearance
- Add figure numbers and captions

### Excel Analysis

**Import CSV for Pivot Tables:**

1. Export CSV from dashboard
2. Excel → **Data** → **Get Data** → **From File** → **From Text/CSV**
3. Load data into Excel
4. **Insert** → **PivotTable**
5. Analyze by:
   - Metric Category
   - Date
   - Value ranges

**Create Custom Charts:**

1. Import CSV data
2. Select columns for charting
3. **Insert** → Chart type (Line, Bar, etc.)
4. Customize colors to match Kearney purple theme
5. Remove gridlines (Kearney standard)

**Example Analysis:**

```
Metric Category | Average Value | Trend
----------------|---------------|-------
DORA            | ...           | ↑ 15%
GitHub          | ...           | → 0%
Contributions   | ...           | ↑ 8%
```

### Google Docs

**Inserting Images:**
1. Export charts as PNG
2. Google Docs → **Insert** → **Image** → **Upload from computer**
3. Select PNG files
4. Resize by dragging corners
5. Right-click → **Image options** → **Text wrapping**

**Adding Captions:**
- Insert table below image (1 row, 1 column)
- Type caption in table cell
- Format as italic or gray text

### Email Sharing

**Inline Images (Recommended):**
1. Export charts as PNG
2. Compose email
3. Drag PNG files directly into email body
4. Works in: Gmail, Outlook, Apple Mail, Thunderbird

**Attachments:**
- Attach multiple PNGs for comprehensive reports
- Include CSV for detailed data
- Add cover email explaining context

**Email Template:**

```
Subject: Weekly Metrics Report - Week of [Date]

Hi Team,

Please find this week's metrics below:

[Drag deployment_frequency.png here]

Key Findings:
- Deployment frequency up 15%
- Lead time reduced by 20%
- AI collaboration at 65%

Full data attached as CSV.

Best,
[Your Name]
```

### Slack / Teams Sharing

**Quick Share:**
1. Export chart as PNG
2. Drag PNG into Slack/Teams message
3. Add context in message

**Channel Updates:**
```
📊 Weekly Metrics Update

Deployment Frequency: ↑ 15%
[deployment_frequency.png]

Lead Time: ↓ 20%
[lead_time.png]

Great work team! 🎉
```

### Confluence / Wiki

**Embedding:**
1. Export charts as PNG
2. Confluence → Edit page → **+** → **Image**
3. Upload PNG files
4. Add to page gallery or inline

**Creating Metrics Page:**
- Weekly Metrics section
- Embed 3-4 key charts
- Link to full dashboard
- Update weekly with new exports

## Data Analysis Workflows

### Weekly Review

```bash
# 1. Export current data
# Click "Export Data" in dashboard

# 2. Open in Excel
# Import CSV using Data → From Text/CSV

# 3. Compare to previous week
# Create new column: "Change from Last Week"
# Formula: =(Current - Previous) / Previous

# 4. Identify trends
# Sort by "Change from Last Week" descending
# Flag items with >20% change

# 5. Create action items
# Export insights to task tracker
```

### Monthly Reporting

```bash
# 1. Export CSV for entire month
# Run metrics collection for last 30 days

# 2. Create pivot table
# Rows: Metric Name
# Columns: Week
# Values: Average of Value

# 3. Export key charts
# Deployment Frequency, Lead Time, Failure Rate

# 4. Create PowerPoint
# Title slide: "Monthly Metrics Review"
# DORA metrics slides (4 charts)
# AI contribution slide (2 charts)
# Recommendations slide

# 5. Present to stakeholders
```

### Quarterly Analysis

```bash
# 1. Collect 3 months of data
# Export CSV weekly, combine in Excel

# 2. Calculate trends
# Use Excel TREND() function
# Identify sustained improvements

# 3. Benchmark against goals
# Compare to DORA benchmarks (Elite/High/Medium/Low)
# Set goals for next quarter

# 4. Create executive summary
# 1-page PDF with key charts
# Include 3 wins, 3 areas for improvement
```

## Automation

### Scheduled Exports (Advanced)

**Option 1: Manual Weekly**
1. Set calendar reminder for Monday 9am
2. Open dashboard
3. Export CSV and key charts
4. Email to team

**Option 2: Automated Email**
- Already configured via GitHub Actions
- Sends every Monday at 9am UTC
- Includes HTML email and markdown attachment
- See `docs/EMAIL_NOTIFICATION_SETUP.md`

**Option 3: Scripted Export**
```bash
#!/bin/bash
# weekly-export.sh

# Run metrics collection
python -m src.orchestrator.metrics.aggregator --weeks 4

# Open dashboard (manual export)
open src/dashboard/index.html

# TODO: Add programmatic export
```

### Programmatic Export (Advanced)

**JavaScript in Browser Console:**

```javascript
// Export CSV
window.dashboard.exportToCSV();

// Export specific chart
window.exportChartAsPNG('chart-deploy-frequency', 'deployment_frequency');

// Export all charts
const charts = [
  'deploy-frequency', 'lead-time', 'mttr', 'change-failure-rate',
  'pr-cycle-time', 'merge-conflicts', 'feature-velocity',
  'attribution', 'contribution-trend', 'commit-distribution',
  'review-coverage', 'suggestions-per-pr', 'acceptance-rate', 'response-time'
];

charts.forEach(chartId => {
  window.exportChartAsPNG(`chart-${chartId}`, chartId);
});
```

## Troubleshooting

### CSV Issues

**Problem:** Excel shows garbage characters

**Solution:** Use "Data → From Text/CSV" import with UTF-8 encoding

---

**Problem:** Commas in data break columns

**Solution:** CSV properly escapes commas. If broken, re-export from dashboard.

---

**Problem:** Can't open CSV in Excel

**Solution:** Right-click → "Open With" → Microsoft Excel

### PNG Issues

**Problem:** Download button doesn't appear

**Solution:** Hover slowly over chart card. Button has 0.2s transition delay.

---

**Problem:** PNG has wrong background color

**Solution:** Switch theme before exporting. Dark mode = dark background.

---

**Problem:** PNG quality is low

**Solution:** Charts export at full resolution. Don't scale up beyond original size.

---

**Problem:** Download doesn't start

**Solution:** Check browser's download settings. May be blocked by popup blocker.

## Best Practices

### File Organization

Create folder structure for exports:

```
metrics_exports/
├── 2025-01-07_week01/
│   ├── metrics_export_2025-01-07.csv
│   ├── deployment_frequency_2025-01-07.png
│   ├── lead_time_2025-01-07.png
│   └── ...
├── 2025-01-14_week02/
│   └── ...
└── quarterly_reports/
    └── Q1_2025_summary.pptx
```

### Version Control

- **Don't commit** PNG/CSV exports to git
- **Do commit** analysis scripts and templates
- **Do commit** `.gitkeep` in reports/ directory
- **Use** `.gitignore` for export directories

### Data Retention

- Keep CSV exports for 1 year
- Archive quarterly summaries indefinitely
- Delete individual chart PNGs after presentation

### Sharing Guidelines

**Internal (Team):**
- Share raw CSV and PNGs freely
- No PII or sensitive data in metrics

**Management:**
- Export professional PDF reports
- Include context and recommendations
- Highlight trends, not raw numbers

**External (Clients):**
- Remove project-specific identifiers
- Aggregate data if needed
- Get approval before sharing

## Related Documentation

- [Metrics Dashboard Guide](METRICS_DASHBOARD_GUIDE.md) - Complete dashboard documentation
- [Email Notification Setup](EMAIL_NOTIFICATION_SETUP.md) - Automated report delivery
- [Design System Audit](DESIGN_SYSTEM_AUDIT.md) - Kearney branding standards
