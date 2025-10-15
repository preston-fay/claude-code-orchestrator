---
sidebar_position: 0
title: Design System Overview
---

# Design System Overview

The Kearney Data Platform design system provides a comprehensive set of design tokens
for building brand-compliant interfaces.

## Principles

### Brand Constraints

- **No Emojis**: True
- **No Gridlines**: True
- **Label First**: True
- **Spot Color Emphasis**: True

### Typography

Modular scale 1.25 ratio used as kearney.com CSS was not accessible. Inter font with Arial fallback.

## Token Categories

The design system includes the following token categories:

1. **Colors** - Core palette, extended colors, and semantic theme tokens
2. **Typography** - Font families, weights, sizes, and scales
3. **Spacing** - Consistent spacing values based on modular scale
4. **Border Radius** - Rounded corner values
5. **Shadows** - Elevation and depth effects

## Usage

### In CSS

```css
:root {
  --kearney-purple: #7823DC;
  --kearney-charcoal: #1E1E1E;
}

.button {
  background-color: var(--kearney-purple);
  color: var(--kearney-white);
  padding: var(--spacing-4);
  border-radius: var(--border-radius-base);
}
```

### In JavaScript/TypeScript

```typescript
import tokens from './design_system/tokens.json';

const primaryColor = tokens.theme.light.emphasis;
const headingFont = tokens.typography.fontFamily.primary;
```

### In React

```tsx
import { getThemeColors } from './design-system/tokens';

const theme = getThemeColors('light');

<div style={{
  backgroundColor: theme.background,
  color: theme.text
}}>
  Content
</div>
```

## Version

Design system version: **1.0.0**

Source: Kearney brand guidelines

