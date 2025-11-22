"""
Base tool protocol for Orchestrator v2.

Defines the standard interface for tool wrappers.

See ADR-003 for tools architecture.
"""

from typing import Any, Protocol

from pydantic import BaseModel, Field

from orchestrator_v2.engine.state_models import ArtifactInfo, PhaseType, ProjectState, TokenUsage


class ToolAction(BaseModel):
    """Definition of a tool action."""
    name: str
    description: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    returns: dict[str, Any] = Field(default_factory=dict)


class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    id: str
    version: str = "1.0.0"
    category: str  # version_control, file_system, data, etc.
    description: str = ""

    actions: list[ToolAction] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)


class ToolResult(BaseModel):
    """Result from a tool invocation."""
    tool_id: str
    success: bool = True
    output: str = ""
    artifacts: list[ArtifactInfo] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    error_message: str | None = None
    duration_ms: int = 0


class BaseTool(Protocol):
    """Base protocol for tool wrappers."""

    id: str
    description: str
    metadata: ToolMetadata

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Run the tool with given parameters.

        Args:
            agent_id: ID of the calling agent.
            phase: Current workflow phase.
            project_state: Current project state.
            params: Tool parameters.

        Returns:
            Tool execution result.
        """
        ...


class BaseToolImpl:
    """Base implementation for tools."""

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.id = metadata.id
        self.description = metadata.description

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Run the tool - to be overridden by subclasses."""
        return ToolResult(
            tool_id=self.id,
            success=True,
            output=f"Tool {self.id} executed by {agent_id}",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
        )

    def get_capabilities(self) -> list[ToolAction]:
        """Get tool capabilities."""
        return self.metadata.actions


# Concrete tool implementations

class GitTool(BaseToolImpl):
    """Git version control tool."""

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Execute git operations."""
        from hashlib import sha256

        action = params.get("action", "status")

        if action == "diff":
            content = f"""diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,10 @@
+# Updated by {agent_id}
 def main():
-    pass
+    print("Hello, World!")
+
+if __name__ == "__main__":
+    main()
"""
            artifact = ArtifactInfo(
                path=f".claude/checkpoints/{phase.value}/changes.patch",
                sha256=sha256(content.encode()).hexdigest(),
                size_bytes=len(content),
                phase=phase,
                project_id=project_state.project_id,
            )
            return ToolResult(
                tool_id=self.id,
                success=True,
                output="Generated patch file",
                artifacts=[artifact],
                token_usage=TokenUsage(input_tokens=20, output_tokens=10, total_tokens=30),
            )

        return ToolResult(
            tool_id=self.id,
            success=True,
            output=f"Git {action} completed",
            token_usage=TokenUsage(input_tokens=15, output_tokens=8, total_tokens=23),
        )


class DataTool(BaseToolImpl):
    """Data querying tool (DuckDB)."""

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Execute data queries."""
        from hashlib import sha256

        query = params.get("query", "SELECT COUNT(*) FROM data")

        content = f"""Query: {query}

Results:
| column1 | column2 | column3 |
|---------|---------|---------|
| value1  | value2  | value3  |
| value4  | value5  | value6  |

Rows: 2
Execution time: 0.05s
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/query_results.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return ToolResult(
            tool_id=self.id,
            success=True,
            output="Query executed successfully",
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=50, output_tokens=30, total_tokens=80),
        )


class SecurityTool(BaseToolImpl):
    """Security scanning tool."""

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Execute security scans."""
        from hashlib import sha256

        scan_type = params.get("scan_type", "full")

        content = f"""# Security Scan Report

## Scan Type: {scan_type}
## Project: {project_state.project_name}

### Vulnerabilities Found

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0     | PASS   |
| High     | 0     | PASS   |
| Medium   | 2     | WARN   |
| Low      | 5     | INFO   |

### Details

**Medium Issues:**
1. Outdated dependency: requests==2.25.0
2. Missing rate limiting on API endpoint

**Low Issues:**
1-5. Minor code quality issues

### Recommendations
- Update dependencies
- Add rate limiting middleware
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/security_report.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return ToolResult(
            tool_id=self.id,
            success=True,
            output="Security scan completed - PASS",
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=100, output_tokens=60, total_tokens=160),
        )


class DeployTool(BaseToolImpl):
    """Deployment tool."""

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Execute deployment operations."""
        from hashlib import sha256

        environment = params.get("environment", "staging")

        content = f"""# Deployment Log

## Environment: {environment}
## Project: {project_state.project_name}
## Timestamp: 2025-11-21T10:00:00Z

### Deployment Steps

1. [OK] Build artifacts
2. [OK] Run pre-deploy checks
3. [OK] Deploy to {environment}
4. [OK] Health check passed
5. [OK] Notify stakeholders

### Summary
- Status: SUCCESS
- Version: 1.0.0
- Duration: 45s
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/deploy_log.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return ToolResult(
            tool_id=self.id,
            success=True,
            output=f"Deployed to {environment} successfully",
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=80, output_tokens=50, total_tokens=130),
        )


class VisualizationTool(BaseToolImpl):
    """Visualization tool."""

    async def run(
        self,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Generate visualizations."""
        from hashlib import sha256

        chart_type = params.get("chart_type", "mermaid")

        content = f"""# Visualization

## Project: {project_state.project_name}

```mermaid
graph TD
    A[Data Input] --> B[Processing]
    B --> C[Analysis]
    C --> D[Visualization]
    D --> E[Report]

    B --> F[Validation]
    F --> C
```

## Description
System architecture showing data flow from input through processing,
analysis, and visualization to final report generation.
"""
        artifact = ArtifactInfo(
            path=f".claude/checkpoints/{phase.value}/diagram.md",
            sha256=sha256(content.encode()).hexdigest(),
            size_bytes=len(content),
            phase=phase,
            project_id=project_state.project_id,
        )

        return ToolResult(
            tool_id=self.id,
            success=True,
            output="Generated mermaid diagram",
            artifacts=[artifact],
            token_usage=TokenUsage(input_tokens=40, output_tokens=25, total_tokens=65),
        )
