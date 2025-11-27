#!/usr/bin/env python3
"""
Manual test script for LLM-enabled agents.

This script runs a quick test of the agent LLM integration.
Useful for verifying the setup without running the full test suite.

Usage:
    # Test without LLM (simulated mode)
    python scripts/test_llm_agents.py
    
    # Test with real LLM
    ANTHROPIC_API_KEY=your_key python scripts/test_llm_agents.py --real-llm
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator_v2.agents import (
    create_architect_agent,
    get_prompt_builder,
    get_response_parser,
)
from orchestrator_v2.engine.state_models import (
    AgentContext,
    PhaseType,
    ProjectState,
    TaskDefinition,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_prompt_builder():
    """Test the prompt builder."""
    print("\n" + "="*60)
    print("Testing Prompt Builder")
    print("="*60)
    
    builder = get_prompt_builder()
    
    print(f"\nLoaded templates for roles: {builder.available_roles}")
    
    # Test building a plan prompt
    prompt = builder.build_plan_prompt(
        role="architect",
        task_id="test_001",
        task_description="Design system architecture",
        project_context={
            "project_name": "Test Project",
            "project_id": "proj_123",
            "client": "Test Client",
        },
        phase="architecture",
    )
    
    print(f"\nBuilt plan prompt:")
    print(f"  Role: {prompt.role}")
    print(f"  Task ID: {prompt.task_id}")
    print(f"  Estimated tokens: {prompt.estimated_tokens}")
    print(f"  System prompt length: {len(prompt.system_prompt)} chars")
    print(f"  User prompt length: {len(prompt.user_prompt)} chars")
    
    print("\n✓ Prompt builder working correctly")


def test_response_parser():
    """Test the response parser."""
    print("\n" + "="*60)
    print("Testing Response Parser")
    print("="*60)
    
    parser = get_response_parser()
    
    # Test parsing a JSON plan response
    plan_response = '''Here's my analysis:

```json
{
  "analysis": "The project requires a scalable architecture",
  "steps": [
    {"step_id": "step_1", "description": "Analyze requirements", "estimated_tokens": 300}
  ],
  "outputs": ["architecture.md"],
  "dependencies": [],
  "validation_criteria": ["Complete"]
}
```
'''
    
    result = parser.parse_plan_response(plan_response)
    
    print(f"\nParsed plan response:")
    print(f"  Analysis: {result.analysis[:50]}...")
    print(f"  Steps: {len(result.steps)}")
    print(f"  Outputs: {result.outputs}")
    
    print("\n✓ Response parser working correctly")


async def test_architect_agent_simulated():
    """Test architect agent in simulated mode."""
    print("\n" + "="*60)
    print("Testing Architect Agent (Simulated Mode)")
    print("="*60)
    
    # Create agent and project state
    architect = create_architect_agent()
    
    project_state = ProjectState(
        project_id="sim_test_project",
        run_id="run_001",
        project_name="Simulated Test Project",
        client="Test Client",
        current_phase=PhaseType.ARCHITECTURE,
    )
    
    task = TaskDefinition(
        task_id="sim_task_001",
        description="Design architecture for a REST API",
    )
    
    print(f"\nProject: {project_state.project_name}")
    print(f"Task: {task.description}")
    
    # Run agent lifecycle without LLM context
    print("\nRunning agent lifecycle (simulated)...")
    
    event = await architect.initialize(project_state)
    print(f"  ✓ Initialized: {event.event_type}")
    
    plan = await architect.plan(task, PhaseType.ARCHITECTURE, project_state)
    print(f"  ✓ Plan created: {len(plan.steps)} steps")
    for step in plan.steps:
        print(f"      - {step.description}")
    
    output = await architect.act(plan, project_state)
    print(f"  ✓ Execution complete: {len(output.artifacts)} artifacts")
    for artifact in output.artifacts:
        print(f"      - {artifact.path}")
    
    summary = await architect.summarize(plan, output, project_state)
    print(f"  ✓ Summary: {summary.summary[:100]}...")
    
    complete = await architect.complete(project_state)
    print(f"  ✓ Complete: {complete.event_type}")
    
    print(f"\nTotal tokens used: {architect._token_usage.total_tokens}")
    print("\n✓ Architect agent working correctly in simulated mode")


async def test_architect_agent_real_llm():
    """Test architect agent with real LLM calls."""
    print("\n" + "="*60)
    print("Testing Architect Agent (Real LLM Mode)")
    print("="*60)
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠ ANTHROPIC_API_KEY not set, skipping real LLM test")
        return
    
    # Create agent and project state
    architect = create_architect_agent()
    
    project_state = ProjectState(
        project_id="real_test_project",
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
    
    task = TaskDefinition(
        task_id="real_task_001",
        description="Design architecture for task management API",
    )
    
    agent_context = AgentContext(
        project_state=project_state,
        task=task,
        user_id="test_user",
        llm_api_key=api_key,
        llm_provider="anthropic",
        model="claude-sonnet-4-5-20250929",
    )
    
    print(f"\nProject: {project_state.project_name}")
    print(f"Task: {task.description}")
    print(f"Model: {agent_context.model}")
    
    # Run agent lifecycle with LLM context
    print("\nRunning agent lifecycle (real LLM)...")
    
    event = await architect.initialize(project_state, agent_context)
    print(f"  ✓ Initialized: {event.event_type}")
    
    print("\n  Calling LLM for planning...")
    plan = await architect.plan(task, PhaseType.ARCHITECTURE, project_state, agent_context)
    print(f"  ✓ Plan created: {len(plan.steps)} steps")
    print(f"    Analysis: {plan.analysis[:200]}..." if plan.analysis else "    No analysis")
    for step in plan.steps:
        print(f"      - {step.description}")
    
    print(f"\nTotal tokens used: {architect._token_usage.total_tokens}")
    print("\n✓ Architect agent working correctly with real LLM")


async def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test LLM-enabled agents")
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Run test with real LLM (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()
    
    print("\n" + "#"*60)
    print("# LLM Agent Integration Tests")
    print("#"*60)
    
    # Test components
    test_prompt_builder()
    test_response_parser()
    
    # Test agent (simulated)
    await test_architect_agent_simulated()
    
    # Test agent (real LLM) if requested
    if args.real_llm:
        await test_architect_agent_real_llm()
    
    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
