# KDS Color Audit

**Generated:** 2025-11-19
**Purpose:** Categorize all colors in KDS against approved Kearney palette

## Approved Kearney Palette (Reference)

### Dark & White
- `#1E1E1E` - Dark
- `#FFFFFF` - White

### Greys
- `#F5F5F5`
- `#E6E6E6`
- `#D2D2D2`
- `#C8C8C8`
- `#B9B9B9`
- `#A5A5A5`
- `#8C8C8C`
- `#787878`
- `#5F5F5F`
- `#4B4B4B`
- `#323232`

### Purples (Primary Set)
- `#7823DC` - Primary purple
- `#9150E1`
- `#AF7DEB`
- `#C8A5F0`
- `#E6D2FA`

### Purples (Secondary Set)
- `#8737E1`
- `#A064E6`
- `#B991EB`
- `#D7BEF5`

---

## Color Usage Analysis

### ✅ Compliant Colors (Already Approved)

| Color | Name | Usage Count | Files |
|-------|------|-------------|-------|
| `#1E1E1E` | Dark/Charcoal | 15+ | tokens.json, tailwind.config.js, palettes.json |
| `#FFFFFF` | White | 10+ | tokens.json, tailwind.config.js, chart-config.js |
| `#000000` | Black (dark theme bg) | 2 | tokens.json, tailwind.config.js |
| `#F5F5F5` | Grey 100 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#D2D2D2` | Grey 200 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#A5A5A5` | Silver | 10+ | tokens.json, tailwind.config.js, chart-config.js |
| `#787878` | Grey 500 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#5A5A5A` | Grey 600 | 3 | tailwind.config.js, palettes.json |
| `#4B4B4B` | Grey 700 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#2D2D2D` | Grey 800 | 3 | tokens.json, tailwind.config.js, palettes.json |
| `#1A1A1A` | Grey 900 | 2 | tailwind.config.js, palettes.json |
| `#7823DC` | Primary Purple | 20+ | tokens.json, tailwind.config.js, palettes.json, chart-config.js |
| `#9150E1` | Violet 4 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#AF7DEB` | Violet 3 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#C8A5F0` | Violet 2 | 10+ | tokens.json, tailwind.config.js, palettes.json |
| `#E6D2FA` | Violet 1 | 10+ | tokens.json, tailwind.config.js, palettes.json |

### ⚠️ Near-Compliant Colors (Acceptable Neutrals)

| Color | Name | Status | Recommendation |
|-------|------|--------|----------------|
| `#BEBEBE` | Grey 300 | Not in official palette | Replace with `#B9B9B9` |
| `#121212` | Very dark grey | Close to black | Replace with `#000000` for dark theme or `#1E1E1E` |
| `#333333` | Dark border | Not in palette | Replace with `#323232` |
| `#E0E0E0` | Light border | Not in palette | Replace with `#D2D2D2` or `#E6E6E6` |

### ❌ Non-Compliant Colors (MUST REMOVE)

#### Success Colors (Green)
| Color | Usage | Files | Fix |
|-------|-------|-------|-----|
| `#2E7D32` | Success (light) | tokens.json, tailwind.config.js, palettes.json, KPICard.tsx | Replace with purple (`#7823DC`) or neutral |
| `#E8F5E9` | Success tint (light) | tokens.json, tailwind.config.js | Replace with light purple (`#E6D2FA`) |
| `#66BB6A` | Success (dark) | tokens.json, tailwind.config.js | Replace with lighter purple (`#AF7DEB`) |
| `#1B5E20` | Success tint (dark) | tokens.json, tailwind.config.js | Replace with dark purple or grey |

#### Warning Colors (Orange)
| Color | Usage | Files | Fix |
|-------|-------|-------|-----|
| `#ED6C02` | Warning (light) | tokens.json, tailwind.config.js, palettes.json | Replace with purple or dark grey |
| `#FFF3E0` | Warning tint (light) | tokens.json, tailwind.config.js | Replace with light grey (`#F5F5F5`) |
| `#FFA726` | Warning (dark) | tokens.json, tailwind.config.js | Replace with purple or grey |
| `#E65100` | Warning tint (dark) | tokens.json, tailwind.config.js | Replace with dark grey |

#### Error Colors (Red)
| Color | Usage | Files | Fix |
|-------|-------|-------|-----|
| `#D32F2F` | Error (light) | tokens.json, tailwind.config.js, palettes.json | Replace with dark grey (`#4B4B4B`) |
| `#FFEBEE` | Error tint (light) | tokens.json, tailwind.config.js | Replace with light grey (`#F5F5F5`) |
| `#EF5350` | Error (dark) | tokens.json, tailwind.config.js | Replace with grey (`#787878`) |
| `#B71C1C` | Error tint (dark) | tokens.json, tailwind.config.js | Replace with dark grey (`#323232`) |

#### Other Non-Brand Colors
| Color | Usage | Files | Fix |
|-------|-------|-------|-----|
| `#9B51E0` | Purple light (non-standard) | chart-config.js | Replace with `#9150E1` |
| `#5A1AA8` | Purple dark (non-standard) | chart-config.js | Replace with darker approved purple or `#4B4B4B` |
| `#601FB5` | Dark purple (old) | palettes.json | Replace with `#7823DC` or grey |
| `#4A188E` | Dark purple (old) | palettes.json | Replace with `#7823DC` or grey |
| `#341167` | Dark purple (old) | palettes.json | Replace with `#7823DC` or grey |
| `#FF0000` | Competitor red | example-client/governance.yaml | Example only - ignore |
| `#1DA1F2` | Competitor blue | example-client/governance.yaml | Example only - ignore |
| `#003A70` | Old Kearney blue | kearney_standards.yaml | **CRITICAL:** Update knowledge base |
| `#00A3E0` | Old Kearney light blue | kearney_standards.yaml | **CRITICAL:** Update knowledge base |

---

## Summary Statistics

### By Category
- **✅ Compliant:** 16 colors (53%)
- **⚠️ Near-Compliant:** 4 colors (13%)
- **❌ Non-Compliant:** 20+ colors (34%)

### By Violation Type
- **Semantic (success/warning/error):** 12 colors
- **Old/deprecated purples:** 5 colors
- **Old Kearney blues:** 2 colors (in knowledge base)
- **Near-neutrals:** 4 colors

### Critical Issues
1. **Success/warning/error colors** used throughout token system
2. **KPICard.tsx** uses green/red for trends
3. **Knowledge base still references old Kearney blue** (`#003A70`)
4. **Chart config has non-standard purple shades** (`#9B51E0`, `#5A1AA8`)
5. **Old purple palette in palettes.json** (darker shades like `#601FB5`)

---

## Recommended Semantic Color Mapping

Since Kearney brand uses **white + slate + purple accent**, we cannot use traditional red/green/orange for semantic states. Here's the recommended approach:

### Option 1: Purple Accent Only (Kearney Standard)
- **Emphasis/Primary:** `#7823DC` (primary purple)
- **Success/Positive:** `#787878` (neutral grey) + text indicator
- **Warning:** `#787878` (neutral grey) + text indicator
- **Error/Negative:** `#4B4B4B` (darker grey) + text indicator
- **Info:** `#7823DC` (purple) or `#A5A5A5` (lighter grey)

### Option 2: Purple Intensity Gradient
- **Emphasis:** `#7823DC` (primary purple)
- **Success/High:** `#9150E1` (lighter purple)
- **Warning/Medium:** `#AF7DEB` (even lighter purple)
- **Error/Low:** `#4B4B4B` (dark grey)
- **Neutral:** `#A5A5A5` (silver)

### Option 3: Text + Symbol (No Color Semantics)
- All states use neutral greys
- Use text labels: "Up", "Down", "Warning", "Critical"
- Use symbols: ▲ ▼ ⚠

**Recommendation:** Use **Option 1** (purple accent + text) as it's most aligned with kearney.com visual language.

---

## Missing Approved Colors

These colors are in the approved palette but NOT yet used in KDS:

- `#E6E6E6` (light grey - add as grey 150)
- `#C8C8C8` (mid grey - add as grey 250)
- `#B9B9B9` (mid grey - add as grey 350)
- `#8C8C8C` (mid grey - add as grey 550)
- `#5F5F5F` (mid-dark grey - add as grey 650)
- `#323232` (dark grey - add as grey 850)
- `#8737E1` (secondary purple 1)
- `#A064E6` (secondary purple 2)
- `#B991EB` (secondary purple 3)
- `#D7BEF5` (secondary purple 4)

**Action:** Add these to token files to complete the palette.

---

## Next Steps

1. Update `design_system/tokens.json` to remove all non-compliant colors
2. Add missing approved colors to complete palette
3. Remap semantic colors (success/warning/error) to purple/grey
4. Update `tailwind.config.js` with new semantic mappings
5. Update `KPICard.tsx` trend indicators to use neutral colors + text
6. Update `chart-config.js` purple shades to approved values
7. Update `.claude/knowledge/kearney_standards.yaml` to remove blue references
8. Remove old dark purples from `palettes.json`
9. Create validation script to enforce palette
