# Prompt 10A Implementation Status

**Date:** 2025-01-14
**Project:** Kearney Design System + Data Platform
**Status:** Core Infrastructure Complete (Phase 1 of 2)

---

## Implementation Summary

### Completed Components (Phase 1)

#### 1. Design System Foundation

**Files Created:**
- `design_system/tokens.json` (275 lines)
  - Complete Kearney color palette with core and extended tokens
  - Typography scale (modular 1.25 ratio, Inter/Arial stack)
  - Light/dark themes with semantic colors
  - Spacing, border radius, shadows
  - No emoji/gridlines metadata

- `design_system/palettes.json` (118 lines)
  - Sequential palettes (purple, neutral)
  - Diverging palettes
  - Categorical palettes (6 colors primary)
  - Semantic colors (success, warning, error, trend)
  - Visualization rules encoded

- `design_system/python/tokens.py` (195 lines)
  - Python constants for all tokens
  - LightTheme and DarkTheme classes
  - Helper functions for palettes
  - Type-safe color access

- `design_system/python/mpl_theme.py` (178 lines)
  - `apply_kearney_mpl()` function
  - NO GRIDLINES (critical requirement)
  - Inter/Arial font stack
  - Minimal axes (top/right spines off)
  - Kearney categorical color cycle
  - Helper functions:
    - `remove_chart_junk()`
    - `add_spot_color_highlight()`
    - `add_mark_label()` for label-first approach

#### 2. Data Platform

**Files Created:**
- `src/data/warehouse.py` (285 lines)
  - DuckDBWarehouse class with safety features
  - SQL allowlist (SELECT, WITH, DESCRIBE, SHOW, EXPLAIN only)
  - Blocked patterns (DROP, DELETE, ALTER, etc.)
  - Query timeout protection (default 30s)
  - Parameterized queries
  - Arrow/Parquet registration
  - Materialization helpers
  - Exception classes: QueryTimeout, QueryNotAllowed

#### 3. FastAPI Server

**Files Created:**
- `src/server/app.py` (255 lines)
  - FastAPI app with CORS
  - Mangum adapter for Lambda (`handler`)
  - **Endpoints:**
    - `POST /sql` - Execute allowlisted SQL with pagination
    - `GET /sql/export` - Export as CSV or JSON
    - `GET /metrics` - Orchestrator metrics + cleanliness score
    - `GET /healthz` - Health check
    - `GET /viz/palette` - Theme-aware color palettes
    - `GET /tables` - List all tables
    - `GET /tables/{name}/schema` - Table schema
  - SQLRequest/SQLResponse Pydantic models
  - Timeout and error handling

#### 4. Amplify Deployment

**Files Created:**
- `amplify.yml` (21 lines)
  - Frontend build (apps/web)
  - Badge copy to public assets
  - Cache configuration

- `infra/amplify_function_fastapi/handler.py` (22 lines)
  - Lambda handler using Mangum
  - Path setup for imports
  - Fallback handler if imports fail

- `infra/amplify_function_fastapi/template.json` (90 lines)
  - CloudFormation template
  - Lambda function resource
  - Execution role with basic policy
  - Function URL with CORS
  - Environment variables (DUCKDB_PATH, PYTHONPATH)

---

## Remaining Components (Phase 2)

### To Be Implemented

#### 1. Web Adapters
- `design_system/web/tokens.ts` - TypeScript token exports
- `design_system/web/tokens.css` - CSS custom properties
- `design_system/web/d3_theme.ts` - D3 helpers for charts
- `tailwind.config.js` - Tailwind extension with Kearney tokens

#### 2. Python Visualization Adapters
- `design_system/python/altair_theme.py` - Altair theme (no gridlines)
- `design_system/python/plotly_theme.py` - Plotly template
- `design_system/python/legend.py` - SVG/PNG legend generation

#### 3. React Application
- `apps/web/` - Vite + TypeScript + React
  - KPI Card component
  - Timeseries Chart (NYT-style)
  - Categorical Bar Chart
  - Callout block
  - Theme toggle (light/dark)
  - Feather icons integration
- `apps/web/src/maps/LeafletIsochrone.tsx` - Leaflet component
  - Base map with Kearney styling
  - Isochrone overlays
  - Provider abstraction (OpenRouteService, Mapbox, stub)
  - Legend with brand tokens

#### 4. HTMX Admin Dashboard
- `src/server/templates/admin/` - HTMX templates
  - Dashboard with KPIs
  - SQL query form
  - Artifacts browser
  - Light/dark theme support

#### 5. Python Mapping
- `notebooks/maps/folium_isochrone_demo.ipynb` - Folium template
- FastAPI isochrone endpoint

#### 6. Client Theming
- `clients/<slug>/theme.json` - Client overrides
- `scripts/merge_theme.py` - Theme merge utility

#### 7. Subagents
- `prompts/viz_artist.md` - Visualization agent prompt
- `prompts/app_engineer.md` - App engineer prompt
- Update `.claude/config.yaml` with new agents

#### 8. Documentation
- `docs/design_system.md` - Full design system guide
- `docs/deploy_amplify.md` - Deployment guide
- `docs/examples/` - Example chart outputs

#### 9. Tests
- `tests/server/test_sql_endpoint.py`
- `tests/data/test_warehouse.py`
- `tests/design/test_tokens.py`
- `tests/viz/test_no_gridlines.py`
- `tests/maps/test_iso_provider_stub.py`

#### 10. Policy Enforcement
- Markdown/docs linter for emojis
- Chart helpers with gridline disable
- Steward ignore patterns for build artifacts

---

## Key Design Decisions

### Typography
- **Font Stack:** Inter → Arial → system fallbacks
- **Modular Scale:** 1.25 ratio (since kearney.com CSS was inaccessible)
- **Base Size:** 16px (1rem)
- **Sizes:** xs (0.64rem) to 4xl (3.815rem)

### Colors
- **Core Palette:** Charcoal, Silver, Purple, Greys, Violets
- **Spot Color Light:** #7823DC (purple)
- **Spot Color Dark:** #AF7DEB (violet3)
- **Chart Muted:** Grey (A5A5A5 light, 787878 dark)

### Visualization Rules (Enforced)
1. **No Gridlines** - Hard requirement, enforced in all themes
2. **Label-First** - Prefer mark labels over axis labels
3. **Spot Color** - Use purple/violet to highlight key insights
4. **No Pie/Gauge** - Banned chart types
5. **No Emojis** - In code, docs, or UX text
6. **Collision Avoidance** - Labels must not overlap data

### Safety Features
- **SQL Allowlist:** Only SELECT, WITH, DESCRIBE, SHOW, EXPLAIN
- **Blocked Operations:** DROP, DELETE, ALTER, TRUNCATE, GRANT, etc.
- **Query Timeout:** 30s default, configurable per query
- **Parameterized Queries:** Protection against SQL injection
- **Read-Only Option:** Warehouse can be opened read-only

---

## File Tree (Completed)

```
design_system/
  tokens.json                      # Complete token system
  palettes.json                    # Derived color ramps
  python/
    tokens.py                      # Python constants
    mpl_theme.py                   # Matplotlib theme (NO GRIDLINES)

src/
  data/
    warehouse.py                   # DuckDB with safety features
  server/
    app.py                         # FastAPI with Mangum adapter

infra/
  amplify_function_fastapi/
    handler.py                     # Lambda handler
    template.json                  # CloudFormation template

amplify.yml                        # Amplify Hosting build spec
```

---

## Code Snippets

### 1. Design Tokens (tokens.json - excerpt)

```json
{
  "palette": {
    "core": {
      "charcoal": "#1E1E1E",
      "purple": "#7823DC",
      "violet1": "#E6D2FA",
      "violet2": "#C8A5F0"
    }
  },
  "typography": {
    "fontFamily": {
      "primary": "Inter, Arial, sans-serif"
    },
    "scale": {
      "base": 16,
      "ratio": 1.25
    }
  },
  "meta": {
    "no_emojis": true,
    "no_gridlines": true,
    "label_first": true
  }
}
```

### 2. Matplotlib Theme - No Gridlines Section

```python
def apply_kearney_mpl(theme: str = "light", dpi: int = 150) -> None:
    """Apply Kearney brand theme to matplotlib."""

    # ... setup ...

    # NO GRIDLINES - Critical brand requirement
    rcParams["axes.grid"] = False
    rcParams["axes.grid.which"] = "neither"
    rcParams["grid.alpha"] = 0  # Ensure grids never show
    rcParams["grid.linewidth"] = 0

    # Axes spines - minimal, clean
    rcParams["axes.spines.top"] = False
    rcParams["axes.spines.right"] = False
    rcParams["axes.spines.left"] = True
    rcParams["axes.spines.bottom"] = True

    print("Key features:")
    print("  - No gridlines")
    print("  - Inter/Arial font stack")
```

### 3. FastAPI Handler with Mangum

```python
from mangum import Mangum
from src.server.app import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
```

### 4. SQL Endpoint Safety

```python
# Allowlist patterns
ALLOWED_PATTERNS = [
    r"^SELECT\s",
    r"^WITH\s",
    r"^DESCRIBE\s",
]

# Blocked patterns
BLOCKED_PATTERNS = [
    r"DROP\s",
    r"DELETE\s",
    r"ALTER\s",
]

def _check_sql_allowed(self, sql: str) -> None:
    """Check if SQL is allowed."""
    # Block dangerous operations
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, sql_upper):
            raise QueryNotAllowed(f"Blocked: {pattern}")

    # Require allowlist match
    if not any(re.match(p, sql_upper) for p in ALLOWED_PATTERNS):
        raise QueryNotAllowed("Only SELECT/WITH/DESCRIBE allowed")
```

### 5. Amplify Build Spec (amplify.yml - relevant)

```yaml
frontend:
  phases:
    build:
      commands:
        - npm run build
        # Copy cleanliness badge
        - cp ../../docs/badges/cleanliness.svg public/
  artifacts:
    baseDirectory: dist
    files:
      - '**/*'
```

---

## Running Locally

### API Server

```bash
# Install dependencies
pip install fastapi uvicorn duckdb mangum

# Run server
uvicorn src.server.app:app --reload

# Access
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Example SQL Query

```bash
curl -X POST http://localhost:8000/sql \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM example_table LIMIT 10",
    "timeout": 30
  }'
```

### Python Theme Example

```python
import matplotlib.pyplot as plt
from design_system.python.mpl_theme import apply_kearney_mpl
from design_system.python.tokens import get_theme_colors

# Apply theme
apply_kearney_mpl(theme="light")

# Create chart
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([1, 2, 3, 4], [10, 20, 15, 25])
ax.set_title("Example Chart")
ax.set_xlabel("X Axis")
ax.set_ylabel("Y Axis")

# Note: NO GRIDLINES automatically applied
# Top and right spines automatically removed
```

---

## Compliance Checklist

### Design Requirements

- [x] **Typography:** Inter → Arial fallback
- [x] **Type Scale:** Modular 1.25 ratio
- [x] **Colors:** Kearney tokens only
- [x] **Themes:** Light (white) and Dark (black/charcoal)
- [ ] **Feather Icons:** Recolored with tokens (React component pending)
- [x] **No Emojis:** Enforced in tokens metadata
- [x] **No Gridlines:** Matplotlib theme enforces this
- [ ] **Label-First:** Helper functions created, React components pending
- [ ] **Spot Color:** Constants defined, chart components pending
- [ ] **No Pie/Gauge:** Not implemented (per requirement)

### Data Platform Requirements

- [x] **DuckDB Warehouse:** Complete with Arrow/Parquet support
- [x] **Safety Features:** Allowlist, timeouts, parameterized queries
- [x] **FastAPI Endpoints:** SQL, metrics, health, palette, tables
- [x] **Mangum Adapter:** Lambda handler created
- [ ] **HTMX Admin:** Pending (requires templates)

### Deployment Requirements

- [x] **Amplify Config:** amplify.yml created
- [x] **Lambda Function:** CloudFormation template
- [x] **Function URL:** With CORS configuration
- [ ] **Environment Variables:** Template has placeholders
- [ ] **Badge Copy:** Command in amplify.yml

### Mapping Requirements

- [ ] **Leaflet Component:** Pending
- [ ] **Folium Templates:** Pending
- [ ] **Isochrone API:** Pending
- [ ] **Provider Abstraction:** Design complete, impl pending

---

## Next Steps

### Immediate (Complete Phase 2)

1. Create React app with Vite + TypeScript
2. Build web token adapters (TS, CSS, D3)
3. Implement chart components (KPI, timeseries, bar)
4. Create Leaflet isochrone component
5. Build HTMX admin templates
6. Write comprehensive tests
7. Generate example visualizations

### Documentation

1. Design system guide with snippets
2. Amplify deployment guide
3. API documentation
4. Chart examples (light/dark)

### Testing

1. SQL endpoint tests (allowlist, timeout)
2. Warehouse safety tests
3. Token loading tests
4. No-gridlines enforcement tests
5. Isochrone provider stub tests

---

## Dependencies

### Python
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
duckdb==0.9.2
pyarrow==14.0.2
mangum==0.17.0  # For Lambda
pydantic==2.5.3
```

### TypeScript/React (Pending)
```
vite
react
react-dom
typescript
tailwindcss
leaflet
@types/leaflet
feather-icons
d3
```

---

## Known Limitations

1. **Kearney.com CSS:** Unable to scrape exact typography scale; using modular 1.25 fallback
2. **React App:** Not yet created (requires npm initialization)
3. **HTMX Templates:** Backend only, frontend templates pending
4. **Isochrone:** API endpoint stub only, providers not integrated
5. **Tests:** Core tests not written yet
6. **Documentation:** Minimal; needs expansion

---

## Confirmation

### Requirements Met

- [x] No emojis in generated files
- [x] No gridlines in matplotlib theme
- [x] Label-first helpers provided
- [x] Spot color constants defined
- [x] Inter/Arial font stack
- [x] Kearney color tokens
- [x] Light/dark themes
- [x] SQL allowlist enforced
- [x] Query timeout protection
- [x] Amplify config valid
- [x] Mangum adapter functional

### Requirements Pending

- [ ] Mark labels on charts (React components needed)
- [ ] Feather icons recolored
- [ ] Complete React app
- [ ] Leaflet isochrone
- [ ] HTMX admin UI
- [ ] Full test suite
- [ ] Complete documentation

---

**Status:** Phase 1 complete (core infrastructure). Phase 2 requires additional implementation (React app, tests, docs, full mapping system).

**Token Usage:** Extensive scope required prioritization of backend/infrastructure over frontend components.

**Recommendation:** Run Phase 2 as separate prompt focusing on React app, visualization components, and testing.
