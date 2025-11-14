"""Types for Skills Activation Engine v2."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillRef(BaseModel):
    """Reference to a skill with its metadata."""

    name: str = Field(..., description="Unique skill name (e.g., 'time_series_analytics')")
    keywords: List[str] = Field(default_factory=list, description="Keywords that trigger this skill")
    requires: List[str] = Field(default_factory=list, description="Required MCP modules (e.g., 'orchestrator.mcp.data.load_csv')")
    snippets: Dict[str, str] = Field(default_factory=dict, description="Agent-specific code snippets")
    description: Optional[str] = Field(None, description="Brief description of the skill")
    category: Optional[str] = Field(None, description="Skill category (analytics, ml, optimization, etc.)")

    class Config:
        """Pydantic config."""
        frozen = False


class MissingPrereq(BaseModel):
    """A missing prerequisite module."""

    module_path: str = Field(..., description="Missing module path (e.g., 'orchestrator.mcp.data.load_csv')")
    hint: str = Field(..., description="Actionable hint for resolving the missing module")
    skill_name: str = Field(..., description="Skill that requires this module")

    class Config:
        """Pydantic config."""
        frozen = False


class SkillsMatchResult(BaseModel):
    """Result of skill matching and validation."""

    matched: List[SkillRef] = Field(default_factory=list, description="Skills that matched")
    available: List[SkillRef] = Field(default_factory=list, description="Matched skills with all prereqs available")
    missing_prereqs: List[MissingPrereq] = Field(default_factory=list, description="Missing prerequisites")

    class Config:
        """Pydantic config."""
        frozen = False
