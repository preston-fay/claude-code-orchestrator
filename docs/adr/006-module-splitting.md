# ADR-006: Module Splitting for Maintainability

**Status:** Accepted
**Date:** 2025-11-14
**Context:** Phase 4.1 - Module Refactoring

## Context

The orchestrator codebase has grown to include several large monolithic modules:
- `cli.py` (1595 LOC) - All CLI commands in one file
- `runloop.py` (1095 LOC) - State machine, detectors, transitions mixed
- Server modules with mixed concerns

As the codebase scales, these large files become difficult to navigate, test, and maintain.

## Decision

Split large modules into logical subpackages while maintaining backward compatibility:

### 1. RunLoop Module → runloop/ Package

**Structure:**
```
runloop/
├── __init__.py          # Exports Orchestrator
├── core.py              # Main state machine (600 LOC)
├── detectors.py         # Auto-agent detection (120 LOC)
├── transitions.py       # Phase navigation (280 LOC)
└── utils.py             # Helper functions (40 LOC)
```

**Benefits:**
- Clear separation: state management vs. detection vs. transitions
- Easier testing of individual components
- Mixin pattern enables composition

### 2. CLI Module → cli/ Package

**Structure:**
```
cli/
├── __init__.py          # Exports app
├── main.py              # App setup + top-level commands (270 LOC)
├── commands_run.py      # Run workflow commands (1000 LOC)
└── commands_release.py  # Release management (330 LOC)
```

**Benefits:**
- Logical command grouping
- Easier to add new command groups
- Reduced cognitive load per file

### 3. Backward Compatibility Shims

Created shims at original locations:
- `orchestrator/cli.py` → imports from `orchestrator/cli/`
- `orchestrator/runloop.py` → imports from `orchestrator/runloop/`

All existing imports continue to work without changes.

## Consequences

### Positive

- **Maintainability:** Easier to understand and modify individual components
- **Testability:** Can test detectors, transitions independently
- **Scalability:** Clear pattern for adding new functionality
- **Zero Breaking Changes:** Shims preserve all existing imports

### Negative

- **Extra Files:** More files to navigate (mitigated by clear structure)
- **Import Paths:** Internal imports slightly longer (but explicit)

### Neutral

- **Migration Path:** Gradual migration possible via shims
- **Documentation:** Updated imports in new code, old code works unchanged

## Alternatives Considered

1. **Keep Monolithic Files**
   - Rejected: Already hard to maintain at current size
   - Would only get worse as features are added

2. **Split Without Shims**
   - Rejected: Would break all existing imports
   - Too much churn for downstream code

3. **Use Submodules Instead of Packages**
   - Rejected: Harder to manage related functionality
   - Package structure is more scalable

## Implementation

**Completed:** 2025-11-14
**Files Modified:** 2 shims created, 9 new module files
**Tests:** All 48 existing tests pass, imports verified
**Coverage:** Maintained at previous levels

## Related

- Phase 4.2: Swarm Orchestrator (benefits from modular structure)
- Phase 3: Specialized Agents (cleaner integration with detectors.py)
