"""
Authentication and authorization dependencies for FastAPI.

Provides middleware for:
- SSO token validation (OIDC/JWT)
- Dev mode header-based auth
- Role-based access control
- Project-level access control
"""

import base64
import json
from typing import Optional, Callable
from datetime import datetime

from fastapi import Header, HTTPException, Depends, status

from orchestrator_v2.user.models import UserProfile, UserRole
from orchestrator_v2.user.repository import FileSystemUserRepository


# Global user repository instance
_user_repository = FileSystemUserRepository()


def get_user_repository() -> FileSystemUserRepository:
    """Get the user repository instance."""
    return _user_repository


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
    user_repo: FileSystemUserRepository = Depends(get_user_repository),
) -> UserProfile:
    """
    Get the current authenticated user.

    Supports two authentication modes:

    1. SSO Mode (Production):
       Authorization: Bearer <ID_TOKEN>
       Token is validated and user info extracted from claims.

    2. Dev Mode (Development):
       X-User-Id: <user_id>
       X-User-Email: <email>
       X-User-Name: <name> (optional)

    Returns:
        UserProfile for the authenticated user.

    Raises:
        HTTPException 401: If authentication is missing or invalid.
    """
    user_id = None
    email = None
    name = None

    # Mode 1: SSO Token (Bearer)
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix

        try:
            # Stub implementation: decode JWT payload without verification
            # In production, replace with proper JWKS verification
            user_info = _decode_token_stub(token)
            user_id = user_info.get("sub") or user_info.get("user_id")
            email = user_info.get("email")
            name = user_info.get("name")

            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user_id or email",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    # Mode 2: Dev headers
    elif x_user_id and x_user_email:
        user_id = x_user_id
        email = x_user_email
        name = x_user_name

    # No authentication provided
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Authorization header (Bearer token) or X-User-Id and X-User-Email headers.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load or create user profile
    user = await user_repo.get_by_id(user_id)

    if not user:
        # Create new user profile on first login
        user = UserProfile(
            user_id=user_id,
            email=email,
            name=name,
            role=UserRole.DEVELOPER,  # Default role
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await user_repo.save(user)

    # Update last login
    user.last_login = datetime.utcnow()
    await user_repo.save(user)

    return user


def _decode_token_stub(token: str) -> dict:
    """
    Stub JWT decoder for development.

    In production, replace with proper JWKS verification using:
    - python-jose
    - authlib
    - or similar library

    This stub just decodes the payload without signature verification.
    """
    try:
        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            # Not a JWT, try as base64 JSON
            decoded = base64.b64decode(token + "==")  # Add padding
            return json.loads(decoded)

        # Decode payload (middle part)
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Failed to decode token: {e}")


def require_role(required_role: UserRole) -> Callable:
    """
    Dependency that requires a specific user role.

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(user: UserProfile = Depends(require_role(UserRole.ADMIN))):
            ...
    """
    async def role_checker(
        user: UserProfile = Depends(get_current_user)
    ) -> UserProfile:
        if user.role != required_role and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role",
            )
        return user

    return role_checker


def require_admin() -> Callable:
    """Dependency that requires admin role."""
    return require_role(UserRole.ADMIN)


async def require_project_access(
    project_id: str,
    user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """
    Verify user has access to the specified project.

    Usage:
        @app.get("/projects/{project_id}")
        async def get_project(
            project_id: str,
            user: UserProfile = Depends(require_project_access)
        ):
            ...
    """
    if not user.has_project_access(project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No access to project {project_id}",
        )
    return user


def get_project_access_checker(project_id: str) -> Callable:
    """
    Create a dependency that checks project access.

    Usage:
        async def endpoint(
            project_id: str,
            user: UserProfile = Depends(get_project_access_checker(project_id))
        ):
            ...
    """
    async def checker(
        user: UserProfile = Depends(get_current_user)
    ) -> UserProfile:
        if not user.has_project_access(project_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No access to project {project_id}",
            )
        return user

    return checker


async def optional_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    user_repo: FileSystemUserRepository = Depends(get_user_repository),
) -> Optional[UserProfile]:
    """
    Get current user if authenticated, otherwise return None.

    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if not authorization and not x_user_id:
        return None

    try:
        return await get_current_user(
            authorization=authorization,
            x_user_id=x_user_id,
            x_user_email=x_user_email,
            user_repo=user_repo,
        )
    except HTTPException:
        return None
