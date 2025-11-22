#!/usr/bin/env python3
"""
Test script for Orchestrator v2 Workspace Manager and RepoAdapter.

Tests:
1. Workspace creation and directory structure
2. Repository cloning/initialization
3. RepoAdapter safe write operations
4. Path validation and security
5. Engine integration with workspace

Run with: python scripts/test_workspace_manager.py
"""

import asyncio
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from orchestrator_v2.engine.engine import WorkflowEngine
from orchestrator_v2.engine.state_models import PhaseType
from orchestrator_v2.workspace.repo_adapter import RepoAdapter, UnsafeRepoWrite
from orchestrator_v2.workspace.manager import (
    WorkspaceError,
    WorkspaceManager,
    WorkspaceNotFoundError,
)
from orchestrator_v2.workspace.models import WorkspaceConfig


async def test_workspace_creation():
    """Test workspace creation and directory structure."""
    print("\n" + "=" * 60)
    print("TEST 1: Workspace Creation")
    print("=" * 60)

    # Create temp base directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = WorkspaceManager(temp_dir)

        # Create workspace
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(
            project_id=project_id,
            metadata={"test": True},
        )

        print(f"\n  Created workspace: {project_id}")
        print(f"  Root: {config.workspace_root}")

        # Verify directory structure
        assert config.repo_path.exists(), "repo/ not created"
        assert config.state_path.exists(), ".orchestrator/ not created"
        assert config.artifacts_path.exists(), "artifacts/ not created"
        assert config.logs_path.exists(), "logs/ not created"
        assert config.tmp_path.exists(), "tmp/ not created"

        print("  Directories:")
        print(f"    repo/ exists: {config.repo_path.exists()}")
        print(f"    .orchestrator/ exists: {config.state_path.exists()}")
        print(f"    artifacts/ exists: {config.artifacts_path.exists()}")
        print(f"    logs/ exists: {config.logs_path.exists()}")
        print(f"    tmp/ exists: {config.tmp_path.exists()}")

        # Verify metadata file
        metadata_path = config.state_path / "workspace.json"
        assert metadata_path.exists(), "workspace.json not created"
        print(f"    workspace.json exists: {metadata_path.exists()}")

        # Verify git repo initialized
        git_dir = config.repo_path / ".git"
        assert git_dir.exists(), "Git repo not initialized"
        print(f"    .git/ exists: {git_dir.exists()}")

        # Verify gitignore updated
        gitignore = config.repo_path / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            assert "Orchestrator workspace" in content
            print(f"    .gitignore configured: True")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_workspace_loading():
    """Test loading an existing workspace."""
    print("\n" + "=" * 60)
    print("TEST 2: Workspace Loading")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = WorkspaceManager(temp_dir)

        # Create workspace
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(project_id=project_id)

        # Load workspace
        loaded = manager.load_workspace(project_id)

        print(f"\n  Loaded workspace: {loaded.project_id}")
        print(f"  Root: {loaded.workspace_root}")

        # Verify loaded config matches
        assert loaded.project_id == config.project_id
        assert loaded.repo_path == config.repo_path
        assert loaded.state_path == config.state_path

        print("  Config matches: True")

        # Test listing workspaces
        workspaces = manager.list_workspaces()
        assert project_id in workspaces
        print(f"  Listed workspaces: {len(workspaces)}")

        # Test not found error
        try:
            manager.load_workspace("nonexistent")
            print("  NotFoundError: FAIL")
            return False
        except WorkspaceNotFoundError:
            print("  NotFoundError: PASS")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_repo_adapter_safe_write():
    """Test RepoAdapter safe write operations."""
    print("\n" + "=" * 60)
    print("TEST 3: RepoAdapter Safe Write")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = WorkspaceManager(temp_dir)
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(project_id=project_id)

        adapter = RepoAdapter(config)

        # Test safe write within repo
        result_path = adapter.safe_write_file(
            "src/main.py",
            "print('Hello, World!')",
        )
        print(f"\n  Safe write to src/main.py: {result_path.exists()}")

        # Test create_or_update_file
        result_path = adapter.create_or_update_file(
            "README.md",
            "# Test Project\n",
        )
        print(f"  Create README.md: {result_path.exists()}")

        # Test reading file
        content = adapter.read_file("README.md")
        assert "Test Project" in content
        print(f"  Read file: OK")

        # Test unsafe write (path traversal)
        try:
            adapter.safe_write_file(
                "../../../etc/passwd",
                "malicious",
            )
            print("  Path traversal blocked: FAIL")
            return False
        except UnsafeRepoWrite:
            print("  Path traversal blocked: PASS")

        # Test unsafe write (orchestrator directory)
        try:
            adapter.safe_write_file(
                "../.orchestrator/hack.txt",
                "malicious",
            )
            print("  Orchestrator dir protected: FAIL")
            return False
        except UnsafeRepoWrite:
            print("  Orchestrator dir protected: PASS")

        # Test git status
        status = adapter.get_status()
        print(f"  Git status: {status['branch']}, clean={status['clean']}")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_path_resolution():
    """Test workspace path resolution."""
    print("\n" + "=" * 60)
    print("TEST 4: Path Resolution")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = WorkspaceManager(temp_dir)
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(project_id=project_id)

        # Test resolve methods
        repo_path = config.resolve_repo_path("src/main.py")
        print(f"\n  resolve_repo_path: {repo_path}")
        assert str(config.repo_path) in str(repo_path)

        artifact_path = config.resolve_artifact_path("model.pkl")
        print(f"  resolve_artifact_path: {artifact_path}")
        assert str(config.artifacts_path) in str(artifact_path)

        state_path = config.resolve_state_path("checkpoints")
        print(f"  resolve_state_path: {state_path}")
        assert str(config.state_path) in str(state_path)

        log_path = config.resolve_log_path("debug.log")
        print(f"  resolve_log_path: {log_path}")
        assert str(config.logs_path) in str(log_path)

        tmp_path = config.resolve_tmp_path("temp.csv")
        print(f"  resolve_tmp_path: {tmp_path}")
        assert str(config.tmp_path) in str(tmp_path)

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_engine_workspace_integration():
    """Test WorkflowEngine integration with workspace."""
    print("\n" + "=" * 60)
    print("TEST 5: Engine Workspace Integration")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create workspace
        manager = WorkspaceManager(temp_dir)
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(project_id=project_id)

        # Create engine with workspace
        engine = WorkflowEngine(workspace=config)

        print(f"\n  Created engine with workspace")
        print(f"  Workspace: {engine.workspace.project_id if engine.workspace else None}")
        print(f"  Repo adapter: {'Yes' if engine.repo_adapter else 'No'}")

        # Verify workspace is set
        assert engine.workspace is not None
        assert engine.repo_adapter is not None

        # Start project
        state = await engine.start_project(
            project_name="Workspace Test Project",
            client="kearney-default",
        )

        print(f"  Started project: {state.project_id}")
        print(f"  Phase: {state.current_phase.value}")

        # Verify project state
        assert state.current_phase == PhaseType.PLANNING
        print(f"  Initial phase: PLANNING")

        # Test set_workspace method
        new_config = manager.create_workspace(
            project_id=f"test-project-{uuid4().hex[:8]}"
        )
        engine.set_workspace(new_config)
        assert engine.workspace == new_config
        print(f"  set_workspace: OK")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def test_workspace_deletion():
    """Test workspace deletion."""
    print("\n" + "=" * 60)
    print("TEST 6: Workspace Deletion")
    print("=" * 60)

    temp_dir = Path(tempfile.mkdtemp())

    try:
        manager = WorkspaceManager(temp_dir)
        project_id = f"test-project-{uuid4().hex[:8]}"
        config = manager.create_workspace(project_id=project_id)

        print(f"\n  Created workspace: {project_id}")

        # Delete workspace
        manager.delete_workspace(project_id)

        # Verify deleted
        assert not config.workspace_root.exists()
        print(f"  Workspace deleted: True")

        # Verify not in list
        workspaces = manager.list_workspaces()
        assert project_id not in workspaces
        print(f"  Removed from list: True")

        # Test delete not found
        try:
            manager.delete_workspace("nonexistent")
            print("  Delete nonexistent: FAIL")
            return False
        except WorkspaceNotFoundError:
            print("  Delete nonexistent raises error: PASS")

        print("\n  Status: PASS")
        return True

    finally:
        shutil.rmtree(temp_dir)


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Workspace Manager & RepoAdapter Validation")
    print("=" * 60)

    results = {}

    results["workspace_creation"] = await test_workspace_creation()
    results["workspace_loading"] = await test_workspace_loading()
    results["repo_adapter_safe_write"] = await test_repo_adapter_safe_write()
    results["path_resolution"] = await test_path_resolution()
    results["engine_workspace_integration"] = await test_engine_workspace_integration()
    results["workspace_deletion"] = await test_workspace_deletion()

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
        print("Workspace isolation and RepoAdapter security working correctly")
        print("\nKey features validated:")
        print("  - Workspace directory structure creation")
        print("  - Git repository initialization")
        print("  - Safe file write with path validation")
        print("  - Protection of orchestrator directories")
        print("  - Engine integration with workspace")
    else:
        print("Some tests failed - review output above")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
