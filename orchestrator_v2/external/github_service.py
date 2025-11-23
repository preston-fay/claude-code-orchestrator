"""
GitHub service for automatic repository creation.

Provides functions to create repositories and add default files
using the GitHub API.
"""

import os
import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GitHubServiceError(Exception):
    """Exception raised by GitHub service operations."""
    pass


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self, token: str | None = None):
        """Initialize GitHub service.

        Args:
            token: GitHub Personal Access Token. If not provided,
                   reads from GITHUB_PAT environment variable.
        """
        self.token = token or os.getenv("GITHUB_PAT")
        if not self.token:
            logger.warning("No GitHub PAT configured. Auto-repo creation will be disabled.")

        self.api_base = "https://api.github.com"
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if GitHub service is properly configured."""
        return bool(self.token)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_authenticated_user(self) -> dict[str, Any]:
        """Get the authenticated user's information.

        Returns:
            User information dict.

        Raises:
            GitHubServiceError: If request fails.
        """
        if not self.is_configured:
            raise GitHubServiceError("GitHub PAT not configured")

        client = await self._get_client()
        response = await client.get(f"{self.api_base}/user")

        if response.status_code != 200:
            raise GitHubServiceError(f"Failed to get user: {response.text}")

        return response.json()

    async def create_repo(
        self,
        name: str,
        description: str = "",
        visibility: str = "private",
        auto_init: bool = False,
    ) -> str:
        """Create a new GitHub repository.

        Args:
            name: Repository name.
            description: Repository description.
            visibility: Repository visibility ('private' or 'public').
            auto_init: Whether to initialize with README.

        Returns:
            Repository clone URL.

        Raises:
            GitHubServiceError: If repository creation fails.
        """
        if not self.is_configured:
            raise GitHubServiceError("GitHub PAT not configured")

        client = await self._get_client()

        payload = {
            "name": name,
            "description": description,
            "private": visibility == "private",
            "auto_init": auto_init,
        }

        response = await client.post(f"{self.api_base}/user/repos", json=payload)

        if response.status_code == 201:
            repo_data = response.json()
            repo_url = repo_data.get("clone_url", "")
            logger.info(f"Created repository: {repo_url}")
            return repo_url
        elif response.status_code == 422:
            # Repository might already exist
            error_data = response.json()
            errors = error_data.get("errors", [])
            for error in errors:
                if error.get("field") == "name" and "already exists" in error.get("message", ""):
                    raise GitHubServiceError(f"Repository '{name}' already exists")
            raise GitHubServiceError(f"Validation error: {response.text}")
        else:
            raise GitHubServiceError(f"Failed to create repository: {response.text}")

    async def add_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str = "Add file",
        branch: str = "main",
    ) -> bool:
        """Add or update a file in a repository.

        Args:
            owner: Repository owner username.
            repo: Repository name.
            path: File path in repository.
            content: File content.
            message: Commit message.
            branch: Target branch.

        Returns:
            True if successful.

        Raises:
            GitHubServiceError: If file creation fails.
        """
        if not self.is_configured:
            raise GitHubServiceError("GitHub PAT not configured")

        client = await self._get_client()

        # Encode content to base64
        encoded_content = base64.b64encode(content.encode()).decode()

        # Check if file exists to get SHA
        sha = None
        check_response = await client.get(
            f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch},
        )
        if check_response.status_code == 200:
            sha = check_response.json().get("sha")

        payload = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        response = await client.put(
            f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )

        if response.status_code in (200, 201):
            logger.info(f"Added file {path} to {owner}/{repo}")
            return True
        else:
            raise GitHubServiceError(f"Failed to add file: {response.text}")

    async def add_default_files(
        self,
        owner: str,
        repo: str,
        files: dict[str, str],
        branch: str = "main",
    ) -> bool:
        """Add multiple default files to a repository.

        Args:
            owner: Repository owner username.
            repo: Repository name.
            files: Dictionary mapping file paths to contents.
            branch: Target branch.

        Returns:
            True if all files added successfully.

        Raises:
            GitHubServiceError: If any file creation fails.
        """
        for path, content in files.items():
            await self.add_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=f"Add {path}",
                branch=branch,
            )
        return True


# Default scaffold files for new project repositories
DEFAULT_SCAFFOLD_FILES = {
    "README.md": """# Project Repository

This repository was automatically created by RSC (Ready-Set-Code).

## Project Structure

```
.
├── docs/           # Documentation
├── src/            # Source code
├── tests/          # Test files
└── README.md       # This file
```

## Getting Started

1. Clone this repository
2. Review the PRD and architecture documents
3. Set up your development environment
4. Start implementing!

## Documentation

- [PRD.md](docs/PRD.md) - Product Requirements Document
- [architecture.md](docs/architecture.md) - System Architecture
""",
    "docs/PRD.md": """# Product Requirements Document

## Overview

[Project description will be generated here]

## Objectives

- [ ] Objective 1
- [ ] Objective 2
- [ ] Objective 3

## Requirements

### Functional Requirements

1. FR-1: [Description]
2. FR-2: [Description]

### Non-Functional Requirements

1. NFR-1: Performance
2. NFR-2: Security
3. NFR-3: Scalability

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
""",
    "docs/architecture.md": """# System Architecture

## Overview

[Architecture overview will be generated here]

## Components

### Component 1

- Purpose:
- Technology:
- Interfaces:

### Component 2

- Purpose:
- Technology:
- Interfaces:

## Data Flow

1. Step 1
2. Step 2
3. Step 3

## Technology Stack

- Backend:
- Frontend:
- Database:
- Infrastructure:

## Security Considerations

- Authentication:
- Authorization:
- Data Protection:
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local
*.pem

# OS
.DS_Store
Thumbs.db

# Project specific
data/raw/
*.pkl
*.h5
""",
}


async def create_project_repo(
    project_name: str,
    description: str = "",
    visibility: str = "private",
    add_scaffold: bool = True,
    custom_files: dict[str, str] | None = None,
) -> str:
    """Create a new project repository with optional scaffold files.

    This is a convenience function that creates a repository and
    optionally adds default scaffold files.

    Args:
        project_name: Repository name (will be sanitized).
        description: Repository description.
        visibility: Repository visibility ('private' or 'public').
        add_scaffold: Whether to add default scaffold files.
        custom_files: Additional files to add.

    Returns:
        Repository clone URL.

    Raises:
        GitHubServiceError: If creation fails.
    """
    # Sanitize repo name
    repo_name = project_name.lower().replace(" ", "-").replace("_", "-")
    repo_name = "".join(c for c in repo_name if c.isalnum() or c == "-")

    service = GitHubService()

    try:
        # Get authenticated user
        user = await service.get_authenticated_user()
        owner = user["login"]

        # Create repository
        repo_url = await service.create_repo(
            name=repo_name,
            description=description,
            visibility=visibility,
            auto_init=True,  # Initialize with README to create main branch
        )

        # Add scaffold files
        if add_scaffold:
            files = DEFAULT_SCAFFOLD_FILES.copy()
            if custom_files:
                files.update(custom_files)

            await service.add_default_files(
                owner=owner,
                repo=repo_name,
                files=files,
            )

        return repo_url

    finally:
        await service.close()


def is_github_configured() -> bool:
    """Check if GitHub service is configured.

    Returns:
        True if GITHUB_PAT is set.
    """
    return bool(os.getenv("GITHUB_PAT"))
