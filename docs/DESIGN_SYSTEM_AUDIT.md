# Design System Audit - Phase 1B Metrics Dashboard

**Status:** COMPLETE - READY FOR REVIEW
**Date:** 2025-01-07
**Purpose:** Document existing design system for Phase 1B dashboard implementation

---

## Executive Summary

The Claude Code Orchestrator has a **complete, production-ready design system** located in `design_system/`. This system MUST be used for the metrics dashboard—no new design tokens should be created.

**Key Findings:**
- Comprehensive token system with 150+ design variables
- Kearney brand-compliant colors, typography, spacing
- Dark mode fully supported with semantic tokens
- Web-specific CSS custom properties ready to use
- Component patterns documented in C-suite templates
- **NO EMOJIS policy** enforced across all design assets
- **NO GRIDLINES policy** for all charts and visualizations

**Dashboard Implementation Rule:** Use existing `design_system/web/tokens.css` as base stylesheet. Do NOT create new CSS variables.

---

## 1. Design System Location

### Primary Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `design_system/tokens.json` | Master design tokens (source of truth) | 153 | Production |
| `design_system/web/tokens.css` | Web CSS custom properties | 193 | Production |
| `design_system/web/tokens.ts` | TypeScript type definitions | N/A | Production |
| `design_system/web/d3_theme.ts` | D3.js chart theming utilities | N/A | Production |
| `design_system/palettes.json` | Extended color palettes | N/A | Production |

### Templates & Patterns

| Directory | Purpose | Status |
|-----------|---------|--------|
| `design_system/templates/c-suite/` | Executive presentation templates | Production |
| `design_system/templates/c-suite/styles.css` | Component styles | Production |
| `design_system/python/` | Python visualization themes (matplotlib) | Production |

---

## 2. Kearney Brand Colors (Exact Hex Codes)

### Core Palette

```css
/* PRIMARY BRAND COLOR */
--color-purple: #7823DC          /* Kearney purple - primary emphasis */

/* NEUTRALS */
--color-charcoal: #1E1E1E        /* Dark text, surfaces */
--color-silver: #A5A5A5          /* Muted text, chart gridlines (if used) */
--color-white: #FFFFFF            /* Light backgrounds */
--color-black: #000000            /* Dark backgrounds, true black */

/* GREYS (9-step scale) */
--color-grey-100: #F5F5F5        /* Lightest grey - light mode surface */
--color-grey-200: #D2D2D2        /* Light borders */
--color-grey-300: #BEBEBE        /* Muted borders */
--color-grey-500: #787878        /* Muted text */
--color-grey-600: #5A5A5A        /* Medium text */
--color-grey-700: #4B4B4B        /* Dark borders */
--color-grey-800: #2D2D2D        /* Dark surface elevated */
--color-grey-900: #1A1A1A        /* Darkest grey */

/* VIOLET SCALE (for gradients, highlights) */
--color-violet-1: #E6D2FA        /* Lightest - tints, backgrounds */
--color-violet-2: #C8A5F0        /* Light - hover states */
--color-violet-3: #AF7DEB        /* Medium - dark mode emphasis */
--color-violet-4: #9150E1        /* Dark - hover states */
```

### Status Colors (Kearney Brand Compliant)

**CRITICAL:** Kearney does NOT use green for success. Always use purple.

```css
--color-success: #7823DC         /* Purple - NOT GREEN per brand guidelines */
--color-success-tint: #E6D2FA    /* Light purple tint */
--color-warning: #ED6C02         /* Orange - acceptable */
--color-error: #D32F2F           /* Red - acceptable */
--color-info: #7823DC            /* Purple - same as success */
```

### Chart Colors

```css
/* Light Theme Charts */
--chart-muted: #A5A5A5           /* Grey for secondary data */
--chart-highlight: #7823DC       /* Purple for primary data */

/* Dark Theme Charts */
--chart-muted: #787878           /* Darker grey for secondary data */
--chart-highlight: #C8A5F0       /* Lighter purple for primary data */
```

---

## 3. Semantic Tokens (Theme-Aware)

The design system uses **semantic tokens** that automatically switch based on theme (light/dark).

### Background & Surfaces

```css
/* Light Theme Values */
--background: #FFFFFF             /* Page background */
--surface: #F5F5F5                /* Card backgrounds */
--surface-elevated: #FFFFFF       /* Modal, dropdown backgrounds */

/* Dark Theme Values */
--background: #000000             /* Page background */
--surface: #1E1E1E                /* Card backgrounds */
--surface-elevated: #2D2D2D       /* Modal, dropdown backgrounds */
```

### Text Colors

```css
/* Light Theme Values */
--text: #1E1E1E                   /* Primary text color */
--text-muted: #787878             /* Secondary text, captions */
--text-inverse: #FFFFFF           /* Text on dark backgrounds */

/* Dark Theme Values */
--text: #FFFFFF                   /* Primary text color */
--text-muted: #A5A5A5             /* Secondary text, captions */
--text-inverse: #1E1E1E           /* Text on light backgrounds */
```

### Borders & Emphasis

```css
/* Light Theme Values */
--border: #D2D2D2                 /* Card borders, dividers */
--emphasis: #7823DC               /* Interactive elements, links */
--emphasis-hover: #9150E1         /* Hover state */

/* Dark Theme Values */
--border: #4B4B4B                 /* Card borders, dividers */
--emphasis: #AF7DEB               /* Interactive elements, links */
--emphasis-hover: #C8A5F0         /* Hover state */
```

### Spot Color (Charts & Highlights)

```css
/* Light Theme */
--spot-color: #7823DC             /* Chart accents, highlights */

/* Dark Theme */
--spot-color: #AF7DEB             /* Chart accents, highlights */
```

---

## 4. Typography System

### Font Families

```css
/* PRIMARY - For web applications (NOT presentations) */
--font-family-primary: Inter, Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif;

/* MONOSPACE - For code, data tables */
--font-family-mono: 'SF Mono', 'Roboto Mono', 'Courier New', monospace;
```

**Note:** Kearney C-suite presentations use **Arial only**, but web dashboards use **Inter** with Arial fallback.

### Font Weights

```css
--font-weight-light: 300          /* Rarely used */
--font-weight-regular: 400        /* Body text */
--font-weight-medium: 500         /* Subheadings */
--font-weight-semibold: 600       /* Section headings */
--font-weight-bold: 700           /* Major headings */
```

### Font Sizes (Modular Scale 1.25 ratio)

```css
--font-size-xs: 0.64rem           /* 10.24px - Tiny labels */
--font-size-sm: 0.8rem            /* 12.8px - Small text */
--font-size-base: 1rem            /* 16px - Body text */
--font-size-md: 1.25rem           /* 20px - H4 */
--font-size-lg: 1.563rem          /* 25px - H3 */
--font-size-xl: 1.953rem          /* 31.25px - H2 */
--font-size-2xl: 2.441rem         /* 39px - H1 */
--font-size-3xl: 3.052rem         /* 48.8px - Hero */
--font-size-4xl: 3.815rem         /* 61px - Marketing hero */
```

### Line Heights

```css
--line-height-tight: 1.2          /* Headings */
--line-height-normal: 1.5         /* Body text */
--line-height-relaxed: 1.75       /* Long-form content */
--line-height-loose: 2            /* Rarely used */
```

### Letter Spacing

```css
--letter-spacing-tighter: -0.02em /* Large headings */
--letter-spacing-tight: -0.01em   /* Headings */
--letter-spacing-normal: 0        /* Body text */
--letter-spacing-wide: 0.01em     /* Uppercase labels */
--letter-spacing-wider: 0.02em    /* All-caps headings */
```

---

## 5. Spacing System (Modular Scale)

```css
--spacing-0: 0                    /* No spacing */
--spacing-1: 0.25rem              /* 4px - Tight spacing */
--spacing-2: 0.5rem               /* 8px - Small gaps */
--spacing-3: 0.75rem              /* 12px - Compact */
--spacing-4: 1rem                 /* 16px - Base unit */
--spacing-5: 1.25rem              /* 20px - Medium gaps */
--spacing-6: 1.5rem               /* 24px - Card padding */
--spacing-8: 2rem                 /* 32px - Section spacing */
--spacing-10: 2.5rem              /* 40px - Large sections */
--spacing-12: 3rem                /* 48px - Major sections */
--spacing-16: 4rem                /* 64px - Page sections */
--spacing-20: 5rem                /* 80px - Hero spacing */
--spacing-24: 6rem                /* 96px - Marketing spacing */
```

**Common Patterns:**
- Card padding: `var(--spacing-6)` (24px)
- Section spacing: `var(--spacing-8)` (32px)
- Gap between elements: `var(--spacing-4)` (16px)
- Header padding: `var(--spacing-5)` (20px)

---

## 6. Border Radius

```css
--radius-none: 0                  /* Sharp corners */
--radius-sm: 0.125rem             /* 2px - Subtle */
--radius-base: 0.25rem            /* 4px - Default */
--radius-md: 0.375rem             /* 6px - Cards */
--radius-lg: 0.5rem               /* 8px - Modals */
--radius-xl: 0.75rem              /* 12px - Feature cards */
--radius-2xl: 1rem                /* 16px - Hero cards */
--radius-full: 9999px             /* Pills, circles */
```

**Common Patterns:**
- Cards: `var(--radius-md)` (6px)
- Buttons: `var(--radius-base)` (4px)
- Input fields: `var(--radius-base)` (4px)
- Pills/badges: `var(--radius-full)`

---

## 7. Shadows (Elevation System)

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-base: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)
```

**Common Patterns:**
- Cards: `var(--shadow-base)` or `var(--shadow-md)`
- Modals: `var(--shadow-lg)`
- Dropdowns: `var(--shadow-md)`
- Hover elevation: Transition from `--shadow-base` to `--shadow-md`

---

## 8. Component Patterns (From C-Suite Templates)

### Card Component

```html
<div class="card">
  <h3 class="card-title">Title</h3>
  <div class="card-content">
    <!-- Content -->
  </div>
</div>
```

```css
.card {
  background-color: var(--surface-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  margin-bottom: var(--spacing-4);
}

.card-content {
  color: var(--text-muted);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
}
```

### Button Component

```html
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
```

```css
.btn {
  padding: var(--spacing-3) var(--spacing-5);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn-primary {
  background-color: var(--emphasis);
  color: var(--text-inverse);
}

.btn-primary:hover {
  background-color: var(--emphasis-hover);
}

.btn-secondary {
  background-color: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn-secondary:hover {
  background-color: var(--surface-elevated);
}
```

### KPI Card (Metric Display)

```html
<div class="kpi-card">
  <div class="kpi-label">Deployment Frequency</div>
  <div class="kpi-value">2.3/week</div>
  <div class="kpi-trend positive">+15%</div>
</div>
```

```css
.kpi-card {
  background-color: var(--surface-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-5);
  text-align: center;
}

.kpi-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
  margin-bottom: var(--spacing-2);
}

.kpi-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--text);
  margin-bottom: var(--spacing-2);
}

.kpi-trend {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
}

.kpi-trend.positive {
  color: var(--emphasis);  /* Purple - NO GREEN per Kearney brand */
}

.kpi-trend.negative {
  color: var(--error);
}
```

---

## 9. Theme Switching Implementation

The design system supports two methods for theme switching:

### Method 1: data-theme attribute (Recommended)

```html
<html data-theme="dark">
  <!-- All semantic tokens automatically switch -->
</html>
```

```javascript
// Toggle theme
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
}

// Apply saved theme on load
const savedTheme = localStorage.getItem('theme') || 'dark';  // DEFAULT TO DARK
document.documentElement.setAttribute('data-theme', savedTheme);
```

### Method 2: .dark class (Alternative)

```html
<html class="dark">
  <!-- Same behavior as data-theme="dark" -->
</html>
```

Both methods are supported in `design_system/web/tokens.css` (lines 122-163).

**IMPORTANT:** Default to dark mode per requirements.

---

## 10. Chart Styling Guidelines (NO GRIDLINES)

### Kearney Chart Standards

From `design_system/templates/README.md` (lines 82-87):

```
✅ NO GRIDLINES on charts (mandatory Kearney standard)
✅ Label-first approach: Title ABOVE chart, not below
✅ Clear axis labels with units specified
✅ Legend included when multiple data series present
✅ Data source cited in caption below chart
✅ Simple, clean design (avoid 3D effects, excessive colors, decorative elements)
```

### Chart.js Configuration (NO GRIDLINES)

```javascript
const chartOptions = {
  plugins: {
    legend: {
      labels: {
        color: 'var(--text)',  // Theme-aware text
        font: {
          family: 'var(--font-family-primary)',
          size: 14
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false  // NO GRIDLINES per Kearney brand
      },
      ticks: {
        color: 'var(--text-muted)',
        font: {
          family: 'var(--font-family-primary)'
        }
      }
    },
    y: {
      grid: {
        display: false  // NO GRIDLINES per Kearney brand
      },
      ticks: {
        color: 'var(--text-muted)',
        font: {
          family: 'var(--font-family-primary)'
        }
      }
    }
  }
};
```

### Chart Color Palette

```javascript
const chartColors = {
  primary: 'var(--chart-highlight)',      // Purple
  secondary: 'var(--chart-muted)',        // Grey
  positive: 'var(--emphasis)',            // Purple (NO GREEN per brand)
  negative: 'var(--error)',               // Red
  neutral: 'var(--text-muted)'            // Grey
};
```

---

## 11. Existing Utility Classes

From `design_system/web/tokens.css` (lines 176-192):

```css
/* Background Utilities */
.bg-background { background-color: var(--background); }
.bg-surface { background-color: var(--surface); }
.bg-surface-elevated { background-color: var(--surface-elevated); }

/* Text Utilities */
.text-primary { color: var(--text); }
.text-muted { color: var(--text-muted); }
.text-inverse { color: var(--text-inverse); }
.text-emphasis { color: var(--emphasis); }

/* Border Utilities */
.border-base { border-color: var(--border); }

/* Font Weight Utilities */
.font-light { font-weight: var(--font-weight-light); }
.font-regular { font-weight: var(--font-weight-regular); }
.font-medium { font-weight: var(--font-weight-medium); }
.font-semibold { font-weight: var(--font-weight-semibold); }
.font-bold { font-weight: var(--font-weight-bold); }
```

**Usage:** Apply these classes directly instead of creating custom CSS.

---

## 12. Brand Compliance Checklist

From `tokens.json` metadata (lines 143-151):

```json
{
  "no_emojis": true,                  // NO EMOJI anywhere
  "no_gridlines": true,               // NO GRIDLINES on charts
  "label_first": true,                // Chart title ABOVE, not below
  "spot_color_emphasis": true,        // Purple for emphasis
  "typography_note": "Inter font with Arial fallback"
}
```

### Critical Rules for Metrics Dashboard

1. **NO EMOJIS** - No emoji in code, UI, documentation, or git commits
2. **NO GRIDLINES** - Charts must not have gridlines (Kearney standard)
3. **NO GREEN for success** - Use purple (#7823DC) for positive metrics
4. **Inter font** - Use Inter with Arial fallback (NOT Arial alone)
5. **Purple emphasis** - Kearney purple (#7823DC) is primary brand color
6. **Dark mode default** - Dashboard defaults to dark theme
7. **Label-first charts** - Title above chart, not below
8. **Semantic tokens** - Use theme-aware CSS variables, not hardcoded colors

---

## 13. How to Extend the Design System

### DO: Extend using existing tokens

```css
/* GOOD - Uses existing design system tokens */
.metric-dashboard {
  background-color: var(--background);
  color: var(--text);
  padding: var(--spacing-8);
  border-radius: var(--radius-md);
}

.metric-card {
  background-color: var(--surface-elevated);
  border: 1px solid var(--border);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-md);
}
```

### DON'T: Create new color variables

```css
/* BAD - Creates new colors instead of using existing tokens */
.metric-dashboard {
  background-color: #FAFAFA;  /* Should use var(--background) */
  color: #222222;             /* Should use var(--text) */
  border: 1px solid #DDDDDD;  /* Should use var(--border) */
}

:root {
  --my-custom-color: #FF00FF; /* DON'T create new design tokens */
}
```

### Component-Specific Styles

If you need dashboard-specific styles, create `src/dashboard/dashboard.css` that **extends** (not replaces) the base system:

```css
/* src/dashboard/dashboard.css */

/* Import base design system */
@import url('../../design_system/web/tokens.css');

/* Dashboard-specific layout (using existing tokens) */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-6);
  padding: var(--spacing-8);
}

.chart-container {
  background-color: var(--surface-elevated);
  border-radius: var(--radius-md);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-md);
}

.chart-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  margin-bottom: var(--spacing-4);
}
```

---

## 14. File Structure for Dashboard Implementation

```
src/dashboard/
├── index.html                    # Dashboard HTML
├── styles.css                    # Dashboard-specific styles (extends tokens.css)
├── metrics.js                    # Chart rendering + data loading
├── theme.js                      # Theme toggle system
└── exporters.js                  # CSV/PNG export functionality

IMPORTANT: Import design system tokens FIRST:
<link rel="stylesheet" href="../../design_system/web/tokens.css">
<link rel="stylesheet" href="styles.css">
```

---

## 15. Testing Checklist

Before deploying dashboard, validate:

### Theme Switching
- [ ] Dark mode is default on first load
- [ ] Theme toggle switches all colors correctly
- [ ] Charts update colors when theme changes
- [ ] Theme preference persists across page loads (localStorage)

### Brand Compliance
- [ ] NO EMOJIS anywhere (search codebase for emoji unicode)
- [ ] NO GRIDLINES on any charts
- [ ] Purple (#7823DC) used for positive metrics (NO GREEN)
- [ ] Inter font loads correctly with Arial fallback
- [ ] All colors use semantic tokens (no hardcoded hex codes)

### Accessibility
- [ ] Sufficient color contrast (4.5:1 minimum)
- [ ] Text readable in both light and dark themes
- [ ] Charts have text labels (not color-only)
- [ ] Keyboard navigation works (Tab, Enter, Space)

### Browser Compatibility
- [ ] Chrome (latest)
- [ ] Safari (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)

---

## 16. Resources & References

### Design System Files
- **Master tokens:** `design_system/tokens.json`
- **Web CSS:** `design_system/web/tokens.css`
- **TypeScript types:** `design_system/web/tokens.ts`
- **D3.js utilities:** `design_system/web/d3_theme.ts`
- **Templates:** `design_system/templates/c-suite/`

### Documentation
- **Template guide:** `design_system/templates/README.md` (916 lines)
- **Brand guidelines:** Embedded in `tokens.json` metadata
- **Kearney standards:** Internal portal (not in repo)

### Tools
- **Token generator:** `design_system/build/generate_tokens.py` (if exists)
- **Color contrast checker:** https://webaim.org/resources/contrastchecker/
- **CSS validator:** https://jigsaw.w3.org/css-validator/

---

## 17. Decision: How to Implement Metrics Dashboard

### Approved Approach

1. **Import existing design system:**
   ```html
   <link rel="stylesheet" href="../../design_system/web/tokens.css">
   ```

2. **Create minimal dashboard-specific CSS:**
   - Layout grid for charts
   - Component-specific overrides (if needed)
   - **NO NEW COLOR VARIABLES**

3. **Use semantic tokens for all styling:**
   ```css
   .metric-card {
     background-color: var(--surface-elevated);  /* NOT #2D2D2D */
     color: var(--text);                         /* NOT #FFFFFF */
     border: 1px solid var(--border);            /* NOT #4B4B4B */
   }
   ```

4. **Default to dark theme:**
   ```javascript
   const defaultTheme = 'dark';  // NOT 'light'
   ```

5. **NO EMOJIS anywhere:**
   - Theme toggle: "Light Mode" / "Dark Mode" (text only)
   - Buttons: "Export" / "Download" (text only)
   - Status: "Success" / "Error" / "Warning" (text only)

6. **Configure Chart.js with NO GRIDLINES:**
   ```javascript
   scales: {
     x: { grid: { display: false } },
     y: { grid: { display: false } }
   }
   ```

---

## 18. STOP POINT - READY FOR REVIEW

This audit is complete. Key takeaways for implementation:

1. **Design system exists and is comprehensive** - Use `design_system/web/tokens.css`
2. **Kearney purple is #7823DC** - Primary brand color
3. **NO GREEN for success** - Use purple per brand guidelines
4. **NO EMOJIS** - Text-only labels and messages
5. **NO GRIDLINES** - Charts must be clean per Kearney standard
6. **Dark mode is default** - Dashboard starts in dark theme
7. **Inter font primary** - With Arial fallback

**Next Step:** Proceed with dashboard implementation using existing design system.

---

**Audit Completed:** 2025-01-07
**Reviewed By:** Pending human approval
**Status:** READY FOR PHASE 1B DASHBOARD IMPLEMENTATION
