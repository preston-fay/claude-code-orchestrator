"""
User repository for persistent storage of user profiles.

Provides file-system based storage with interface for future
database or external identity provider integration.
"""

import json
from pathlib import Path
from typing import Protocol, Optional
from datetime import datetime

from .models import UserProfile, UserProfileCreate


class UserRepository(Protocol):
    """Protocol for user profile storage."""

    async def get_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        ...

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user profile by email."""
        ...

    async def save(self, user: UserProfile) -> UserProfile:
        """Save or update user profile."""
        ...

    async def delete(self, user_id: str) -> bool:
        """Delete user profile."""
        ...

    async def list_users(self) -> list[UserProfile]:
        """List all user profiles."""
        ...

    async def create(self, data: UserProfileCreate) -> UserProfile:
        """Create a new user profile."""
        ...


class FileSystemUserRepository:
    """
    File-system based user repository.

    Stores user profiles as JSON files at:
    ~/.orchestrator/users/<user_id>.json
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize repository.

        Args:
            base_path: Base directory for user storage.
                      Defaults to ~/.orchestrator/users
        """
        if base_path is None:
            base_path = Path.home() / ".orchestrator" / "users"
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _user_path(self, user_id: str) -> Path:
        """Get file path for a user profile."""
        # Sanitize user_id for filesystem safety
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_id)
        return self._base_path / f"{safe_id}.json"

    async def get_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        path = self._user_path(user_id)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text())
            return UserProfile(**data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error in production
            return None

    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user profile by email (searches all profiles)."""
        for user_file in self._base_path.glob("*.json"):
            try:
                data = json.loads(user_file.read_text())
                if data.get("email") == email:
                    return UserProfile(**data)
            except (json.JSONDecodeError, ValueError):
                continue
        return None

    async def save(self, user: UserProfile) -> UserProfile:
        """Save or update user profile."""
        user.updated_at = datetime.utcnow()
        path = self._user_path(user.user_id)

        # Convert to JSON-serializable dict
        data = user.model_dump(mode="json")
        path.write_text(json.dumps(data, indent=2, default=str))

        return user

    async def delete(self, user_id: str) -> bool:
        """Delete user profile."""
        path = self._user_path(user_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_users(self) -> list[UserProfile]:
        """List all user profiles."""
        users = []
        for user_file in self._base_path.glob("*.json"):
            try:
                data = json.loads(user_file.read_text())
                users.append(UserProfile(**data))
            except (json.JSONDecodeError, ValueError):
                continue
        return users

    async def create(self, data: UserProfileCreate) -> UserProfile:
        """Create a new user profile."""
        # Check if user already exists
        existing = await self.get_by_id(data.user_id)
        if existing:
            raise ValueError(f"User {data.user_id} already exists")

        # Create new profile
        user = UserProfile(
            user_id=data.user_id,
            email=data.email,
            name=data.name,
            role=data.role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return await self.save(user)

    async def grant_project_access(self, user_id: str, project_id: str) -> bool:
        """Grant user access to a project."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if project_id not in user.projects:
            user.projects.append(project_id)
            await self.save(user)

        return True

    async def revoke_project_access(self, user_id: str, project_id: str) -> bool:
        """Revoke user access to a project."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        if project_id in user.projects:
            user.projects.remove(project_id)
            await self.save(user)

        return True

    async def update_token_usage(
        self,
        user_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> bool:
        """Update token usage counters for a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        user.token_usage.total_input_tokens += input_tokens
        user.token_usage.total_output_tokens += output_tokens
        user.token_usage.total_requests += 1
        await self.save(user)

        return True
