"""
Signed URL generation for time-limited artifact access.

Uses HMAC-SHA256 with TTL validation.
"""

import hmac
import hashlib
import time
from typing import Optional, Tuple
from urllib.parse import urlencode, parse_qs

from src.ops.secrets import get_secret


def get_signing_secret() -> str:
    """
    Get URL signing secret.

    Returns:
        Signing secret from environment or generated default
    """
    secret = get_secret("SIGNED_URL_SECRET")
    if secret:
        return secret

    # Fallback: use a default (should be set in production)
    return "kearney-signed-url-secret-change-me"


def sign_url(
    path: str,
    tenant: str,
    ttl_seconds: int = 900,
    ip_address: Optional[str] = None
) -> str:
    """
    Generate signed URL for artifact access.

    Args:
        path: Artifact path (e.g., /api/artifacts/run_123/output.csv)
        tenant: Tenant slug
        ttl_seconds: TTL in seconds (default: 900 = 15 minutes)
        ip_address: Optional IP address to bind signature to

    Returns:
        Signed URL with query parameters
    """
    # Compute expiration timestamp
    expires_at = int(time.time()) + ttl_seconds

    # Build payload
    payload_parts = [path, tenant, str(expires_at)]
    if ip_address:
        payload_parts.append(ip_address)
    payload = "|".join(payload_parts)

    # Compute signature
    secret = get_signing_secret()
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    # Build signed URL
    query_params = {
        "tenant": tenant,
        "expires": str(expires_at),
        "signature": signature,
    }
    if ip_address:
        query_params["ip"] = ip_address

    signed_url = f"{path}?{urlencode(query_params)}"
    return signed_url


def verify_signature(
    path: str,
    tenant: str,
    expires: int,
    signature: str,
    ip_address: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Verify signed URL signature.

    Args:
        path: Artifact path
        tenant: Tenant slug
        expires: Expiration timestamp
        signature: HMAC signature
        ip_address: Optional IP address (must match if provided during signing)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check expiration
    now = int(time.time())
    if now > expires:
        return False, "Signed URL has expired"

    # Rebuild payload
    payload_parts = [path, tenant, str(expires)]
    if ip_address:
        payload_parts.append(ip_address)
    payload = "|".join(payload_parts)

    # Compute expected signature
    secret = get_signing_secret()
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    # Verify signature (constant-time comparison)
    if not hmac.compare_digest(signature, expected_signature):
        return False, "Invalid signature"

    return True, None


def parse_signed_url(url: str) -> Optional[dict]:
    """
    Parse signed URL query parameters.

    Args:
        url: Signed URL

    Returns:
        Dict with path, tenant, expires, signature, ip (if present)
        None if URL is not properly formatted
    """
    try:
        # Split path and query
        if "?" not in url:
            return None

        path, query_string = url.split("?", 1)
        params = parse_qs(query_string)

        # Extract parameters (parse_qs returns lists)
        tenant = params.get("tenant", [None])[0]
        expires_str = params.get("expires", [None])[0]
        signature = params.get("signature", [None])[0]
        ip_address = params.get("ip", [None])[0]

        if not all([tenant, expires_str, signature]):
            return None

        try:
            expires = int(expires_str)
        except ValueError:
            return None

        return {
            "path": path,
            "tenant": tenant,
            "expires": expires,
            "signature": signature,
            "ip": ip_address,
        }

    except Exception:
        return None


def create_signed_artifact_url(
    artifact_path: str,
    tenant: str,
    ttl_minutes: int = 15,
    ip_address: Optional[str] = None
) -> str:
    """
    Create signed URL for artifact download.

    Args:
        artifact_path: Path to artifact (e.g., datasets/run_123/output.csv)
        tenant: Tenant slug
        ttl_minutes: TTL in minutes
        ip_address: Optional IP to bind to

    Returns:
        Full signed URL
    """
    # Prepend /api/artifacts if not present
    if not artifact_path.startswith("/api/artifacts"):
        artifact_path = f"/api/artifacts/{artifact_path}"

    ttl_seconds = ttl_minutes * 60
    return sign_url(artifact_path, tenant, ttl_seconds, ip_address)


def validate_artifact_access(
    url: str,
    requesting_ip: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate signed artifact URL.

    Args:
        url: Signed URL
        requesting_ip: IP address of requester (for IP binding check)

    Returns:
        Tuple of (is_valid, tenant, error_message)
    """
    # Parse URL
    parsed = parse_signed_url(url)
    if parsed is None:
        return False, None, "Invalid signed URL format"

    path = parsed["path"]
    tenant = parsed["tenant"]
    expires = parsed["expires"]
    signature = parsed["signature"]
    signed_ip = parsed.get("ip")

    # Check IP binding if present
    if signed_ip and requesting_ip:
        if signed_ip != requesting_ip:
            return False, None, f"IP address mismatch: expected {signed_ip}, got {requesting_ip}"

    # Verify signature
    is_valid, error = verify_signature(path, tenant, expires, signature, signed_ip)

    if not is_valid:
        return False, None, error

    return True, tenant, None
