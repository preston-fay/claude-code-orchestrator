---
sidebar_position: 2
title: Typography
---

# Typography

Typography system for the Kearney Data Platform.

## Brand Guidelines

### Critical Rules

1. **NO ALL CAPS headings** - Use sentence case or title case instead
2. **Semibold (600) for emphasis** - Avoid bold (700) except for critical alerts
3. **Inter with fallback** - Always include Arial and system font fallbacks
4. **Generous line height** - Use `normal` (1.5) for body text, minimum

### Heading Case Styles

**Correct:**
- Sentence case: "Platform health scorecard"
- Title case: "Platform Health Scorecard"

**Incorrect:**
- All caps: ~~"PLATFORM HEALTH SCORECARD"~~
- No fallback: ~~"Inter, sans-serif"~~ (missing Arial)

---

## Font Family

Primary: `Inter, Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif`

Monospace: `'SF Mono', 'Roboto Mono', 'Courier New', monospace`

## Font Weights

<table>
  <thead><tr><th>Name</th><th>Value</th><th>Preview</th></tr></thead>
  <tbody>
    <tr><td><code>light</code></td><td><code>300</code></td><td style="font-weight: 300;">The quick brown fox</td></tr>
    <tr><td><code>regular</code></td><td><code>400</code></td><td style="font-weight: 400;">The quick brown fox</td></tr>
    <tr><td><code>medium</code></td><td><code>500</code></td><td style="font-weight: 500;">The quick brown fox</td></tr>
    <tr><td><code>semibold</code></td><td><code>600</code></td><td style="font-weight: 600;">The quick brown fox</td></tr>
    <tr><td><code>bold</code></td><td><code>700</code></td><td style="font-weight: 700;">The quick brown fox</td></tr>
  </tbody>
</table>

## Type Scale

Base size: 16px

Ratio: 1.25

<table>
  <thead><tr><th>Size</th><th>Value</th><th>Preview</th></tr></thead>
  <tbody>
    <tr><td><code>xs</code></td><td><code>0.64rem</code></td><td style="font-size: 0.64rem;">Aa</td></tr>
    <tr><td><code>sm</code></td><td><code>0.8rem</code></td><td style="font-size: 0.8rem;">Aa</td></tr>
    <tr><td><code>base</code></td><td><code>1rem</code></td><td style="font-size: 1rem;">Aa</td></tr>
    <tr><td><code>md</code></td><td><code>1.25rem</code></td><td style="font-size: 1.25rem;">Aa</td></tr>
    <tr><td><code>lg</code></td><td><code>1.563rem</code></td><td style="font-size: 1.563rem;">Aa</td></tr>
    <tr><td><code>xl</code></td><td><code>1.953rem</code></td><td style="font-size: 1.953rem;">Aa</td></tr>
    <tr><td><code>2xl</code></td><td><code>2.441rem</code></td><td style="font-size: 2.441rem;">Aa</td></tr>
    <tr><td><code>3xl</code></td><td><code>3.052rem</code></td><td style="font-size: 3.052rem;">Aa</td></tr>
    <tr><td><code>4xl</code></td><td><code>3.815rem</code></td><td style="font-size: 3.815rem;">Aa</td></tr>
  </tbody>
</table>

## Line Height

- **tight**: `1.2`
- **normal**: `1.5`
- **relaxed**: `1.75`
- **loose**: `2`

## Letter Spacing

- **tighter**: `-0.02em`
- **tight**: `-0.01em`
- **normal**: `0`
- **wide**: `0.01em`
- **wider**: `0.02em`

---

## Usage Guidelines

### Font Weight Selection

| Element | Weight | Token | Example |
|---------|--------|-------|---------|
| Body text | 400 | `regular` | Paragraph content, descriptions |
| Secondary text | 400 | `regular` | Captions, footnotes, metadata |
| Headings (H1-H3) | 600 | `semibold` | Page titles, section headers |
| Subheadings (H4-H6) | 500 | `medium` | Subsection titles |
| Emphasis | 600 | `semibold` | KPI values, data labels, highlights |
| Buttons | 600 | `semibold` | CTA buttons, interactive elements |
| Labels | 500 | `medium` | Form labels, chart axis labels |
| Critical alerts | 700 | `bold` | Error messages only (use sparingly) |

### Heading Hierarchy

```css
h1 {
  font-size: var(--font-size-3xl);  /* 3.052rem */
  font-weight: 600;                  /* semibold */
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}

h2 {
  font-size: var(--font-size-2xl);  /* 2.441rem */
  font-weight: 600;
  line-height: var(--line-height-tight);
}

h3 {
  font-size: var(--font-size-xl);   /* 1.953rem */
  font-weight: 600;
  line-height: var(--line-height-normal);
}

h4 {
  font-size: var(--font-size-lg);   /* 1.563rem */
  font-weight: 500;                  /* medium */
  line-height: var(--line-height-normal);
}

h5, h6 {
  font-size: var(--font-size-md);   /* 1.25rem */
  font-weight: 500;
  line-height: var(--line-height-normal);
}

p {
  font-size: var(--font-size-base); /* 1rem */
  font-weight: 400;
  line-height: var(--line-height-normal);
}
```

### Text Transform Rules

**Allowed:**
- `text-transform: none` (default)
- `text-transform: capitalize` (for specific words only)

**Forbidden:**
- `text-transform: uppercase` (violates NO ALL CAPS rule)
- `text-transform: lowercase` (for proper nouns)

### Accessibility

- **Minimum font size**: 0.8rem (12.8px) for body text
- **Minimum line height**: 1.5 for readability
- **Minimum contrast**: WCAG 2.1 AA compliant
  - Body text (#1E1E1E) on white (#FFFFFF): 16.1:1 ✓
  - Muted text (#787878) on white: 4.54:1 ✓
- **No ALL CAPS**: Reduces readability for dyslexic users

### Examples

**Good:**
```html
<h1 style="font-weight: 600;">Platform Health Scorecard</h1>
<p style="font-weight: 400; line-height: 1.5;">
  The governance dashboard shows real-time metrics and compliance insights.
</p>
<span style="font-weight: 600; color: var(--emphasis);">92.5</span>
```

**Bad:**
```html
<!-- ❌ All caps heading -->
<h1 style="text-transform: uppercase;">PLATFORM HEALTH SCORECARD</h1>

<!-- ❌ No fallback fonts -->
<p style="font-family: Inter;">Content here</p>

<!-- ❌ Too tight line height -->
<p style="line-height: 1.2;">Long paragraph with poor readability...</p>

<!-- ❌ Using bold for non-critical emphasis -->
<span style="font-weight: 700;">Regular emphasis</span>
```

