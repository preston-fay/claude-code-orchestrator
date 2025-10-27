# Architecture Decision Records (ADRs)

Architecture Decision Records document **significant architectural and technical decisions** made during project development. They capture the **context, reasoning, and trade-offs** behind decisions to help future developers (and AI agents) understand **why** choices were made, not just **what** was chosen.

## What are ADRs?

An ADR is a short document that:
- **Captures a significant decision** (technical architecture, tool selection, design pattern)
- **Records the context** (why this decision was needed)
- **Documents alternatives** (what else was considered and why rejected)
- **Explains consequences** (trade-offs, benefits, costs)
- **Remains immutable** (once accepted, not edited; superseded by new ADRs if needed)

### Why ADRs Matter

**For Humans**:
- New team members understand architectural rationale quickly
- Avoid relitigating past decisions ("we tried that, here's why it didn't work")
- Provide institutional memory when team composition changes
- Enable informed decision-making (learn from past trade-offs)

**For AI Agents**:
- Consensus agent references ADRs when validating new proposals
- Architect agent follows established patterns documented in ADRs
- Developer agent implements according to accepted architectural decisions
- QA agent validates implementations align with ADR guidance

**For Projects**:
- Consistency across modules (all follow same architectural patterns)
- Faster onboarding (read ADRs instead of spelunking code)
- Better debugging (understand why system works this way)
- Informed evolution (know what constraints guided original design)

---

## When to Create an ADR

### Always Create ADRs For

**Architectural Decisions**:
- System architecture patterns (microservices, monolith, event-driven)
- Data architecture (database choice, schema design, data flow)
- Integration patterns (APIs, messaging, batch processing)
- Deployment architecture (cloud provider, container orchestration)

**Technology Selection**:
- Core technology stack (frameworks, libraries, languages)
- Infrastructure tools (databases, caches, message queues)
- Development tools (CI/CD, testing frameworks, monitoring)

**Design Patterns and Standards**:
- Code organization patterns (project structure, module boundaries)
- API design standards (REST, GraphQL, versioning strategy)
- Error handling and logging approaches
- Security and authentication patterns

**Process and Workflow Decisions**:
- Development workflow (branching strategy, review process)
- Agent orchestration patterns (how agents collaborate)
- Quality gates and checkpoints (when to validate, what to check)

### Do NOT Create ADRs For

**Tactical Decisions** (day-to-day coding choices):
- Variable naming conventions (use linter/style guide instead)
- Which library function to use for sorting
- Specific bug fixes or minor refactors

**Obvious Defaults**:
- "We'll use Git for version control" (industry standard)
- "We'll write tests" (assumed best practice)

**Reversible Decisions**:
- Decisions easily changed without significant rework
- Configuration tuning (can adjust without documenting)

**Rule of Thumb**: If changing the decision would require significant refactoring, architectural changes, or team discussion, write an ADR.

---

## ADR Lifecycle and Status

Each ADR progresses through statuses:

### Status: **Proposed**
- Decision is under consideration
- Consensus agent is reviewing
- Stakeholders can provide input
- Not yet implemented

### Status: **Accepted**
- Consensus reached, decision finalized
- Implementation can proceed
- ADR becomes reference for future work

### Status: **Deprecated**
- Decision no longer recommended (but not yet replaced)
- Use for transitional state before superseding
- Example: "Deprecated: Use ADR-015 instead"

### Status: **Superseded**
- Decision replaced by newer ADR
- Original ADR remains for historical context
- Must reference superseding ADR
- Example: "Superseded by ADR-023"

**Important**: Once **Accepted**, ADRs are **immutable**. To change a decision:
1. Create a new ADR with updated decision
2. Mark old ADR as **Superseded by ADR-XXX**
3. New ADR should reference the old one in "Related Decisions"

---

## Numbering Convention

### Format: `ADR-XXX-brief-title.md`

- **ADR-001**: First decision (reserved for foundational choices)
- **ADR-002**, **ADR-003**, etc.: Sequential numbering
- **Brief title**: Lowercase, hyphen-separated (e.g., `multi-agent-orchestration`)

### Examples
- `ADR-001-multi-agent-orchestration.md`
- `ADR-002-duckdb-for-analytics.md`
- `ADR-015-api-versioning-strategy.md`
- `ADR-023-migration-to-postgres.md` (supersedes ADR-002)

### Numbering Best Practices
- **Never reuse numbers**: Even if ADR is superseded, keep original number
- **Sequential only**: Don't skip numbers or use sub-numbering (ADR-002a)
- **Global sequence**: All ADRs in project share one sequence
- **Start at 001**: Use leading zeros for sorting (ADR-001, not ADR-1)

---

## Integration with Orchestrator Workflow

ADRs integrate with the checkpoint-driven workflow:

### Phase 1: Planning (Architect Agent)

**Architect proposes decisions**:
1. Designs system architecture
2. Selects technologies and patterns
3. **Drafts ADRs** for significant decisions (Status: **Proposed**)
4. Submits ADRs to Consensus agent

**Checkpoint**: Architecture proposal with draft ADRs

### Phase 2: Consensus Validation (Consensus Agent)

**Consensus reviews proposals**:
1. Evaluates ADRs against project requirements
2. Checks for conflicts with existing ADRs
3. Validates alternatives were considered
4. Requests clarifications or revisions
5. **Accepts or rejects** each ADR

**Checkpoint**: Accepted ADRs (Status: **Accepted**)

### Phase 3: Development (Developer Agent)

**Developer implements per ADRs**:
1. References accepted ADRs for guidance
2. Follows architectural patterns documented
3. Raises concerns if ADR guidance is unclear
4. Proposes new ADRs if encountering undocumented decisions

**Checkpoint**: Implementation aligned with ADRs

### Phase 4: QA (QA Agent)

**QA validates ADR compliance**:
1. Checks implementation follows ADR guidance
2. Validates technology choices match ADR decisions
3. Flags deviations from accepted ADRs
4. Reports gaps (needed ADRs not yet created)

**Checkpoint**: QA report including ADR compliance

### Phase 5: Documentation (Documentarian Agent)

**Documentarian references ADRs**:
1. Links technical documentation to relevant ADRs
2. Summarizes key decisions for stakeholders
3. Maintains ADR index and cross-references

**Checkpoint**: Documentation with ADR references

---

## How to Write an ADR

### Step 1: Use the Template

Copy `.claude/decisions/template.md` and fill in sections:
```bash
cp .claude/decisions/template.md .claude/decisions/ADR-XXX-your-title.md
```

### Step 2: Fill in Context

**Context** explains:
- **Problem**: What issue/need triggered this decision?
- **Constraints**: Business, technical, timeline, budget constraints
- **Forces**: Competing concerns (performance vs cost, flexibility vs simplicity)

**Good Context Example**:
> We need to store and query 100GB of analytical data with complex joins. Current CSV files in S3 are slow (30+ second queries). Team has Python expertise but limited database admin experience. Budget allows moderate cloud spend but not enterprise database licensing.

**Bad Context Example**:
> We need a database.

### Step 3: State the Decision Clearly

**Decision** states:
- **What** was decided (be specific)
- **Why** this choice (key reasoning in 1-2 sentences)

**Good Decision Example**:
> We will use DuckDB as our primary analytical database. DuckDB provides SQL query performance comparable to traditional databases while running in-process with zero configuration, aligning with our team's Python expertise and avoiding operational overhead.

**Bad Decision Example**:
> Use DuckDB because it's fast.

### Step 4: Document Alternatives

**Alternatives Considered** lists:
- Other options seriously evaluated (minimum 2-3)
- Why each was **rejected** (specific reasons)

**Good Alternatives Example**:
> - **PostgreSQL**: Rejected due to operational complexity (server management, backups, connection pooling). Overkill for analytical workload with single-user access pattern.
> - **SQLite**: Rejected due to poor performance on large aggregations and lack of parallel query execution.
> - **Snowflake**: Rejected due to high cost for our data volume and complexity of cloud data warehouse setup.

**Bad Alternatives Example**:
> - Postgres: Too hard
> - Snowflake: Too expensive

### Step 5: Explain Consequences

**Consequences** covers:
- **Benefits**: What we gain from this decision
- **Costs/Trade-offs**: What we sacrifice or accept
- **Risks**: What could go wrong
- **Implementation effort**: What it takes to implement

**Good Consequences Example**:
> **Benefits**:
> - Zero operational overhead (no server management)
> - Fast analytical queries (10-100x faster than CSV)
> - Native Python integration via DuckDB API
>
> **Trade-offs**:
> - Single-process limitation (not suitable for multi-user production databases)
> - Less mature ecosystem than PostgreSQL
> - May need migration if concurrency requirements change
>
> **Risks**:
> - DuckDB is relatively new; potential for bugs or API changes
> - Limited cloud-native integrations compared to BigQuery/Snowflake

### Step 6: Add Implementation Notes (Optional)

**Implementation Notes** provide:
- Practical guidance for developers
- Configuration recommendations
- Integration patterns
- Migration strategies (if applicable)

### Step 7: Cross-Reference Related Decisions

**Related Decisions** links:
- ADRs this decision builds upon
- ADRs that depend on this decision
- ADRs that provide complementary context

---

## Referencing ADRs

### In Code Comments
```python
# Per ADR-002, we use DuckDB for analytical queries
# See: .claude/decisions/ADR-002-duckdb-for-analytics.md
import duckdb
```

### In Documentation
```markdown
Our analytical database is DuckDB ([ADR-002](../.claude/decisions/ADR-002-duckdb-for-analytics.md)),
chosen for its simplicity and performance for single-user analytical workloads.
```

### In Pull Requests
```
This PR implements the user analytics dashboard per ADR-002 (DuckDB) and ADR-007 (dashboard architecture).
```

### In ADRs (Cross-Reference)
```markdown
## Related Decisions

- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Establishes agent collaboration pattern
- Supersedes: [ADR-002: DuckDB for Analytics](./ADR-002-duckdb-for-analytics.md)
```

---

## Superseding ADRs

When a decision changes significantly:

### Step 1: Create New ADR
Write new ADR explaining updated decision:
```markdown
# ADR-023: Migrate to PostgreSQL for Multi-User Analytics

Status: Accepted

## Context
Since ADR-002 (DuckDB), requirements have evolved to support 50+ concurrent analysts.
DuckDB's single-process limitation is now a blocker...
```

### Step 2: Update Old ADR Status
Mark original ADR as superseded (edit **only** status section):
```markdown
# ADR-002: DuckDB for Analytics

Status: Superseded by [ADR-023](./ADR-023-migration-to-postgres.md)
```

### Step 3: Link ADRs
Ensure bidirectional references:
- New ADR mentions "Supersedes: ADR-002"
- Old ADR mentions "Superseded by: ADR-023"

---

## ADR Index

Maintain an index of all ADRs for quick reference:

### Current ADRs (Accepted)

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./ADR-001-multi-agent-orchestration.md) | Multi-Agent Orchestration | Accepted | 2025-01-26 |
| [ADR-002](./ADR-002-duckdb-for-analytics.md) | DuckDB for Analytics | Accepted | 2025-01-26 |

### Superseded ADRs

| ADR | Title | Superseded By | Date |
|-----|-------|---------------|------|
| *(None yet)* | | | |

---

## Best Practices

### DO:
- ✅ Write ADRs **when decision is made** (not retrospectively)
- ✅ Keep ADRs **short and focused** (1-2 pages max)
- ✅ Use **plain language** (avoid jargon)
- ✅ Document **alternatives considered** (shows due diligence)
- ✅ Be **honest about trade-offs** (every decision has costs)
- ✅ Update **status** when decision changes (mark superseded)

### DON'T:
- ❌ Write ADRs for **trivial decisions** (code style, naming)
- ❌ **Edit accepted ADRs** (create new ADR instead)
- ❌ **Omit alternatives** ("this is the only option" is rarely true)
- ❌ Use ADRs for **requirements** (ADRs document decisions, not features)
- ❌ **Justify decisions retroactively** (write ADRs prospectively)

---

## Common Questions

**Q: How long should an ADR be?**

A: 1-2 pages. If longer, decision may be too broad—split into multiple ADRs.

**Q: What if we made a decision but didn't write an ADR?**

A: Write it now! Retrospective ADRs are better than no ADRs. Mark the date and note "Written retrospectively."

**Q: Can we edit an accepted ADR?**

A: Only to fix typos or clarify wording. For substantial changes, create a new ADR and mark the old one superseded.

**Q: Do we need ADRs for small projects?**

A: If the project lasts > 1 month or has > 1 developer (including AI agents), yes. ADRs prevent knowledge loss.

**Q: What if an ADR becomes irrelevant?**

A: Mark it **Deprecated** or **Superseded** (with reference to new ADR). Never delete ADRs—they provide historical context.

**Q: Who approves ADRs?**

A: For orchestrator projects, the **Consensus agent** reviews and approves. For human-led projects, the **Tech Lead** or **Architect**.

**Q: Can ADRs reference external docs?**

A: Yes, link to RFCs, vendor documentation, research papers. But keep core decision reasoning in the ADR itself (external links may break).

---

## Examples

See example ADRs in this directory:
- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Process decision example
- [ADR-002: DuckDB for Analytics](./ADR-002-duckdb-for-analytics.md) - Technology selection example

---

## Resources

**ADR Methodology**:
- [Michael Nygard's ADR Template](https://github.com/joelparkerhenderson/architecture-decision-record)
- [When to Write an ADR (ThoughtWorks)](https://www.thoughtworks.com/en-us/insights/blog/architecture/architecture-decision-records)

**Tools**:
- [adr-tools](https://github.com/npryce/adr-tools) - Command-line ADR management
- [log4brains](https://github.com/thomvaill/log4brains) - ADR management with web UI

---

**Maintained by**: Claude Code Orchestrator Team
**Last Updated**: 2025-01-26
**Version**: 1.0.0
