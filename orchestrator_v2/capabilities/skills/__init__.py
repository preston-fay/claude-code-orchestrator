"""
Skills module for Orchestrator v2.

Skills are executable methodology modules that encode domain-agnostic
problem-solving approaches. They provide structured approaches for
common analytical and development tasks.

See ADR-003 for skills architecture.
"""

from orchestrator_v2.capabilities.skills.models import BaseSkill, SkillMetadata
from orchestrator_v2.capabilities.skills.registry import SkillRegistry

__all__ = [
    "BaseSkill",
    "SkillMetadata",
    "SkillRegistry",
]
