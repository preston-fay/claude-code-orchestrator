# ADR-004: Governance and Quality Gates Engine

**Status:** Accepted
**Date:** 2025-11-21
**Deciders:** Platform Team
**Supersedes:** N/A

## Context

The current Orchestrator v1 has governance defined in `clients/<client>/governance.yaml` files that are manually loaded and checked. This works but has limitations:

1. **Manual enforcement** - Agents must remember to check governance constraints
2. **Inconsistent application** - Quality gates applied differently across phases
3. **No real-time validation** - Compliance violations caught late in workflow
4. **Limited composability** - Can't combine client + firm + universal rules elegantly
5. **No audit trail** - Difficult to prove governance was enforced

For Orchestrator v2, we need:
- Automatic governance enforcement at every phase boundary
- Composable rule engine supporting hierarchical policies
- Real-time validation with immediate feedback
- Complete audit trail for compliance reporting
- Extensible gate definitions for custom requirements

## Decision

**We will implement a centralized Governance Engine that automatically enforces quality gates, compliance requirements, and brand constraints through a composable rule system with full audit logging.**

### Governance Architecture

```
┌─────────────────────────────────────────────────────┐
│                 GOVERNANCE ENGINE                   │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Policy    │  │    Gate     │  │   Audit     │ │
│  │   Loader    │  │  Evaluator  │  │   Logger    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │        │
│         v                v                v        │
│  ┌─────────────────────────────────────────────┐  │
│  │            Rule Composition Engine           │  │
│  │  (Client > Kearney Default > Universal)     │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Rule Hierarchy

Policies compose from three levels (most specific wins):

```yaml
# Level 1: Universal defaults (always applied)
# governance/universal.yaml
governance:
  quality_gates:
    min_test_coverage: 70
    require_linting: true
    max_complexity: 15

  compliance:
    require_license_headers: true
    no_secrets_in_code: true

# Level 2: Kearney firm-wide standards
# governance/kearney-default.yaml
governance:
  quality_gates:
    min_test_coverage: 80  # Override universal
    require_documentation: true
    security_scan_required: true

  brand_constraints:
    colors: ["#7823DC", "#000000", "#FFFFFF", "#787878"]
    fonts: ["Arial", "Arial Bold"]
    no_emojis: true

# Level 3: Client-specific requirements
# clients/acme-corp/governance.yaml
governance:
  quality_gates:
    min_test_coverage: 90  # Override Kearney default
    require_accessibility_audit: true

  compliance:
    gdpr:
      data_retention_days: 365
      require_consent_tracking: true
    hipaa:
      require_phi_encryption: true
      audit_trail_required: true

  deployment:
    approval_required: true
    deployment_windows: ["Tuesday 2am-6am", "Thursday 2am-6am"]
```

### Quality Gate Definitions

Gates are declarative rules evaluated at phase boundaries:

```yaml
# gates/test_coverage.yaml
gate:
  id: test_coverage
  type: metric
  description: "Minimum test coverage threshold"

  evaluation:
    metric: coverage_percentage
    operator: ">="
    threshold: "{{ governance.quality_gates.min_test_coverage }}"

  applies_to:
    phases: [development, qa]
    artifacts: ["**/coverage.json", "**/coverage.xml"]

  on_failure:
    action: block
    message: "Test coverage {{ actual }}% below required {{ threshold }}%"
    remediation: "Add tests for uncovered code paths"

# gates/security_scan.yaml
gate:
  id: security_scan
  type: tool
  description: "Security vulnerability scan"

  evaluation:
    tool: bandit  # or snyk, semgrep
    args: ["-r", ".", "-f", "json"]
    success_criteria:
      high_severity: 0
      medium_severity: "<= 5"

  applies_to:
    phases: [development, qa]
    file_patterns: ["**/*.py", "**/*.js", "**/*.ts"]

  on_failure:
    action: block
    message: "Security scan found {{ high_count }} high severity issues"
    remediation: "Review security report and fix vulnerabilities"

# gates/brand_compliance.yaml
gate:
  id: brand_compliance
  type: validator
  description: "Brand guideline compliance"

  evaluation:
    checks:
      - type: color_palette
        allowed: "{{ governance.brand_constraints.colors }}"
        scan: ["**/*.css", "**/*.scss", "**/*.html"]
      - type: font_family
        allowed: "{{ governance.brand_constraints.fonts }}"
        scan: ["**/*.css", "**/*.scss"]
      - type: forbidden_terms
        terms: "{{ governance.brand_constraints.forbidden_terms }}"
        scan: ["**/*.md", "**/*.html", "**/*.txt"]

  applies_to:
    phases: [documentation]

  on_failure:
    action: warn  # Not blocking, but logged
    message: "Brand compliance issues found"
```

### Gate Evaluation Engine

```python
class GovernanceEngine:
    def __init__(self):
        self.policy_loader = PolicyLoader()
        self.gate_evaluator = GateEvaluator()
        self.audit_logger = AuditLogger()

    async def evaluate_phase_transition(
        self,
        from_phase: Phase,
        to_phase: Phase,
        context: WorkflowContext
    ) -> GateResult:
        """Evaluate all applicable gates for phase transition."""

        # Load composed policy
        policy = self.policy_loader.compose(
            universal="governance/universal.yaml",
            firm="governance/kearney-default.yaml",
            client=f"clients/{context.client}/governance.yaml"
        )

        # Find applicable gates
        gates = self.gate_evaluator.get_gates_for_phase(to_phase)

        # Evaluate each gate
        results = []
        for gate in gates:
            result = await self.gate_evaluator.evaluate(gate, policy, context)
            results.append(result)

            # Log for audit trail
            self.audit_logger.log_gate_evaluation(
                gate_id=gate.id,
                phase=to_phase.name,
                result=result,
                context=context
            )

        # Determine overall result
        if any(r.status == "blocked" for r in results):
            return GateResult(status="blocked", details=results)
        elif any(r.status == "warned" for r in results):
            return GateResult(status="passed_with_warnings", details=results)
        else:
            return GateResult(status="passed", details=results)

class GateEvaluator:
    async def evaluate(
        self,
        gate: Gate,
        policy: ComposedPolicy,
        context: WorkflowContext
    ) -> EvaluationResult:
        """Evaluate a single gate against current context."""

        if gate.type == "metric":
            return await self._evaluate_metric_gate(gate, policy, context)
        elif gate.type == "tool":
            return await self._evaluate_tool_gate(gate, policy, context)
        elif gate.type == "validator":
            return await self._evaluate_validator_gate(gate, policy, context)
        else:
            raise ValueError(f"Unknown gate type: {gate.type}")
```

### Audit Trail

Every governance decision is logged for compliance reporting:

```yaml
# Example audit log entry
audit_entry:
  timestamp: "2025-11-21T14:32:15Z"
  workflow_id: "proj-123-run-456"
  phase: "development"
  gate_id: "test_coverage"

  evaluation:
    threshold: 90
    actual: 87
    status: "blocked"

  context:
    client: "acme-corp"
    agent: "developer"
    artifacts_checked:
      - "coverage/coverage.json"

  remediation:
    message: "Test coverage 87% below required 90%"
    action_taken: "Blocked phase transition"
```

### Integration with Checkpoints

Governance integrates with the checkpoint system (ADR-002):

```python
class CheckpointManager:
    async def complete_checkpoint(
        self,
        checkpoint: Checkpoint,
        context: WorkflowContext
    ) -> CheckpointResult:

        # First, validate checkpoint artifacts
        validation = await self.validate_artifacts(checkpoint)
        if not validation.passed:
            return CheckpointResult(status="invalid", errors=validation.errors)

        # Then, evaluate governance gates
        governance = await self.governance_engine.evaluate_phase_transition(
            from_phase=checkpoint.phase,
            to_phase=checkpoint.next_phase,
            context=context
        )

        if governance.status == "blocked":
            return CheckpointResult(
                status="blocked_by_governance",
                gate_results=governance.details
            )

        # Checkpoint passes
        return CheckpointResult(status="completed", warnings=governance.warnings)
```

### Agent Awareness

Agents can query governance constraints before acting:

```python
class Agent:
    async def plan(self, task: Task) -> ExecutionPlan:
        # Get applicable constraints for this agent/phase
        constraints = await self.governance_engine.get_constraints(
            phase=self.current_phase,
            agent=self.id
        )

        # Factor constraints into planning
        plan = await self._generate_plan(task, constraints)

        return plan
```

## Consequences

### Benefits

1. **Automatic enforcement** - No manual governance checks needed
2. **Consistency** - Same rules applied uniformly across all workflows
3. **Composability** - Elegant hierarchy of universal → firm → client
4. **Auditability** - Complete trail of all governance decisions
5. **Flexibility** - Easy to add new gates without code changes
6. **Early feedback** - Violations caught at phase boundaries
7. **Compliance ready** - Built-in support for GDPR, HIPAA, SOC2

### Trade-offs

1. **Complexity** - More infrastructure to maintain
2. **Performance** - Gate evaluation adds latency at checkpoints
3. **Rigidity risk** - Overly strict gates could block valid work
4. **Configuration burden** - Must define gates and policies carefully

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Gate false positives | Allow `warn` action, not just `block` |
| Performance bottleneck | Cache policy composition, parallelize gate evaluation |
| Policy conflicts | Clear precedence rules, validation at load time |
| Audit log growth | Retention policies, log aggregation to external systems |

## Alternatives Considered

### 1. Agent-Level Governance Checks
- **Pros:** Simpler, agents handle their own validation
- **Cons:** Inconsistent enforcement, no centralized audit
- **Why rejected:** Want uniform, auditable governance

### 2. Post-Workflow Validation Only
- **Pros:** Non-blocking, doesn't slow workflow
- **Cons:** Late feedback, violations may propagate
- **Why rejected:** Need early enforcement at phase boundaries

### 3. External Policy Engine (OPA, Kyverno)
- **Pros:** Battle-tested, rich policy language
- **Cons:** External dependency, learning curve
- **Why rejected:** Start with internal engine, consider OPA integration later

## Implementation Notes

### Custom Gate Types

New gate types can be registered:

```python
@gate_evaluator.register("custom")
async def evaluate_custom_gate(gate, policy, context):
    # Custom evaluation logic
    result = await my_custom_check(context)
    return EvaluationResult(
        status="passed" if result.ok else "blocked",
        message=result.message
    )
```

### Governance CLI

```bash
# Validate governance configuration
orchestrator governance validate --client acme-corp

# List applicable gates for a phase
orchestrator governance gates --phase development

# Run gates manually (dry-run)
orchestrator governance check --phase qa --dry-run

# View audit trail
orchestrator governance audit --workflow proj-123-run-456
```

### Notification Hooks

```yaml
# In governance policy
notifications:
  on_gate_failure:
    - type: slack
      webhook: "{{ secrets.SLACK_WEBHOOK }}"
      channel: "#project-alerts"
    - type: email
      recipients: ["pm@client.com"]

  on_compliance_violation:
    - type: pagerduty
      severity: high
```

## Related Decisions

- ADR-001: Agent Architecture (agents query governance constraints)
- ADR-002: Phase Model (governance gates at phase boundaries)
- ADR-003: Skills and Tools (tools may have governance requirements)
- ADR-005: Token Efficiency (governance evaluation tracked for cost)
