"""
LLM Agent Mixin for Orchestrator v2.

Provides LLM calling capabilities that can be mixed into agent classes.
This mixin handles prompt building, LLM calls, and response parsing.
"""

import logging
from typing import Any, TYPE_CHECKING

from orchestrator_v2.agents.prompt_builder import get_prompt_builder, BuiltPrompt
from orchestrator_v2.agents.response_parser import (
    get_response_parser,
    PlanResponse,
    ActResponse,
)
from orchestrator_v2.llm import get_provider_registry, LlmResult

if TYPE_CHECKING:
    from orchestrator_v2.engine.state_models import (
        AgentContext,
        AgentPlan,
        AgentPlanStep,
        PhaseType,
        ProjectState,
        TaskDefinition,
    )

logger = logging.getLogger(__name__)


class LlmAgentMixin:
    """Mixin that provides LLM calling capabilities to agents.
    
    This mixin should be used with BaseAgent or subclasses.
    It provides methods for:
    - Building prompts from templates
    - Calling the LLM
    - Parsing responses into structured data
    
    Usage:
        class MyAgent(LlmAgentMixin, BaseAgent):
            async def plan(self, task, phase, project_state):
                response = await self._llm_plan(task, phase, project_state)
                # Use response.steps, response.outputs, etc.
    """
    
    # These should be set by the concrete agent class
    id: str
    role: str
    _record_tokens: Any  # Token recording method from BaseAgent
    
    async def _llm_plan(
        self,
        task: "TaskDefinition",
        phase: "PhaseType",
        project_state: "ProjectState",
        context: "AgentContext | None" = None,
    ) -> PlanResponse:
        """Call LLM to create an execution plan.
        
        Args:
            task: Task to plan for.
            phase: Current workflow phase.
            project_state: Project state for context.
            context: Optional agent context with LLM credentials.
            
        Returns:
            Parsed plan response.
        """
        prompt_builder = get_prompt_builder()
        parser = get_response_parser()
        
        # Build project context for prompt
        project_context = self._build_project_context(project_state)
        
        # Build the planning prompt
        built_prompt = prompt_builder.build_plan_prompt(
            role=self.role,
            task_id=task.task_id,
            task_description=task.description,
            project_context=project_context,
            phase=phase.value,
        )
        
        logger.info(
            f"Agent {self.id} building plan for task {task.task_id}, "
            f"estimated tokens: {built_prompt.estimated_tokens}"
        )
        
        # Call LLM if context provided
        if context:
            try:
                result = await self._call_llm_with_prompt(built_prompt, context)
                return parser.parse_plan_response(result.text)
            except Exception as e:
                logger.error(f"LLM call failed for planning: {e}")
                # Fall through to simulated response
        
        # Return simulated response if no context or LLM failed
        return self._simulate_plan_response(task, phase)
    
    async def _llm_act(
        self,
        plan: "AgentPlan",
        project_state: "ProjectState",
        context: "AgentContext | None" = None,
        step_index: int = 0,
    ) -> ActResponse:
        """Call LLM to execute plan steps.
        
        Args:
            plan: Execution plan with steps.
            project_state: Project state for context.
            context: Optional agent context with LLM credentials.
            step_index: Which step to execute.
            
        Returns:
            Parsed execution response.
        """
        prompt_builder = get_prompt_builder()
        parser = get_response_parser()
        
        # Build project context
        project_context = self._build_project_context(project_state)
        
        # Extract step descriptions
        plan_steps = [step.description for step in plan.steps]
        
        # Build the execution prompt
        built_prompt = prompt_builder.build_act_prompt(
            role=self.role,
            task_id=plan.task_id,
            plan_steps=plan_steps,
            project_context=project_context,
            phase=project_state.current_phase.value,
            step_index=step_index,
        )
        
        logger.info(
            f"Agent {self.id} executing step {step_index + 1}/{len(plan_steps)} "
            f"for task {plan.task_id}"
        )
        
        # Call LLM if context provided
        if context:
            try:
                result = await self._call_llm_with_prompt(built_prompt, context)
                return parser.parse_act_response(result.text)
            except Exception as e:
                logger.error(f"LLM call failed for execution: {e}")
                # Fall through to simulated response
        
        # Return simulated response if no context or LLM failed
        return self._simulate_act_response(plan, project_state)
    
    async def _call_llm_with_prompt(
        self,
        built_prompt: BuiltPrompt,
        context: "AgentContext",
    ) -> LlmResult:
        """Call the LLM with a built prompt.
        
        Args:
            built_prompt: Constructed prompt.
            context: Agent context with credentials.
            
        Returns:
            LLM result.
        """
        registry = get_provider_registry()
        
        # Combine system and user prompts
        # Most providers expect a single prompt, so we combine them
        full_prompt = f"{built_prompt.system_prompt}\n\n{built_prompt.user_prompt}"
        
        # Get model from context or use default
        model = context.model or "claude-sonnet-4-5-20250929"
        
        # Call the provider
        result = await registry.generate(
            prompt=full_prompt,
            model=model,
            context=context,
        )
        
        # Record token usage
        if hasattr(self, '_record_tokens'):
            self._record_tokens(result.input_tokens, result.output_tokens)
        
        logger.info(
            f"LLM call complete: {result.input_tokens} input, "
            f"{result.output_tokens} output tokens"
        )
        
        return result
    
    def _build_project_context(self, project_state: "ProjectState") -> dict[str, Any]:
        """Build project context dictionary for prompts.
        
        Args:
            project_state: Current project state.
            
        Returns:
            Context dictionary.
        """
        context = {
            "project_id": project_state.project_id,
            "project_name": project_state.project_name,
            "client": project_state.client,
            "current_phase": project_state.current_phase.value,
            "completed_phases": [p.value for p in project_state.completed_phases],
        }
        
        # Add artifacts if available
        if project_state.artifacts:
            context["artifacts"] = list(project_state.artifacts.keys())
        
        # Add metadata if available
        if project_state.metadata:
            if "requirements" in project_state.metadata:
                context["requirements"] = project_state.metadata["requirements"]
            if "constraints" in project_state.metadata:
                context["constraints"] = project_state.metadata["constraints"]
            if "description" in project_state.metadata:
                context["description"] = project_state.metadata["description"]
        
        return context
    
    def _simulate_plan_response(
        self,
        task: "TaskDefinition",
        phase: "PhaseType",
    ) -> PlanResponse:
        """Generate a simulated plan response.
        
        Used when no LLM context is available.
        
        Args:
            task: Task definition.
            phase: Current phase.
            
        Returns:
            Simulated plan response.
        """
        return PlanResponse(
            analysis=f"Simulated analysis for {task.task_id} in {phase.value} phase",
            steps=[
                {
                    "step_id": f"{task.task_id}_step_1",
                    "description": f"{self.role} analysis step",
                    "estimated_tokens": 500,
                },
                {
                    "step_id": f"{task.task_id}_step_2",
                    "description": f"{self.role} execution step",
                    "estimated_tokens": 500,
                },
            ],
            outputs=[f"{self.role}_output.md"],
            dependencies=[],
            validation_criteria=["Output is complete", "Quality standards met"],
            raw_response="[Simulated response - no LLM context provided]",
        )
    
    def _simulate_act_response(
        self,
        plan: "AgentPlan",
        project_state: "ProjectState",
    ) -> ActResponse:
        """Generate a simulated execution response.
        
        Used when no LLM context is available.
        
        Args:
            plan: Execution plan.
            project_state: Project state.
            
        Returns:
            Simulated execution response.
        """
        from orchestrator_v2.agents.response_parser import ArtifactData
        
        return ActResponse(
            execution_summary=f"Simulated execution of {plan.task_id} by {self.role}",
            artifacts=[
                ArtifactData(
                    filename=f"{self.role}_output.md",
                    content=f"""# {self.role.title()} Output

## Project: {project_state.project_name}
## Task: {plan.task_id}
## Phase: {project_state.current_phase.value}

### Summary
This is a simulated artifact from the {self.role} agent.
No LLM context was provided, so this is placeholder content.

### Steps Executed
{chr(10).join(f"- {s.description}" for s in plan.steps)}
""",
                    artifact_type="document",
                )
            ],
            recommendations=["Provide LLM context for real execution"],
            success=True,
            raw_response="[Simulated response - no LLM context provided]",
        )
