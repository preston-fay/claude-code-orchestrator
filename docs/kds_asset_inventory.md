# KDS Asset Inventory

**Generated:** 2025-11-19
**Purpose:** Complete inventory of Kearney Design System assets for brand alignment audit

## 1. Design Token Files

### Core Tokens

| File | Purpose | Status |
|------|---------|--------|
| `design_system/tokens.json` | Master token definition (JSON) | ⚠️ Contains non-brand colors |
| `design_system/palettes.json` | Extended palette definitions | ⚠️ Contains non-brand colors |
| `design_system/web/tokens.ts` | TypeScript tokens for web | Synced from tokens.json |
| `design_system/web/tokens.css` | CSS custom properties | Synced from tokens.json |
| `design_system/python/tokens.py` | Python tokens (old system) | ⚠️ Uses different schema |
| `src/orchestrator/design/tokens.py` | Python token loader (new) | ✅ Loads from kearney_brand.yml |
| `apps/web/src/design-system/tokens.ts` | React app tokens | Synced from tokens.json |
| `src/server/static/tokens.css` | Server-side CSS tokens | Synced from tokens.json |

### Brand Configuration

| File | Purpose | Status |
|------|---------|--------|
| `src/orchestrator/design/kearney_brand.yml` | **Single source of truth** for brand tokens | ✅ Primary brand file |
| `scripts/sync_tokens_for_docs.py` | Token synchronization script | To be updated |

## 2. Theme Files

| File | Purpose | Status |
|------|---------|--------|
| `apps/web/tailwind.config.js` | Tailwind theme configuration | ⚠️ Contains non-brand colors |
| `design_system/web/d3_theme.ts` | D3.js chart theme | To be reviewed |
| `design_system/python/mpl_theme.py` | Matplotlib theme | ✅ Uses approved workflow |
| `apps/web/src/design-system/d3_theme.ts` | React D3 theme | To be reviewed |
| `clients/acme-corp/theme.json` | Client override example | Not reviewed |
| `scripts/merge_theme.py` | Theme merging utility | Not reviewed |

## 3. Global Styles

### CSS Files

| File | Purpose | Status |
|------|---------|--------|
| `design_system/web/tokens.css` | CSS custom properties from tokens | Synced |
| `src/server/static/tokens.css` | Server CSS tokens | Synced |
| `src/dashboard/css/dashboard.css` | Dashboard-specific styles | To be reviewed |
| `site/src/css/custom.css` | Documentation site custom styles | To be reviewed |
| `apps/web/src/App.css` | React app global styles | To be reviewed |
| `apps/web/src/index.css` | React root styles | To be reviewed |
| `design_system/templates/c-suite/styles.css` | C-suite template styles | To be reviewed |

## 4. Component Library

### React Components

| File | Purpose | Status |
|------|---------|--------|
| `apps/web/src/components/KPICard.tsx` | KPI display card | ⚠️ Uses success/error colors |
| `apps/web/src/components/CategoricalBarChart.tsx` | Bar chart component | To be reviewed |
| `apps/web/src/components/TimeseriesChart.tsx` | Time series chart | To be reviewed |
| `apps/web/src/components/ThemeToggle.tsx` | Theme switcher | ✅ Likely OK |
| `apps/web/src/components/FlagGuard.tsx` | Feature flag guard | ✅ Likely OK |
| `site/src/components/HomepageFeatures/index.tsx` | Doc site homepage | To be reviewed |

### Context Providers

| File | Purpose | Status |
|------|---------|--------|
| `apps/web/src/contexts/ThemeContext.tsx` | Theme state management | ✅ Likely OK |

### Theme Manager

| File | Purpose | Status |
|------|---------|--------|
| `src/dashboard/js/theme-manager.js` | Dashboard theme switcher | To be reviewed |

## 5. Chart Configurations

### Chart.js (JavaScript/Web)

| File | Purpose | Status |
|------|---------|--------|
| `src/dashboard/js/chart-config.js` | Base Chart.js configuration | ⚠️ Has non-brand purple shades |
| `src/dashboard/js/charts/github-charts.js` | GitHub metrics charts | To be reviewed |
| `src/dashboard/js/charts/dora-charts.js` | DORA metrics charts | To be reviewed |
| `src/dashboard/js/charts/ai-review-charts.js` | AI review charts | To be reviewed |
| `src/dashboard/js/charts/contribution-charts.js` | Contribution charts | To be reviewed |

### Matplotlib (Python)

| File | Purpose | Status |
|------|---------|--------|
| `design_system/python/mpl_theme.py` | Matplotlib theme configuration | ✅ Uses token loader pattern |

## 6. HTML Templates

| File | Purpose | Status |
|------|---------|--------|
| `design_system/templates/c-suite/presentation.html` | C-suite presentation template | To be reviewed |
| `design_system/templates/c-suite/one-pager.html` | C-suite one-pager template | To be reviewed |
| `src/server/admin/templates/base.html` | Admin base template | To be reviewed |
| `src/server/admin/templates/index.html` | Admin index | To be reviewed |
| `src/server/admin/templates/sql.html` | SQL admin interface | To be reviewed |
| `src/server/admin/templates/artifacts.html` | Artifacts viewer | To be reviewed |

## 7. Documentation

| File | Purpose | Status |
|------|---------|--------|
| `site/docs/design-system/index.md` | Design system docs home | To be updated |
| `site/docs/design-system/overview.md` | Design system overview | To be updated |
| `site/docs/design-system/colors.md` | Color palette documentation | ⚠️ To be fully rewritten |
| `site/docs/design-system/typography.md` | Typography documentation | To be reviewed |
| `site/docs/design-system/spacing.md` | Spacing documentation | To be reviewed |

## 8. CLI & Utilities

| File | Purpose | Status |
|------|---------|--------|
| `src/orchestrator/cli_kds.py` | KDS CLI commands | To be reviewed |
| `scripts/sync_tokens_for_docs.py` | Token sync script | To be updated |
| `scripts/merge_theme.py` | Theme merging utility | To be reviewed |

## 9. Tests

| File | Purpose | Status |
|------|---------|--------|
| `tests/test_kds_tokens.py` | Token validation tests | To be updated |
| `tests/test_kds_preflight_and_registry.py` | KDS preflight tests | ✅ Brand guardrails in place |
| `tests/server/test_theme_routes.py` | Theme API tests | To be reviewed |
| `tests/design/test_theme_schema.py` | Theme schema validation | To be reviewed |
| `tests/design/test_merge_theme.py` | Theme merge tests | To be reviewed |

## Summary Statistics

- **Total Token Files:** 8
- **Total Theme Files:** 7
- **Total Global CSS Files:** 7
- **Total React Components:** 6
- **Total Chart Files:** 5
- **Total HTML Templates:** 6
- **Total Documentation Files:** 5
- **Total Test Files:** 5

## Next Steps

1. Complete color audit (categorize all hex values)
2. Research kearney.com for design patterns
3. Create refactor plan mapping violations to fixes
4. Implement token updates
5. Update all dependent files
6. Create validation script
7. Generate demo page
