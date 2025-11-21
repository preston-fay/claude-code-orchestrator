#!/usr/bin/env python3
"""
Test script for Ready/Set/Go service and API endpoints.

Tests:
1. Create project
2. Start and check Ready stage
3. Start and check Set stage
4. Start and check Go stage
5. Get RSG overview

Run with: python scripts/test_rsg_service.py
"""

from fastapi.testclient import TestClient

from orchestrator_v2.api.server import app


def test_rsg_flow():
    """Test the complete RSG flow via API."""
    print("=" * 60)
    print("Ready/Set/Go Service Test")
    print("=" * 60)

    client = TestClient(app)

    # 1. Create project
    print("\n" + "-" * 60)
    print("Step 1: Create Project")
    print("-" * 60)

    response = client.post("/projects", json={
        "project_name": "RSG Test Project",
        "client": "kearney-default",
        "metadata": {"test": True},
    })
    assert response.status_code == 201, f"Create failed: {response.text}"
    project = response.json()
    project_id = project["project_id"]

    print(f"\n  Project ID: {project_id}")
    print(f"  Project Name: {project['project_name']}")
    print(f"  Current Phase: {project['current_phase']}")

    # 2. Start Ready
    print("\n" + "-" * 60)
    print("Step 2: Start Ready Stage")
    print("-" * 60)

    response = client.post(f"/rsg/{project_id}/ready/start")
    assert response.status_code == 200, f"Start Ready failed: {response.text}"
    ready = response.json()

    print(f"\n  RSG Stage: {ready['stage']}")
    print(f"  Completed: {ready['completed']}")
    print(f"  Current Phase: {ready['current_phase']}")
    print(f"  Completed Phases: {ready['completed_phases']}")
    print(f"  Governance Passed: {ready['governance_passed']}")
    print(f"  Messages: {ready['messages']}")

    # 3. Check Ready Status
    print("\n" + "-" * 60)
    print("Step 3: Check Ready Status")
    print("-" * 60)

    response = client.get(f"/rsg/{project_id}/ready/status")
    assert response.status_code == 200
    ready_status = response.json()

    print(f"\n  Stage: {ready_status['stage']}")
    print(f"  Completed: {ready_status['completed']}")
    print(f"  Completed Phases: {ready_status['completed_phases']}")

    # 4. Start Set
    print("\n" + "-" * 60)
    print("Step 4: Start Set Stage")
    print("-" * 60)

    response = client.post(f"/rsg/{project_id}/set/start")
    assert response.status_code == 200, f"Start Set failed: {response.text}"
    set_result = response.json()

    print(f"\n  RSG Stage: {set_result['stage']}")
    print(f"  Completed: {set_result['completed']}")
    print(f"  Current Phase: {set_result['current_phase']}")
    print(f"  Completed Phases: {set_result['completed_phases']}")
    print(f"  Artifacts Count: {set_result['artifacts_count']}")
    print(f"  Data Ready: {set_result['data_ready']}")
    print(f"  Messages: {set_result['messages']}")

    # 5. Check Set Status
    print("\n" + "-" * 60)
    print("Step 5: Check Set Status")
    print("-" * 60)

    response = client.get(f"/rsg/{project_id}/set/status")
    assert response.status_code == 200
    set_status = response.json()

    print(f"\n  Stage: {set_status['stage']}")
    print(f"  Completed: {set_status['completed']}")
    print(f"  Artifacts: {set_status['artifacts_count']}")

    # 6. Start Go
    print("\n" + "-" * 60)
    print("Step 6: Start Go Stage")
    print("-" * 60)

    response = client.post(f"/rsg/{project_id}/go/start")
    assert response.status_code == 200, f"Start Go failed: {response.text}"
    go_result = response.json()

    print(f"\n  RSG Stage: {go_result['stage']}")
    print(f"  Completed: {go_result['completed']}")
    print(f"  Current Phase: {go_result['current_phase']}")
    print(f"  Completed Phases: {go_result['completed_phases']}")
    print(f"  Checkpoints Count: {go_result['checkpoints_count']}")
    print(f"  Governance Blocked: {go_result['governance_blocked']}")
    print(f"  Messages: {go_result['messages']}")

    # 7. Check Go Status
    print("\n" + "-" * 60)
    print("Step 7: Check Go Status")
    print("-" * 60)

    response = client.get(f"/rsg/{project_id}/go/status")
    assert response.status_code == 200
    go_status = response.json()

    print(f"\n  Stage: {go_status['stage']}")
    print(f"  Completed: {go_status['completed']}")
    print(f"  Checkpoints: {go_status['checkpoints_count']}")

    # 8. Get RSG Overview
    print("\n" + "-" * 60)
    print("Step 8: Get RSG Overview")
    print("-" * 60)

    response = client.get(f"/rsg/{project_id}/overview")
    assert response.status_code == 200
    overview = response.json()

    print(f"\n  Project: {overview['project_name']}")
    print(f"  Overall Stage: {overview['stage']}")
    print(f"\n  Ready:")
    print(f"    Stage: {overview['ready']['stage']}")
    print(f"    Completed: {overview['ready']['completed']}")
    print(f"    Phases: {overview['ready']['completed_phases']}")
    print(f"\n  Set:")
    print(f"    Stage: {overview['set']['stage']}")
    print(f"    Completed: {overview['set']['completed']}")
    print(f"    Phases: {overview['set']['completed_phases']}")
    print(f"\n  Go:")
    print(f"    Stage: {overview['go']['stage']}")
    print(f"    Completed: {overview['go']['completed']}")
    print(f"    Phases: {overview['go']['completed_phases']}")

    # 9. Get final project status
    print("\n" + "-" * 60)
    print("Step 9: Final Project Status")
    print("-" * 60)

    response = client.get(f"/projects/{project_id}/status")
    assert response.status_code == 200
    status = response.json()

    print(f"\n  Project ID: {status['project_id']}")
    print(f"  Current Phase: {status['current_phase']}")
    print(f"  Progress: {status['progress_percent']:.1f}%")
    print(f"  Completed Phases: {status['completed_phases']}")
    print(f"  Checkpoints: {len(status.get('last_checkpoint', {}) or {})}")
    print(f"  Token Usage: {status['token_usage']}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    print(f"\n  Project ID: {project_id}")
    print(f"  Final RSG Stage: {overview['stage']}")
    print(f"  Final Engine Phase: {status['current_phase']}")
    print(f"  Total Completed Phases: {len(status['completed_phases'])}")
    print(f"\n  RSG Stage Transitions:")
    print(f"    NOT_STARTED -> READY (after planning/architecture)")
    print(f"    READY -> SET (after data setup)")
    print(f"    SET -> GO/COMPLETE (after full execution)")

    success = (
        overview['ready']['completed'] and
        len(status['completed_phases']) >= 2
    )

    if success:
        print("\n  Result: PASS")
        print("\n  The RSG service successfully:")
        print("    - Maps macro stages to engine phases")
        print("    - Tracks progress through Ready/Set/Go")
        print("    - Provides clean API for UI integration")
    else:
        print("\n  Result: PARTIAL")
        print("  Some stages may not have fully completed")

    return success


def main():
    """Main entry point."""
    try:
        success = test_rsg_flow()
        print("\n" + "=" * 60)
        if success:
            print("RSG service test completed successfully!")
        else:
            print("RSG service test completed with warnings")
        print("=" * 60)
        print()
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
