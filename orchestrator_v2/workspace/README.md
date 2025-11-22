# Workspace

Workspace and repository isolation for Orchestrator v2.

## Purpose

Provides isolated execution environments for projects:
- File system isolation per project
- Git repository management and safety
- Artifact storage and organization

## Key Components

- **models.py**: `WorkspaceConfig` defining paths and structure
- **manager.py**: `WorkspaceManager` for creating/managing workspaces
- **repo_adapter.py**: `RepoAdapter` for safe Git operations

## Workspace Structure

```
~/.orchestrator/workspaces/{project_id}/
├── repo/           # Cloned repository
├── artifacts/      # Generated artifacts
├── logs/           # Execution logs
├── state/          # Checkpoints and state
└── tmp/            # Temporary files
```

## RepoAdapter Safety

The `RepoAdapter` enforces safety policies:
- Blocks writes outside allowed paths
- Prevents accidental secret commits
- Validates file operations
- Tracks changes for rollback

## Usage

```python
from orchestrator_v2.workspace.manager import WorkspaceManager

manager = WorkspaceManager()
workspace = await manager.create_workspace(project_id)

# Safe repo operations
from orchestrator_v2.workspace.repo_adapter import RepoAdapter
adapter = RepoAdapter(workspace)
adapter.write_file("src/main.py", content)
```

## Related Documentation

- ADR-003: Workspace Isolation Model
