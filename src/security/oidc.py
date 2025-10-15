"""
Optional OIDC (OpenID Connect) authentication.

Supports:
- JWKS fetching and caching
- JWT validation (signature, exp, nbf, aud, iss)
- Identity extraction from claims

Disabled if no OIDC configuration provided.
"""

import jwt
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache

from .schemas import Identity, RoleEnum, ScopeEnum

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class OIDCVerifier:
    """
    OIDC JWT verifier.

    Fetches JWKS, validates tokens, extracts identity.
    """

    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str,
        cache_ttl_seconds: int = 3600
    ):
        """
        Initialize OIDC verifier.

        Args:
            issuer: Expected issuer (iss claim)
            audience: Expected audience (aud claim)
            jwks_url: JWKS endpoint URL
            cache_ttl_seconds: JWKS cache TTL
        """
        self.issuer = issuer
        self.audience = audience
        self.jwks_url = jwks_url
        self.cache_ttl_seconds = cache_ttl_seconds
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cached_at: Optional[datetime] = None

    def verify_token(self, token: str) -> Optional[Identity]:
        """
        Verify JWT token and extract identity.

        Args:
            token: JWT token string

        Returns:
            Identity if valid, None otherwise
        """
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("cryptography package required for OIDC")

        try:
            # Fetch JWKS
            jwks = self._get_jwks()

            # Decode and verify
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            if kid not in jwks:
                return None

            public_key = jwks[kid]

            # Verify signature and claims
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )

            # Extract identity
            return self._extract_identity(payload)

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def _get_jwks(self) -> Dict[str, Any]:
        """
        Fetch JWKS with caching.

        Returns:
            Dict mapping kid to public key
        """
        # Check cache
        if self._jwks_cache is not None and self._jwks_cached_at is not None:
            if datetime.utcnow() - self._jwks_cached_at < timedelta(seconds=self.cache_ttl_seconds):
                return self._jwks_cache

        # Fetch JWKS
        response = requests.get(self.jwks_url, timeout=10)
        response.raise_for_status()
        jwks_data = response.json()

        # Parse keys
        keys = {}
        for key_data in jwks_data.get("keys", []):
            kid = key_data.get("kid")
            if not kid:
                continue

            # Convert JWK to public key
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
            keys[kid] = public_key

        # Cache
        self._jwks_cache = keys
        self._jwks_cached_at = datetime.utcnow()

        return keys

    def _extract_identity(self, payload: Dict[str, Any]) -> Identity:
        """
        Extract Identity from JWT payload.

        Maps claims to Identity fields:
        - sub -> id
        - roles -> roles (custom claim)
        - scopes -> scopes (space-separated string in 'scope' claim)
        - tenants -> tenants (custom claim)

        Args:
            payload: JWT payload

        Returns:
            Identity
        """
        # Extract standard claims
        identity_id = payload.get("sub")
        email = payload.get("email")
        name = payload.get("name")

        # Extract custom claims
        roles_str = payload.get("roles", [])
        scopes_str = payload.get("scope", "")
        tenants = payload.get("tenants", [])

        # Parse roles
        roles = []
        if isinstance(roles_str, list):
            for role_str in roles_str:
                try:
                    roles.append(RoleEnum(role_str))
                except ValueError:
                    pass

        # Parse scopes (space-separated)
        scopes = set()
        for scope_str in scopes_str.split():
            try:
                scopes.add(ScopeEnum(scope_str))
            except ValueError:
                pass

        # Extract expiration
        exp = payload.get("exp")
        expires_at = None
        if exp:
            expires_at = datetime.fromtimestamp(exp)

        return Identity(
            id=identity_id,
            type="user",
            roles=roles,
            scopes=scopes,
            tenants=tenants,
            source="oidc",
            expires_at=expires_at,
            metadata={
                "email": email,
                "name": name,
                "iss": payload.get("iss"),
                "aud": payload.get("aud"),
            }
        )


# Global instance
_oidc_verifier: Optional[OIDCVerifier] = None


def get_oidc_verifier() -> Optional[OIDCVerifier]:
    """
    Get global OIDC verifier instance.

    Returns None if OIDC not configured.
    """
    global _oidc_verifier

    if _oidc_verifier is not None:
        return _oidc_verifier

    # Check if OIDC configured
    try:
        from src.ops.secrets import get_secret

        issuer = get_secret("OIDC_ISSUER")
        audience = get_secret("OIDC_AUDIENCE")
        jwks_url = get_secret("OIDC_JWKS_URL")

        if not all([issuer, audience, jwks_url]):
            return None

        _oidc_verifier = OIDCVerifier(
            issuer=issuer,
            audience=audience,
            jwks_url=jwks_url
        )

        return _oidc_verifier

    except Exception:
        return None


def is_oidc_enabled() -> bool:
    """Check if OIDC is enabled."""
    return get_oidc_verifier() is not None
