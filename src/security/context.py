"""
FastAPI dependencies for authentication and authorization.

Provides:
- get_identity: Extract Identity from X-API-Key or Authorization header
- get_tenant_context: Extract TenantContext from header
- require_auth: Dependency that enforces authentication
"""

from fastapi import Depends, Header, HTTPException, Request
from typing import Optional, Annotated

from .schemas import Identity, TenantContext
from .keys import get_key_manager
from .oidc import get_oidc_verifier


async def get_identity(
    x_api_key: Annotated[Optional[str], Header()] = None,
    authorization: Annotated[Optional[str], Header()] = None,
) -> Optional[Identity]:
    """
    Extract identity from request headers.

    Tries:
    1. X-API-Key header
    2. Authorization: Bearer <token> (OIDC)

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Authorization header (Bearer token)

    Returns:
        Identity if authenticated, None otherwise
    """
    # Try API key
    if x_api_key:
        key_manager = get_key_manager()
        api_key = key_manager.authenticate(x_api_key)
        if api_key:
            return api_key.to_identity()

    # Try OIDC
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        oidc_verifier = get_oidc_verifier()
        if oidc_verifier:
            identity = oidc_verifier.verify_token(token)
            if identity:
                return identity

    return None


async def require_auth(
    identity: Annotated[Optional[Identity], Depends(get_identity)]
) -> Identity:
    """
    Require authentication.

    Raises 401 if not authenticated.

    Args:
        identity: Identity from get_identity

    Returns:
        Identity

    Raises:
        HTTPException: 401 if not authenticated
    """
    if identity is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized",
                "message": "Authentication required. Provide X-API-Key or Authorization header."
            }
        )

    # Check expiration
    if identity.is_expired():
        raise HTTPException(
            status_code=401,
            detail={
                "error": "token_expired",
                "message": "Authentication token has expired."
            }
        )

    return identity


async def get_tenant_context(
    identity: Annotated[Identity, Depends(require_auth)],
    x_tenant: Annotated[Optional[str], Header()] = None,
) -> TenantContext:
    """
    Extract tenant context from request.

    Uses X-Tenant header or defaults to first tenant in identity.

    Args:
        identity: Authenticated identity
        x_tenant: Tenant slug from X-Tenant header

    Returns:
        TenantContext

    Raises:
        HTTPException: 400 if tenant not specified, 403 if no access
    """
    # Determine tenant
    tenant = x_tenant

    if not tenant:
        # Default to first tenant
        if identity.tenants:
            tenant = identity.tenants[0]
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "tenant_required",
                    "message": "X-Tenant header required. Specify tenant slug."
                }
            )

    # Create context
    context = TenantContext(tenant=tenant, identity=identity)

    # Check access
    if not context.check_access():
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": f"No access to tenant: {tenant}"
            }
        )

    return context


async def get_optional_identity(
    x_api_key: Annotated[Optional[str], Header()] = None,
    authorization: Annotated[Optional[str], Header()] = None,
) -> Optional[Identity]:
    """
    Optional identity extraction (does not raise on failure).

    Use for endpoints that support both authenticated and anonymous access.

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Authorization header

    Returns:
        Identity if authenticated, None otherwise
    """
    return await get_identity(x_api_key, authorization)


def attach_identity_to_request(request: Request, identity: Optional[Identity]):
    """
    Attach identity to request state.

    Allows access via request.state.identity in route handlers.

    Args:
        request: FastAPI request
        identity: Identity to attach
    """
    request.state.identity = identity


def get_identity_from_request(request: Request) -> Optional[Identity]:
    """
    Get identity from request state.

    Args:
        request: FastAPI request

    Returns:
        Identity if attached, None otherwise
    """
    return getattr(request.state, "identity", None)
