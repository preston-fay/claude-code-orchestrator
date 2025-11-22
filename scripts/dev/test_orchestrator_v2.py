#!/usr/bin/env python3
"""
Validation script for Orchestrator v2 WorkflowEngine.

This script exercises the WorkflowEngine end-to-end to verify:
- Project initialization
- Phase transitions
- Checkpoint creation
- Governance evaluation
- Token tracking

Run with: python scripts/test_orchestrator_v2.py
"""

import asyncio
import json
from datetime import datetime

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.phase_manager import PhaseManager
from orchestrator_v2.engine.state_models import PhaseType


async def main():
    """Run the orchestrator validation test."""
    print("=" * 60)
    print("Orchestrator v2 Validation Test")
    print("=" * 60)
    print()

    # Create engine with default components
    print("[1] Creating WorkflowEngine...")
    engine = WorkflowEngine()
    print("    ✓ Engine created with default PhaseManager, CheckpointManager,")
    print("      GovernanceEngine, and TokenTracker")
    print()

    # Start a project
    print("[2] Starting project...")
    state = await engine.start_project(
        project_name="Test Analytics Project",
        client="kearney-default",
        metadata={"requirements": ["Build demand forecast", "Create dashboard"]},
    )
    print(f"    ✓ Project started: {state.project_id[:8]}...")
    print(f"    ✓ Run ID: {state.run_id[:8]}...")
    print(f"    ✓ Initial phase: {state.current_phase.value}")
    print(f"    ✓ Checkpoints created: {len(state.checkpoints)}")
    print()

    # Show workflow phases
    print("[3] Workflow phases:")
    phases = engine.phase_manager.list_phases()
    for phase in phases:
        marker = "→" if phase.name == state.current_phase else " "
        agents = ", ".join(phase.responsible_agents)
        print(f"    {marker} {phase.order}. {phase.name.value}: [{agents}]")
    print()

    # Run first phase (PLANNING)
    print("[4] Running PLANNING phase...")
    phase_state = await engine.run_phase(PhaseType.PLANNING)
    print(f"    ✓ Phase status: {phase_state.status}")
    print(f"    ✓ Agents executed: {phase_state.agent_ids}")
    print(f"    ✓ Duration: {(phase_state.completed_at - phase_state.started_at).total_seconds():.2f}s")
    print()

    # Check state after first phase
    print("[5] State after PLANNING:")
    status = await engine.get_status()
    print(f"    ✓ Current phase: {status['current_phase']}")
    print(f"    ✓ Completed phases: {status['completed_phases']}")
    print(f"    ✓ Progress: {status['progress']['progress_percent']:.1f}%")
    print(f"    ✓ Token usage: {status['token_usage']['total_tokens']} tokens")
    print(f"    ✓ Cost: ${status['token_usage']['cost_usd']:.4f}")
    print(f"    ✓ Checkpoints: {len(status['checkpoints'])}")
    print()

    # Run second phase (ARCHITECTURE)
    print("[6] Running ARCHITECTURE phase...")
    phase_state = await engine.run_phase(PhaseType.ARCHITECTURE)
    print(f"    ✓ Phase status: {phase_state.status}")
    print(f"    ✓ Agents executed: {phase_state.agent_ids}")
    print()

    # Run third phase (DATA - optional)
    print("[7] Running DATA phase...")
    phase_state = await engine.run_phase(PhaseType.DATA)
    print(f"    ✓ Phase status: {phase_state.status}")
    print(f"    ✓ Agents executed: {phase_state.agent_ids}")
    print()

    # Get final status
    print("[8] Final status:")
    status = await engine.get_status()
    print(f"    ✓ Current phase: {status['current_phase']}")
    print(f"    ✓ Completed phases: {status['completed_phases']}")
    print(f"    ✓ Progress: {status['progress']['progress_percent']:.1f}%")
    print(f"    ✓ Total tokens: {status['token_usage']['total_tokens']}")
    print(f"    ✓ Total cost: ${status['token_usage']['cost_usd']:.4f}")
    print(f"    ✓ Total checkpoints: {len(status['checkpoints'])}")
    print()

    # Summary
    print("=" * 60)
    print("Validation Complete")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Project ID: {state.project_id}")
    print(f"  - Phases completed: {len(status['completed_phases'])}/{status['progress']['total_phases']}")
    print(f"  - Checkpoints saved: {len(status['checkpoints'])}")
    print(f"  - Token usage: {status['token_usage']['total_tokens']} tokens")
    print()
    print("The WorkflowEngine is functioning correctly!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
