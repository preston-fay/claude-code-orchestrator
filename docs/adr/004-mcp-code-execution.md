# ADR-004: MCP Code Execution Pattern

**Status**: Accepted
**Date**: 2025-11-14
**Deciders**: Orchestrator Team
**Context**: Phase 2 MCP Implementation

## Context and Problem Statement

The orchestrator's legacy execution mode passes entire file contents and context to LLMs via tool calls, leading to token bloat. For example, a typical data analysis task might require 150k tokens to send CSV files, dataframes, and intermediate results back and forth between the agent and LLM.

Research into Model Context Protocol (MCP) patterns suggests a code execution approach where the LLM generates Python code that imports filesystem-based APIs, reducing token usage by ~98% (from 150k to 2k tokens).

**Key Question**: How can we enable efficient, safe code generation and execution while preserving backward compatibility with existing executors?

## Decision

We will implement an **opt-in MCP code execution mode** alongside the existing legacy executors, with the following architecture:

### 1. Filesystem MCP Registry (`src/orchestrator/mcp/`)

A tree of importable Python modules organized by domain:
- `orchestrator.mcp.data` - Data loading (CSV, SQL, schema validation)
- `orchestrator.mcp.analytics` - Descriptive stats, drift detection
- `orchestrator.mcp.models` - Model training (Prophet, evaluation)
- `orchestrator.mcp.viz` - Plotting and HTML report generation

**Design Principles**:
- Pure, side-effect-free functions where possible
- Soft-import optional dependencies (pandas, prophet, matplotlib)
- Clear typing and docstrings
- Outputs written to well-known paths (`data/processed/`, `reports/`)

### 2. Sandboxed Code Executor (`src/orchestrator/executors/code_executor.py`)

A new executor that:
1. Prompts LLM to generate Python code using MCP APIs
2. Validates code safety (import guard, eval/exec detection)
3. Runs code in sandboxed subprocess with resource limits
4. Collects artifacts and logs

**Sandbox Security**:
- **Import whitelist**: Only allow stdlib data modules (json, csv, pathlib) + numpy/pandas + `orchestrator.mcp.*`
- **Import blacklist**: Block `os`, `subprocess`, `socket`, `requests`, `eval`, `exec`, `__import__`
- **Network blocking**: Monkeypatch socket module to raise on connect
- **Resource limits**: CPU time limit (120s), memory limit (1GB) via POSIX rlimit (when available)
- **Timeout**: Subprocess timeout kills long-running processes
- **Working directory**: Isolated `.work/` with controlled artifact paths

### 3. CLI Integration (Opt-In)

Add `--mode {legacy|code}` flag to `orchestrator run start`:
- **`legacy`** (default): Existing LLM/subprocess executors - zero breaking changes
- **`code`**: New MCP code executor with sandboxed execution

Mode is stored in `RunState.metadata["execution_mode"]` for phase-level execution decisions.

### 4. Execution Flow

```
User: orchestrator run start --mode code --intake intake.yaml

CLI → Orchestrator.start_run(mode="code")
    → Store mode in state.metadata
    → Orchestrator.run_phase()
        → CodeExecutor.execute(agent, task, context)
            → LLM generates Python code with MCP imports
            → Validate code safety (import guard, eval detection)
            → Write to .work/generated/<agent>_<ts>.py
            → Run in sandboxed subprocess (PYTHONPATH=src)
            → Collect artifacts from data/processed/, reports/
            → Return ExecutionResult
```

## Consequences

### Positive

1. **98% Token Reduction**: From ~150k to ~2k tokens for typical data tasks
   - LLM sees only task description and MCP API docs
   - No need to send full CSV contents, intermediate dataframes, or results

2. **Backward Compatible**: Legacy mode unchanged, default preserved
   - Existing workflows continue to work
   - Gradual migration path (per-run opt-in)

3. **Security Hardening**: Multi-layer sandbox
   - Static import analysis before execution
   - Network blocking
   - Resource limits
   - No eval/exec/subprocess allowed

4. **Extensibility**: Easy to add new MCP domains
   - `orchestrator.mcp.security` for vulnerability scanning
   - `orchestrator.mcp.performance` for profiling
   - `orchestrator.mcp.database` for schema operations

5. **Testability**: Pure functions, mocked code generation
   - Unit tests verify sandbox safety
   - Integration tests verify MCP API usage
   - Smoke tests verify end-to-end execution

### Negative

1. **Additional Complexity**: New code paths to maintain
   - Mitigated by: Comprehensive test coverage (20 tests), clear separation from legacy

2. **Platform Constraints**: Resource limits only work on POSIX systems
   - Mitigated by: Graceful degradation on Windows (warning + continue)

3. **Dependency on LLM Quality**: Generated code must be valid Python
   - Mitigated by: Safety validation catches syntax errors and dangerous patterns

4. **Limited to Python**: Can't generate code in other languages
   - Accepted tradeoff: Python is primary language for data/ML workflows

### Neutral

1. **Prompt Engineering Required**: LLM must learn MCP API patterns
   - Future work: Add .claude/prompts/code_executor_system.md with examples
   - Currently: Embedded template in CodeExecutor._generate_code_with_llm()

2. **Artifact Collection Heuristic**: Collects files modified in last 60s
   - Works for most cases, may miss artifacts from multi-hour runs
   - Alternative: Explicit artifact registration in generated code

## Alternatives Considered

### Alternative 1: Replace Legacy Executors Entirely

**Rejected**: Too risky, would break existing workflows

Instead: Opt-in mode preserves backward compatibility

### Alternative 2: Use Docker Containers for Sandboxing

**Rejected**: Adds infrastructure complexity, slower startup

Instead: POSIX rlimit + subprocess timeout provides "good enough" isolation for most use cases

### Alternative 3: Use External MCP Servers (Network Protocol)

**Rejected**: Adds network layer, more moving parts

Instead: Filesystem registry is simpler, faster, and doesn't require additional processes

### Alternative 4: Generate Bash Scripts Instead of Python

**Rejected**: Python provides better error handling, typing, and ML library ecosystem

Instead: Python code generation aligns with data science workflows

## Implementation Notes

**Phase 2 Deliverables** (Completed):
- ✅ Filesystem MCP registry (9 exemplar APIs)
- ✅ Sandboxed code executor with safety checks
- ✅ CLI `--mode` flag integration
- ✅ 20 passing tests (unit + integration)
- ✅ Sandbox self-test script
- ✅ Documentation and ADR

**Future Enhancements** (Post-Phase 2):
- [ ] Prompt engineering: .claude/prompts/code_executor_fewshot.md with real examples
- [ ] LLM integration: Replace placeholder code generator with actual LLM calls (Anthropic/OpenAI)
- [ ] Extended MCP domains: security, performance, database
- [ ] Explicit artifact registration in generated code
- [ ] Windows sandbox improvements (if needed)

## References

- Original design spec: Phase 2 MCP Code Execution requirements
- MCP pattern research: Token reduction from 150k → 2k tokens
- Sandbox implementation: `src/orchestrator/executors/sandbox.py`
- Tests: `tests/executors/test_code_executor_*.py`, `tests/mcp/test_mcp_imports.py`
- Self-test: `scripts/ops/sandbox_selftest.sh`

---

**Decision Record**: Approved for Phase 2 implementation. Code mode is opt-in via `--mode code` flag. Legacy mode remains default and unchanged.
