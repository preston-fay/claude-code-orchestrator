"""
Prompt builder for Orchestrator v2 agents.

Loads prompt templates from subagent_prompts/ and builds
formatted prompts with project context for LLM calls.

Template Loading:
- Templates are loaded from the subagent_prompts/ directory
- Each agent role has a corresponding .md template file
- Templates use markdown with YAML blocks for structure

Prompt Construction:
- System prompt from template header
- Project context injection
- Task-specific instructions
- Output format specifications
"""

import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default template directory relative to project root
DEFAULT_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "subagent_prompts"


class PromptTemplate(BaseModel):
    """A loaded prompt template."""
    role: str
    raw_content: str
    system_context: str = ""
    instructions: str = ""
    input_format: str = ""
    output_format: str = ""
    checkpoint_artifacts: list[str] = Field(default_factory=list)
    quality_guidelines: str = ""
    validation_checklist: list[str] = Field(default_factory=list)


class BuiltPrompt(BaseModel):
    """A fully constructed prompt ready for LLM."""
    system_prompt: str
    user_prompt: str
    role: str
    task_id: str
    estimated_tokens: int = 0


class PromptBuilder:
    """Builder for agent prompts from templates.
    
    Loads markdown templates and constructs prompts with:
    - Role-specific system context
    - Project and task context injection
    - Structured output format specifications
    """
    
    def __init__(self, template_dir: Path | None = None):
        """Initialize the prompt builder.
        
        Args:
            template_dir: Directory containing template files.
                         Defaults to subagent_prompts/.
        """
        self._template_dir = template_dir or DEFAULT_TEMPLATE_DIR
        self._templates: dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all available templates from the template directory."""
        if not self._template_dir.exists():
            logger.warning(f"Template directory not found: {self._template_dir}")
            return
        
        for template_file in self._template_dir.glob("*.md"):
            role = template_file.stem  # e.g., "architect" from "architect.md"
            try:
                content = template_file.read_text(encoding="utf-8")
                template = self._parse_template(role, content)
                self._templates[role] = template
                logger.debug(f"Loaded template for role: {role}")
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")
        
        logger.info(f"Loaded {len(self._templates)} prompt templates")
    
    def _parse_template(self, role: str, content: str) -> PromptTemplate:
        """Parse a markdown template into structured components.
        
        Args:
            role: Agent role name.
            content: Raw template content.
            
        Returns:
            Parsed PromptTemplate.
        """
        template = PromptTemplate(role=role, raw_content=content)
        
        # Extract sections using markdown headers
        sections = self._extract_sections(content)
        
        # Map sections to template fields
        if "System Context & Role Definition" in sections:
            template.system_context = sections["System Context & Role Definition"]
        elif "Role Definition" in sections:
            template.system_context = sections["Role Definition"]
        
        if "Instructions" in sections:
            template.instructions = sections["Instructions"]
        
        if "Input/Output Format Specification" in sections:
            template.input_format = self._extract_subsection(
                sections["Input/Output Format Specification"], "Expected Input Format"
            )
            template.output_format = self._extract_subsection(
                sections["Input/Output Format Specification"], "Required Output Format"
            )
        
        if "Checkpoint Artifacts" in sections:
            template.checkpoint_artifacts = self._extract_list_items(
                sections["Checkpoint Artifacts"]
            )
        
        if "Quality Guidelines" in sections:
            template.quality_guidelines = sections["Quality Guidelines"]
        
        if "Validation Checklist" in sections:
            template.validation_checklist = self._extract_checklist_items(
                sections["Validation Checklist"]
            )
        
        return template
    
    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract top-level sections from markdown content.
        
        Args:
            content: Markdown content.
            
        Returns:
            Dict mapping section headers to content.
        """
        sections: dict[str, str] = {}
        
        # Match ## headers and capture content until next ## or end
        pattern = r"^## ([^\n]+)\n(.*?)(?=^## |\Z)"
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for header, body in matches:
            sections[header.strip()] = body.strip()
        
        return sections
    
    def _extract_subsection(self, content: str, subsection: str) -> str:
        """Extract a subsection from section content.
        
        Args:
            content: Section content.
            subsection: Subsection header to find.
            
        Returns:
            Subsection content or empty string.
        """
        pattern = rf"### {re.escape(subsection)}\n(.*?)(?=### |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def _extract_list_items(self, content: str) -> list[str]:
        """Extract list items from markdown content.
        
        Args:
            content: Content containing lists.
            
        Returns:
            List of item texts.
        """
        items = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:].strip())
            elif re.match(r"^\d+\. ", line):
                items.append(re.sub(r"^\d+\. ", "", line).strip())
        return items
    
    def _extract_checklist_items(self, content: str) -> list[str]:
        """Extract checklist items from markdown.
        
        Args:
            content: Content containing checkboxes.
            
        Returns:
            List of checklist item texts.
        """
        items = []
        for line in content.split("\n"):
            line = line.strip()
            # Match [ ], [x], [X], ✓, etc.
            if re.match(r"^[-*] \[.\]", line):
                items.append(re.sub(r"^[-*] \[.\] ", "", line).strip())
            elif line.startswith("✓ ") or line.startswith("☐ "):
                items.append(line[2:].strip())
        return items
    
    def get_template(self, role: str) -> PromptTemplate | None:
        """Get a template by role name.
        
        Args:
            role: Agent role (e.g., "architect", "developer").
            
        Returns:
            Template if found, None otherwise.
        """
        return self._templates.get(role)
    
    def build_plan_prompt(
        self,
        role: str,
        task_id: str,
        task_description: str,
        project_context: dict[str, Any],
        phase: str,
    ) -> BuiltPrompt:
        """Build a planning prompt for an agent.
        
        Args:
            role: Agent role.
            task_id: Task identifier.
            task_description: What the agent should plan.
            project_context: Project state and context.
            phase: Current workflow phase.
            
        Returns:
            BuiltPrompt ready for LLM.
        """
        template = self.get_template(role)
        
        # Build system prompt
        if template:
            system_prompt = self._build_system_prompt_from_template(template)
        else:
            system_prompt = self._build_default_system_prompt(role)
        
        # Build user prompt for planning
        user_prompt = self._build_plan_user_prompt(
            role=role,
            task_id=task_id,
            task_description=task_description,
            project_context=project_context,
            phase=phase,
            template=template,
        )
        
        # Estimate tokens (rough approximation)
        estimated_tokens = (len(system_prompt) + len(user_prompt)) // 4
        
        return BuiltPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            role=role,
            task_id=task_id,
            estimated_tokens=estimated_tokens,
        )
    
    def build_act_prompt(
        self,
        role: str,
        task_id: str,
        plan_steps: list[str],
        project_context: dict[str, Any],
        phase: str,
        step_index: int = 0,
    ) -> BuiltPrompt:
        """Build an execution prompt for an agent.
        
        Args:
            role: Agent role.
            task_id: Task identifier.
            plan_steps: Steps from the plan to execute.
            project_context: Project state and context.
            phase: Current workflow phase.
            step_index: Which step to execute (0-based).
            
        Returns:
            BuiltPrompt ready for LLM.
        """
        template = self.get_template(role)
        
        # Build system prompt
        if template:
            system_prompt = self._build_system_prompt_from_template(template)
        else:
            system_prompt = self._build_default_system_prompt(role)
        
        # Build user prompt for execution
        user_prompt = self._build_act_user_prompt(
            role=role,
            task_id=task_id,
            plan_steps=plan_steps,
            project_context=project_context,
            phase=phase,
            step_index=step_index,
            template=template,
        )
        
        # Estimate tokens
        estimated_tokens = (len(system_prompt) + len(user_prompt)) // 4
        
        return BuiltPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            role=role,
            task_id=task_id,
            estimated_tokens=estimated_tokens,
        )
    
    def _build_system_prompt_from_template(
        self,
        template: PromptTemplate,
    ) -> str:
        """Build system prompt from a template.
        
        Args:
            template: Parsed prompt template.
            
        Returns:
            Formatted system prompt.
        """
        parts = [
            f"# {template.role.title()} Agent",
            "",
            template.system_context,
        ]
        
        if template.instructions:
            parts.extend(["", "## Instructions", "", template.instructions])
        
        if template.quality_guidelines:
            parts.extend(["", "## Quality Guidelines", "", template.quality_guidelines])
        
        return "\n".join(parts)
    
    def _build_default_system_prompt(self, role: str) -> str:
        """Build a default system prompt when no template exists.
        
        Args:
            role: Agent role.
            
        Returns:
            Default system prompt.
        """
        return f"""# {role.title()} Agent

You are a specialized {role} agent within an orchestrated workflow system.
Your role is to perform {role}-specific tasks as part of a larger project.

## Guidelines
- Focus on your area of expertise: {role}
- Produce clear, actionable outputs
- Follow the output format specifications
- Consider dependencies on other agents' work
- Maintain quality and consistency
"""
    
    def _build_plan_user_prompt(
        self,
        role: str,
        task_id: str,
        task_description: str,
        project_context: dict[str, Any],
        phase: str,
        template: PromptTemplate | None,
    ) -> str:
        """Build user prompt for planning.
        
        Args:
            role: Agent role.
            task_id: Task identifier.
            task_description: Task description.
            project_context: Project context.
            phase: Current phase.
            template: Optional template.
            
        Returns:
            Formatted user prompt.
        """
        # Format project context
        context_str = self._format_project_context(project_context)
        
        prompt = f"""## Task: Create Execution Plan

**Task ID:** {task_id}
**Phase:** {phase}
**Role:** {role}

### Project Context
{context_str}

### Task Description
{task_description}

### Your Assignment
Create a detailed execution plan for this task. Your plan should include:

1. **Analysis**: What needs to be understood or investigated
2. **Steps**: Concrete steps to complete the task
3. **Outputs**: What artifacts or deliverables will be produced
4. **Dependencies**: What information or artifacts from other agents are needed
5. **Validation**: How to verify the work is complete and correct

### Output Format
Provide your plan in the following JSON format:

```json
{{
  "analysis": "Brief analysis of the task requirements",
  "steps": [
    {{
      "step_id": "step_1",
      "description": "Step description",
      "estimated_tokens": 500
    }}
  ],
  "outputs": ["artifact1.md", "artifact2.md"],
  "dependencies": ["List of required inputs"],
  "validation_criteria": ["Criterion 1", "Criterion 2"]
}}
```
"""
        
        # Add template-specific output format if available
        if template and template.output_format:
            prompt += f"\n### Role-Specific Output Requirements\n{template.output_format}\n"
        
        return prompt
    
    def _build_act_user_prompt(
        self,
        role: str,
        task_id: str,
        plan_steps: list[str],
        project_context: dict[str, Any],
        phase: str,
        step_index: int,
        template: PromptTemplate | None,
    ) -> str:
        """Build user prompt for execution.
        
        Args:
            role: Agent role.
            task_id: Task identifier.
            plan_steps: Steps to execute.
            project_context: Project context.
            phase: Current phase.
            step_index: Current step index.
            template: Optional template.
            
        Returns:
            Formatted user prompt.
        """
        # Format project context
        context_str = self._format_project_context(project_context)
        
        # Format plan steps
        steps_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan_steps))
        current_step = plan_steps[step_index] if step_index < len(plan_steps) else "Complete all steps"
        
        prompt = f"""## Task: Execute Plan Step

**Task ID:** {task_id}
**Phase:** {phase}
**Role:** {role}
**Current Step:** {step_index + 1} of {len(plan_steps)}

### Project Context
{context_str}

### Full Plan
{steps_str}

### Current Step to Execute
{current_step}

### Your Assignment
Execute the current step and produce the required artifacts.

### Output Format
Provide your output in the following format:

1. **Execution Summary**: Brief description of what was done
2. **Artifacts**: The actual content of any files/documents produced
3. **Next Steps**: Any recommendations for subsequent steps

```json
{{
  "execution_summary": "What was accomplished",
  "artifacts": [
    {{
      "filename": "artifact_name.md",
      "content": "Full artifact content here"
    }}
  ],
  "recommendations": ["Recommendation 1"],
  "success": true
}}
```
"""
        
        # Add template-specific requirements
        if template and template.checkpoint_artifacts:
            artifacts_str = "\n".join(f"- {a}" for a in template.checkpoint_artifacts)
            prompt += f"\n### Expected Artifacts for {role.title()}\n{artifacts_str}\n"
        
        if template and template.validation_checklist:
            checklist_str = "\n".join(f"- [ ] {c}" for c in template.validation_checklist)
            prompt += f"\n### Validation Checklist\n{checklist_str}\n"
        
        return prompt
    
    def _format_project_context(self, context: dict[str, Any]) -> str:
        """Format project context for prompt injection.
        
        Args:
            context: Project context dictionary.
            
        Returns:
            Formatted context string.
        """
        lines = []
        
        # Core project info
        if "project_name" in context:
            lines.append(f"**Project:** {context['project_name']}")
        if "project_id" in context:
            lines.append(f"**Project ID:** {context['project_id']}")
        if "client" in context:
            lines.append(f"**Client:** {context['client']}")
        if "description" in context:
            lines.append(f"**Description:** {context['description']}")
        
        # Phase info
        if "current_phase" in context:
            lines.append(f"**Current Phase:** {context['current_phase']}")
        if "completed_phases" in context:
            phases = context['completed_phases']
            if phases:
                lines.append(f"**Completed Phases:** {', '.join(phases)}")
        
        # Requirements
        if "requirements" in context:
            lines.append("\n**Requirements:**")
            for req in context["requirements"]:
                lines.append(f"- {req}")
        
        # Constraints
        if "constraints" in context:
            lines.append("\n**Constraints:**")
            for constraint in context["constraints"]:
                lines.append(f"- {constraint}")
        
        # Previous artifacts
        if "artifacts" in context and context["artifacts"]:
            lines.append("\n**Available Artifacts:**")
            for artifact in context["artifacts"]:
                lines.append(f"- {artifact}")
        
        return "\n".join(lines) if lines else "No additional context provided."
    
    @property
    def available_roles(self) -> list[str]:
        """Get list of roles with loaded templates."""
        return list(self._templates.keys())


# Singleton instance
_prompt_builder: PromptBuilder | None = None


def get_prompt_builder() -> PromptBuilder:
    """Get the global prompt builder instance.
    
    Returns:
        Singleton PromptBuilder instance.
    """
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def reset_prompt_builder() -> None:
    """Reset the global prompt builder (for testing)."""
    global _prompt_builder
    _prompt_builder = None
