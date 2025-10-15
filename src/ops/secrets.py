"""
Secrets management for Kearney Data Platform.

Precedence order:
1. Environment variable (os.environ)
2. AWS SSM Parameter Store (/{APP}/{ENV}/{name})
3. AWS Secrets Manager ({APP}/{ENV}/{name})
4. .env file fallback (dotenv)

Results are cached in-process with TTL for performance.
"""

import os
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class SecretSource(str, Enum):
    """Source of secret value."""
    ENVIRONMENT = "environment"
    SSM = "aws_ssm"
    SECRETS_MANAGER = "aws_secrets_manager"
    DOTENV = "dotenv"
    NOT_FOUND = "not_found"


# In-process cache with TTL
_secret_cache: Dict[str, Tuple[str, datetime, SecretSource]] = {}
_cache_ttl_seconds = 300  # 5 minutes default


def get_secret(
    name: str,
    default: Optional[str] = None,
    ttl_seconds: int = 300,
) -> Optional[str]:
    """
    Get secret value with fallback hierarchy.

    Precedence:
    1. Environment variable (os.environ[name])
    2. AWS SSM Parameter Store (/{APP}/{ENV}/{name})
    3. AWS Secrets Manager ({APP}/{ENV}/{name})
    4. .env file (dotenv)

    Args:
        name: Secret name
        default: Default value if not found
        ttl_seconds: Cache TTL in seconds

    Returns:
        Secret value or default
    """
    # Check cache
    if name in _secret_cache:
        value, expires_at, source = _secret_cache[name]
        if datetime.now() < expires_at:
            return value

    # Try sources in order
    value, source = _get_secret_from_sources(name)

    if value is not None:
        # Cache result
        _secret_cache[name] = (value, datetime.now() + timedelta(seconds=ttl_seconds), source)
        return value

    return default


def get_secret_source(name: str) -> SecretSource:
    """
    Get the source of a secret value.

    Args:
        name: Secret name

    Returns:
        Source enum
    """
    _, source = _get_secret_from_sources(name)
    return source


def _get_secret_from_sources(name: str) -> Tuple[Optional[str], SecretSource]:
    """
    Try all secret sources in precedence order.

    Returns:
        Tuple of (value, source)
    """
    # 1. Environment variable
    if name in os.environ:
        return os.environ[name], SecretSource.ENVIRONMENT

    # 2. AWS SSM Parameter Store
    if AWS_AVAILABLE:
        value = _get_from_ssm(name)
        if value is not None:
            return value, SecretSource.SSM

    # 3. AWS Secrets Manager
    if AWS_AVAILABLE:
        value = _get_from_secrets_manager(name)
        if value is not None:
            return value, SecretSource.SECRETS_MANAGER

    # 4. .env file
    if DOTENV_AVAILABLE:
        value = _get_from_dotenv(name)
        if value is not None:
            return value, SecretSource.DOTENV

    return None, SecretSource.NOT_FOUND


def _get_from_ssm(name: str) -> Optional[str]:
    """Get secret from AWS SSM Parameter Store."""
    try:
        # Get app/env from environment
        app = os.environ.get("APP", "kearney-platform")
        env = os.environ.get("ENV", "dev")

        # Build parameter path
        param_path = f"/{app}/{env}/{name}"

        # Get from SSM
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(Name=param_path, WithDecryption=True)
        return response["Parameter"]["Value"]

    except ClientError as e:
        if e.response["Error"]["Code"] != "ParameterNotFound":
            # Log unexpected errors but don't fail
            pass
        return None
    except Exception:
        return None


def _get_from_secrets_manager(name: str) -> Optional[str]:
    """Get secret from AWS Secrets Manager."""
    try:
        # Get app/env from environment
        app = os.environ.get("APP", "kearney-platform")
        env = os.environ.get("ENV", "dev")

        # Build secret name
        secret_name = f"{app}/{env}/{name}"

        # Get from Secrets Manager
        sm = boto3.client("secretsmanager")
        response = sm.get_secret_value(SecretId=secret_name)

        # Return string value or parse JSON if needed
        if "SecretString" in response:
            return response["SecretString"]
        else:
            # Binary secret (base64 decode if needed)
            return response["SecretBinary"].decode("utf-8")

    except ClientError as e:
        if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "DecryptionFailure"]:
            pass
        return None
    except Exception:
        return None


def _get_from_dotenv(name: str) -> Optional[str]:
    """Get secret from .env file."""
    try:
        # Load .env from project root
        project_root = Path(__file__).parent.parent.parent
        dotenv_path = project_root / ".env"

        if dotenv_path.exists():
            load_dotenv(dotenv_path)
            return os.environ.get(name)

    except Exception:
        pass

    return None


def clear_cache():
    """Clear secret cache (useful for testing)."""
    global _secret_cache
    _secret_cache = {}


def redact_value(value: str, show_chars: int = 4) -> str:
    """
    Redact secret value for display.

    Args:
        value: Secret value
        show_chars: Number of chars to show

    Returns:
        Redacted string (e.g., "abcd****")
    """
    if len(value) <= show_chars:
        return "****"

    return value[:show_chars] + "****"
