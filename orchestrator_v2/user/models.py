"""
User models for authentication and entitlements.

This module defines the user profile schema including:
- User identity (from SSO/OIDC)
- Role-based access control
- BYOK (Bring Your Own Key) LLM API keys
- Model entitlements per agent role
- Project access control
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class TokenUsage(BaseModel):
    """Track token usage for billing and limits."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    last_reset: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """
    User profile with authentication and entitlement information.

    Supports BYOK (Bring Your Own Key) model where each user
    provides their own LLM API key for agent execution.
    """
    # Identity (from SSO/OIDC)
    user_id: str
    email: str
    name: Optional[str] = None

    # Access control
    role: UserRole = UserRole.DEVELOPER

    # BYOK LLM API key (encrypted at rest in production)
    llm_api_key: Optional[str] = None
    llm_provider: str = "anthropic"  # anthropic, openai, etc.

    # Model entitlements: agent_role -> list of allowed models
    # e.g., {"architect": ["claude-3-opus", "claude-3-sonnet"], "developer": ["claude-3-sonnet"]}
    model_entitlements: dict[str, list[str]] = Field(default_factory=dict)

    # Default model preferences
    default_model: str = "claude-sonnet-4-20250514"

    # Token limits per period (optional caps)
    # e.g., {"daily_input": 100000, "daily_output": 50000}
    token_limits: dict[str, int] = Field(default_factory=dict)

    # Token usage tracking
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    # Project access: list of project_ids the user can access
    # Empty list = no access, special value "*" = all projects (admin)
    projects: list[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # SSO metadata (for future OIDC integration)
    sso_provider: Optional[str] = None  # azure_ad, okta, etc.
    sso_subject: Optional[str] = None   # Subject claim from ID token

    def has_project_access(self, project_id: str) -> bool:
        """Check if user has access to a specific project."""
        if self.role == UserRole.ADMIN:
            return True
        if "*" in self.projects:
            return True
        return project_id in self.projects

    def get_allowed_models(self, agent_role: str) -> list[str]:
        """Get list of models allowed for a specific agent role."""
        if agent_role in self.model_entitlements:
            return self.model_entitlements[agent_role]
        # Fall back to default model
        return [self.default_model]

    def can_use_model(self, agent_role: str, model: str) -> bool:
        """Check if user can use a specific model for an agent role."""
        allowed = self.get_allowed_models(agent_role)
        return model in allowed or not allowed  # Empty = all allowed


class UserProfileCreate(BaseModel):
    """Schema for creating a new user profile."""
    user_id: str
    email: str
    name: Optional[str] = None
    role: UserRole = UserRole.DEVELOPER


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile fields."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    llm_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    default_model: Optional[str] = None
    model_entitlements: Optional[dict[str, list[str]]] = None
    token_limits: Optional[dict[str, int]] = None


class ApiKeyUpdate(BaseModel):
    """Schema for updating BYOK API key."""
    api_key: str
    provider: str = "anthropic"


class UserPublicProfile(BaseModel):
    """
    Sanitized user profile for API responses.

    Never exposes the full API key - only indicates if set and shows last 4 chars.
    """
    user_id: str
    email: str
    name: Optional[str] = None
    role: UserRole
    llm_provider: str
    llm_key_set: bool
    llm_key_suffix: Optional[str] = None
    default_model: str
    model_entitlements: dict[str, list[str]] = Field(default_factory=dict)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    projects: list[str] = Field(default_factory=list)


def to_public_profile(user: UserProfile) -> UserPublicProfile:
    """
    Convert a UserProfile to a sanitized UserPublicProfile.

    This ensures API keys are never returned in full.
    """
    suffix = None
    if user.llm_api_key and len(user.llm_api_key) >= 4:
        suffix = user.llm_api_key[-4:]

    return UserPublicProfile(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role=user.role,
        llm_provider=user.llm_provider,
        llm_key_set=bool(user.llm_api_key),
        llm_key_suffix=suffix,
        default_model=user.default_model,
        model_entitlements=user.model_entitlements,
        token_usage=user.token_usage,
        projects=user.projects,
    )
