#!/usr/bin/env python3
"""
Test script for Orchestrator v2 Persistence and API.

Tests:
1. FileSystem repositories (Project, Checkpoint, Artifact, Governance)
2. API endpoints via FastAPI TestClient

Run with: python scripts/test_persistence_api.py
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from orchestrator_v2.api.server import app
from orchestrator_v2.engine.state_models import (
    ArtifactInfo,
    CheckpointState,
    CheckpointType,
    GateResult,
    GateStatus,
    GovernanceResults,
    PhaseType,
    ProjectState,
)
from orchestrator_v2.persistence.fs_repository import (
    FileSystemArtifactRepository,
    FileSystemCheckpointRepository,
    FileSystemGovernanceLogRepository,
    FileSystemProjectRepository,
)


async def test_project_repository():
    """Test FileSystem project repository."""
    print("\n" + "=" * 60)
    print("TEST 1: Project Repository")
    print("=" * 60)

    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        repo = FileSystemProjectRepository(temp_dir / "projects")

        # Create project
        project = ProjectState(
            project_id=str(uuid4()),
            run_id=str(uuid4()),
            project_name="Test Project",
            client="kearney-default",
            current_phase=PhaseType.PLANNING,
        )

        # Save
        await repo.save(project)
        print(f"\n  Saved project: {project.project_id}")

        # Check exists
        exists = await repo.exists(project.project_id)
        print(f"  Exists: {exists}")

        # Load
        loaded = await repo.load(project.project_id)
        print(f"  Loaded project: {loaded.project_name}")
        print(f"  Phase: {loaded.current_phase.value}")

        # List
        projects = await repo.list_projects()
        print(f"  Projects in repo: {len(projects)}")

        # Delete
        await repo.delete(project.project_id)
        exists_after = await repo.exists(project.project_id)
        print(f"  Exists after delete: {exists_after}")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_checkpoint_repository():
    """Test FileSystem checkpoint repository."""
    print("\n" + "=" * 60)
    print("TEST 2: Checkpoint Repository")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        repo = FileSystemCheckpointRepository(temp_dir / "checkpoints")

        project_id = str(uuid4())

        # Create checkpoints
        checkpoint1 = CheckpointState(
            id=str(uuid4()),
            phase=PhaseType.PLANNING,
            checkpoint_type=CheckpointType.POST,
            run_id=project_id,
            current_phase=PhaseType.PLANNING,
            completed_phases=[],
        )

        checkpoint2 = CheckpointState(
            id=str(uuid4()),
            phase=PhaseType.DEVELOPMENT,
            checkpoint_type=CheckpointType.POST,
            run_id=project_id,
            current_phase=PhaseType.DEVELOPMENT,
            completed_phases=[PhaseType.PLANNING],
        )

        # Save
        await repo.save(checkpoint1)
        await repo.save(checkpoint2)
        print(f"\n  Saved checkpoints: 2")

        # Load
        loaded = await repo.load(checkpoint1.id)
        print(f"  Loaded checkpoint: {loaded.phase.value}")

        # List for project
        checkpoints = await repo.list_for_project(project_id)
        print(f"  Checkpoints for project: {len(checkpoints)}")

        # List for phase
        planning_checkpoints = await repo.list_for_phase(project_id, PhaseType.PLANNING)
        print(f"  Planning checkpoints: {len(planning_checkpoints)}")

        # Get latest
        latest = await repo.get_latest(project_id)
        print(f"  Latest checkpoint phase: {latest.phase.value if latest else 'None'}")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_artifact_repository():
    """Test FileSystem artifact repository."""
    print("\n" + "=" * 60)
    print("TEST 3: Artifact Repository")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        repo = FileSystemArtifactRepository(temp_dir / "artifacts")

        project_id = str(uuid4())

        # Create artifact
        artifact = ArtifactInfo(
            path=".claude/checkpoints/planning/design.md",
            hash="abc123",
            size_bytes=1024,
        )
        content = b"# Design Document\n\nThis is the design."

        # Save
        path = await repo.save(project_id, artifact, content)
        print(f"\n  Saved artifact to: {path}")

        # Check exists
        exists = await repo.exists(project_id, artifact.path)
        print(f"  Exists: {exists}")

        # Load
        loaded_content = await repo.load(project_id, artifact.path)
        print(f"  Loaded content size: {len(loaded_content)} bytes")

        # List for project
        artifacts = await repo.list_for_project(project_id)
        print(f"  Artifacts for project: {len(artifacts)}")

        # Delete
        await repo.delete(project_id, artifact.path)
        exists_after = await repo.exists(project_id, artifact.path)
        print(f"  Exists after delete: {exists_after}")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_governance_repository():
    """Test FileSystem governance log repository."""
    print("\n" + "=" * 60)
    print("TEST 4: Governance Log Repository")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        repo = FileSystemGovernanceLogRepository(temp_dir / "governance")

        project_id = str(uuid4())

        # Create governance results
        results = GovernanceResults(
            quality_gates=[
                GateResult(
                    gate_id="test_coverage",
                    status=GateStatus.PASSED,
                    message="Coverage 85% meets 80% threshold",
                    threshold=80,
                    actual=85,
                ),
            ],
            compliance_checks=[],
            passed=True,
        )

        # Log
        await repo.log(project_id, PhaseType.QA, results)
        print(f"\n  Logged governance results for QA phase")

        # Get logs
        logs = await repo.get_logs(project_id)
        print(f"  Total logs: {len(logs)}")

        # Get logs for phase
        qa_logs = await repo.get_logs(project_id, PhaseType.QA)
        print(f"  QA phase logs: {len(qa_logs)}")

        # Get latest
        latest = await repo.get_latest(project_id, PhaseType.QA)
        print(f"  Latest passed: {latest.passed if latest else 'None'}")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


def test_api_endpoints():
    """Test API endpoints via TestClient."""
    print("\n" + "=" * 60)
    print("TEST 5: API Endpoints")
    print("=" * 60)

    client = TestClient(app)

    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    health = response.json()
    print(f"\n  Health check: {health['status']}")

    # Create project
    response = client.post("/projects", json={
        "project_name": "API Test Project",
        "client": "kearney-default",
        "metadata": {"test": True},
    })
    assert response.status_code == 201
    project = response.json()
    project_id = project["project_id"]
    print(f"  Created project: {project_id}")

    # Get project
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    print(f"  Got project: {response.json()['project_name']}")

    # Get status
    response = client.get(f"/projects/{project_id}/status")
    assert response.status_code == 200
    status = response.json()
    print(f"  Status - Phase: {status['current_phase']}, Progress: {status['progress_percent']}%")

    # List projects
    response = client.get("/projects")
    assert response.status_code == 200
    projects = response.json()
    print(f"  Listed projects: {len(projects)}")

    # Get checkpoints
    response = client.get(f"/projects/{project_id}/checkpoints")
    assert response.status_code == 200
    checkpoints = response.json()
    print(f"  Checkpoints: {len(checkpoints)}")

    # Get governance (should return empty)
    response = client.get(f"/projects/{project_id}/governance/planning")
    assert response.status_code == 200
    governance = response.json()
    print(f"  Governance passed: {governance['passed']}")

    # Test 404
    response = client.get("/projects/nonexistent")
    assert response.status_code == 404
    print(f"  404 handling: OK")

    # Delete project
    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200
    print(f"  Deleted project: OK")

    print("\n  Status: PASS")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Persistence & API Validation")
    print("=" * 60)

    results = {}

    # Run async tests
    results["project_repository"] = await test_project_repository()
    results["checkpoint_repository"] = await test_checkpoint_repository()
    results["artifact_repository"] = await test_artifact_repository()
    results["governance_repository"] = await test_governance_repository()

    # Run sync API tests
    results["api_endpoints"] = test_api_endpoints()

    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!")
        print("Persistence layer and API working correctly")
    else:
        print("Some tests failed - review output above")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
