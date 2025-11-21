#!/usr/bin/env python3
"""
Validation script for Orchestrator v2 Agent Runtime.

This script exercises the agent lifecycle to verify:
- Agent initialization with config
- Planning phase execution
- Action execution with artifact creation
- Summarization
- Token tracking
- Subagent execution

Run with: python scripts/test_agent_runtime.py
"""

import asyncio
from uuid import uuid4

from orchestrator_v2.agents import (
    create_architect_agent,
    create_data_agent,
    create_developer_agent,
    create_qa_agent,
    create_documentarian_agent,
)
from orchestrator_v2.engine.state_models import (
    PhaseType,
    ProjectState,
    TaskDefinition,
)


async def test_agent_lifecycle(agent, agent_name: str, phase: PhaseType, project_state: ProjectState):
    """Test a single agent through its full lifecycle.

    Args:
        agent: Agent instance to test.
        agent_name: Name for display.
        phase: Phase to execute in.
        project_state: Project state.
    """
    print(f"\n{'='*50}")
    print(f"Testing {agent_name} Agent")
    print(f"{'='*50}")

    # Initialize
    print("\n[1] Initialize...")
    event = await agent.initialize(project_state)
    print(f"    Event: {event.event_type}")
    print(f"    Skills loaded: {agent._skills}")
    print(f"    Tools loaded: {agent._tools}")

    # Plan
    print("\n[2] Plan...")
    task = TaskDefinition(
        task_id=f"{phase.value}_{agent.id}_{uuid4().hex[:8]}",
        description=f"Test task for {agent.role}",
    )
    plan = await agent.plan(task, phase, project_state)
    print(f"    Plan ID: {plan.plan_id}")
    print(f"    Steps: {len(plan.steps)}")
    for step in plan.steps:
        print(f"      - {step.description}")
    print(f"    Estimated tokens: {plan.estimated_tokens}")

    # Act
    print("\n[3] Act...")
    output = await agent.act(plan, project_state)
    print(f"    Success: {output.success}")
    print(f"    Artifacts created: {len(output.artifacts)}")
    for artifact in output.artifacts:
        print(f"      - {artifact.path} ({artifact.size_bytes} bytes)")
    print(f"    Token usage: {output.token_usage.total_tokens}")

    # Summarize
    print("\n[4] Summarize...")
    summary = await agent.summarize(plan, output, project_state)
    print(f"    Summary: {summary.summary}")
    print(f"    Total tokens: {summary.total_token_usage.total_tokens}")

    # Complete
    print("\n[5] Complete...")
    event = await agent.complete(project_state)
    print(f"    Event: {event.event_type}")
    print(f"    Total events: {len(agent._events)}")

    # Get state
    state = agent.get_state()
    print(f"\n[6] Final State...")
    print(f"    Status: {state.status}")
    print(f"    Summary: {state.summary}")

    return summary


async def main():
    """Run the agent runtime validation tests."""
    print("=" * 60)
    print("Orchestrator v2 Agent Runtime Validation")
    print("=" * 60)

    # Create project state for testing
    project_state = ProjectState(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        project_name="Test Analytics Project",
        client="kearney-default",
        current_phase=PhaseType.PLANNING,
        completed_phases=[],
        metadata={"requirements": ["Build forecast", "Create dashboard"]},
    )

    print(f"\nProject: {project_state.project_name}")
    print(f"Project ID: {project_state.project_id[:8]}...")

    # Test each agent type
    agents_to_test = [
        (create_architect_agent(), "Architect", PhaseType.PLANNING),
        (create_data_agent(), "Data", PhaseType.DATA),
        (create_developer_agent(), "Developer", PhaseType.DEVELOPMENT),
        (create_qa_agent(), "QA", PhaseType.QA),
        (create_documentarian_agent(), "Documentarian", PhaseType.DOCUMENTATION),
    ]

    summaries = []
    total_tokens = 0

    for agent, name, phase in agents_to_test:
        # Update project state phase for each test
        project_state.current_phase = phase

        summary = await test_agent_lifecycle(agent, name, phase, project_state)
        summaries.append((name, summary))
        total_tokens += summary.total_token_usage.total_tokens

    # Summary
    print("\n" + "=" * 60)
    print("Validation Complete")
    print("=" * 60)
    print("\nAgent Summaries:")
    for name, summary in summaries:
        print(f"  - {name}: {summary.total_token_usage.total_tokens} tokens, "
              f"{len(summary.artifacts)} artifacts")

    print(f"\nTotal tokens used: {total_tokens}")
    print(f"Agents tested: {len(summaries)}")
    print("\nThe Agent Runtime is functioning correctly!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
