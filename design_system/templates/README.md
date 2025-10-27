# C-Suite Presentation Templates

Production-ready HTML templates for executive communications, following Kearney brand standards and proven C-suite communication frameworks.

## Overview

This directory contains two template types optimized for different executive communication needs:

1. **`presentation.html`** - Interactive scrollytelling presentation for meetings and screen sharing
2. **`one-pager.html`** - Executive summary document optimized for printing and PDF distribution

Both templates are:
- **Brand-compliant** (Kearney purple, Arial font, NO gridlines, NO emojis)
- **Framework-driven** (RAISE insights, SCR structure, label-first charts)
- **Production-ready** (No build process, works standalone in any browser)
- **Domain-agnostic** (Placeholder content adaptable to any industry/project)

---

## Template Comparison

| Feature | `presentation.html` | `one-pager.html` |
|---------|---------------------|------------------|
| **Use Case** | Live presentations, meetings, webinars | Email attachments, printed handouts, quick reference |
| **Format** | Multi-slide scrollytelling (5 sections) | Single-page executive summary |
| **Interactivity** | Animated charts, scroll navigation, fade-ins | Static content, print-optimized |
| **Length** | 10-15 minutes presentation | 3-5 minutes read |
| **Delivery** | Screen sharing, laptop, tablet | PDF export, printed document |
| **Charts** | 4 interactive D3.js visualizations | Tables and compact KPI dashboard |
| **Framework** | Problem → Analysis → Solution → Action | Situation-Complication-Resolution (SCR) |
| **Best For** | Steering committees, board meetings, deep dives | Executive approvals, quick decisions, email distribution |

---

## When to Use Each Template

### Use `presentation.html` When:
- **Presenting live** to executive audience (in-person or virtual)
- **Deep dive** is needed on analysis and recommendations
- **Visual storytelling** will enhance understanding (trends, comparisons, timelines)
- **Interaction expected** (questions during presentation, back-and-forth discussion)
- **Screen sharing** or projector available
- **Example scenarios:**
  - Quarterly business review with C-suite
  - Transformation program kickoff
  - Investment decision committee meeting
  - Strategy offsite presentation

### Use `one-pager.html` When:
- **Executive approval needed quickly** (1-2 day turnaround)
- **Email distribution** to multiple stakeholders
- **Printed handout** for board meetings or executive briefings
- **Pre-read** before live presentation
- **Decision memo** format required
- **Example scenarios:**
  - Budget approval request
  - Project charter approval
  - Executive steering committee pre-read
  - Investment committee memo
  - CEO weekly update

---

## Kearney Brand Compliance Checklist

Before finalizing any C-suite deliverable, validate against these mandatory brand standards:

### Typography
- ✅ **Arial font family** used throughout (Kearney standard for presentations)
  - **Note**: Inter is used for web applications, NOT presentations
- ✅ **NO emojis** in professional content
- ✅ **Consistent hierarchy** (h1 > h2 > h3 > body text)
- ✅ **Readable font sizes** (minimum 11pt for print, 16px for screen)

### Color Palette
- ✅ **Kearney purple (#7823DC)** as primary accent color
- ✅ **NO green** for positive metrics (use purple per brand guidelines)
- ✅ **Charcoal/grey text** (#1E1E1E) for body copy, not pure black
- ✅ **Consistent color usage** (purple for emphasis, grey for data, red for negative)

### Charts & Data Visualization
- ✅ **NO GRIDLINES** on charts (mandatory Kearney standard)
- ✅ **Label-first approach**: Title ABOVE chart, not below
- ✅ **Clear axis labels** with units specified
- ✅ **Legend** included when multiple data series present
- ✅ **Data source** cited in caption below chart
- ✅ **Simple, clean design** (avoid 3D effects, excessive colors, decorative elements)

### Content Structure
- ✅ **RAISE framework** applied to key insights:
  - **Relevant**: Tied to business objectives
  - **Actionable**: Clear next steps
  - **Insightful**: Non-obvious findings
  - **Supported**: Data-backed claims
  - **Engaging**: Compelling narrative
- ✅ **Executive summary first** (key insight upfront, not buried)
- ✅ **Logical flow**: Problem → Analysis → Solution → Action
- ✅ **Quantified impact** ($X savings, Y% improvement, Z months timeline)

### Layout & Design
- ✅ **White space** used effectively (not cluttered)
- ✅ **Consistent alignment** (left-aligned text, centered headings)
- ✅ **Professional imagery** (no clipart, stock photos used sparingly)
- ✅ **Print-friendly** (works on black-and-white printer)
- ✅ **Accessible** (sufficient contrast, readable text sizes)

---

## Customizing Templates

### Step 1: Copy Template
```bash
# Copy the template you need
cp design_system/templates/c-suite/presentation.html my-project/executive-presentation.html
# OR
cp design_system/templates/c-suite/one-pager.html my-project/executive-summary.html

# Copy shared styles
cp design_system/templates/c-suite/styles.css my-project/
```

### Step 2: Replace Placeholder Content

All templates use bracketed placeholders like `[Client Name]`, `[Date]`, `$X million`. Search and replace:

```bash
# Find all placeholders
grep -o '\[.*?\]' my-project/executive-presentation.html

# Common placeholders to replace:
# [Client Name] → "Acme Corporation"
# [Date] → "October 26, 2024"
# $X million → "$15 million"
# Y months → "18 months"
# [Project Name] → "Digital Transformation Initiative"
```

**Key content sections to customize:**

**For `presentation.html`:**
- Slide 1: Hero title and key insight
- Slide 2: Current state KPIs and trend data
- Slide 3: Root cause analysis and breakdown
- Slide 4: Strategic recommendations and initiatives
- Slide 5: Implementation timeline and next steps

**For `one-pager.html`:**
- Header: Client name, date, project title
- Situation: Current state and performance metrics
- Complication: Why this matters and urgency drivers
- Resolution: Recommended actions and decision framework
- Next Steps: Timeline and immediate actions

### Step 3: Update Data in Charts

Charts use inline JavaScript with sample data arrays. Update the data to reflect your analysis:

**Example: Updating trend chart data in `presentation.html`**

```javascript
// Find this section in the <script> tag:
const data = [
  { month: 'Jan 23', efficiency: 78, cost: 100 },
  { month: 'Feb 23', efficiency: 76, cost: 102 },
  // ... add your actual data points
];
```

**Chart data locations:**
- **Trend Chart**: `createTrendChart()` function → `data` array
- **Waterfall Chart**: `createWaterfallChart()` function → `data` array
- **Bubble Chart**: `createBubbleChart()` function → `data` array
- **Gantt Chart**: `createGanttChart()` function → `tasks` array

### Step 4: Apply Client Theme (Optional)

If client has custom brand colors or fonts (see `clients/[client-name]/governance.yaml`):

```html
<!-- Add after the <link rel="stylesheet" href="styles.css"> -->
<style>
  :root {
    /* Override with client colors */
    --color-primary: #0066CC; /* Client brand color */
    --color-accent: #3385D6;

    /* Override font if needed (rare - most clients accept Arial) */
    --font-family-presentation: 'Client Font', Arial, sans-serif;
  }
</style>
```

**Common client theme overrides:**
- Primary accent color (corporate brand color)
- Logo in header (add `<img src="logo.svg">`)
- Custom font (only if client requires and font is available)
- Color restrictions (avoid competitor colors - see governance.yaml)

### Step 5: Test and Validate

**Browser testing:**
```bash
# Open in default browser
open my-project/executive-presentation.html

# Test in multiple browsers (Chrome, Safari, Firefox)
# Ensure charts render correctly and animations work
```

**Print testing:**
```bash
# Print to PDF (Cmd+P or Ctrl+P)
# Verify:
# - Content fits on pages without awkward breaks
# - Charts are readable in black-and-white
# - All text is legible at print resolution
# - Footer/header information displays correctly
```

**Brand compliance:**
```bash
# Run through checklist above
# Common issues:
# - Forgot to remove emojis from source data
# - Charts have gridlines (check D3.js code)
# - Using green for positive metrics (should be purple)
# - Font not Arial (check CSS overrides)
```

---

## D3.js Chart Patterns

All charts follow these patterns to ensure brand compliance and clarity.

### Pattern 1: Line Chart (Trend Analysis)

**Use when:** Showing performance over time, before/after comparisons, forecasts

**Best practices:**
- NO GRIDLINES (Kearney standard)
- Label-first: Title ABOVE chart
- Clear axis labels with units
- Legend for multiple lines
- Data source in caption

**Example:**
```javascript
const createLineChart = () => {
  // Sample data structure
  const data = [
    { date: '2023-01', value: 100 },
    { date: '2023-02', value: 105 },
    // ...
  ];

  // Scales
  const x = d3.scaleTime()
    .domain(d3.extent(data, d => new Date(d.date)))
    .range([0, innerWidth]);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .range([innerHeight, 0]);

  // Axes (NO GRIDLINES)
  g.append('g')
    .attr('class', 'axis')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x));

  g.append('g')
    .attr('class', 'axis')
    .call(d3.axisLeft(y));

  // Line
  const line = d3.line()
    .x(d => x(new Date(d.date)))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX); // Smooth curve

  g.append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-chart-primary)')
    .attr('stroke-width', 3)
    .attr('d', line);
};
```

### Pattern 2: Bar Chart (Comparisons)

**Use when:** Comparing categories, showing rankings, discrete comparisons

**Best practices:**
- Horizontal bars for long category names
- Consistent bar color (purple) unless showing positive/negative
- Value labels on bars for precise readability
- Sort by value (descending) unless logical order exists

**Example:**
```javascript
const createBarChart = () => {
  const data = [
    { category: 'Process A', value: 85 },
    { category: 'Process B', value: 72 },
    // ...
  ].sort((a, b) => b.value - a.value); // Sort descending

  const x = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .range([0, innerWidth]);

  const y = d3.scaleBand()
    .domain(data.map(d => d.category))
    .range([0, innerHeight])
    .padding(0.2);

  // Bars
  g.selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', 0)
    .attr('y', d => y(d.category))
    .attr('width', d => x(d.value))
    .attr('height', y.bandwidth())
    .attr('fill', 'var(--color-chart-primary)');

  // Value labels
  g.selectAll('.label')
    .data(data)
    .enter()
    .append('text')
    .attr('x', d => x(d.value) + 5)
    .attr('y', d => y(d.category) + y.bandwidth() / 2)
    .attr('dominant-baseline', 'central')
    .text(d => d.value);
};
```

### Pattern 3: Waterfall Chart (Decomposition)

**Use when:** Breaking down a total into components, showing cumulative effect, bridge from baseline to target

**Best practices:**
- Start with baseline, end with total
- Use connecting lines between bars
- Color code: Grey for baseline/total, purple for increases, red for decreases
- Label each bar with value

**Example:** See `createWaterfallChart()` in `presentation.html` for complete implementation.

### Pattern 4: Bubble/Scatter Chart (Two-Dimensional Analysis)

**Use when:** Comparing items across two dimensions (e.g., impact vs. effort), portfolio analysis, priority matrices

**Best practices:**
- Bubble size represents third dimension (value, importance)
- Quadrant lines to show decision zones
- Color code by category or priority
- Label bubbles directly (not in legend)

**Example:** See `createBubbleChart()` in `presentation.html` for complete implementation.

---

## RAISE Framework Validation

Every insight and recommendation should pass the RAISE test. Use this checklist:

### ✅ Relevant
- [ ] Tied to client's strategic objectives
- [ ] Addresses a pain point the executive cares about
- [ ] Timing is appropriate (not too early or too late)
- [ ] Audience has authority to act on the insight

**Example:**
- ❌ "Data quality issues detected" (vague, no business impact)
- ✅ "Data quality issues are causing $2M in annual revenue leakage, threatening Q4 targets"

### ✅ Actionable
- [ ] Clear next steps provided
- [ ] Recommendations are specific (not "improve X")
- [ ] Timeline included
- [ ] Accountability assigned or suggested
- [ ] Resource requirements specified

**Example:**
- ❌ "Consider improving efficiency" (vague)
- ✅ "Implement automated workflow in Process A by Q2 2025 (6-month project, 3 FTE, $1.2M investment)"

### ✅ Insightful
- [ ] Non-obvious finding (not just reporting metrics)
- [ ] Reveals underlying pattern or root cause
- [ ] Challenges assumptions or conventional wisdom
- [ ] Provides "aha moment" for audience

**Example:**
- ❌ "Sales declined 10% last quarter" (reporting a fact)
- ✅ "Sales decline is concentrated in 3 of 12 regions, driven by competitor's new pricing strategy—remaining 9 regions are growing 5%"

### ✅ Supported
- [ ] Backed by quantitative data
- [ ] Sample size is sufficient
- [ ] Data source is credible
- [ ] Analysis methodology is sound
- [ ] Confidence level stated (if statistical)

**Example:**
- ❌ "Customers prefer Option A" (no evidence)
- ✅ "87% of surveyed customers (n=450) prefer Option A, with 95% confidence interval [83%, 91%]"

### ✅ Engaging
- [ ] Compelling narrative (not just bullet points)
- [ ] Visual elements support the story
- [ ] Language is crisp and jargon-free
- [ ] Key insight stated upfront (not buried)
- [ ] Emotional resonance (urgency, opportunity, risk)

**Example:**
- ❌ "Efficiency metrics indicate suboptimal performance relative to benchmarks"
- ✅ "We're leaving $15M on the table annually—our efficiency is 35% below industry leaders, putting market position at risk"

---

## Common Pitfalls & How to Avoid Them

### Pitfall 1: Burying the Insight

**Symptom:** Key finding appears on slide 15, after background and methodology.

**Fix:** Use pyramid structure—start with the answer, then provide supporting evidence.

**Example:**
```
❌ BAD STRUCTURE:
1. Background and context
2. Methodology overview
3. Data analysis
4. Findings
5. Key insight (finally!)

✅ GOOD STRUCTURE:
1. Key insight upfront ("$15M opportunity through 3 initiatives")
2. Current state (why this matters)
3. Root cause analysis (how we know)
4. Recommended solution (what to do)
5. Implementation plan (how to get started)
```

### Pitfall 2: Death by Data

**Symptom:** 47 metrics, 12 charts, overwhelming detail, no clear message.

**Fix:** Use "Rule of Three"—3 key metrics, 3 root causes, 3 recommendations.

**Example:**
```
❌ TOO MUCH:
- 12 KPIs on dashboard
- 8 different root causes
- 15 potential initiatives

✅ FOCUSED:
- 3 critical KPIs (efficiency, cost, cycle time)
- 3 primary root causes (56%, 28%, 16% of gap)
- 3 prioritized initiatives (high, medium, low)
```

### Pitfall 3: Vague Recommendations

**Symptom:** "Improve efficiency," "Optimize processes," "Leverage technology."

**Fix:** Specify WHAT, HOW, WHEN, HOW MUCH.

**Example:**
```
❌ VAGUE:
"Recommendation: Improve operational efficiency through process optimization"

✅ SPECIFIC:
"Redesign Order-to-Cash process (eliminate 4 approval steps, automate invoice matching)
→ Timeline: 6 months
→ Investment: $1.2M
→ Impact: $8M annual savings, 18 ppt efficiency gain
→ Owner: VP Operations"
```

### Pitfall 4: Lack of Urgency

**Symptom:** Recommendations feel optional, no compelling reason to act now.

**Fix:** Articulate the complication—what happens if we DON'T act?

**Example:**
```
❌ NO URGENCY:
"We could improve efficiency by implementing these initiatives."

✅ URGENCY:
"Without action, we'll face:
- $45M in cumulative losses over 3 years
- Legacy system end-of-life in 18 months (forced migration)
- Competitor gaining 15% market share advantage
- Contract renewals at risk due to SLA misses

→ Window to act is narrowing. Delays increase cost and complexity."
```

### Pitfall 5: Not Brand Compliant

**Symptom:** Gridlines on charts, green used for positive metrics, emoji in text, Comic Sans (please no).

**Fix:** Run through brand compliance checklist before finalizing.

**Common violations:**
```
❌ BRAND VIOLATIONS:
- Chart gridlines present
- Green for positive change (should be purple)
- Emoji in executive summary (🚀 ⚠️)
- Non-Arial font
- Kearney logo misused

✅ BRAND COMPLIANT:
- NO gridlines on any chart
- Purple (#7823DC) for positive metrics
- NO emoji anywhere
- Arial font throughout
- Kearney logo per brand guidelines (if used)
```

### Pitfall 6: Not Print-Friendly

**Symptom:** Prints across 14 pages, charts unreadable, white text on dark background, colors become grey mush.

**Fix:** Test print to PDF, ensure black-and-white readability.

**Print optimization:**
```css
@media print {
  /* Remove backgrounds that waste ink */
  .hero, .callout {
    background-color: white;
    border: 1px solid var(--color-border);
  }

  /* Ensure all text is dark */
  body { color: black; }

  /* Avoid page breaks inside elements */
  .chart-container {
    page-break-inside: avoid;
  }

  /* Hide interactive elements */
  .btn { display: none; }
}
```

---

## Accessibility Considerations

C-suite presentations should be accessible to all executives, including those with visual impairments or color blindness.

### Color Contrast
- ✅ Text has minimum 4.5:1 contrast ratio against background
- ✅ Charts use color + pattern/texture (not color alone)
- ✅ Works in greyscale (test by printing black-and-white)

### Font Legibility
- ✅ Minimum 11pt font for print
- ✅ Minimum 16px font for screen
- ✅ No light grey text on white background (fails contrast)
- ✅ Adequate line spacing (1.5x for body text)

### Alternative Text
- ✅ Charts have text descriptions (caption or alt text)
- ✅ Key data points stated in text (not just visualized)
- ✅ Tables used as alternative to charts when appropriate

### Keyboard Navigation
- ✅ All interactive elements accessible via Tab key
- ✅ Logical tab order (top to bottom, left to right)
- ✅ No keyboard traps

---

## Exporting to PDF

Both templates support high-quality PDF export for distribution.

### Method 1: Browser Print (Recommended)

1. Open template in Chrome, Safari, or Firefox
2. Press `Cmd+P` (Mac) or `Ctrl+P` (Windows)
3. Select "Save as PDF" as destination
4. Settings:
   - **Layout:** Portrait (for `one-pager.html`), Landscape optional for `presentation.html`
   - **Margins:** Default or None
   - **Background graphics:** ON (ensures colors print)
   - **Scale:** 100% (don't shrink to fit)
5. Save to desired location

**Result:** High-quality, vector-based PDF with selectable text.

### Method 2: Command-Line (Automated Workflows)

Use headless Chrome for batch PDF generation:

```bash
# Install puppeteer (Node.js)
npm install puppeteer

# Generate PDF via script
node generate-pdf.js my-project/executive-summary.html output.pdf
```

**generate-pdf.js:**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.argv[2], { waitUntil: 'networkidle0' });
  await page.pdf({
    path: process.argv[3],
    format: 'Letter',
    printBackground: true,
    margin: { top: '0.5in', right: '0.5in', bottom: '0.5in', left: '0.5in' }
  });
  await browser.close();
})();
```

### Method 3: Presentation Software (Last Resort)

If client requires PowerPoint format:

1. Export each slide as PNG (screenshot)
2. Import PNGs into PowerPoint template
3. Add presenter notes

**Note:** This is lossy (raster images) and time-consuming. Prefer HTML/PDF delivery when possible.

---

## Version Control Best Practices

Templates evolve throughout project lifecycle. Follow these practices:

### File Naming Convention
```
executive-summary-v1.0-draft.html        # Initial draft
executive-summary-v1.1-draft.html        # After first review
executive-summary-v2.0-client-review.html # Sent to client
executive-summary-v2.1-final.html        # Approved version
```

### Git Commit Messages
```bash
git add executive-summary.html
git commit -m "docs: update exec summary with Q3 financials

- Updated KPI dashboard with Q3 actuals
- Revised timeline based on tech team feedback
- Added risk mitigation for resource constraints

Status: Ready for client review"
```

### Archive Old Versions
```bash
# Create archive folder
mkdir archive/

# Move superseded versions
mv executive-summary-v1.*.html archive/

# Keep only current and previous version in main directory
```

---

## Integration with Client Governance

Templates can be customized based on client-specific governance requirements (see `clients/[client-name]/governance.yaml`).

### Brand Constraints
```yaml
# clients/acme-corp/governance.yaml
brand_constraints:
  theme_path: "clients/acme-corp/theme.json"
  custom_fonts: ["Acme Sans"]
  color_restrictions: ["#FF0000"]  # Competitor red
  logo_path: "clients/acme-corp/logo.svg"
  forbid_terms: ["legacy", "outdated"]
  presentation_template: "clients/acme-corp/template.pptx"
```

**Apply to templates:**
```html
<style>
  :root {
    /* Load Acme brand colors from theme.json */
    --color-primary: #0066CC; /* Acme blue */
    --font-family-presentation: 'Acme Sans', Arial, sans-serif;
  }
</style>
```

### Documentation Requirements
```yaml
# clients/acme-corp/governance.yaml
documentation:
  require_disclaimers: true
  language: "en"
```

**Apply to templates:**
```html
<div class="footer">
  <p>This document is confidential and proprietary to Acme Corporation and Kearney.
  Do not distribute without written authorization.</p>
</div>
```

---

## Troubleshooting

### Charts Not Rendering

**Symptom:** Blank space where chart should be.

**Causes:**
1. D3.js library not loaded (check CDN link)
2. Data format incorrect (check console for errors)
3. Container dimensions not set (check CSS)

**Fix:**
```javascript
// Check browser console for errors (F12 → Console tab)
// Common errors:
// "d3 is not defined" → CDN link broken
// "Cannot read property 'append' of null" → Container ID mismatch

// Ensure container has dimensions:
.chart-wrapper {
  width: 100%;
  height: 400px; /* REQUIRED */
}
```

### Print Layout Broken

**Symptom:** Content spills across multiple pages awkwardly.

**Causes:**
1. Page break inside chart or table
2. Content taller than page height
3. Margins not set

**Fix:**
```css
@media print {
  /* Prevent page breaks inside elements */
  .chart-container,
  .metric-card,
  table {
    page-break-inside: avoid;
  }

  /* Force page break before major sections */
  .scr-section {
    page-break-before: auto;
  }
}
```

### Fonts Not Displaying

**Symptom:** Fallback font (Times New Roman) used instead of Arial.

**Causes:**
1. Arial not installed (rare—Arial is system font)
2. Font override in client CSS
3. Browser issue

**Fix:**
```css
/* Check computed font in browser DevTools */
/* Ensure Arial is first in fallback chain */
body {
  font-family: Arial, 'Helvetica Neue', Helvetica, sans-serif;
}
```

### Colors Look Wrong

**Symptom:** Purple looks blue, or colors are muted.

**Causes:**
1. Monitor calibration
2. CSS variable not defined
3. Print color adjust not set

**Fix:**
```css
/* Ensure CSS variables defined in :root */
:root {
  --color-primary: #7823DC;
}

/* For print, ensure colors preserved */
@media print {
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
```

---

## Examples Gallery

### Example 1: Quarterly Business Review
**Template:** `presentation.html`
**Customization:**
- Updated all KPIs with Q3 actuals
- Replaced trend chart with quarterly comparison
- Added "What's Changed" section to hero
- Removed bubble chart, added customer segmentation

### Example 2: Investment Committee Memo
**Template:** `one-pager.html`
**Customization:**
- Expanded "Decision Required" section
- Added financial projections table
- Included risk/return matrix
- Shortened next steps to 3 bullets

### Example 3: Transformation Steering Committee Update
**Template:** `presentation.html`
**Customization:**
- Gantt chart updated with actual progress vs. plan
- Added "Risks & Mitigations" slide (new slide 4)
- Dashboard shows project health (green/yellow/red)
- Next steps include specific action items with owners

---

## Further Resources

### Kearney Brand Guidelines
- **Presentation Standards:** See internal Kearney portal for PowerPoint templates and guidelines
- **Color Palette:** `design_system/web/tokens.css` for complete Kearney color system
- **Typography:** Arial for presentations, Inter for web applications

### D3.js Documentation
- **Official Docs:** https://d3js.org/
- **Examples Gallery:** https://observablehq.com/@d3/gallery
- **Tutorials:** https://www.d3-graph-gallery.com/

### C-Suite Communication Best Practices
- **Pyramid Principle:** Barbara Minto's framework for executive communication
- **SCQA Framework:** Situation-Complication-Question-Answer structure
- **RAISE Framework:** Kearney's standard for insights quality (Relevant, Actionable, Insightful, Supported, Engaging)

### Accessibility Standards
- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/
- **Color Contrast Checker:** https://webaim.org/resources/contrastchecker/
- **Accessibility Checklist:** https://www.a11yproject.com/checklist/

---

## Contributing

Found a bug or have a suggestion? Follow these steps:

1. **Document the issue:**
   - What template (presentation.html or one-pager.html)?
   - What's the expected vs. actual behavior?
   - Can you reproduce it consistently?
   - Screenshot if visual issue

2. **Propose a fix:**
   - Fork the template
   - Make your changes
   - Test in multiple browsers (Chrome, Safari, Firefox)
   - Validate against brand compliance checklist

3. **Submit for review:**
   - Create detailed PR description
   - Include before/after screenshots
   - Explain rationale for changes
   - Tag relevant stakeholders

### Template Enhancement Ideas
- Slide transition animations (subtle, professional)
- Print-optimized appendix section
- Multi-language support (FR, DE, ES)
- Dark mode variant (for screen viewing only)
- Mobile-responsive improvements

---

**Last Updated:** 2025-01-26
**Maintained by:** Kearney Data & Analytics Team
**Questions?** Contact design-system@kearney.com
