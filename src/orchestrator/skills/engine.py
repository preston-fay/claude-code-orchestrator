"""Skills Activation Engine v2 - Auto-match, validate prereqs, inject snippets."""

import yaml
import importlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from .types import SkillRef, MissingPrereq, SkillsMatchResult


class SkillsEngine:
    """
    Skills activation engine for auto-matching and snippet injection.

    Features:
    - Auto-match skills based on keywords in task/intake/governance
    - Validate MCP module prerequisites
    - Render agent-specific concise snippets (<2k chars per agent)
    - Telemetry tracking
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize skills engine.

        Args:
            index_path: Path to skills index YAML (defaults to built-in)
        """
        if index_path is None:
            index_path = Path(__file__).parent / "index.yaml"

        self.index_path = index_path
        self.skills_catalog: Dict[str, SkillRef] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load skills from index YAML."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Skills index not found: {self.index_path}")

        with open(self.index_path) as f:
            data = yaml.safe_load(f)

        # Parse skills
        for skill_name, skill_data in data.get("skills", {}).items():
            self.skills_catalog[skill_name] = SkillRef(
                name=skill_name,
                keywords=skill_data.get("keywords", []),
                requires=skill_data.get("requires", []),
                snippets=skill_data.get("snippets", {}),
                description=skill_data.get("description", ""),
                category=skill_data.get("category", ""),
            )

    def match(
        self,
        task_text: str,
        intake: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
    ) -> List[SkillRef]:
        """
        Match skills based on keywords in task text, intake, and governance.

        Args:
            task_text: Task description text
            intake: Intake configuration dict
            governance: Governance configuration dict

        Returns:
            List of matched SkillRefs (sorted by match score, then alphabetically)
        """
        # Build combined search text
        search_text = task_text.lower()

        if intake:
            # Add intake requirements
            if "requirements" in intake:
                reqs = intake["requirements"]
                if isinstance(reqs, list):
                    search_text += " " + " ".join(str(r).lower() for r in reqs)
                elif isinstance(reqs, dict):
                    for key, values in reqs.items():
                        if isinstance(values, list):
                            search_text += " " + " ".join(str(v).lower() for v in values)
                        else:
                            search_text += " " + str(values).lower()
                else:
                    search_text += " " + str(reqs).lower()

            # Add project description
            if "project" in intake and isinstance(intake["project"], dict):
                desc = intake["project"].get("description", "")
                search_text += " " + str(desc).lower()

        if governance:
            # Add governance keywords
            for key, value in governance.items():
                search_text += " " + str(value).lower()

        # Match skills by keywords
        matched = []
        for skill in self.skills_catalog.values():
            match_count = sum(1 for kw in skill.keywords if kw.lower() in search_text)
            if match_count > 0:
                matched.append((match_count, skill.name, skill))

        # Sort by match count (descending), then name (ascending)
        matched.sort(key=lambda x: (-x[0], x[1]))

        return [skill for _, _, skill in matched]

    def validate_prereqs(
        self, skills: List[SkillRef]
    ) -> Tuple[List[SkillRef], List[MissingPrereq]]:
        """
        Validate that required MCP modules are available.

        Args:
            skills: List of skills to validate

        Returns:
            Tuple of (available_skills, missing_prereqs)
        """
        available = []
        missing = []

        for skill in skills:
            skill_missing = []

            for module_path in skill.requires:
                if not self._check_module_available(module_path):
                    hint = self._generate_hint(module_path)
                    skill_missing.append(
                        MissingPrereq(
                            module_path=module_path,
                            hint=hint,
                            skill_name=skill.name,
                        )
                    )

            if skill_missing:
                missing.extend(skill_missing)
            else:
                available.append(skill)

        return available, missing

    def _check_module_available(self, module_path: str) -> bool:
        """
        Check if a module is available for import.

        Args:
            module_path: Full module path (e.g., 'orchestrator.mcp.data.load_csv')

        Returns:
            True if module is available
        """
        # Try to import the module
        parts = module_path.split(".")
        module_name = ".".join(parts[:-1]) if len(parts) > 1 else parts[0]

        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def _generate_hint(self, module_path: str) -> str:
        """
        Generate actionable hint for missing module.

        Args:
            module_path: Missing module path

        Returns:
            Hint string
        """
        if module_path.startswith("orchestrator.mcp"):
            return f"Ensure MCP modules are installed. Module path: {module_path}"
        else:
            package = module_path.split(".")[0]
            return f"Install required package: pip install {package}"

    def render_for_agent(
        self, agent: str, skills: List[SkillRef], max_chars: int = 2000
    ) -> str:
        """
        Render agent-specific skill snippets.

        Args:
            agent: Agent name (e.g., 'data', 'developer', 'qa')
            skills: List of skills to render
            max_chars: Maximum characters to render (prevents context bloat)

        Returns:
            Concatenated skill snippets for this agent
        """
        snippets = []
        total_chars = 0

        for skill in skills:
            # Check if skill has snippet for this agent
            if agent not in skill.snippets:
                continue

            snippet = skill.snippets[agent]
            snippet_text = f"\n# Skill: {skill.name}\n{snippet}\n"

            # Check if adding this would exceed max_chars
            if total_chars + len(snippet_text) > max_chars:
                # Add truncation notice
                remaining = max_chars - total_chars
                if remaining > 50:
                    snippets.append(f"\n# [Truncated - {len(skills) - len(snippets)} skills omitted]\n")
                break

            snippets.append(snippet_text)
            total_chars += len(snippet_text)

        return "".join(snippets).strip()

    def summarize(
        self, matched: List[SkillRef], available: List[SkillRef], missing: List[MissingPrereq]
    ) -> Dict[str, Any]:
        """
        Generate telemetry summary.

        Args:
            matched: All matched skills
            available: Skills with all prereqs available
            missing: Missing prerequisites

        Returns:
            Telemetry dict
        """
        return {
            "skills_matched": [s.name for s in matched],
            "skills_available": [s.name for s in available],
            "skills_missing_prereqs": [s.name for s in matched if s not in available],
            "missing_modules": [
                {"module": m.module_path, "skill": m.skill_name, "hint": m.hint}
                for m in missing
            ],
            "match_count": len(matched),
            "available_count": len(available),
            "missing_count": len(missing),
        }

    def get_match_result(
        self,
        task_text: str,
        intake: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
    ) -> SkillsMatchResult:
        """
        Convenience method to match and validate in one call.

        Args:
            task_text: Task description text
            intake: Intake configuration
            governance: Governance configuration

        Returns:
            SkillsMatchResult with matched, available, and missing_prereqs
        """
        matched = self.match(task_text, intake, governance)
        available, missing_prereqs = self.validate_prereqs(matched)

        return SkillsMatchResult(
            matched=matched,
            available=available,
            missing_prereqs=missing_prereqs,
        )
