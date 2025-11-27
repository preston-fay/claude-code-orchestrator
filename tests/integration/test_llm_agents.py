"""
Integration tests for LLM-enabled agents.

These tests verify that agents can:
1. Load prompt templates
2. Build prompts with project context
3. Call the LLM (when context provided)
4. Parse responses into structured data
5. Create artifacts from LLM output

Note: Tests with actual LLM calls require ANTHROPIC_API_KEY to be set.
"""

import asyncio
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from orchestrator_v2.agents import (
    BaseAgent,
    BaseAgentConfig,
    ArchitectAgent,
    create_architect_agent,
    PromptBuilder,
    get_prompt_builder,
    ResponseParser,
    get_response_parser,
)
from orchestrator_v2.engine.state_models import (
    AgentContext,
    PhaseType,
    ProjectState,
    TaskDefinition,
    TokenUsage,
)
from orchestrator_v2.llm import LlmResult


class TestPromptBuilder:
    """Test the PromptBuilder class."""
    
    def test_loads_templates_from_directory(self):
        """Verify prompt builder loads templates from subagent_prompts/."""
        builder = get_prompt_builder()
        
        # Should have loaded templates for all agent roles
        assert len(builder.available_roles) > 0
        
        # Architect template should be available
        assert "architect" in builder.available_roles
    
    def test_builds_plan_prompt(self):
        """Verify plan prompts are built correctly."""
        builder = get_prompt_builder()
        
        prompt = builder.build_plan_prompt(
            role="architect",
            task_id="test_task_001",
            task_description="Design the system architecture",
            project_context={
                "project_name": "Test Project",
                "project_id": "proj_123",
                "client": "Test Client",
                "current_phase": "architecture",
            },
            phase="architecture",
        )
        
        # Verify prompt structure
        assert prompt.role == "architect"
        assert prompt.task_id == "test_task_001"
        assert "Test Project" in prompt.user_prompt
        assert "Create Execution Plan" in prompt.user_prompt
        assert prompt.estimated_tokens > 0
    
    def test_builds_act_prompt(self):
        """Verify act prompts are built correctly."""
        builder = get_prompt_builder()
        
        prompt = builder.build_act_prompt(
            role="architect",
            task_id="test_task_001",
            plan_steps=["Analyze requirements", "Create proposal", "Design data model"],
            project_context={
                "project_name": "Test Project",
                "project_id": "proj_123",
            },
            phase="architecture",
            step_index=0,
        )
        
        # Verify prompt structure
        assert prompt.role == "architect"
        assert "Execute Plan Step" in prompt.user_prompt
        assert "Step 1" in prompt.user_prompt or "1 of 3" in prompt.user_prompt


class TestResponseParser:
    """Test the ResponseParser class."""
    
    def test_parses_plan_json_response(self):
        """Verify JSON plan responses are parsed correctly."""
        parser = get_response_parser()
        
        response_text = '''Here's my analysis:

```json
{
  "analysis": "The project requires a scalable API architecture",
  "steps": [
    {"step_id": "step_1", "description": "Analyze requirements", "estimated_tokens": 300},
    {"step_id": "step_2", "description": "Design architecture", "estimated_tokens": 500}
  ],
  "outputs": ["architecture.md", "data_model.md"],
  "dependencies": ["requirements.md"],
  "validation_criteria": ["All requirements addressed"]
}
```
'''
        
        result = parser.parse_plan_response(response_text)
        
        assert result.analysis == "The project requires a scalable API architecture"
        assert len(result.steps) == 2
        assert result.steps[0]["description"] == "Analyze requirements"
        assert "architecture.md" in result.outputs
    
    def test_parses_act_json_response(self):
        """Verify JSON act responses are parsed correctly."""
        parser = get_response_parser()
        
        response_text = '''Execution complete.

```json
{
  "execution_summary": "Created architecture documentation",
  "artifacts": [
    {
      "filename": "architecture.md",
      "content": "# Architecture\n\nSystem overview..."
    }
  ],
  "recommendations": ["Review with stakeholders"],
  "success": true
}
```
'''
        
        result = parser.parse_act_response(response_text)
        
        assert result.success is True
        assert result.execution_summary == "Created architecture documentation"
        assert len(result.artifacts) == 1
        assert result.artifacts[0].filename == "architecture.md"
    
    def test_handles_malformed_response(self):
        """Verify parser handles non-JSON responses gracefully."""
        parser = get_response_parser()
        
        response_text = '''Here's what I found:

1. First step: Analyze requirements
2. Second step: Design architecture
3. Third step: Create documentation

- Output: architecture.md
- Dependency: requirements input
'''
        
        result = parser.parse_plan_response(response_text)
        
        # Should have extracted some steps
        assert len(result.steps) >= 1
        assert result.raw_response == response_text


class TestBaseAgentLlm:
    """Test BaseAgent LLM integration."""
    
    @pytest.fixture
    def agent(self):
        """Create a test agent."""
        config = BaseAgentConfig(
            id="test_agent",
            role="architect",
            description="Test agent",
        )
        return BaseAgent(config)
    
    @pytest.fixture
    def project_state(self):
        """Create test project state."""
        return ProjectState(
            project_id="test_project",
            run_id="run_001",
            project_name="Test Project",
            client="Test Client",
            current_phase=PhaseType.ARCHITECTURE,
        )
    
    @pytest.fixture
    def task(self):
        """Create test task."""
        return TaskDefinition(
            task_id="task_001",
            description="Design the system architecture",
        )
    
    @pytest.fixture
    def agent_context(self, project_state, task):
        """Create agent context with mock credentials."""
        return AgentContext(
            project_state=project_state,
            task=task,
            user_id="user_001",
            llm_api_key="test_key",
            llm_provider="anthropic",
            model="claude-sonnet-4-5-20250929",
        )
    
    @pytest.mark.asyncio
    async def test_plan_without_context_returns_simulated(self, agent, task, project_state):
        """Verify plan returns simulated response without LLM context."""
        await agent.initialize(project_state)
        
        # Plan without context - should return simulated plan
        plan = await agent.plan(task, PhaseType.ARCHITECTURE, project_state)
        
        assert plan.plan_id == f"{task.task_id}_plan"
        assert plan.agent_id == agent.id
        assert len(plan.steps) >= 1
    
    @pytest.mark.asyncio
    async def test_act_without_context_returns_simulated(self, agent, task, project_state):
        """Verify act returns simulated response without LLM context."""
        await agent.initialize(project_state)
        plan = await agent.plan(task, PhaseType.ARCHITECTURE, project_state)
        
        # Act without context - should return simulated output
        output = await agent.act(plan, project_state)
        
        assert output.success is True
        assert len(output.artifacts) >= 1
    
    @pytest.mark.asyncio
    async def test_plan_with_mocked_llm(self, agent, task, project_state, agent_context):
        """Verify plan calls LLM when context is provided."""
        # Mock the LLM provider
        mock_result = LlmResult(
            text='''```json
{
  "analysis": "Test analysis",
  "steps": [{"step_id": "s1", "description": "Test step", "estimated_tokens": 100}],
  "outputs": ["test.md"],
  "dependencies": [],
  "validation_criteria": ["Complete"]
}
```''',
            input_tokens=100,
            output_tokens=50,
        )
        
        with patch.object(agent, '_call_llm_with_prompt', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_result
            
            await agent.initialize(project_state, agent_context)
            plan = await agent.plan(task, PhaseType.ARCHITECTURE, project_state, agent_context)
            
            # Should have called LLM
            mock_llm.assert_called_once()
            
            # Plan should reflect LLM response
            assert plan.analysis == "Test analysis"
            assert len(plan.steps) == 1


class TestArchitectAgentLlm:
    """Test ArchitectAgent LLM integration."""
    
    @pytest.fixture
    def architect(self):
        """Create an architect agent."""
        return create_architect_agent()
    
    @pytest.fixture
    def project_state(self):
        """Create test project state."""
        return ProjectState(
            project_id="arch_test_project",
            run_id="run_001",
            project_name="Architecture Test Project",
            client="Test Client",
            current_phase=PhaseType.ARCHITECTURE,
        )
    
    @pytest.fixture
    def task(self):
        """Create architecture task."""
        return TaskDefinition(
            task_id="arch_task_001",
            description="Design system architecture for a REST API",
            requirements=["Scalable", "Secure", "Well-documented"],
        )
    
    @pytest.mark.asyncio
    async def test_architect_creates_architecture_artifacts(self, architect, task, project_state):
        """Verify architect creates expected artifacts."""
        await architect.initialize(project_state)
        plan = await architect.plan(task, PhaseType.ARCHITECTURE, project_state)
        output = await architect.act(plan, project_state)
        
        # Should have created artifacts
        assert len(output.artifacts) >= 1
        
        # Should have architecture-related artifacts
        artifact_names = [a.path for a in output.artifacts]
        has_architecture = any("architecture" in name.lower() for name in artifact_names)
        assert has_architecture, f"Expected architecture artifact, got: {artifact_names}"
    
    @pytest.mark.asyncio
    async def test_architect_full_lifecycle(self, architect, task, project_state):
        """Test complete architect agent lifecycle."""
        # Initialize
        event = await architect.initialize(project_state)
        assert event.event_type == "agent_initialized"
        
        # Plan
        plan = await architect.plan(task, PhaseType.ARCHITECTURE, project_state)
        assert len(plan.steps) >= 1
        
        # Act
        output = await architect.act(plan, project_state)
        assert output.success is True
        
        # Summarize
        summary = await architect.summarize(plan, output, project_state)
        assert summary.success is True
        assert "Architect" in summary.summary
        
        # Complete
        complete_event = await architect.complete(project_state)
        assert complete_event.event_type == "agent_completed"


# Integration test with real LLM (requires API key)
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestRealLlmIntegration:
    """Integration tests with real LLM calls.
    
    These tests require ANTHROPIC_API_KEY to be set in the environment.
    They make actual API calls and should be run sparingly.
    """
    
    @pytest.fixture
    def project_state(self):
        return ProjectState(
            project_id="real_llm_test",
            run_id="run_001",
            project_name="Real LLM Test Project",
            client="Integration Test",
            current_phase=PhaseType.ARCHITECTURE,
            metadata={
                "requirements": [
                    "Build a REST API for task management",
                    "Support user authentication",
                    "Allow CRUD operations on tasks",
                ],
                "constraints": [
                    "Must use Python",
                    "Budget: $100/month for hosting",
                ],
            },
        )
    
    @pytest.fixture
    def agent_context(self, project_state):
        task = TaskDefinition(
            task_id="real_test_task",
            description="Design architecture for task management API",
        )
        return AgentContext(
            project_state=project_state,
            task=task,
            user_id="test_user",
            llm_api_key=os.environ["ANTHROPIC_API_KEY"],
            llm_provider="anthropic",
            model="claude-sonnet-4-5-20250929",
        )
    
    @pytest.mark.asyncio
    async def test_architect_with_real_llm(self, project_state, agent_context):
        """Test architect agent with real LLM calls."""
        architect = create_architect_agent()
        
        task = TaskDefinition(
            task_id="real_arch_task",
            description="Design architecture for a task management REST API",
        )
        
        # Initialize with context
        await architect.initialize(project_state, agent_context)
        
        # Plan - should call real LLM
        plan = await architect.plan(task, PhaseType.ARCHITECTURE, project_state, agent_context)
        
        # Verify LLM-generated plan
        assert plan.analysis != ""  # Should have real analysis
        assert len(plan.steps) >= 1
        
        print(f"\n=== LLM-Generated Plan ===")
        print(f"Analysis: {plan.analysis[:200]}...")
        print(f"Steps: {len(plan.steps)}")
        for step in plan.steps:
            print(f"  - {step.description}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
