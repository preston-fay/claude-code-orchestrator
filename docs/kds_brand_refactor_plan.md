# KDS Brand Refactor Plan

**Generated:** 2025-11-19
**Purpose:** Complete plan for aligning KDS to Kearney brand standards
**Status:** Ready for implementation

## Executive Summary

This refactor brings the Kearney Design System (KDS) into strict alignment with Kearney brand guidelines. The core change is removing ALL non-brand colors (greens, oranges, reds, blues) and implementing a **white + slate + purple accent** color scheme.

**Scope:**
- 20+ color violations to fix
- 8 token files to update
- 6+ components to refactor
- 5 chart configurations to update
- Documentation and validation scripts to create

**Impact:**
- ✅ Brand compliance across all outputs
- ✅ Consistent visual language
- ✅ CI enforcement of color palette
- ✅ Future-proof design system

---

## Phase 1: Token & Palette Updates

### 1.1 Update `design_system/tokens.json`

**Current Issues:**
- Contains green success colors (`#2E7D32`, `#E8F5E9`, `#66BB6A`, `#1B5E20`)
- Contains orange warning colors (`#ED6C02`, `#FFF3E0`, `#FFA726`, `#E65100`)
- Contains red error colors (`#D32F2F`, `#FFEBEE`, `#EF5350`, `#B71C1C`)
- Missing approved greys and secondary purples

**Changes:**

#### Add Missing Approved Colors
```json
"palette": {
  "core": {
    "charcoal": "#1E1E1E",
    "silver": "#A5A5A5",
    "purple": "#7823DC",
    // Add complete grey scale
    "grey100": "#F5F5F5",
    "grey150": "#E6E6E6",
    "grey200": "#D2D2D2",
    "grey250": "#C8C8C8",
    "grey350": "#B9B9B9",
    "grey500": "#A5A5A5",
    "grey550": "#8C8C8C",
    "grey600": "#787878",
    "grey650": "#5F5F5F",
    "grey700": "#4B4B4B",
    "grey850": "#323232",
    // Add complete purple scale (primary)
    "violet1": "#E6D2FA",
    "violet2": "#C8A5F0",
    "violet3": "#AF7DEB",
    "violet4": "#9150E1",
    "violet5": "#7823DC",
    // Add secondary purple scale
    "violet1Alt": "#D7BEF5",
    "violet2Alt": "#B991EB",
    "violet3Alt": "#A064E6",
    "violet4Alt": "#8737E1"
  }
}
```

#### Remap Semantic Colors (Light Theme)
```json
"theme": {
  "light": {
    "background": "#FFFFFF",
    "surface": "#F5F5F5",
    "surfaceElevated": "#FFFFFF",
    "text": "#1E1E1E",
    "textMuted": "#787878",
    "textInverse": "#FFFFFF",
    "border": "#D2D2D2",
    "borderSubtle": "#E6E6E6",
    "borderMedium": "#C8C8C8",
    "emphasis": "#7823DC",
    "emphasisHover": "#9150E1",
    "emphasisLight": "#E6D2FA",
    // REMOVE: success, successTint, warning, warningTint, error, errorTint
    // REPLACE WITH:
    "positive": "#7823DC",      // Use purple for positive emphasis
    "positiveTint": "#E6D2FA",  // Light purple background
    "negative": "#4B4B4B",      // Dark grey for negative
    "negativeTint": "#F5F5F5",  // Light grey background
    "neutral": "#787878",       // Mid grey for neutral
    "neutralTint": "#F5F5F5",   // Light grey background
    "spotColor": "#7823DC",
    "chartMuted": "#A5A5A5",
    "chartHighlight": "#7823DC"
  }
}
```

#### Remap Semantic Colors (Dark Theme)
```json
"theme": {
  "dark": {
    "background": "#000000",
    "surface": "#1E1E1E",
    "surfaceElevated": "#2D2D2D",
    "text": "#FFFFFF",
    "textMuted": "#A5A5A5",
    "textInverse": "#1E1E1E",
    "border": "#4B4B4B",
    "borderSubtle": "#323232",
    "borderMedium": "#5F5F5F",
    "emphasis": "#AF7DEB",
    "emphasisHover": "#C8A5F0",
    "emphasisLight": "#8737E1",
    // REMOVE: success, successTint, warning, warningTint, error, errorTint
    // REPLACE WITH:
    "positive": "#AF7DEB",      // Lighter purple for dark mode
    "positiveTint": "#323232",  // Dark grey background
    "negative": "#787878",      // Mid grey for negative
    "negativeTint": "#1E1E1E",  // Very dark background
    "neutral": "#A5A5A5",       // Light grey for neutral
    "neutralTint": "#1E1E1E",   // Very dark background
    "spotColor": "#AF7DEB",
    "chartMuted": "#787878",
    "chartHighlight": "#C8A5F0"
  }
}
```

**Files to Update:**
- `design_system/tokens.json` ⬅️ Primary file
- `design_system/web/tokens.ts` (auto-synced)
- `design_system/web/tokens.css` (auto-synced)
- `apps/web/src/design-system/tokens.ts` (auto-synced)
- `src/server/static/tokens.css` (auto-synced)

---

### 1.2 Update `design_system/palettes.json`

**Current Issues:**
- Contains old dark purples (`#601FB5`, `#4A188E`, `#341167`)
- Contains semantic red/green colors in `semantic` section
- Contains `positive`/`negative` mapped to green/red

**Changes:**

#### Remove Old Dark Purples
Delete lines 11-13 (old purples: `#601FB5`, `#4A188E`, `#341167`)

#### Update Sequential Palette
```json
"sequential": {
  "purple": [
    "#E6D2FA",  // Lightest
    "#C8A5F0",
    "#AF7DEB",
    "#9150E1",
    "#7823DC",  // Primary (middle)
    "#323232",  // Darkest (grey, not purple)
    "#1E1E1E"   // Near black (grey, not purple)
  ]
}
```

#### Update Diverging Palette
```json
"diverging": {
  "purpleGrey": [
    "#7823DC",  // Purple (positive/primary)
    "#9150E1",
    "#AF7DEB",
    "#C8A5F0",
    "#E6D2FA",
    "#787878",  // Grey (neutral/secondary)
    "#A5A5A5",
    "#D2D2D2"
  ]
}
```

#### Update Semantic Section
```json
"semantic": {
  // REMOVE: success, warning, error, info with green/orange/red
  // REPLACE WITH:
  "emphasis": "#7823DC",
  "positive": "#7823DC",
  "neutral": "#787878",
  "negative": "#4B4B4B",
  "muted": "#A5A5A5"
}
```

#### Update Trend Section
```json
"trend": {
  // REMOVE: positive/negative with green/red
  // REPLACE WITH:
  "up": "#787878",       // Neutral grey + symbol ▲
  "down": "#787878",     // Neutral grey + symbol ▼
  "neutral": "#A5A5A5"   // Lighter grey + symbol ─
}
```

---

### 1.3 Update `apps/web/tailwind.config.js`

**Current Issues:**
- Has `grey.300: #BEBEBE` (not approved → use `#B9B9B9`)
- Has success/warning/error colors in light/dark themes
- Missing secondary purples and some greys

**Changes:**

#### Fix Grey Scale
```javascript
grey: {
  100: '#F5F5F5',
  150: '#E6E6E6',   // ADD
  200: '#D2D2D2',
  250: '#C8C8C8',   // ADD
  300: '#B9B9B9',   // CHANGE from #BEBEBE
  350: '#B9B9B9',   // ADD (duplicate for now)
  500: '#A5A5A5',
  550: '#8C8C8C',   // ADD
  600: '#787878',
  650: '#5F5F5F',   // ADD
  700: '#4B4B4B',
  800: '#2D2D2D',
  850: '#323232',   // ADD
  900: '#1A1A1A',
}
```

#### Add Secondary Purples
```javascript
violet: {
  1: '#E6D2FA',
  2: '#C8A5F0',
  3: '#AF7DEB',
  4: '#9150E1',
  5: '#7823DC',     // ADD (primary)
},
violetAlt: {        // ADD entire section
  1: '#D7BEF5',
  2: '#B991EB',
  3: '#A064E6',
  4: '#8737E1',
},
```

#### Update Light Theme Semantics
```javascript
light: {
  // Keep existing (mostly OK)
  background: '#FFFFFF',
  surface: '#F5F5F5',
  surfaceElevated: '#FFFFFF',
  text: '#1E1E1E',
  textMuted: '#787878',
  textInverse: '#FFFFFF',
  border: '#D2D2D2',
  borderSubtle: '#E6E6E6',     // ADD
  emphasis: '#7823DC',
  emphasisHover: '#9150E1',
  emphasisLight: '#E6D2FA',    // ADD
  // REMOVE: success, successTint, warning, warningTint, error, errorTint
  // ADD:
  positive: '#7823DC',
  positiveTint: '#E6D2FA',
  negative: '#4B4B4B',
  negativeTint: '#F5F5F5',
  neutral: '#787878',
  neutralTint: '#F5F5F5',
  spotColor: '#7823DC',
  chartMuted: '#A5A5A5',
  chartHighlight: '#7823DC',
}
```

#### Update Dark Theme Semantics (same pattern as light)

---

### 1.4 Update `src/dashboard/js/chart-config.js`

**Current Issues:**
- Has `purpleLight: #9B51E0` (not approved → use `#9150E1`)
- Has `purpleDark: #5A1AA8` (not approved → use grey or existing purple)
- Has `#121212` (not approved → use `#000000` or `#1E1E1E`)
- Has `#333333` (not approved → use `#323232`)
- Has `#E0E0E0` (not approved → use `#D2D2D2` or `#E6E6E6`)

**Changes:**

```javascript
export const COLORS = {
  purple: '#7823DC',
  purpleLight: '#9150E1',    // CHANGE from #9B51E0
  purpleDark: '#4B4B4B',     // CHANGE from #5A1AA8 (use grey instead)
  charcoal: '#1E1E1E',
  silver: '#A5A5A5',
  white: '#FFFFFF',

  // Additional purple shades for charts
  purple10: 'rgba(120, 35, 220, 0.1)',
  purple20: 'rgba(120, 35, 220, 0.2)',
  purple50: 'rgba(120, 35, 220, 0.5)',
  purple80: 'rgba(120, 35, 220, 0.8)',
};

export function getThemeColors(isDark = true) {
  return {
    text: isDark ? COLORS.white : COLORS.charcoal,
    textMuted: COLORS.silver,
    background: isDark ? '#000000' : '#FFFFFF',      // CHANGE from #121212
    surface: isDark ? '#1E1E1E' : '#F5F5F5',
    border: isDark ? '#323232' : '#D2D2D2'           // CHANGE from #333333 and #E0E0E0
  };
}
```

---

### 1.5 Update `.claude/knowledge/kearney_standards.yaml`

**CRITICAL:** This file still references old Kearney blue!

**Current:**
```yaml
brand_colors:
  primary: "Kearney blue (#003A70)"
  secondary: "Kearney light blue (#00A3E0)"
```

**Change to:**
```yaml
brand_colors:
  primary: "Kearney Purple (#7823DC)"
  accent: "Light Purple (#9150E1, #AF7DEB, #C8A5F0, #E6D2FA)"
  neutral: "Greys (#F5F5F5 to #1E1E1E)"
  visual_principle: "White + Slate + Purple Accent"
  forbidden: "NO blue, red, green, or orange"
```

---

## Phase 2: Component Updates

### 2.1 Update `apps/web/src/components/KPICard.tsx`

**Current Issue:**
Lines 36-44: Uses `colors.success` (green) and `colors.error` (red) for trend indicators.

**Fix:**

```typescript
const getTrendColor = (direction: TrendDirection): string => {
  // Use neutral greys - NO green/red
  switch (direction) {
    case 'up':
      return colors.textMuted;      // #787878 (neutral grey)
    case 'down':
      return colors.textMuted;      // #787878 (neutral grey)
    case 'neutral':
      return colors.textMuted;      // #787878 (neutral grey)
  }
};

const getTrendSymbol = (direction: TrendDirection): string => {
  // Rely on symbol for direction (not color)
  switch (direction) {
    case 'up':
      return '▲';
    case 'down':
      return '▼';
    case 'neutral':
      return '─';
  }
};
```

**Rationale:** Kearney brand does not use color-coded semantics (no red/green). Use **text + symbols** instead.

**Alternative (if purple emphasis desired):**
```typescript
const getTrendColor = (direction: TrendDirection): string => {
  switch (direction) {
    case 'up':
      return colors.emphasis;       // #7823DC (purple for emphasis)
    case 'down':
      return colors.text;           // #1E1E1E (dark for de-emphasis)
    case 'neutral':
      return colors.textMuted;      // #787878 (grey for neutral)
  }
};
```

---

### 2.2 Update Chart Components

**Files:**
- `apps/web/src/components/CategoricalBarChart.tsx`
- `apps/web/src/components/TimeseriesChart.tsx`
- `src/dashboard/js/charts/*.js`

**Required Changes:**
1. Ensure chart colors use only approved purple/grey palette
2. Verify NO gridlines are rendered
3. Use `getColorPalette()` from `chart-config.js` for multi-series
4. Ensure tooltips use theme colors (no hardcoded colors)

**Example Fix (if violations found):**
```typescript
// OLD: const colors = ['#FF6384', '#36A2EB', '#FFCE56'];
// NEW:
import { getColorPalette } from '../design-system/chart-config';
const colors = getColorPalette(datasetCount);
```

---

## Phase 3: Global Styles & CSS

### 3.1 Audit CSS Files

**Files to Review:**
- `src/dashboard/css/dashboard.css`
- `site/src/css/custom.css`
- `apps/web/src/App.css`
- `apps/web/src/index.css`
- `design_system/templates/c-suite/styles.css`

**Action:**
1. Search for hex colors in each file
2. Replace any non-approved colors with approved equivalents
3. Ensure ALL CAPS removal in any hardcoded text
4. Verify generous whitespace in layouts

**Common Replacements:**
- `#E0E0E0` → `#D2D2D2` or `#E6E6E6`
- `#BEBEBE` → `#B9B9B9`
- `#121212` → `#000000` or `#1E1E1E`
- `#333333` → `#323232`
- Any green/red/orange → purple or grey

---

## Phase 4: Validation & Enforcement

### 4.1 Create Color Validation Script

**File:** `scripts/validate_kds_colors.py`

**Purpose:** Scan all KDS files for hex colors and fail if non-approved colors found.

**Implementation:**

```python
"""Validate KDS color compliance."""

import re
import sys
from pathlib import Path
from typing import Set, List, Tuple

# Approved Kearney palette
APPROVED_COLORS = {
    # Dark & White
    "#1E1E1E", "#FFFFFF", "#000000",
    # Greys
    "#F5F5F5", "#E6E6E6", "#D2D2D2", "#C8C8C8", "#B9B9B9",
    "#A5A5A5", "#8C8C8C", "#787878", "#5F5F5F", "#4B4B4B",
    "#323232", "#2D2D2D", "#1A1A1A",
    # Purples (primary)
    "#7823DC", "#9150E1", "#AF7DEB", "#C8A5F0", "#E6D2FA",
    # Purples (secondary)
    "#8737E1", "#A064E6", "#B991EB", "#D7BEF5",
    # Additional
    "#FAFAFA",  # Very light grey (alternating table rows)
}

# Files to scan
SCAN_PATTERNS = [
    "design_system/**/*.json",
    "design_system/**/*.ts",
    "design_system/**/*.js",
    "design_system/**/*.css",
    "apps/web/src/**/*.tsx",
    "apps/web/src/**/*.ts",
    "apps/web/src/**/*.css",
    "apps/web/tailwind.config.js",
    "src/dashboard/**/*.js",
    "src/dashboard/**/*.css",
]

# Files to ignore
IGNORE_PATTERNS = [
    "*/node_modules/*",
    "*/dist/*",
    "*/build/*",
    "*/__pycache__/*",
    "htmlcov/*",
    "clients/*/governance.yaml",    # Client examples OK
    ".claude/knowledge/*",          # After updating kearney_standards.yaml
]

HEX_COLOR_PATTERN = re.compile(r'#[0-9A-Fa-f]{6}\b')

def scan_file(file_path: Path) -> List[Tuple[int, str]]:
    """Scan a file for hex colors and return violations."""
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for match in HEX_COLOR_PATTERN.finditer(line):
                    color = match.group().upper()
                    if color not in APPROVED_COLORS:
                        violations.append((line_num, color))
    except (UnicodeDecodeError, PermissionError):
        pass  # Skip binary files
    return violations

def validate_colors() -> int:
    """Validate all KDS files for color compliance."""
    root = Path(__file__).parent.parent
    violations_found = False

    print("🎨 Validating KDS Color Compliance...\n")

    for pattern in SCAN_PATTERNS:
        for file_path in root.glob(pattern):
            # Check ignore patterns
            if any(ignore in str(file_path) for ignore in IGNORE_PATTERNS):
                continue

            violations = scan_file(file_path)
            if violations:
                violations_found = True
                print(f"❌ {file_path.relative_to(root)}")
                for line_num, color in violations:
                    print(f"   Line {line_num}: {color} (not in approved palette)")

    if violations_found:
        print("\n❌ KDS color validation FAILED")
        print("See approved palette in docs/kds_color_audit.md")
        return 1
    else:
        print("✅ All colors comply with Kearney brand palette")
        return 0

if __name__ == "__main__":
    sys.exit(validate_colors())
```

**CI Integration:**

Add to `.github/workflows/kds-validation.yml`:

```yaml
name: KDS Validation

on: [push, pull_request]

jobs:
  validate-colors:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Validate KDS Colors
        run: python scripts/validate_kds_colors.py
```

---

### 4.2 Update `tests/test_kds_tokens.py`

**Add test for approved colors:**

```python
def test_only_approved_colors_in_tokens():
    """Ensure tokens.json contains only approved Kearney colors."""
    approved = {
        "#1E1E1E", "#FFFFFF", "#000000",
        "#F5F5F5", "#E6E6E6", "#D2D2D2", "#C8C8C8", "#B9B9B9",
        "#A5A5A5", "#8C8C8C", "#787878", "#5F5F5F", "#4B4B4B",
        "#323232", "#2D2D2D", "#1A1A1A", "#FAFAFA",
        "#7823DC", "#9150E1", "#AF7DEB", "#C8A5F0", "#E6D2FA",
        "#8737E1", "#A064E6", "#B991EB", "#D7BEF5",
    }

    tokens_file = Path(__file__).parent.parent / "design_system" / "tokens.json"
    with open(tokens_file) as f:
        content = f.read()

    hex_colors = set(re.findall(r'#[0-9A-Fa-f]{6}', content))
    hex_colors_upper = {c.upper() for c in hex_colors}

    violations = hex_colors_upper - approved

    assert not violations, f"Non-approved colors found: {violations}"
```

---

## Phase 5: Documentation

### 5.1 Update `site/docs/design-system/colors.md`

**Complete rewrite with:**
- Approved color palette (with swatches if possible)
- Usage guidelines (white + slate + purple accent)
- Semantic color mapping (positive/negative/neutral)
- Forbidden colors list
- Code examples

**Structure:**

```markdown
# KDS Colors

## Brand Principle

Kearney's visual language is built on **white + slate + purple accent**.

- **Foundation:** White and neutral greys
- **Emphasis:** Purple for key actions and information
- **Forbidden:** NO green, red, orange, or blue

## Color Palette

### Dark & White
[Color swatches]
- `#1E1E1E` - Dark (primary text, dark theme surface)
- `#FFFFFF` - White (backgrounds, inverse text)
- `#000000` - Black (dark theme background)

### Greys
[Color swatches with full scale]

### Purples
[Color swatches with primary and secondary sets]

## Usage Guidelines

### Backgrounds
- **Primary:** White (`#FFFFFF`)
- **Secondary:** Light grey (`#F5F5F5`)
- **Elevated:** White with shadow

### Text
- **Primary:** Dark (`#1E1E1E`)
- **Muted:** Grey (`#787878`)
- **Inverse:** White (`#FFFFFF`)

### Emphasis
- **Primary:** Purple (`#7823DC`)
- **Hover:** Lighter purple (`#9150E1`)
- **Highlights:** Light purple tint (`#E6D2FA`)

### Semantic States (NO red/green/orange)
- **Positive:** Purple (`#7823DC`) or neutral grey + ▲ symbol
- **Negative:** Dark grey (`#4B4B4B`) or neutral grey + ▼ symbol
- **Neutral:** Mid grey (`#787878`)

## Forbidden

❌ **Never use:**
- Green (old semantic success color)
- Red (old semantic error color)
- Orange (old semantic warning color)
- Blue (old Kearney brand color)

## Code Examples
[Add TypeScript/CSS examples]
```

---

### 5.2 Update Other Design System Docs

- `site/docs/design-system/overview.md` - Update principles
- `site/docs/design-system/typography.md` - Add "no ALL CAPS" rule
- `site/docs/design-system/spacing.md` - Emphasize generous whitespace

---

## Phase 6: Demo Page

### 6.1 Create KDS Demo Page

**File:** `apps/web/src/pages/KDSDemo.tsx` or update existing demo

**Contents:**
1. **Color Swatches** - All approved colors displayed
2. **Buttons** - Primary, secondary, text-only variants
3. **KPI Cards** - With different trend indicators (up/down/neutral)
4. **Tables** - Header, alternating rows, hover state
5. **Badges/Tags** - Different variants
6. **Charts** - Bar, line, pie with purple/grey palette
7. **Typography** - Headings (sentence case), body text
8. **Spacing Examples** - Generous whitespace demonstration

**Validation:**
- All elements use only approved palette
- No green/red/orange visible
- No ALL CAPS headings
- No gridlines in charts
- Generous whitespace evident

---

## Phase 7: Final Cleanup

### 7.1 Remove Old Purple Shades

**File:** `design_system/palettes.json`

Remove lines with:
- `#601FB5`
- `#4A188E`
- `#341167`

These are old, deprecated purples not in the approved palette.

---

### 7.2 Update Sync Script

**File:** `scripts/sync_tokens_for_docs.py`

Ensure this script syncs the updated `tokens.json` to all dependent files:
- `design_system/web/tokens.ts`
- `design_system/web/tokens.css`
- `apps/web/src/design-system/tokens.ts`
- `src/server/static/tokens.css`

Run after token updates to propagate changes.

---

## Implementation Checklist

### Phase 1: Tokens ✅
- [ ] Update `design_system/tokens.json` (add greys, purples; remove green/red/orange)
- [ ] Update `design_system/palettes.json` (remove old purples, update semantic)
- [ ] Update `apps/web/tailwind.config.js` (fix greys, add violetAlt, update semantics)
- [ ] Update `src/dashboard/js/chart-config.js` (fix purple shades, theme colors)
- [ ] Update `.claude/knowledge/kearney_standards.yaml` (remove blue, add purple)
- [ ] Run `scripts/sync_tokens_for_docs.py` to propagate changes

### Phase 2: Components ✅
- [ ] Update `apps/web/src/components/KPICard.tsx` (remove green/red trends)
- [ ] Audit `apps/web/src/components/CategoricalBarChart.tsx`
- [ ] Audit `apps/web/src/components/TimeseriesChart.tsx`
- [ ] Audit `src/dashboard/js/charts/*.js` files

### Phase 3: Global Styles ✅
- [ ] Audit `src/dashboard/css/dashboard.css`
- [ ] Audit `site/src/css/custom.css`
- [ ] Audit `apps/web/src/App.css`
- [ ] Audit `apps/web/src/index.css`
- [ ] Audit `design_system/templates/c-suite/styles.css`

### Phase 4: Validation ✅
- [ ] Create `scripts/validate_kds_colors.py`
- [ ] Add CI workflow `.github/workflows/kds-validation.yml`
- [ ] Update `tests/test_kds_tokens.py` with approved color test
- [ ] Run validation script and fix any violations

### Phase 5: Documentation ✅
- [ ] Rewrite `site/docs/design-system/colors.md`
- [ ] Update `site/docs/design-system/overview.md`
- [ ] Update `site/docs/design-system/typography.md` (add no ALL CAPS rule)
- [ ] Update `site/docs/design-system/spacing.md` (add generous whitespace)

### Phase 6: Demo ✅
- [ ] Create/update KDS demo page
- [ ] Verify all components use approved colors
- [ ] Verify no gridlines in charts
- [ ] Verify no ALL CAPS headings
- [ ] Verify generous whitespace

### Phase 7: Cleanup ✅
- [ ] Remove old purple shades from `palettes.json`
- [ ] Run full test suite
- [ ] Run color validation script
- [ ] Generate demo page screenshots for documentation

---

## Success Criteria

**Before Merge:**
1. ✅ `scripts/validate_kds_colors.py` passes with zero violations
2. ✅ All tests pass (`pytest tests/test_kds_tokens.py`)
3. ✅ Demo page renders with no green/red/orange colors
4. ✅ Charts have no gridlines
5. ✅ No ALL CAPS headings in any component
6. ✅ `.claude/knowledge/kearney_standards.yaml` references purple (not blue)

**Documentation:**
1. ✅ `docs/kds_color_audit.md` shows zero non-compliant colors
2. ✅ `site/docs/design-system/colors.md` fully updated
3. ✅ `docs/kds_brand_alignment_summary.md` created with before/after

---

## Rollback Plan

If issues arise:
1. Revert `design_system/tokens.json` to previous version
2. Run `scripts/sync_tokens_for_docs.py` to propagate revert
3. Restart browser instances to clear cached styles
4. Investigate issue before re-attempting

---

## Estimated Effort

- **Phase 1 (Tokens):** 2-3 hours
- **Phase 2 (Components):** 1-2 hours
- **Phase 3 (Global Styles):** 1-2 hours
- **Phase 4 (Validation):** 1 hour
- **Phase 5 (Documentation):** 2 hours
- **Phase 6 (Demo):** 1 hour
- **Phase 7 (Cleanup):** 30 minutes

**Total:** ~9-12 hours

---

## Next Steps

Ready to begin implementation. Start with Phase 1 (token updates) as all other changes depend on the token system.
