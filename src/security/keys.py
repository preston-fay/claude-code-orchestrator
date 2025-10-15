"""
API key management.

Handles:
- Key generation with secure random
- Hashing with bcrypt
- Key lifecycle (create, list, revoke)
- Validation and verification
"""

import secrets
import bcrypt
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from .schemas import ApiKey, RoleEnum, ScopeEnum


class ApiKeyManager:
    """
    Manage API keys with persistence.

    Keys stored in NDJSON format (one JSON object per line).
    """

    def __init__(self, storage_path: str = ".claude/security/api_keys.ndjson"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if not exists
        if not self.storage_path.exists():
            self.storage_path.touch()

    def generate_key(self, prefix: str = "kdk") -> str:
        """
        Generate a secure random API key.

        Format: <prefix>_<32-char-hex>
        Example: kdk_a1b2c3d4e5f6...

        Args:
            prefix: Key prefix (default: kdk = Kearney Data Key)

        Returns:
            Generated API key
        """
        random_part = secrets.token_hex(32)  # 64 hex chars
        return f"{prefix}_{random_part}"

    def hash_key(self, key: str) -> str:
        """
        Hash API key with bcrypt.

        Args:
            key: Plain API key

        Returns:
            Bcrypt hash
        """
        return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()

    def verify_key(self, key: str, key_hash: str) -> bool:
        """
        Verify API key against hash.

        Args:
            key: Plain API key
            key_hash: Bcrypt hash

        Returns:
            True if key matches hash
        """
        try:
            return bcrypt.checkpw(key.encode(), key_hash.encode())
        except Exception:
            return False

    def create(
        self,
        owner_id: str,
        roles: List[RoleEnum],
        tenants: List[str],
        scopes: Optional[List[ScopeEnum]] = None,
        ttl_days: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> tuple[ApiKey, str]:
        """
        Create new API key.

        Args:
            owner_id: Owner identity ID
            roles: RBAC roles
            tenants: Accessible tenant slugs or ['*'] for all
            scopes: Explicit scopes (if None, derived from roles)
            ttl_days: TTL in days (None = no expiration)
            name: Human-readable name
            description: Description

        Returns:
            Tuple of (ApiKey metadata, plain key string)
        """
        # Generate key
        plain_key = self.generate_key()
        key_hash = self.hash_key(plain_key)
        key_id = secrets.token_hex(8)  # 16 hex chars
        prefix = plain_key.split("_")[0] + "_" + plain_key.split("_")[1][:8]

        # Compute scopes from roles if not provided
        if scopes is None:
            from .schemas import Role
            default_roles = Role.get_default_roles()
            computed_scopes = set()
            for role in roles:
                if role in default_roles:
                    computed_scopes.update(default_roles[role].default_scopes)
            scopes = list(computed_scopes)

        # Compute expiration
        expires_at = None
        if ttl_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=ttl_days)

        # Create ApiKey
        api_key = ApiKey(
            id=key_id,
            key_hash=key_hash,
            prefix=prefix,
            owner_id=owner_id,
            roles=roles,
            scopes=set(scopes),
            tenants=tenants,
            expires_at=expires_at,
            name=name,
            description=description,
        )

        # Persist
        self._append(api_key)

        return api_key, plain_key

    def list(
        self,
        tenant: Optional[str] = None,
        owner_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[ApiKey]:
        """
        List API keys.

        Args:
            tenant: Filter by tenant
            owner_id: Filter by owner
            active_only: Only return active keys

        Returns:
            List of ApiKey objects
        """
        keys = self._load_all()

        # Apply filters
        if active_only:
            keys = [k for k in keys if k.is_active()]

        if tenant:
            keys = [k for k in keys if tenant in k.tenants or "*" in k.tenants]

        if owner_id:
            keys = [k for k in keys if k.owner_id == owner_id]

        return keys

    def get_by_id(self, key_id: str) -> Optional[ApiKey]:
        """Get API key by ID."""
        keys = self._load_all()
        for key in keys:
            if key.id == key_id:
                return key
        return None

    def authenticate(self, plain_key: str) -> Optional[ApiKey]:
        """
        Authenticate with API key.

        Args:
            plain_key: Plain API key string

        Returns:
            ApiKey if valid and active, None otherwise
        """
        keys = self._load_all()

        # Try to match key
        for key in keys:
            if self.verify_key(plain_key, key.key_hash):
                # Check if active
                if not key.is_active():
                    return None

                # Update last used
                key.last_used_at = datetime.utcnow()
                self._update(key)

                return key

        return None

    def revoke(self, key_id: str) -> bool:
        """
        Revoke API key.

        Args:
            key_id: Key ID to revoke

        Returns:
            True if revoked, False if not found
        """
        key = self.get_by_id(key_id)
        if key is None:
            return False

        key.revoked_at = datetime.utcnow()
        self._update(key)
        return True

    def _append(self, api_key: ApiKey):
        """Append API key to storage."""
        with open(self.storage_path, "a") as f:
            f.write(api_key.model_dump_json() + "\n")

    def _load_all(self) -> List[ApiKey]:
        """Load all API keys from storage."""
        keys = []
        if not self.storage_path.exists():
            return keys

        with open(self.storage_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    key_data = json.loads(line)
                    keys.append(ApiKey(**key_data))
                except Exception:
                    # Skip malformed lines
                    continue

        return keys

    def _update(self, api_key: ApiKey):
        """
        Update API key in storage.

        Rewrites entire file with updated key.
        """
        keys = self._load_all()

        # Replace key
        updated_keys = []
        for key in keys:
            if key.id == api_key.id:
                updated_keys.append(api_key)
            else:
                updated_keys.append(key)

        # Rewrite file
        with open(self.storage_path, "w") as f:
            for key in updated_keys:
                f.write(key.model_dump_json() + "\n")


# Global instance
_key_manager: Optional[ApiKeyManager] = None


def get_key_manager() -> ApiKeyManager:
    """Get global API key manager instance."""
    global _key_manager
    if _key_manager is None:
        _key_manager = ApiKeyManager()
    return _key_manager
