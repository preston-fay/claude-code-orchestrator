# ADR-005: Specialized Agents with Auto-Detection

**Status**: Accepted
**Date**: 2025-11-14
**Context**: Phase 3 Specialized Agents Implementation

## Context and Problem Statement

The orchestrator's base workflow includes core agents (Architect, Developer, QA, Consensus, etc.) that handle general project lifecycle phases. However, certain projects require specialized expertise in areas like performance optimization, security auditing, or database architecture.

**Key Question**: How can we extend the orchestrator to support specialized agents that are automatically triggered based on project requirements, without breaking existing workflows or forcing users to manually configure every agent?

## Decision

We will implement **three specialized agents with automatic detection** based on intake requirements and governance policies:

### 1. Performance Engineer
- **Triggers**: Performance SLAs defined, production environment, performance keywords in requirements
- **Responsibilities**: Profile application, identify bottlenecks, recommend optimizations, validate against SLAs
- **Artifacts**: `reports/performance_profile.json`, `reports/performance_recommendations.md`, `reports/load_test_results.json`

### 2. Security Auditor
- **Triggers**: Security scan required in governance, compliance requirements (GDPR/HIPAA/SOC2), production environment, security keywords
- **Responsibilities**: Scan for vulnerabilities (OWASP Top 10), validate compliance, check dependency vulnerabilities
- **Artifacts**: `reports/security_scan.json`, `reports/security_compliance.md`, `reports/dependency_vulnerabilities.json`

### 3. Database Architect
- **Triggers**: Database/SQL/schema keywords in requirements, data engineering phases
- **Responsibilities**: Design database schema, generate migrations, optimize indexes, document ER diagrams
- **Artifacts**: `schema.sql`, `migrations/`, `reports/database_architecture.md`, `reports/index_recommendations.json`

### Auto-Detection Architecture

**Integration Point**: `Orchestrator._auto_detect_optional_agents(phase_name, base_agents)` called in `run_phase()`

**Detection Rules**:
```python
# Database Architect (insert before developer)
if phase in ["planning", "data_engineering", "developer"]:
    if ["db", "database", "sql", "schema"] in requirements:
        add "database-architect" before "developer"

# Performance Engineer (append after developer)
if phase in ["developer", "qa"]:
    if governance.performance_slas.latency_p95_ms > 0:
        add "performance-engineer"
    if ["performance", "latency", "throughput"] in requirements:
        add "performance-engineer"
    if environment == "production":
        add "performance-engineer"

# Security Auditor (append after developer)
if phase in ["developer", "qa"]:
    if governance.require_security_scan == true:
        add "security-auditor"
    if compliance in ["gdpr", "hipaa", "soc2"]:
        add "security-auditor"
    if environment == "production":
        add "security-auditor"
```

**Agent Ordering**:
- Database Architect: Inserted **before** developer (needs schema design first)
- Performance Engineer: Appended **after** developer/qa
- Security Auditor: Appended **after** developer/qa

**Duplicate Prevention**: Checks if agent already in base list before adding

## Consequences

### Positive

1. **Zero Configuration Overhead**: Agents automatically detected - no manual phase configuration needed
2. **Backward Compatible**: Existing workflows unchanged - specialized agents only added when triggered
3. **Context-Aware**: Detection based on actual project needs (not one-size-fits-all)
4. **Extensible**: Easy to add more specialized agents following same pattern
5. **Comprehensive Coverage**: Addresses three common gaps (performance, security, database)

### Negative

1. **False Positives**: Keyword matching may trigger agents unnecessarily
   - Mitigated by: Multiple trigger conditions, conservative keywords
2. **Additional Execution Time**: Each agent adds 30-60s to workflow
   - Acceptable: Only triggered when genuinely needed
3. **Agent Maintenance**: More agents to maintain and update
   - Mitigated by: Mock implementations for testing, clear separation of concerns

### Neutral

1. **Agent Discovery**: Users need to know specialized agents exist
   - Documentation: README section, playbook with examples
2. **Governance Schema**: Requires new governance fields
   - Added: `performance_slas.latency_p95_ms`, existing `require_security_scan` reused

## Alternatives Considered

### Alternative 1: Manual Agent Configuration
**Rejected**: Requires users to know about and configure every specialized agent. High friction, error-prone.

### Alternative 2: Always Run All Agents
**Rejected**: Unnecessary execution time (3-5 minutes per run). Many projects don't need all specialized agents.

### Alternative 3: Separate "Extended" Workflow Mode
**Rejected**: Creates two divergent workflows. Maintenance burden, user confusion about which mode to use.

### Alternative 4: LLM-Based Agent Selection
**Rejected**: Adds LLM call overhead, non-deterministic, harder to test and debug.

## Implementation Notes

**Phase 3 Deliverables** (Completed):
- ✅ 3 agent definitions (`.claude/agents/*.md`)
- ✅ 3 agent implementations (`src/orchestrator/agents/*.py`)
- ✅ Auto-detection logic in `Orchestrator._auto_detect_optional_agents()`
- ✅ Governance bindings (`performance_slas` in governance.yaml)
- ✅ 22 passing tests (agents + auto-detection logic)
- ✅ Documentation (ADR, playbook, README)

**Agent Capabilities** (Mock Implementations):
- Performance Engineer: Detects N+1 queries, CPU bottlenecks, generates optimization recommendations
- Security Auditor: Scans for SQL injection, XSS, hardcoded secrets, weak crypto, GDPR/HIPAA compliance
- Database Architect: Generates PostgreSQL/MySQL schemas, migrations, ER diagrams, index recommendations

**Future Enhancements** (Post-Phase 3):
- [ ] Real tool integration (bandit, semgrep, pganalyze, etc.)
- [ ] LLM-based analysis for deeper insights
- [ ] Agent coordination (security auditor reviews database architect's schema)
- [ ] Parallel agent execution (swarm mode)
- [ ] User-defined custom agents

## References

- Implementation: `src/orchestrator/agents/`, `src/orchestrator/runloop.py:328-432`
- Tests: `tests/agents/`, `tests/runloop/test_autodetect_agents.py`
- Governance: `clients/kearney-default/governance.yaml:235-250`
- Agent definitions: `.claude/agents/performance-engineer.md`, `security-auditor.md`, `database-architect.md`

---

**Decision Record**: Approved for Phase 3 implementation. Specialized agents provide high-value extensions to base workflow with minimal user friction.
