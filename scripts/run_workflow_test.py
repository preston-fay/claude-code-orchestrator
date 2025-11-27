#!/usr/bin/env python3
"""
Manual test script for end-to-end workflow testing.

Usage:
    # Simulated mode (no API key needed)
    python scripts/run_workflow_test.py
    
    # Real LLM mode
    ANTHROPIC_API_KEY=sk-ant-... python scripts/run_workflow_test.py --real-llm
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import PhaseType, ProjectState, TaskDefinition, AgentContext
from orchestrator_v2.agents.factory import create_agent, list_available_agents
from orchestrator_v2.user.models import UserProfile


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_success(msg: str):
    """Print success message."""
    print(f"  ✅ {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"  ❌ {msg}")


def print_info(msg: str):
    """Print info message."""
    print(f"  ℹ️  {msg}")


async def test_agent_factory():
    """Test the agent factory."""
    print_header("Testing Agent Factory")
    
    agents = list_available_agents()
    print_info(f"Available agents: {', '.join(agents)}")
    
    for agent_id in agents:
        agent = create_agent(agent_id)
        if agent:
            print_success(f"Created {agent_id} -> {type(agent).__name__}")
        else:
            print_error(f"Failed to create {agent_id}")


async def test_simulated_agent(agent_id: str = "architect"):
    """Test an agent in simulated mode."""
    print_header(f"Testing {agent_id.title()} Agent (Simulated)")
    
    agent = create_agent(agent_id)
    if not agent:
        print_error(f"Failed to create {agent_id}")
        return
    
    state = ProjectState(
        project_id="test-123",
        run_id="run-456",
        project_name="Test Project",
        metadata={
            "description": "A test project for validation",
            "requirements": ["Feature A", "Feature B"],
        },
    )
    
    task = TaskDefinition(
        task_id="task-001",
        description=f"Execute {agent_id} tasks",
        requirements=state.metadata.get("requirements", []),
    )
    
    # Initialize
    print_info("Initializing...")
    agent.initialize(state)
    print_success("Initialized")
    
    # Plan (no context = simulated)
    print_info("Planning...")
    plan = agent.plan(task, PhaseType.DEVELOPMENT, state)
    print_success(f"Created plan with {len(plan.steps)} steps")
    if plan.analysis:
        print_info(f"Analysis: {plan.analysis[:100]}...")
    
    # Act
    print_info("Acting...")
    output = agent.act(plan, state)
    print_success(f"Generated {len(output.artifacts)} artifacts")
    for artifact in output.artifacts:
        print_info(f"  - {artifact.name} ({len(artifact.content)} bytes)")
    
    # Summarize
    print_info("Summarizing...")
    summary = agent.summarize(state.run_id)
    print_success(f"Summary: {summary.summary[:100]}...")
    
    # Complete
    agent.complete(state)
    print_success("Completed")


async def test_real_llm_agent(agent_id: str = "architect"):
    """Test an agent with real LLM calls."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print_error("ANTHROPIC_API_KEY not set")
        return
    
    print_header(f"Testing {agent_id.title()} Agent (Real LLM)")
    print_info(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    agent = create_agent(agent_id)
    if not agent:
        print_error(f"Failed to create {agent_id}")
        return
    
    state = ProjectState(
        project_id="real-123",
        run_id="run-456",
        project_name="Task Management API",
        metadata={
            "description": "A REST API for managing tasks with user authentication",
            "requirements": [
                "CRUD operations for tasks",
                "User authentication with JWT",
                "PostgreSQL database",
                "Rate limiting",
            ],
        },
    )
    
    task = TaskDefinition(
        task_id="task-001",
        description="Design the system architecture for a task management API",
        requirements=state.metadata.get("requirements", []),
    )
    
    context = AgentContext(
        project_state=state,
        task=task,
        user_id="test-user",
        llm_api_key=api_key,
        llm_provider="anthropic",
        model="claude-sonnet-4-5-20250929",
    )
    
    # Initialize with context
    print_info("Initializing with context...")
    agent.initialize(state, context)
    print_success("Initialized")
    
    # Plan with context (triggers real LLM)
    print_info("Planning with LLM...")
    try:
        plan = agent.plan(task, PhaseType.ARCHITECTURE, state, context)
        print_success(f"Created plan with {len(plan.steps)} steps")
        if plan.analysis:
            print_info(f"Analysis: {plan.analysis[:200]}...")
        for i, step in enumerate(plan.steps[:3]):
            print_info(f"  Step {i+1}: {step.description[:80]}...")
    except Exception as e:
        print_error(f"Plan failed: {e}")
        return
    
    # Act with context (triggers real LLM)
    print_info("Acting with LLM...")
    try:
        output = agent.act(plan, state, context)
        print_success(f"Generated {len(output.artifacts)} artifacts")
        for artifact in output.artifacts:
            preview = artifact.content[:200] if len(artifact.content) > 200 else artifact.content
            print_info(f"  - {artifact.name}:")
            print(f"      {preview}...")
    except Exception as e:
        print_error(f"Act failed: {e}")
        return
    
    # Summarize
    print_info("Summarizing...")
    summary = agent.summarize(state.run_id)
    print_success(f"Summary: {summary.summary}")
    
    # Complete
    agent.complete(state)
    print_success("Completed")


async def test_workflow_engine():
    """Test the WorkflowEngine."""
    print_header("Testing WorkflowEngine")
    
    engine = WorkflowEngine(use_real_agents=True)
    
    # Start project
    print_info("Starting project...")
    state = await engine.start_project(
        project_name="Workflow Test Project",
        client="test-client",
        metadata={
            "description": "A test project",
            "requirements": ["Test requirement"],
        },
    )
    print_success(f"Created project: {state.project_id}")
    print_info(f"Current phase: {state.current_phase.value}")
    
    # Check agent creation
    print_info("Creating agents...")
    agent = engine._get_or_create_agent("architect")
    if agent:
        print_success(f"Created architect agent: {type(agent).__name__}")
    else:
        print_error("Failed to create architect agent")
    
    # Get status
    status = await engine.get_status()
    print_info(f"Status: phase={status['current_phase']}, progress={status['progress']}")


async def main():
    parser = argparse.ArgumentParser(description="Test orchestrator workflow")
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use real LLM (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--agent",
        default="architect",
        help="Agent to test (default: architect)",
    )
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  Orchestrator v2 Workflow Test")
    print("="*60)
    
    # Test agent factory
    await test_agent_factory()
    
    # Test simulated agent
    await test_simulated_agent(args.agent)
    
    # Test workflow engine
    await test_workflow_engine()
    
    # Test real LLM if requested
    if args.real_llm:
        await test_real_llm_agent(args.agent)
    else:
        print_header("Skipping Real LLM Tests")
        print_info("Use --real-llm flag to test with real API")
    
    print("\n" + "="*60)
    print("  Tests Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
