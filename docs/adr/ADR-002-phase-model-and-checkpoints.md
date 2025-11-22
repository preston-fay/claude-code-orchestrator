# ADR-002: Phase Model and Checkpoints

**Status:** Accepted
**Date:** 2025-11-21
**Deciders:** Platform Team
**Supersedes:** N/A

## Context

The current Orchestrator v1 has a sequential phase model with glob-based artifact validation. While functional, it has limitations:

1. **Rigid phase ordering** - All projects follow same sequence even when not appropriate
2. **Coarse checkpoints** - Only capture file paths, not agent state or decision context
3. **Limited rollback** - Can mark phase incomplete but can't restore previous state
4. **No checkpoint versioning** - Can't compare checkpoint states over time
5. **Missing metadata** - Checkpoints don't capture governance results, token usage, or timing

For Orchestrator v2, we need a checkpoint system that:
- Captures complete state for true rollback capability
- Supports project-type-specific phase graphs
- Enables comparison and audit of checkpoint evolution
- Integrates with governance and telemetry

## Decision

**We will implement a first-class checkpoint system with versioned state snapshots, project-specific phase graphs, and complete rollback capability.**

### Canonical Phase Graph

```
                    ┌─────────┐
                    │ INTAKE  │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │PLANNING │ (Architect)
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐┌────▼────┐┌────▼────┐
         │  DATA   ││  ARCH   ││SECURITY │ (optional)
         └────┬────┘└────┬────┘└────┬────┘
              │          │          │
              └──────────┼──────────┘
                         │
                    ┌────▼────┐
                    │CONSENSUS│ (gate)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │DEVELOP  │ (Developer + subagents)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │   QA    │ (QA + subagents)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │CONSENSUS│ (gate)
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐┌────▼────┐┌────▼────┐
         │  DOCS   ││ REVIEW  ││HYGIENE  │
         └────┬────┘└────┬────┘└────┬────┘
              │          │          │
              └──────────┼──────────┘
                         │
                    ┌────▼────┐
                    │COMPLETE │
                    └─────────┘
```

### Project-Type Phase Variants

| Project Type | Phases Included | Phases Excluded |
|--------------|-----------------|-----------------|
| Analytics | DATA, DEVELOP, DOCS | SECURITY |
| ML | DATA, DEVELOP, QA, DOCS | - |
| WebApp | DEVELOP, QA, DOCS, SECURITY | DATA |
| Optimization | DATA, DEVELOP, QA, DOCS | - |

### Checkpoint Structure

Each checkpoint captures:

```typescript
interface Checkpoint {
  // Identity
  id: string;                    // UUID
  phase: string;                 // e.g., "development"
  type: "PRE" | "POST";          // Before or after phase
  version: number;               // Increments on re-run

  // Timing
  created_at: ISO8601;
  duration_ms: number;

  // State
  orchestrator_state: {
    run_id: string;
    current_phase: string;
    completed_phases: string[];
    intake_summary: object;
  };

  agent_states: {
    [agent_id: string]: {
      status: "pending" | "running" | "complete" | "failed";
      token_usage: { input: number; output: number };
      tool_invocations: ToolInvocation[];
      summary: string;
    };
  };

  // Artifacts
  artifacts: {
    [name: string]: {
      path: string;
      hash: string;          // SHA-256 for integrity
      size_bytes: number;
    };
  };

  // Governance
  governance_results: {
    quality_gates: GateResult[];
    compliance_checks: ComplianceResult[];
    passed: boolean;
  };

  // Metadata
  parent_checkpoint_id: string | null;
  metadata: Record<string, any>;
}
```

### Checkpoint Storage

```
.claude/checkpoints/
├── index.json                    # Checkpoint index for quick lookup
├── run-{run_id}/
│   ├── PRE_planning_v1.json
│   ├── POST_planning_v1.json
│   ├── PRE_development_v1.json
│   ├── POST_development_v1.json
│   ├── POST_development_v2.json  # Re-run after rollback
│   └── ...
└── artifacts/
    └── {checkpoint_id}/
        └── {artifact_hash}/      # Content-addressed storage
```

### Rollback Mechanism

1. **Select checkpoint** to rollback to (e.g., `POST_planning_v1`)
2. **Restore orchestrator state** from checkpoint
3. **Mark downstream phases** as incomplete
4. **Preserve artifacts** from rolled-back phases (archived, not deleted)
5. **Increment version** for next run of that phase
6. **Create new PRE checkpoint** linking to rollback source

```python
async def rollback_to_checkpoint(checkpoint_id: str) -> None:
    checkpoint = load_checkpoint(checkpoint_id)

    # Restore state
    state.current_phase = checkpoint.phase
    state.completed_phases = phases_up_to(checkpoint.phase)
    state.phase_artifacts = checkpoint.artifacts

    # Archive downstream
    for phase in phases_after(checkpoint.phase):
        archive_phase_artifacts(phase)

    # Create rollback marker
    create_checkpoint(
        phase=checkpoint.phase,
        type="PRE",
        parent_checkpoint_id=checkpoint_id,
        metadata={"rollback_from": current_checkpoint_id}
    )
```

### Checkpoint Triggers

| Event | Checkpoint Type | Contains |
|-------|-----------------|----------|
| Phase start | PRE | Previous state, loaded context |
| Phase success | POST | Agent outputs, artifacts, governance |
| Phase failure | POST (failed) | Error info, partial artifacts |
| Consensus approval | POST (approved) | Approval metadata |
| Rollback | PRE (rollback) | Link to source checkpoint |

## Consequences

### Benefits

1. **True rollback** - Can restore complete state, not just mark incomplete
2. **Audit trail** - Full history of phase executions with versioning
3. **Reproducibility** - Checkpoints capture everything needed to reproduce
4. **Debugging** - Agent states and tool invocations preserved
5. **Governance integration** - Quality gates and compliance in checkpoint
6. **UI support** - Checkpoints provide data for progress visualization

### Trade-offs

1. **Storage overhead** - More data per checkpoint than v1
2. **Complexity** - Checkpoint management adds code complexity
3. **Migration** - Existing v1 checkpoints not compatible

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large checkpoint files | Content-addressed artifact storage, compression |
| Checkpoint corruption | SHA-256 integrity checks, backup to cloud |
| Performance impact | Async checkpoint writes, lazy loading |

## Alternatives Considered

### 1. Keep Glob-Based Validation Only
- **Pros:** Simple, low overhead
- **Cons:** No rollback, no state capture, no versioning
- **Why rejected:** Insufficient for production reliability

### 2. Git-Based Checkpoints
- **Pros:** Built-in versioning, diffing, branching
- **Cons:** Overhead of commits, not all state is file-based
- **Why rejected:** Agent state and telemetry don't fit git model

### 3. Database-Based Checkpoints
- **Pros:** Query capability, transactions
- **Cons:** External dependency, overkill for most projects
- **Why rejected:** JSON files sufficient, keeps repo self-contained

## Implementation Notes

### Checkpoint Service Interface

```python
class CheckpointService:
    async def create(
        self,
        phase: str,
        type: CheckpointType,
        state: OrchestratorState,
        agent_states: Dict[str, AgentState],
        artifacts: Dict[str, ArtifactInfo],
        governance: GovernanceResults,
    ) -> Checkpoint: ...

    async def load(self, checkpoint_id: str) -> Checkpoint: ...

    async def rollback(self, checkpoint_id: str) -> None: ...

    async def list_for_run(self, run_id: str) -> List[CheckpointSummary]: ...

    async def compare(
        self,
        checkpoint_a: str,
        checkpoint_b: str
    ) -> CheckpointDiff: ...
```

### Migration from v1

1. Continue supporting `phase_artifacts` in state for backwards compatibility
2. Generate v2 checkpoints alongside v1 during transition
3. Deprecate v1 checkpoint format after migration complete

## Related Decisions

- ADR-001: Agent Architecture (agent states captured in checkpoints)
- ADR-004: Governance Engine (governance results in checkpoints)
- ADR-005: Token Efficiency (token usage tracked per checkpoint)
