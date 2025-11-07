# Metrics Dashboard Guide

Comprehensive guide to using the Claude Code Orchestrator Metrics Dashboard.

## Overview

The Metrics Dashboard provides real-time visibility into deployment velocity, AI contributions, and code quality metrics following Google's DORA (DevOps Research and Assessment) framework.

**Dashboard Location:** `src/dashboard/index.html`

**Key Features:**
- 📈 4 DORA metrics with industry benchmarks
- 🤖 AI contribution analysis with human/AI/collaborative attribution
- 🔍 AI review impact tracking
- 🔄 GitHub collaboration metrics (PR cycle time, conflicts, velocity)
- 🎨 Kearney design system with purple branding
- 🌓 Dark mode default with light mode toggle
- 💾 CSV and PNG export for all charts

## Accessing the Dashboard

### Local Access
```bash
# Open in default browser
open src/dashboard/index.html

# Or double-click the file in Finder/Explorer
```

### GitHub Pages (Optional)
If deployed to GitHub Pages:
```
https://[username].github.io/claude-code-orchestrator/src/dashboard/
```

## Dashboard Sections

### Hero Metrics (Top Cards)

Three key metrics displayed prominently:

**1. DORA Rating**
- Overall DORA performance level
- Values: Elite, High, Medium, Low
- Based on aggregate of all 4 DORA metrics

**2. Deployment Frequency**
- Current deploys per week
- Calculated from git tags with semantic versioning

**3. AI Contribution**
- Percentage of collaborative commits
- Combines human and AI contributions

### 1. DORA Metrics

#### What are DORA Metrics?

DORA (DevOps Research and Assessment) metrics are industry-standard measurements of software delivery performance identified by Google's research team.

#### Deployment Frequency

**Measures:** How often code is deployed to production

**Calculation:** Deployments per week based on git tags

**Data Source:** Git tags matching semantic versioning pattern (v1.2.3)

**Benchmarks:**
| Rating | Frequency | Deploys/Week |
|--------|-----------|--------------|
| **Elite** | Multiple deploys per day | 7+ |
| **High** | Daily to weekly | 1-7 |
| **Medium** | Weekly to monthly | 0.25-1 |
| **Low** | Less than monthly | <0.25 |

**Chart Type:** Line chart showing deploys per week over last 12 weeks

**Interpretation:**
- Higher is better
- Trend should be stable or increasing
- Sudden drops may indicate process issues

#### Lead Time for Changes

**Measures:** Time from commit to production deployment

**Calculation:** Average hours between commit timestamp and deployment tag

**Data Source:** Git commit history and tag timestamps

**Benchmarks:**
| Rating | Lead Time |
|--------|-----------|
| **Elite** | Less than 1 hour |
| **High** | 1 hour to 1 day |
| **Medium** | 1 day to 1 week |
| **Low** | More than 1 week |

**Chart Type:** Line chart showing lead time in hours for last 20 deployments

**Interpretation:**
- Lower is better
- Indicates deployment pipeline efficiency
- High values suggest review or CI/CD bottlenecks

#### Mean Time to Recovery (MTTR)

**Measures:** How quickly production issues are resolved

**Calculation:** Time between hotfix deployment tags

**Data Source:** Git tags with patch version bumps or "hotfix" keyword within 48 hours

**Benchmarks:**
| Rating | MTTR |
|--------|------|
| **Elite** | Less than 1 hour |
| **High** | Less than 1 day |
| **Medium** | 1 day to 1 week |
| **Low** | More than 1 week |

**Chart Type:** Bar chart showing resolution time per incident

**Special Case:** If no incidents detected, displays "No incidents recorded (Elite DORA rating)"

**Interpretation:**
- Lower is better
- No incidents = Elite rating
- High MTTR suggests need for better monitoring/alerting

#### Change Failure Rate

**Measures:** Percentage of deployments requiring hotfixes

**Calculation:** (Hotfix deployments / Total deployments) × 100

**Data Source:** Git tags identified as hotfixes

**Benchmarks:**
| Rating | Failure Rate |
|--------|--------------|
| **Elite** | 0-15% |
| **High** | 15-30% |
| **Medium** | 30-45% |
| **Low** | 45%+ |

**Chart Type:** Line chart showing failure rate percentage over time

**Interpretation:**
- Lower is better
- Indicates code quality and testing effectiveness
- Trending up = need for better test coverage

### 2. GitHub Collaboration Metrics

#### PR Cycle Time

**Measures:** Hours from PR creation to merge

**Calculation:** Timestamp difference between PR opened and merged events

**Data Source:** GitHub API pull request data

**Chart Type:** Line chart showing cycle time for last 20 merged PRs

**Interpretation:**
- Lower is better
- Indicates review process efficiency
- Very low may suggest insufficient review rigor
- Very high suggests review bottlenecks

#### Merge Conflicts

**Measures:** Number of merge conflicts detected per week

**Calculation:** Count of PRs with merge conflict labels or keywords

**Data Source:** GitHub API PR events and labels

**Chart Type:** Line chart showing conflicts per week over last 12 weeks

**Interpretation:**
- Lower is better
- Frequent conflicts suggest:
  - Long-lived feature branches
  - Multiple developers editing same files
  - Need for better code organization

#### Feature Velocity

**Measures:** Features, bugs, and chores completed per week

**Calculation:** Count of merged PRs by conventional commit type

**Data Source:** Git commit messages (feat:, fix:, chore:)

**Chart Type:** Stacked bar chart showing features vs bugs over last 12 weeks

**Interpretation:**
- Higher is better (with caveats)
- Balance between features and bugs indicates healthy development
- All features, no bugs = technical debt building
- All bugs, no features = stalled product development

### 3. AI Contribution Metrics

#### Attribution Analysis (Pie Chart)

**Measures:** Distribution of commit types by contributor

**Categories:**
- **Human:** Commits with no AI indicators
- **AI:** Commits with [claude], [ai], or Co-Authored-By: Claude markers
- **Collaborative:** Commits with both human and AI contributions

**Detection Patterns:**
```
AI Indicators:
- Co-Authored-By:.*Claude
- \[claude\]
- \[ai\]
- Generated with.*Claude
- 🤖 Generated with Claude Code

Collaborative Indicators:
- Both human commit message AND AI co-author
- Human review of AI-generated code
- AI suggestions implemented by human
```

**Chart Type:** Doughnut chart (pie chart with center hole)

**Interpretation:**
- High collaborative percentage indicates effective AI pair programming
- 100% human suggests AI tools underutilized
- 100% AI suggests lack of human oversight

#### Contribution Trend (Stacked Area Chart)

**Measures:** Lines of code added by contributor type over time

**Calculation:** Sum of lines added per week, grouped by contributor type

**Data Source:** Git commit diffs

**Chart Type:** Stacked area chart showing lines added by type over last 12 weeks

**Interpretation:**
- Shows shift toward AI-assisted development over time
- Collaborative layer growth indicates healthy AI adoption
- Sudden spikes may indicate refactoring or generated code

#### Commit Distribution (Horizontal Bar Chart)

**Measures:** Total commits by contributor type

**Calculation:** Count of commits per category

**Chart Type:** Horizontal bar chart with percentage labels

**Interpretation:**
- Similar to attribution pie chart but shows counts
- Easier to compare absolute numbers
- Percentages shown in tooltips

### 4. AI Review Impact Metrics

#### Review Coverage

**Measures:** Percentage of PRs receiving AI code review

**Calculation:** (PRs with AI review comments / Total PRs) × 100

**Data Source:** GitHub API PR comments from Claude Code Review bot

**Target:** 80%+ coverage

**Chart Type:** Line chart showing coverage percentage per week over last 12 weeks

**Interpretation:**
- Higher is better
- Low coverage suggests reviews not triggered or skipped
- 100% may be excessive for trivial PRs

#### Suggestions Per PR (Histogram)

**Measures:** Distribution of AI suggestions across PRs

**Buckets:**
- 0-2 suggestions
- 3-5 suggestions
- 6-10 suggestions
- 11-20 suggestions
- 20+ suggestions

**Chart Type:** Bar chart histogram

**Interpretation:**
- Most PRs should have 3-10 suggestions
- Too few = reviews not thorough or code already excellent
- Too many = code quality issues or overly strict reviews

#### Acceptance Rate Trend

**Measures:** Percentage of AI suggestions acted upon

**Calculation:** Heuristic based on commits within 24h of review

**Data Source:** GitHub API commit timestamps after review comments

**Target:** 70%+ acceptance

**Chart Type:** Line chart showing acceptance percentage over last 20 reviews

**Interpretation:**
- Higher is better (with caveats)
- Very low = AI suggestions not helpful or too nitpicky
- Very high = developers accepting blindly without thinking
- Sweet spot: 60-80%

#### Response Time Distribution (Histogram)

**Measures:** Time from PR creation to first AI review

**Buckets:**
- < 1 hour
- 1-4 hours
- 4-8 hours
- 8-24 hours
- > 24 hours

**Chart Type:** Bar chart histogram

**Interpretation:**
- Faster is better for developer experience
- Most should be < 1 hour (automated reviews)
- Delays suggest CI/CD issues or API rate limits

## Theme System

### Dark Mode (Default)

**When to Use:**
- Daily development work
- Low-light environments
- Reduces eye strain
- Professional appearance for demos

**Colors:**
- Background: Dark charcoal (#121212)
- Text: White (#FFFFFF)
- Surface: Slightly lighter (#1E1E1E)
- Accents: Purple (#7823DC)

### Light Mode

**When to Use:**
- Client presentations
- Printed materials
- High-contrast projectors
- Bright environments

**Activation:**
- Click "Light Mode" button in header
- Theme preference saved to browser localStorage

**Colors:**
- Background: White (#FFFFFF)
- Text: Dark charcoal (#1E1E1E)
- Surface: Light gray (#F5F5F5)
- Accents: Purple (#7823DC)

### Theme Persistence

Theme preference is automatically saved and restored:
```javascript
// Saved to localStorage: theme = "dark" or "light"
// Restored on page load
// Synced across browser tabs (same origin)
```

## Export Features

### CSV Export

**Button:** "Export Data" in header

**Output File:** `metrics_export_YYYY-MM-DD.csv`

**Contents:** All current metric values with:
- Date (YYYY-MM-DD)
- Metric Category (DORA, GitHub, Contributions, AI Review)
- Metric Name
- Value
- Unit (%, hours, count, deploys/week)

**CSV Structure:**
```csv
Date,Metric Category,Metric Name,Value,Unit
2025-11-07,DORA,Total Deployments,45,count
2025-11-07,DORA,Deployment Frequency,2.5,deploys/week
2025-11-07,DORA,Median Lead Time,4.2,hours
...
```

**Encoding:** UTF-8 with BOM for Excel compatibility

**Use Cases:**
- Import to Excel/Google Sheets for custom analysis
- Share data with stakeholders
- Archive historical metrics
- Create pivot tables and custom charts

### PNG Export

**Button:** "Download" on each chart (appears on hover)

**Output File:** `{metric_name}_YYYY-MM-DD.png`

**Resolution:** 1200x800px (presentation-ready)

**Background:** Matches current theme:
- Dark mode: `rgba(26, 26, 26, 1)`
- Light mode: `rgba(255, 255, 255, 1)`

**Quality:** High-resolution PNG with embedded background

**Use Cases:**
- Add to PowerPoint presentations
- Include in Word documents or PDFs
- Share via email or Slack
- Create executive dashboards

## Data Collection

### Manual Collection

Run metrics collectors individually:

```bash
# DORA metrics (last 30 days)
python -m src.orchestrator.metrics.dora_metrics --days 30

# AI contribution analysis (last 30 days)
python -m src.orchestrator.metrics.contribution_analyzer --days 30

# AI review impact (last 30 days)
python -m src.orchestrator.metrics.ai_review_impact --days 30

# GitHub collaboration (last 30 days)
python -m src.orchestrator.metrics.github_metrics --days 30

# Aggregate all metrics (last 4 weeks)
python -m src.orchestrator.metrics.aggregator --weeks 4
```

### Automated Collection

**Workflow:** `.github/workflows/metrics-collection.yml`

**Triggers:**
- Push to main branch
- PR merged to main
- Daily at 9:00 AM UTC
- Manual workflow dispatch

**Output:** JSON files in `.claude/metrics/` directory:
```
.claude/metrics/
├── dora/
│   ├── deployments.json
│   ├── lead_time.json
│   ├── mttr.json
│   └── change_failure_rate.json
├── github/
│   ├── pull_requests.json
│   ├── conflicts.json
│   └── velocity.json
├── contributions/
│   └── attribution.json
├── ai_review/
│   └── impact.json
└── aggregated/
    ├── weekly_summary.json
    ├── monthly_summary.json
    └── trends.json
```

### Data Refresh

Dashboard loads data from JSON files on every page load. To update metrics:

1. **Automatic:** Wait for scheduled collection (daily at 9am UTC)
2. **Manual:** Run collection scripts
3. **Trigger:** Run GitHub Actions workflow manually

Then refresh dashboard page.

## Troubleshooting

### Dashboard Shows "No data available"

**Cause:** Metrics haven't been collected yet

**Solution:**
```bash
# Run all collectors
python -m src.orchestrator.metrics.dora_metrics --days 30
python -m src.orchestrator.metrics.contribution_analyzer --days 30
python -m src.orchestrator.metrics.ai_review_impact --days 30
python -m src.orchestrator.metrics.aggregator --weeks 4

# Refresh dashboard
```

**Check:** Verify JSON files exist in `.claude/metrics/` directory

### Charts Not Loading

**Cause:** JSON files missing or corrupted

**Symptoms:** Console errors like "Failed to load .claude/metrics/dora/deployments.json"

**Solution:**
1. Open browser console (F12)
2. Check for fetch errors
3. Verify JSON files are valid:
```bash
# Validate JSON
cat .claude/metrics/dora/deployments.json | python -m json.tool
```
4. Re-run metrics collection if invalid

### Theme Toggle Not Working

**Cause:** localStorage blocked by browser

**Solution:**
1. Check browser privacy settings
2. Allow localStorage for file:// protocol
3. Try different browser (Chrome recommended)
4. Clear browser cache and reload

### Export Buttons Not Visible

**Cause:** CSS not loaded or browser compatibility

**Solution:**
1. Hover slowly over chart cards (buttons appear on :hover)
2. Check browser console for CSS errors
3. Try different browser (Chrome, Firefox, Safari, Edge supported)
4. Clear browser cache

### CSV Won't Open in Excel

**Cause:** Encoding issue or Excel version

**Solution:**
1. Use Excel's "Data → From Text/CSV" import feature
2. Select UTF-8 encoding
3. Alternatively, open in Google Sheets first
4. File includes UTF-8 BOM specifically for Excel compatibility

### PNG Export Has Wrong Background

**Cause:** Theme mismatch

**Solution:**
1. Switch to desired theme before exporting
2. Dark mode = dark background PNG
3. Light mode = white background PNG
4. Charts render with current theme's background

## Best Practices

### Regular Review

- **Weekly:** Review automated email reports
- **Bi-weekly:** Check dashboard for trends
- **Monthly:** Export CSV for deeper analysis
- **Quarterly:** Present metrics to stakeholders

### Data Interpretation

**Week-over-Week Changes:**
- More meaningful than absolute values
- Look for sustained trends, not single-week spikes
- Small fluctuations (<10%) are normal

**Benchmarking:**
- Compare against DORA industry benchmarks
- Track progress toward Elite ratings
- Set team goals based on current performance

**Anomalies:**
- Investigate sudden spikes or drops
- Check for external factors (holidays, team changes)
- Review commit history for context

### Presentations

**On-Screen:**
- Use dark mode for aesthetic appeal
- Higher contrast in low-light rooms
- Professional appearance

**Printed Materials:**
- Use light mode for better printing
- Higher contrast on white paper
- Reduces ink usage

**PowerPoint:**
1. Export charts as PNG
2. Insert into slides
3. Resize to fit slide layout
4. Add title and context text
5. Include data source footnote

**Reports:**
1. Export CSV for detailed tables
2. Export key charts as PNG
3. Create Word/PDF document
4. Include interpretation and recommendations

### Privacy & Security

**Dashboard:**
- Uses local files only (no external data transmission)
- Safe to share screenshots (no PII)
- No authentication required for local access

**Email Reports:**
- Contain aggregated data only
- No source code included
- No individual developer metrics
- Safe to forward to management

**GitHub Pages (if deployed):**
- Metrics are public if repo is public
- Consider private repo for sensitive data
- Or restrict to private GitHub Pages deployment

## Advanced Usage

### Custom Time Ranges

Edit collector commands to adjust time windows:

```bash
# Last 60 days
python -m src.orchestrator.metrics.dora_metrics --days 60

# Last 12 weeks
python -m src.orchestrator.metrics.aggregator --weeks 12
```

### Filtering Data

Modify JSON files directly to filter data (advanced):

```bash
# Example: Filter to specific date range
cat .claude/metrics/dora/deployments.json | \
  jq '.deployments |= map(select(.timestamp >= "2025-01-01"))' > temp.json
mv temp.json .claude/metrics/dora/deployments.json
```

### Programmatic Access

Access metrics data programmatically:

```python
import json
from pathlib import Path

# Load DORA deployments
with open('.claude/metrics/dora/deployments.json') as f:
    data = json.load(f)

# Extract summary
summary = data['summary']
print(f"DORA Rating: {summary['rating']}")
print(f"Deploys/Week: {summary['deploys_per_week']}")
```

### Integration with Other Tools

Export CSV to:
- **Tableau/Power BI:** Custom dashboards
- **Jira:** Link metrics to sprints
- **Slack:** Share PNG charts in channels
- **Confluence:** Embed in team documentation

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `T` | Toggle theme |
| `E` | Export CSV |
| `R` | Refresh page |
| `H` | Show/hide help |

*Note: Shortcuts require dashboard to have focus*

## Support

For issues or questions:

1. **Dashboard Issues:** Check browser console for errors
2. **Data Collection:** Review GitHub Actions workflow logs
3. **Export Problems:** Verify browser compatibility
4. **Questions:** Consult this guide or EMAIL_NOTIFICATION_SETUP.md

## Related Documentation

- [Metrics Export Guide](METRICS_EXPORT_GUIDE.md) - Detailed export instructions
- [Email Notification Setup](EMAIL_NOTIFICATION_SETUP.md) - Configure automated reports
- [Design System Audit](DESIGN_SYSTEM_AUDIT.md) - Kearney branding standards
