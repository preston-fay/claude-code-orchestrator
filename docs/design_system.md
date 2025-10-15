# Kearney Design System

**Version:** 1.0.0
**Last Updated:** 2025-10-15

Complete brand-locked design system for Kearney Analytics Platform with D3/Leaflet overlay support.

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

---

## Overview

The Kearney Design System enforces strict brand compliance across all visualizations and interfaces:

- **No emojis** in any outputs
- **No gridlines** on charts or maps
- **Label-first** approach - prefer direct mark labels over axis labels
- **Spot color emphasis** for key insights
- **Inter font** with Arial fallback
- **Kearney colors only** - no colors outside defined palette

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
      "200": "#D2D2D2",
      "500": "#787878",
      "800": "#2D2D2D"
    },
    "violet": {
      "1": "#E6D2FA",
      "2": "#C8A5F0",
      "3": "#AF7DEB",
      "4": "#9150E1"
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
["#E6D2FA", "#C8A5F0", "#AF7DEB", "#9150E1", "#7823DC", "#601FB5", "#4A188E", "#341167"]
```

**Categorical (Primary):**
```typescript
["#7823DC", "#A5A5A5", "#9150E1", "#787878", "#AF7DEB", "#D2D2D2"]
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
   - Only Kearney palette
   - No arbitrary colors
   - Derive ramps from core palette

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

## Resources

- [Kearney Brand Guidelines](https://kearney.com) (external)
- [Design Tokens](../design_system/tokens.json)
- [Python Adapters](../design_system/python/)
- [Web Adapters](../design_system/web/)
- [React Components](../apps/web/src/components/)
- [Maps Components](../apps/web/src/maps/)

---

## License

Internal use only - Kearney Analytics Platform

**Generated:** 2025-10-15
**Version:** 1.0.0
