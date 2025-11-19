# Kearney Design System

**Version:** 1.1.0
**Last Updated:** 2025-11-19

Complete brand-locked design system for Kearney Analytics Platform with D3/Leaflet overlay support.

## Brand Principle

**"White + slate + purple accent"**

The Kearney Design System follows a strict visual principle of clean white or dark backgrounds, a comprehensive grey foundation palette, and purple used sparingly for emphasis. **NO green, red, orange, or blue** are permitted anywhere in the design system.

---

## Table of Contents

1. [Overview](#overview)
2. [Design Tokens](#design-tokens)
3. [Typography](#typography)
4. [Color System](#color-system)
5. [Charts and Visualization](#charts-and-visualization)
6. [D3 Overlay on Leaflet](#d3-overlay-on-leaflet)
7. [Theme System](#theme-system)
8. [Component Library](#component-library)
9. [Brand Guidelines](#brand-guidelines)
10. [CI Validation](#ci-validation)
11. [Auto-Generation on Merge](#auto-generation-on-merge)

---

## Overview

The Kearney Design System enforces strict brand compliance across all visualizations and interfaces:

### Visual Constraints

- **Approved colors only** - 27 colors from KDS palette (white, black, greys, purples)
- **Forbidden colors** - NO green, red, orange, or blue anywhere
- **No emojis** in any outputs (use text symbols: ▲ ▼ ─)
- **No gridlines** on charts or maps
- **No ALL CAPS** headings (use sentence case or title case)
- **Label-first** approach - prefer direct mark labels over axis labels
- **Spot color emphasis** - purple for key insights only
- **Generous whitespace** - breathing room between elements
- **Inter font** with Arial fallback

### Technology Stack

- **TypeScript/React** for web components
- **Python** for backend and data processing
- **D3.js** for advanced visualizations
- **Leaflet** for mapping with D3 overlays
- **Tailwind CSS** for utility styling

---

## Design Tokens

All design values are centralized in `design_system/tokens.json`:

### Core Palette

```json
{
  "palette": {
    "core": {
      "charcoal": "#1E1E1E",
      "silver": "#A5A5A5",
      "purple": "#7823DC"
    },
    "grey": {
      "100": "#F5F5F5",
      "150": "#E6E6E6",
      "200": "#D2D2D2",
      "250": "#C8C8C8",
      "350": "#B9B9B9",
      "500": "#A5A5A5",
      "550": "#8C8C8C",
      "600": "#787878",
      "650": "#5F5F5F",
      "700": "#4B4B4B",
      "850": "#323232",
      "800": "#2D2D2D",
      "900": "#1A1A1A"
    },
    "violet": {
      "1": "#E6D2FA",
      "2": "#C8A5F0",
      "3": "#AF7DEB",
      "4": "#9150E1",
      "5": "#7823DC"
    },
    "violetAlt": {
      "1": "#D7BEF5",
      "2": "#B991EB",
      "3": "#A064E6",
      "4": "#8737E1"
    }
  }
}
```

### Typography Scale

Modular 1.25 ratio scale:

```typescript
{
  xs: "0.64rem",   // 10.24px
  sm: "0.8rem",    // 12.8px
  base: "1rem",    // 16px
  md: "1.25rem",   // 20px
  lg: "1.563rem",  // 25px
  xl: "1.953rem",  // 31px
  "2xl": "2.441rem",
  "3xl": "3.052rem",
  "4xl": "3.815rem"  // 61px
}
```

---

## Typography

### Font Family

```css
--font-family-primary: Inter, Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, sans-serif;
--font-family-mono: 'SF Mono', 'Roboto Mono', 'Courier New', monospace;
```

### Font Weights

- Light: 300
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

### Line Heights

- Tight: 1.2 (headings)
- Normal: 1.5 (body)
- Relaxed: 1.75
- Loose: 2.0

---

## Color System

### Semantic Colors (Light Theme)

```css
--background: #FFFFFF
--surface: #F5F5F5
--text: #1E1E1E
--text-muted: #787878
--emphasis: #7823DC
--spot-color: #7823DC
```

### Semantic Colors (Dark Theme)

```css
--background: #000000
--surface: #1E1E1E
--text: #FFFFFF
--text-muted: #A5A5A5
--emphasis: #AF7DEB
--spot-color: #AF7DEB
```

### Visualization Palettes

**Sequential (Purple):**
```typescript
// Use only approved purples - NO deprecated colors
["#E6D2FA", "#C8A5F0", "#AF7DEB", "#9150E1", "#7823DC"]
```

**Categorical (Primary):**
```typescript
// Alternate purples and greys for visual separation
["#7823DC", "#A5A5A5", "#9150E1", "#787878", "#AF7DEB", "#D2D2D2"]
```

**Semantic States:**
```typescript
// NO green/red/orange - use purple/grey with text labels
{
  positive: "#7823DC",  // With ▲ or "Improved" label
  negative: "#4B4B4B",  // With ▼ or "Declined" label
  neutral: "#787878"    // With ─ or "No change" label
}
```

---

## Charts and Visualization

### Chart Requirements

1. **No gridlines** (enforced programmatically)
2. **Minimal axes** - top and right removed
3. **Direct labels** on data points
4. **Spot color** for emphasis
5. **Theme-aware** colors

### Creating Charts with D3

```typescript
import { applyKearneyStyling, createMinimalAxes, addMarkLabel, spotOutline } from '../design-system/d3_theme';

const svg = createResponsiveSVG(container, { theme, width, height });

// Create scales
const xScale = d3.scaleTime()...;
const yScale = d3.scaleLinear()...;

// Create minimal axes (NO gridlines)
createMinimalAxes(svg, config, xScale, yScale, 'Time', 'Value');

// Add mark labels
data.forEach(d => {
  addMarkLabel(svg, xScale(d.x), yScale(d.y), d.label, theme);
});

// Add spot color highlight
const spotStyle = spotOutline(theme);
svg.append('circle')
  .attr('cx', xScale(keyPoint.x))
  .attr('cy', yScale(keyPoint.y))
  .attr('r', 5)
  .attr('stroke', spotStyle.stroke)
  .attr('stroke-width', spotStyle.strokeWidth);

// Verify NO gridlines
verifyNoGridlines(svg);
```

---

## D3 Overlay on Leaflet

The `LeafletD3Overlay` component renders branded SVG annotations on top of Leaflet maps with collision-avoided labels.

### Basic Usage

```typescript
import { LeafletD3Overlay } from './maps/LeafletD3Overlay';
import { MapContainer, TileLayer } from 'react-leaflet';

function MyMap() {
  const [map, setMap] = useState<L.Map | null>(null);

  const getFeatures = async (): Promise<FeatureCollection> => {
    const response = await fetch('/api/isochrone?lat=51.5&lng=-0.1&range=30');
    return response.json();
  };

  return (
    <MapContainer
      center={[51.5, -0.1]}
      zoom={13}
      ref={(m) => setMap(m)}
    >
      <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />

      <LeafletD3Overlay
        map={map}
        getFeatures={getFeatures}
        labelAccessor={(f) => `${f.properties?.minutes} min`}
        spotPredicate={(f) => f.properties?.isMax === true}
        onHover={(f) => console.log('Hovering:', f)}
      />
    </MapContainer>
  );
}
```

### Component Props

```typescript
type D3OverlayProps = {
  map: L.Map | null;                              // Leaflet map instance
  getFeatures: () => Promise<FeatureCollection>;  // Fetch GeoJSON polygons
  labelAccessor?: (f: Feature) => string;         // Generate label text
  spotPredicate?: (f: Feature) => boolean;        // Identify key features
  onHover?: (f: Feature | null) => void;          // Hover callback
  onClick?: (f: Feature | null) => void;          // Click callback
};
```

### Features

**Automatic Projection Sync:**
- Uses `map.latLngToLayerPoint()` for accurate coordinate mapping
- Re-renders on zoom/pan events
- SVG positioned absolutely to match map viewport

**Collision-Avoided Labels:**
- D3 force simulation with `forceCollide` and centering forces
- Labels hidden if collision cannot be avoided
- Readable stroke halo using `paintOrder: 'stroke'`

**Brand Compliance:**
- Sequential purple ramp for polygon fills
- Spot color outline for emphasized features
- Theme-aware (light/dark)
- No gridlines enforced

### Styling Labels

Labels use `labelStyle(theme)` helper for optimal readability:

```typescript
import { labelStyle } from '../design-system/d3_theme';

const styles = labelStyle(theme);
// Returns:
{
  fontFamily: "Inter, Arial, ...",
  fontSize: "13px",
  fontWeight: "600",
  fill: colors.text,              // Theme text color
  paintOrder: "stroke",           // Stroke behind fill
  stroke: colors.background,      // Halo color
  strokeWidth: "3px",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  pointerEvents: "none"
}
```

### Spot Color Outline

Emphasize key polygons with spot color:

```typescript
import { spotOutline } from '../design-system/d3_theme';

const styles = spotOutline(theme);
// Returns:
{
  stroke: colors.spotColor,       // #7823DC (light) / #AF7DEB (dark)
  strokeWidth: "3px",
  strokeDasharray: "5,3",         // Dashed outline
  fill: "none",
  opacity: 0.9
}
```

---

## Theme System

### React Theme Provider

```typescript
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <MyComponents />
    </ThemeProvider>
  );
}

function MyComponent() {
  const { theme, toggleTheme, setTheme } = useTheme();
  // theme: 'light' | 'dark'
}
```

### Theme Persistence

Themes are automatically saved to `localStorage` under key `kearney-theme` and applied via:
- `[data-theme="light|dark"]` attribute on `<html>`
- `.dark` class for Tailwind CSS

### CSS Custom Properties

All components use CSS variables for theme-aware styling:

```css
.my-component {
  background-color: var(--surface);
  color: var(--text);
  border-color: var(--border);
}

.my-button {
  background-color: var(--emphasis);
  color: var(--text-inverse);
}
```

---

## Component Library

### KPI Card

```typescript
import { KPICard } from './components/KPICard';

<KPICard
  title="Total Revenue"
  value="$2.4M"
  trend={{ direction: 'up', value: '+12.5%' }}
  insight="Revenue increased 12.5% compared to last quarter."
/>
```

### Timeseries Chart

```typescript
import { TimeseriesChart } from './components/TimeseriesChart';

<TimeseriesChart
  data={timeseriesData}
  highlightData={recentData}
  spotHighlight={{ date: peakDate, label: 'Peak' }}
  title="Monthly Revenue"
  xLabel="Month"
  yLabel="Revenue ($K)"
  width={800}
  height={400}
/>
```

### Categorical Bar Chart

```typescript
import { CategoricalBarChart } from './components/CategoricalBarChart';

<CategoricalBarChart
  data={categoryData}
  title="Sales by Product"
  yLabel="Sales ($K)"
  horizontal={false}
  sorted={true}
  width={600}
  height={400}
/>
```

---

## Brand Guidelines

### Critical Requirements

1. **No Emojis**
   - Never use emojis in UI, docs, or code comments
   - Use text symbols: ▲ (up), ▼ (down), ─ (neutral)

2. **No Gridlines**
   - Charts: No background grid
   - Maps: No graticules
   - Use `verifyNoGridlines(svg)` to enforce

3. **Label-First**
   - Prefer direct labels on marks
   - Minimize axis dependency
   - Use collision avoidance for readability

4. **Spot Color Emphasis**
   - Highlight 1 key insight per chart
   - Use brand purple (#7823DC light, #AF7DEB dark)
   - Dashed outline or halo

5. **Typography**
   - Inter font with Arial fallback
   - Modular 1.25 scale
   - Semibold (600) for emphasis

6. **Colors**
   - Only 27 approved colors from KDS palette
   - NO green, red, orange, or blue
   - Validated in CI with `scripts/validate_kds_colors.py`

7. **Typography**
   - NO ALL CAPS headings
   - Use sentence case or title case
   - Semibold (600) for emphasis, not bold (700)

8. **Spacing**
   - Generous whitespace
   - Breathing room between elements
   - Don't crowd interfaces

### Testing Compliance

```typescript
// Verify no emojis
const emojiRegex = /[\u{1F600}-\u{1F64F}]/u;
expect(emojiRegex.test(output)).toBe(false);

// Verify no gridlines
const gridElements = svg.selectAll('.grid, [class*="grid"]');
expect(gridElements.empty()).toBe(true);

// Verify spot color used
const spotElements = svg.selectAll('[stroke="#7823DC"], [stroke="#AF7DEB"]');
expect(spotElements.empty()).toBe(false);

// Verify color compliance
// Run: python scripts/validate_kds_colors.py
// All hex colors must be from approved 27-color palette
```

---

## Examples

### Example 1: Isochrone Map with D3 Overlay

![Isochrone Light Theme](./examples/isochrone_d3_light.png)
![Isochrone Dark Theme](./examples/isochrone_d3_dark.png)

See live demo at `/maps/d3-isochrone`

### Example 2: KPI Dashboard

See [Phase 2 completion report](../PROMPT_10A_PHASE2_COMPLETION.md) for screenshots

### Example 3: Chart Examples

See [Phase 2 completion report](../PROMPT_10A_PHASE2_COMPLETION.md) for chart examples

---

## CI Validation

The theme system includes automated CI/CD workflows that validate themes on every pull request and auto-generate tokens on merge to main.

### What PR Checks Enforce

When you create a pull request that modifies `clients/**/theme.json` or `design_system/tokens.json`, the following checks run automatically:

**1. Schema Validation**
- Validates theme JSON against `clients/.schema/theme.schema.json`
- Checks required fields: `client.slug`, `client.name`, `constraints`
- Validates slug format: lowercase, hyphens only (e.g., `acme-corp`)
- Ensures hex color format: `#RRGGBB` (e.g., `#7823DC`)
- Requires font family fallbacks (e.g., `Inter, Arial, sans-serif`)

**2. Brand Constraint Checks**
- `allowEmojis` must be `false` (no emojis in Kearney brand)
- `allowGridlines` must be `false` (no gridlines on charts)
- `labelFirst` must be `true` (label-first approach required)
- Colors must be valid hex codes from Kearney palette
- Typography must include system font fallbacks

**3. Test Suite**
- Runs `tests/design/test_theme_schema.py` - Schema validation tests
- Runs `tests/design/test_merge_theme.py` - Merge algorithm tests
- Runs `tests/server/test_theme_routes.py` - API endpoint tests
- Runs `tests/orchestrator/test_style_cli.py` - CLI command tests

### How to Read Validation Failures

**Example 1: Invalid Constraint**

```
❌ Missing allowEmojis constraint
File: clients/acme-corp/theme.json
Line: 12

Expected: "allowEmojis": false
Found: "allowEmojis": true
```

**Fix:** Update `theme.json`:
```json
{
  "constraints": {
    "allowEmojis": false,
    "allowGridlines": false,
    "labelFirst": true
  }
}
```

**Example 2: Invalid Color Format**

```
❌ Validation Error
File: clients/acme-corp/theme.json
Error: '#GGGGGG' does not match pattern '^#[0-9A-Fa-f]{6}$'
```

**Fix:** Use valid hex color:
```json
{
  "colors": {
    "light": {
      "primary": "#7823DC"
    }
  }
}
```

**Example 3: Missing Font Fallback**

```
❌ Validation Error
File: clients/acme-corp/theme.json
Error: Font family must include fallback (sans-serif, serif, or monospace)
```

**Fix:** Add fallback:
```json
{
  "typography": {
    "fontFamilyPrimary": "Inter, Arial, sans-serif"
  }
}
```

### Local Testing

Before pushing, validate your theme locally:

**Using CLI:**
```bash
# Validate theme
orchestrator style validate --client acme-corp

# Dry-run (validate + show what would be generated)
orchestrator style apply --client acme-corp --dry-run
```

**Using Merge Script:**
```bash
# Validate only
python scripts/merge_theme.py --client acme-corp --validate-only

# Dry-run
python scripts/merge_theme.py --client acme-corp --dry-run
```

**Using pytest:**
```bash
# Run all theme tests
pytest tests/design/ -v

# Run specific test
pytest tests/design/test_theme_schema.py::TestConstraintsValidation -v
```

---

## Auto-Generation on Merge

When a pull request is merged to `main`, tokens are automatically generated and committed back to the repository.

### What Files Are Updated

For each changed theme (e.g., `clients/acme-corp/theme.json`), the workflow generates:

```
design_system/.generated/
├── acme-corp.css         # CSS custom properties
├── acme-corp.ts          # TypeScript token exports
└── acme-corp.json        # Merged JSON (base + overrides)
```

**Example Generated CSS:**
```css
/**
 * Kearney Design Tokens - Auto-generated
 * DO NOT EDIT MANUALLY - Generated from base tokens + client overrides
 */

:root {
  /* Light Mode Colors */
  --primary: #7823DC;
  --emphasis: #E63946;
  --background: #FFFFFF;
  --text: #1E1E1E;

  /* Typography */
  --font-family-primary: Inter, Arial, sans-serif;
  --font-size-base: 1rem;
}

[data-theme='dark'] {
  /* Dark Mode Colors */
  --primary: #A855F7;
  --emphasis: #EF476F;
  --background: #000000;
  --text: #FFFFFF;
}
```

**Example Generated TypeScript:**
```typescript
/**
 * Kearney Design Tokens - Auto-generated
 * DO NOT EDIT MANUALLY - Generated from base tokens + client overrides
 */

export const tokens = {
  client: {
    slug: "acme-corp",
    name: "Acme Corporation"
  },
  colors: {
    light: { primary: "#7823DC", ... },
    dark: { primary: "#A855F7", ... }
  },
  typography: { ... },
  spacing: { ... }
} as const;

export type Theme = 'light' | 'dark';

export function getThemeColors(theme: Theme) {
  return tokens.colors[theme];
}
```

### Where to Find Generated Files

**In Repository:**
- Generated files are committed to `design_system/.generated/`
- Excluded from tidyignore cleanup (see [.tidyignore](../.tidyignore) line 71)
- Accessible to web apps via relative imports

**In GitHub Actions:**
- Artifacts are uploaded to GitHub Actions for 30 days
- Download from Actions tab → workflow run → "Artifacts" section
- Artifact name: `generated-tokens-<client-slug>`

**Example Import (React):**
```typescript
import { tokens } from '@design-system/.generated/acme-corp';

const primaryColor = tokens.colors.light.primary; // "#7823DC"
```

**Example Import (CSS):**
```html
<link rel="stylesheet" href="/design_system/.generated/acme-corp.css">
```

### Commit Message Format

Auto-generated commits use this format:
```
chore: auto-generate tokens for changed themes

Generated tokens for:
- acme-corp
- another-client

Co-Authored-By: Claude <noreply@anthropic.com>
🤖 Generated with Claude Code
```

### Manual Regeneration

To manually regenerate tokens (e.g., after fixing schema):

```bash
# Generate tokens for specific client
orchestrator style apply --client acme-corp

# Or use merge script directly
python scripts/merge_theme.py --client acme-corp
```

---

## Resources

- [Kearney Brand Guidelines](https://kearney.com) (external)
- [Design Tokens](../design_system/tokens.json)
- [Theme Schema](../clients/.schema/theme.schema.json)
- [Merge Script](../scripts/merge_theme.py)
- [Python Adapters](../design_system/python/)
- [Web Adapters](../design_system/web/)
- [React Components](../apps/web/src/components/)
- [Maps Components](../apps/web/src/maps/)
- [CI Workflow](../.github/workflows/theme-ci.yml)

---

## License

Internal use only - Kearney Analytics Platform

**Generated:** 2025-11-19
**Version:** 1.1.0
