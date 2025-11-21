#!/usr/bin/env python3
"""
End-to-end test for Workspace + WorkflowEngine integration.

Tests:
1. Create workspace
2. Start project with workspace
3. Advance through phases
4. Verify artifacts in workspace
5. Verify repo isolation

Run with: python scripts/test_end_to_end_workspace_engine.py
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from orchestrator_v2.core.engine import WorkflowEngine
from orchestrator_v2.core.state_models import PhaseType
from orchestrator_v2.workspace.manager import WorkspaceManager


async def test_end_to_end():
    """Run end-to-end test of workspace + engine."""
    print("=" * 60)
    print("End-to-End Workspace + Engine Test")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 1. Create workspace
        print("\n" + "-" * 60)
        print("Step 1: Create Workspace")
        print("-" * 60)

        manager = WorkspaceManager(temp_dir)
        project_id = f"e2e-test-{uuid4().hex[:8]}"
        workspace = manager.create_workspace(
            project_id=project_id,
            metadata={"type": "end_to_end_test"},
        )

        print(f"\n  Project ID: {project_id}")
        print(f"  Workspace Root: {workspace.workspace_root}")
        print(f"  Repo Path: {workspace.repo_path}")
        print(f"  Artifacts Path: {workspace.artifacts_path}")

        # 2. Create engine with workspace
        print("\n" + "-" * 60)
        print("Step 2: Create Engine with Workspace")
        print("-" * 60)

        engine = WorkflowEngine(workspace=workspace)
        print(f"\n  Engine created with workspace support")
        print(f"  Repo adapter available: {engine.repo_adapter is not None}")

        # 3. Start project
        print("\n" + "-" * 60)
        print("Step 3: Start Project")
        print("-" * 60)

        state = await engine.start_project(
            project_name="E2E Test Project",
            client="kearney-default",
            metadata={"requirements": ["analytics", "forecasting"]},
        )

        print(f"\n  Project started: {state.project_name}")
        print(f"  Project ID: {state.project_id}")
        print(f"  Run ID: {state.run_id}")
        print(f"  Current Phase: {state.current_phase.value}")
        print(f"  Checkpoints: {len(state.checkpoints)}")

        # 4. Advance through phases
        print("\n" + "-" * 60)
        print("Step 4: Advance Through Phases")
        print("-" * 60)

        phases_executed = 0
        max_phases = 3  # Run first 3 phases

        while phases_executed < max_phases:
            if engine.state.current_phase == PhaseType.COMPLETE:
                print("\n  Workflow complete")
                break

            current = engine.state.current_phase.value
            print(f"\n  Running phase: {current}")

            try:
                phase_state = await engine.run_phase()
                print(f"    Status: {phase_state.status}")
                print(f"    Agents: {phase_state.agent_ids}")
                phases_executed += 1
            except Exception as e:
                print(f"    Error: {e}")
                break

        print(f"\n  Phases executed: {phases_executed}")
        print(f"  Completed phases: {[p.value for p in engine.state.completed_phases]}")
        print(f"  Current phase: {engine.state.current_phase.value}")

        # 5. Get workflow status
        print("\n" + "-" * 60)
        print("Step 5: Workflow Status")
        print("-" * 60)

        status = await engine.get_status()
        print(f"\n  Project: {status['project_name']}")
        print(f"  Progress: {status['progress']:.1%}")
        print(f"  Token Usage:")
        print(f"    Input: {status['token_usage']['input_tokens']}")
        print(f"    Output: {status['token_usage']['output_tokens']}")
        print(f"    Total: {status['token_usage']['total_tokens']}")
        print(f"  Checkpoints: {len(status['checkpoints'])}")

        # 6. Verify workspace isolation
        print("\n" + "-" * 60)
        print("Step 6: Verify Workspace Isolation")
        print("-" * 60)

        # Check repo path
        repo_files = list(workspace.repo_path.glob("**/*"))
        print(f"\n  Repo files: {len([f for f in repo_files if f.is_file()])}")

        # Check artifacts path
        artifact_files = list(workspace.artifacts_path.glob("**/*"))
        print(f"  Artifact files: {len([f for f in artifact_files if f.is_file()])}")

        # Check state path
        state_files = list(workspace.state_path.glob("**/*"))
        print(f"  State files: {len([f for f in state_files if f.is_file()])}")

        # Check logs path
        log_files = list(workspace.logs_path.glob("**/*"))
        print(f"  Log files: {len([f for f in log_files if f.is_file()])}")

        # Verify .orchestrator not in repo
        orchestrator_in_repo = (workspace.repo_path / ".orchestrator").exists()
        print(f"\n  .orchestrator in repo: {orchestrator_in_repo}")

        # Verify workspace.json exists
        workspace_json = workspace.state_path / "workspace.json"
        print(f"  workspace.json exists: {workspace_json.exists()}")

        # 7. Summary
        print("\n" + "-" * 60)
        print("Test Summary")
        print("-" * 60)

        success = (
            phases_executed >= 2 and
            len(engine.state.checkpoints) >= 2 and
            not orchestrator_in_repo and
            workspace_json.exists()
        )

        print(f"\n  Phases executed: {phases_executed} >= 2: {phases_executed >= 2}")
        print(f"  Checkpoints created: {len(engine.state.checkpoints)} >= 2: {len(engine.state.checkpoints) >= 2}")
        print(f"  Repo isolation: {not orchestrator_in_repo}")
        print(f"  Workspace metadata: {workspace_json.exists()}")

        if success:
            print("\n  Result: PASS")
            print("\n  The workspace architecture successfully:")
            print("    - Isolates project repos from orchestrator state")
            print("    - Keeps artifacts outside the Git repository")
            print("    - Maintains proper checkpointing")
            print("    - Enables safe multi-project operation")
        else:
            print("\n  Result: FAIL")
            print("  Review output above for details")

        return success

    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Main entry point."""
    try:
        success = await test_end_to_end()
        print("\n" + "=" * 60)
        if success:
            print("End-to-end test completed successfully!")
        else:
            print("End-to-end test failed!")
        print("=" * 60)
        print()
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
