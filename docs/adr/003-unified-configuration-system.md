# ADR-003: Unified Configuration System

**Status:** Accepted
**Date:** 2025-11-14
**Deciders:** Orchestrator Team
**Context:** Phase 1.2 - Configuration Consolidation

---

## Context

The orchestrator had **3+ different config loading patterns** scattered across modules:
- `steward/config.py` - Custom HygieneConfig class
- `lifecycle/health_webhook.py` - YAML dict loading
- `lifecycle/security_scan.py` - YAML dict loading
- Various other modules loading YAML directly with `yaml.safe_load()`

This led to:
- **Code duplication** (3x `load_config()` implementations)
- **Inconsistent behavior** (different error handling, no validation)
- **No type safety** (configs returned as dicts or custom classes)
- **Hard to test** (no standard override mechanism)

---

## Decision

We will implement a **unified configuration system** using Pydantic with the following characteristics:

### 1. Single Source of Truth

All general application configuration flows through `common.config.AppConfig`:

```python
from common.config import load_config

config = load_config()  # Type-safe AppConfig object
```

### 2. Layered Override System

Configuration is resolved with clear precedence:

```
Base File → Environment Variables → CLI Overrides
(lowest)                               (highest)
```

### 3. Type Safety via Pydantic

All config values are validated at load time:

```python
class AppConfig(BaseModel):
    app: App
    paths: Paths
    logging: LoggingCfg
    governance: Governance
    runtime: Runtime
    secrets: Secrets
    cli: CLI
```

### 4. Environment Variable Convention

Use double-underscore for nesting:

```bash
ORCH_LOGGING__LEVEL=DEBUG → config.logging.level = "DEBUG"
ORCH_RUNTIME__MAX_PARALLEL_AGENTS=4 → config.runtime.max_parallel_agents = 4
```

### 5. Domain-Specific Configs Remain

Specialized configs (HygieneConfig, lifecycle configs) remain as-is for now. They serve different purposes than general app config and will be evaluated separately for migration.

---

## Alternatives Considered

### Alternative 1: Dataclasses Instead of Pydantic

**Pros:**
- Stdlib, no external dependency
- Simpler, less magic

**Cons:**
- No automatic validation
- No type coercion (env vars always strings)
- No field aliases for backward compatibility
- Manual serialization/deserialization

**Decision:** Rejected. Validation and type coercion are critical.

### Alternative 2: OmegaConf

**Pros:**
- Designed for ML/data science configs
- Supports advanced interpolation
- Hierarchical config merging

**Cons:**
- Additional dependency
- More complex than needed
- Less type-safe than Pydantic
- Overkill for our use case

**Decision:** Rejected. Pydantic is sufficient and more widely adopted.

### Alternative 3: Environment Variables Only

**Pros:**
- 12-factor app compliant
- Simple, no file loading
- Works well in containers

**Cons:**
- No complex nested structures
- Hard to manage 50+ config values as env vars
- No local development convenience (must set all vars)
- No config file versioning

**Decision:** Rejected. We support env vars as overrides but need file-based defaults.

### Alternative 4: Replace All Domain Configs Immediately

**Pros:**
- Single unified config system
- No confusion about which config to use

**Cons:**
- Breaking changes for existing code
- Domain configs serve specialized purposes (HygieneConfig has business logic)
- Large migration effort
- Higher risk

**Decision:** Rejected. Introduce new system, migrate incrementally.

---

## Consequences

### Positive

✅ **Type Safety:** Pydantic catches config errors at load time, not runtime
✅ **Testability:** Easy to override config in tests via `cli_overrides`
✅ **Environment Parity:** Same config system for dev/staging/prod with layered overrides
✅ **Discoverability:** All config options visible in AppConfig model
✅ **Validation:** Invalid configs fail fast with clear error messages
✅ **Documentation:** Pydantic models are self-documenting via type hints

### Negative

⚠️ **Migration Effort:** Existing code must migrate to use new system
⚠️ **Dual Systems:** Generic AppConfig and domain-specific configs coexist temporarily
⚠️ **Learning Curve:** Team must learn Pydantic and layered override system
⚠️ **Breaking Changes (Future):** Config schema changes may break deployments

### Neutral

➖ **Dependency:** Adds Pydantic as dependency (but already in pyproject.toml)
➖ **Convention:** Must follow `ORCH_*` env var naming convention

---

## Rationale

### Why Pydantic?

1. **Already a dependency** (in pyproject.toml)
2. **Best-in-class validation** for Python
3. **Type coercion** handles env vars naturally (`"4"` → `4`)
4. **Alias support** for backward compatibility
5. **JSON Schema** generation for documentation
6. **Wide adoption** in FastAPI, data platforms, ML tools

### Why Layered Overrides?

Different environments need different override strategies:

**Development:**
```python
config = load_config()  # Use defaults from config/default.yaml
```

**Staging:**
```python
config = load_config(path="config/staging.yaml")  # Override from file
```

**Production (Kubernetes):**
```bash
# Load from ConfigMap
export ORCH_CONFIG=/etc/orchestrator/prod.yaml

# Override secrets from Secrets
export ORCH_DATABASE__PASSWORD=$(cat /run/secrets/db-password)
export ORCH_ANTHROPIC__API_KEY=$(cat /run/secrets/anthropic-key)
```

**Testing:**
```python
config = load_config(cli_overrides={"runtime": {"auto_advance": False}})
```

### Why Keep Domain Configs?

`HygieneConfig` is not just configuration—it has business logic:

```python
class HygieneConfig:
    @property
    def score_weights(self) -> Dict[str, int]:
        """Score weights for cleanliness calculation."""
        return self.get("quality.score_weights", {
            "no_orphans": 30,
            "no_large_files": 25,
            # ... complex default logic
        })
```

This is better as a specialized class than a Pydantic model with computed fields. We can:
1. Keep it as-is (domain-specific)
2. Have it *use* AppConfig internally
3. Merge later if beneficial

---

## Implementation

### Phase 1: Create Infrastructure ✅

```bash
src/common/
├── __init__.py          # Public API
├── config.py            # AppConfig + ConfigLoader

config/
└── default.yaml         # Default configuration

tests/
└── test_config.py       # 20 test cases
```

### Phase 2: Adopt in Core (Next Sprint)

```python
# orchestrator/runloop.py (before)
def _load_config(self) -> Dict[str, Any]:
    config_path = self.project_root / ".claude" / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

# orchestrator/runloop.py (after)
from common.config import load_config

def _load_config(self) -> AppConfig:
    return load_config()  # Type-safe, validated
```

### Phase 3: Evaluate Domain Configs (Later)

For each domain config:
1. **Keep as-is:** If it has business logic or specialized behavior
2. **Extend AppConfig:** If it's pure configuration
3. **Merge:** If there's significant overlap

---

## Validation

### Acceptance Tests

All 20 test cases passing:

```bash
$ python -m pytest tests/test_config.py -v
========================= 20 passed in 0.30s =========================
```

Tests cover:
- Default values
- File loading
- Environment variable overrides
- CLI overrides
- Layered overrides (precedence)
- Edge cases (empty file, invalid config, etc.)

### Manual Validation

```python
# Scenario: Production deployment
os.environ["ORCH_CONFIG"] = "config/prod.yaml"
os.environ["ORCH_LOGGING__LEVEL"] = "ERROR"
os.environ["ORCH_RUNTIME__MAX_PARALLEL_AGENTS"] = "16"

config = load_config()

assert config.app.environment == "prod"  # From file
assert config.logging.level == "ERROR"  # From env
assert config.runtime.max_parallel_agents == 16  # From env (coerced to int)
```

---

## Monitoring & Rollback

### Monitoring

Track config loading errors in production:

```python
import logging

logger = logging.getLogger("orchestrator.config")

try:
    config = load_config()
except RuntimeError as e:
    logger.error(f"Config load failed: {e}")
    # Fallback to safe defaults or exit
```

### Rollback Plan

If unified config causes issues:

1. **Immediate:** Revert commits introducing AppConfig usage
2. **Temporary:** Use feature flag to disable new config system
3. **Long-term:** Fix issues and re-enable

Domain configs remain unchanged, so rollback is safe.

---

## References

- **Pydantic Documentation:** https://docs.pydantic.dev/
- **12-Factor App Config:** https://12factor.net/config
- **Phase 1.2 Report:** reports/phase1.2_config_consolidation.md
- **Implementation:** src/common/config.py

---

## Decisions

| Decision | Status | Date |
|----------|--------|------|
| Use Pydantic for config validation | ✅ Accepted | 2025-11-14 |
| Implement layered overrides | ✅ Accepted | 2025-11-14 |
| Keep domain configs separate (for now) | ✅ Accepted | 2025-11-14 |
| Use `ORCH_` prefix for env vars | ✅ Accepted | 2025-11-14 |
| Create ADR for this decision | ✅ Accepted | 2025-11-14 |

---

**Supersedes:** None
**Superseded By:** None
**Related:** ADR-001 (Multi-Agent Orchestration), ADR-002 (DuckDB for Analytics)
