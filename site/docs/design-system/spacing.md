---
sidebar_position: 3
title: Spacing
---

# Spacing

Spacing system for the Kearney Data Platform.

## Brand Principle

**"Generous whitespace"**

Kearney brand emphasizes breathing room between elements. Don't crowd interfaces - give content space to be readable and scannable. Use larger spacing values (6+) for section separation and component padding.

### Critical Rules

1. **Prefer larger spacing** - Default to 1.5rem (24px) or more for section spacing
2. **Consistent rhythm** - Use modular scale values, not arbitrary pixel values
3. **Breathing room** - Components should have internal padding (minimum 1rem)
4. **Visual hierarchy** - Larger gaps between sections than within sections

---

## Scale

Modular scale: 1.25

## Values

<table>
  <thead><tr><th>Token</th><th>Value</th><th>Preview</th></tr></thead>
  <tbody>
    <tr><td><code>0</code></td><td><code>0</code></td><td><div style="width: 0; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>1</code></td><td><code>0.25rem</code></td><td><div style="width: 0.25rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>2</code></td><td><code>0.5rem</code></td><td><div style="width: 0.5rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>3</code></td><td><code>0.75rem</code></td><td><div style="width: 0.75rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>4</code></td><td><code>1rem</code></td><td><div style="width: 1rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>5</code></td><td><code>1.25rem</code></td><td><div style="width: 1.25rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>6</code></td><td><code>1.5rem</code></td><td><div style="width: 1.5rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>8</code></td><td><code>2rem</code></td><td><div style="width: 2rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>10</code></td><td><code>2.5rem</code></td><td><div style="width: 2.5rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>12</code></td><td><code>3rem</code></td><td><div style="width: 3rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>16</code></td><td><code>4rem</code></td><td><div style="width: 4rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>20</code></td><td><code>5rem</code></td><td><div style="width: 5rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
    <tr><td><code>24</code></td><td><code>6rem</code></td><td><div style="width: 6rem; height: 20px; background-color: var(--kearney-emphasis);"></div></td></tr>
  </tbody>
</table>

---

## Usage Guidelines

### Spacing Hierarchy

Use spacing to establish visual hierarchy and grouping:

| Context | Recommended Spacing | Token | Example |
|---------|---------------------|-------|---------|
| Between sections | 3rem+ | `12`, `16`, `20` | Major page sections |
| Between components | 1.5-2rem | `6`, `8` | Cards, panels, KPIs |
| Between related items | 0.75-1rem | `3`, `4` | Form fields, list items |
| Component padding (large) | 1.5-2rem | `6`, `8` | Card interiors, modals |
| Component padding (medium) | 1rem | `4` | Buttons, badges |
| Component padding (small) | 0.5rem | `2` | Inline tags, chips |
| Element spacing | 0.25-0.5rem | `1`, `2` | Icon-to-text, label spacing |

### Recommended Defaults

**Page-level:**
```css
.page {
  padding: 2rem;              /* space-8: breathing room from edges */
}

.section {
  margin-bottom: 3rem;        /* space-12: generous section separation */
}
```

**Component-level:**
```css
.card {
  padding: 1.5rem;            /* space-6: internal breathing room */
  margin-bottom: 1.5rem;      /* space-6: separation from next card */
}

.kpi-grid {
  gap: 1rem;                  /* space-4: consistent gaps between KPIs */
}
```

**Element-level:**
```css
.button {
  padding: 0.75rem 1.25rem;  /* space-3 vertical, space-5 horizontal */
  gap: 0.5rem;                /* space-2: icon-to-text spacing */
}

.form-field {
  margin-bottom: 1rem;        /* space-4: field separation */
}
```

### Common Patterns

**Dashboard Layout:**
```css
.dashboard {
  padding: 2rem;                         /* space-8: page padding */
}

.dashboard-header {
  margin-bottom: 2rem;                   /* space-8: header separation */
}

.dashboard-section {
  margin-bottom: 3rem;                   /* space-12: section separation */
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;                           /* space-6: generous card gaps */
}
```

**Form Layout:**
```css
.form {
  padding: 1.5rem;                       /* space-6: form padding */
}

.form-group {
  margin-bottom: 1.5rem;                 /* space-6: group separation */
}

.form-field {
  margin-bottom: 1rem;                   /* space-4: field spacing */
}

.form-label {
  margin-bottom: 0.5rem;                 /* space-2: label-to-input */
}
```

### Examples

**Good (generous whitespace):**
```html
<div style="padding: 2rem;">
  <section style="margin-bottom: 3rem;">
    <h2 style="margin-bottom: 1.5rem;">Platform Health</h2>
    <div style="display: grid; gap: 1.5rem;">
      <div class="kpi-card" style="padding: 1.5rem;">
        <p style="margin-bottom: 0.5rem;">Data Quality</p>
        <h3>92.5</h3>
      </div>
    </div>
  </section>
</div>
```

**Bad (cramped spacing):**
```html
<!-- ❌ Too tight - no breathing room -->
<div style="padding: 0.5rem;">
  <section style="margin-bottom: 0.5rem;">
    <h2 style="margin-bottom: 0.25rem;">Platform Health</h2>
    <div style="display: grid; gap: 0.5rem;">
      <div class="kpi-card" style="padding: 0.5rem;">
        <p style="margin-bottom: 0.25rem;">Data Quality</p>
        <h3>92.5</h3>
      </div>
    </div>
  </section>
</div>
```

### Anti-Patterns to Avoid

**Don't:**
- Use arbitrary pixel values (e.g., `17px`, `23px`) - use modular scale
- Cram components too close together (minimum 1rem between cards)
- Use tight padding inside components (minimum 1rem for card padding)
- Create uneven spacing (be consistent with tokens)

**Do:**
- Use spacing tokens from the modular scale
- Prefer larger spacing values (6, 8, 12 for major elements)
- Create clear visual hierarchy with spacing differences
- Give content room to breathe

### Responsive Spacing

Reduce spacing on mobile, but maintain hierarchy:

```css
/* Desktop */
.section {
  margin-bottom: 3rem;        /* space-12 */
}

.card {
  padding: 1.5rem;            /* space-6 */
}

/* Mobile */
@media (max-width: 768px) {
  .section {
    margin-bottom: 2rem;      /* space-8 (still generous) */
  }

  .card {
    padding: 1rem;            /* space-4 (minimum comfortable) */
  }
}
```

### Accessibility

- **Tap target spacing**: Minimum 0.5rem (8px) between interactive elements
- **Readability**: Generous line spacing (1.5) combined with paragraph spacing (1rem+)
- **Scanability**: Clear visual grouping through spacing differences
- **Touch-friendly**: Larger padding on buttons and form elements (min 0.75rem vertical)

