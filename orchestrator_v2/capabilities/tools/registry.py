"""
Tool registry for Orchestrator v2.

Handles tool discovery, loading, and provisioning.

See ADR-003 for tool registry architecture.
"""

from typing import Any

from orchestrator_v2.engine.state_models import PhaseType, ProjectState
from orchestrator_v2.capabilities.tools.base_tool import (
    BaseTool,
    BaseToolImpl,
    DataTool,
    DeployTool,
    GitTool,
    SecurityTool,
    ToolMetadata,
    ToolResult,
    VisualizationTool,
)


class ToolRegistry:
    """Registry for tool management."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: dict[str, BaseToolImpl] = {}
        self._metadata: dict[str, ToolMetadata] = {}

    def discover_tools(self) -> list[str]:
        """Discover and register built-in tools."""
        # Git tool
        git_metadata = ToolMetadata(
            id="git",
            category="version_control",
            description="Git version control operations",
        )
        self._register_tool(GitTool(git_metadata))

        # Data tool (DuckDB)
        data_metadata = ToolMetadata(
            id="duckdb",
            category="data",
            description="DuckDB data querying",
        )
        self._register_tool(DataTool(data_metadata))

        # Security tool
        security_metadata = ToolMetadata(
            id="security_scanner",
            category="security",
            description="Security vulnerability scanning",
        )
        self._register_tool(SecurityTool(security_metadata))

        # Deploy tool
        deploy_metadata = ToolMetadata(
            id="deploy",
            category="deployment",
            description="Deployment operations",
        )
        self._register_tool(DeployTool(deploy_metadata))

        # Visualization tool
        viz_metadata = ToolMetadata(
            id="visualization",
            category="visualization",
            description="Generate visualizations and diagrams",
        )
        self._register_tool(VisualizationTool(viz_metadata))

        return list(self._tools.keys())

    def _register_tool(self, tool: BaseToolImpl) -> None:
        """Register a tool instance."""
        self._tools[tool.id] = tool
        self._metadata[tool.id] = tool.metadata

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        tool_id = tool.metadata.id
        self._tools[tool_id] = tool
        self._metadata[tool_id] = tool.metadata

    def get_tool(self, tool_id: str) -> BaseToolImpl:
        """Get a tool by ID."""
        if tool_id not in self._tools:
            raise KeyError(f"Tool not found: {tool_id}")
        return self._tools[tool_id]

    async def run_tool(
        self,
        tool_id: str,
        agent_id: str,
        phase: PhaseType,
        project_state: ProjectState,
        params: dict[str, Any],
    ) -> ToolResult:
        """Run a tool with given parameters."""
        tool = self.get_tool(tool_id)
        return await tool.run(agent_id, phase, project_state, params)

    def get_tools_for_skill(self, skill_tools: list[str]) -> dict[str, BaseToolImpl]:
        """Get tools required by a skill."""
        return {
            tool_id: self.get_tool(tool_id)
            for tool_id in skill_tools
            if tool_id in self._tools
        }

    def list_tools(self, category: str | None = None) -> list[str]:
        """List available tools."""
        if category:
            return [
                tid for tid, meta in self._metadata.items()
                if meta.category == category
            ]
        return list(self._tools.keys())

    def get_tool_metadata(self, tool_id: str) -> ToolMetadata:
        """Get metadata for a tool."""
        if tool_id not in self._metadata:
            raise KeyError(f"Tool not found: {tool_id}")
        return self._metadata[tool_id]
