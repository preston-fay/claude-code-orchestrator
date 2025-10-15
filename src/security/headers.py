"""
Security headers middleware.

Sets:
- Content-Security-Policy
- Strict-Transport-Security
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Permissions-Policy
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List
import yaml
from pathlib import Path


def build_csp_header(policy: Dict[str, any]) -> str:
    """
    Build Content-Security-Policy header value.

    Args:
        policy: CSP policy dict

    Returns:
        CSP header value string
    """
    directives = []

    for directive, sources in policy.items():
        if isinstance(sources, list):
            sources_str = " ".join(sources)
            directives.append(f"{directive} {sources_str}")
        elif isinstance(sources, str):
            directives.append(f"{directive} {sources}")

    return "; ".join(directives)


def get_csp_for_path(path: str, config: Dict[str, any]) -> str:
    """
    Get CSP policy for path.

    Args:
        path: Request path
        config: Security config

    Returns:
        CSP header value
    """
    csp_config = config.get("csp", {})

    # Admin paths use admin policy
    if path.startswith("/admin"):
        policy = csp_config.get("admin", csp_config.get("default", {}))
    else:
        policy = csp_config.get("default", {})

    return build_csp_header(policy)


def load_security_config() -> Dict[str, any]:
    """Load security config from YAML."""
    config_path = Path("configs/security.yaml")
    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception:
        return {}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers.
    """

    def __init__(self, app, config: Optional[Dict[str, any]] = None):
        super().__init__(app)
        self.config = config or load_security_config()

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Get headers config
        headers_config = self.config.get("headers", {})

        # Content-Security-Policy
        csp = get_csp_for_path(request.url.path, self.config)
        if csp:
            response.headers["Content-Security-Policy"] = csp

        # Strict-Transport-Security
        hsts = headers_config.get("strict-transport-security")
        if hsts:
            response.headers["Strict-Transport-Security"] = hsts

        # X-Content-Type-Options
        x_content_type_options = headers_config.get("x-content-type-options")
        if x_content_type_options:
            response.headers["X-Content-Type-Options"] = x_content_type_options

        # X-Frame-Options
        x_frame_options = headers_config.get("x-frame-options")
        if x_frame_options:
            response.headers["X-Frame-Options"] = x_frame_options

        # Referrer-Policy
        referrer_policy = headers_config.get("referrer-policy")
        if referrer_policy:
            response.headers["Referrer-Policy"] = referrer_policy

        # Permissions-Policy
        permissions_policy = headers_config.get("permissions-policy")
        if permissions_policy:
            response.headers["Permissions-Policy"] = permissions_policy

        return response
