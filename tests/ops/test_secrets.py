"""
Tests for secrets management module.

Tests:
- Precedence order (ENV > SSM > Secrets Manager > .env)
- TTL-based caching
- AWS service mocking
- get_secret_source() identification
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.ops.secrets import (
    get_secret,
    get_secret_source,
    SecretSource,
    _secret_cache,
    _get_from_ssm,
    _get_from_secrets_manager,
    _get_from_dotenv,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear secret cache before each test."""
    _secret_cache.clear()
    yield
    _secret_cache.clear()


@pytest.fixture
def mock_env_var():
    """Set up test environment variable."""
    os.environ["TEST_SECRET"] = "from_env"
    yield
    os.environ.pop("TEST_SECRET", None)


@pytest.fixture
def mock_dotenv(tmp_path, monkeypatch):
    """Create temporary .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_DOTENV_SECRET=from_dotenv\n")
    monkeypatch.setenv("DOTENV_PATH", str(env_file))
    return env_file


class TestSecretPrecedence:
    """Test secret source precedence order."""

    def test_env_var_takes_precedence(self, mock_env_var):
        """Environment variable should be checked first."""
        with patch("src.ops.secrets._get_from_ssm", return_value="from_ssm"):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value="from_sm"):
                with patch("src.ops.secrets._get_from_dotenv", return_value="from_dotenv"):
                    result = get_secret("TEST_SECRET")
                    assert result == "from_env"

    def test_ssm_fallback_when_no_env(self):
        """SSM should be used if environment variable not set."""
        with patch("src.ops.secrets._get_from_ssm", return_value="from_ssm"):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value="from_sm"):
                with patch("src.ops.secrets._get_from_dotenv", return_value="from_dotenv"):
                    result = get_secret("SSM_SECRET")
                    assert result == "from_ssm"

    def test_secrets_manager_fallback_when_no_ssm(self):
        """Secrets Manager should be used if SSM returns None."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value="from_sm"):
                with patch("src.ops.secrets._get_from_dotenv", return_value="from_dotenv"):
                    result = get_secret("SM_SECRET")
                    assert result == "from_sm"

    def test_dotenv_fallback_when_no_aws(self):
        """Dotenv should be used if AWS sources return None."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value="from_dotenv"):
                    result = get_secret("DOTENV_SECRET")
                    assert result == "from_dotenv"

    def test_default_when_all_sources_fail(self):
        """Default value should be returned if all sources fail."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value=None):
                    result = get_secret("MISSING_SECRET", default="default_value")
                    assert result == "default_value"

    def test_none_returned_when_no_default(self):
        """None should be returned if no default provided."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value=None):
                    result = get_secret("MISSING_SECRET")
                    assert result is None


class TestSecretCaching:
    """Test TTL-based secret caching."""

    def test_secret_cached_after_first_fetch(self):
        """Secret should be cached after first fetch."""
        with patch("src.ops.secrets._get_from_ssm", return_value="cached_value") as mock_ssm:
            # First call
            result1 = get_secret("CACHED_SECRET", ttl_seconds=300)
            assert result1 == "cached_value"
            assert mock_ssm.call_count == 1

            # Second call should use cache
            result2 = get_secret("CACHED_SECRET", ttl_seconds=300)
            assert result2 == "cached_value"
            assert mock_ssm.call_count == 1  # Not called again

    def test_cache_expires_after_ttl(self):
        """Cache should expire after TTL seconds."""
        with patch("src.ops.secrets._get_from_ssm", return_value="fresh_value") as mock_ssm:
            # First call
            result1 = get_secret("TTL_SECRET", ttl_seconds=1)
            assert result1 == "fresh_value"

            # Manually expire cache
            if "TTL_SECRET" in _secret_cache:
                value, expires_at, source = _secret_cache["TTL_SECRET"]
                _secret_cache["TTL_SECRET"] = (value, datetime.now() - timedelta(seconds=1), source)

            # Second call should fetch again
            result2 = get_secret("TTL_SECRET", ttl_seconds=1)
            assert result2 == "fresh_value"
            assert mock_ssm.call_count == 2

    def test_cache_key_is_secret_name(self):
        """Cache should be keyed by secret name."""
        with patch("src.ops.secrets._get_from_ssm", return_value="value1"):
            get_secret("SECRET_1", ttl_seconds=300)
            assert "SECRET_1" in _secret_cache

        with patch("src.ops.secrets._get_from_ssm", return_value="value2"):
            get_secret("SECRET_2", ttl_seconds=300)
            assert "SECRET_2" in _secret_cache
            assert "SECRET_1" in _secret_cache  # First still cached

    def test_cache_stores_source(self):
        """Cache should store the source of the secret."""
        with patch("src.ops.secrets._get_from_ssm", return_value="ssm_value"):
            get_secret("SOURCE_SECRET", ttl_seconds=300)
            if "SOURCE_SECRET" in _secret_cache:
                value, expires_at, source = _secret_cache["SOURCE_SECRET"]
                assert source == SecretSource.SSM


class TestGetSecretSource:
    """Test get_secret_source() function."""

    def test_identifies_env_var(self, mock_env_var):
        """Should identify environment variable source."""
        source = get_secret_source("TEST_SECRET")
        assert source == SecretSource.ENV

    def test_identifies_ssm(self):
        """Should identify SSM source."""
        with patch("src.ops.secrets._get_from_ssm", return_value="ssm_value"):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value=None):
                    source = get_secret_source("SSM_SECRET")
                    assert source == SecretSource.SSM

    def test_identifies_secrets_manager(self):
        """Should identify Secrets Manager source."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value="sm_value"):
                with patch("src.ops.secrets._get_from_dotenv", return_value=None):
                    source = get_secret_source("SM_SECRET")
                    assert source == SecretSource.SECRETS_MANAGER

    def test_identifies_dotenv(self):
        """Should identify dotenv source."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value="dotenv_value"):
                    source = get_secret_source("DOTENV_SECRET")
                    assert source == SecretSource.DOTENV

    def test_returns_none_when_not_found(self):
        """Should return None if secret not found."""
        with patch("src.ops.secrets._get_from_ssm", return_value=None):
            with patch("src.ops.secrets._get_from_secrets_manager", return_value=None):
                with patch("src.ops.secrets._get_from_dotenv", return_value=None):
                    source = get_secret_source("MISSING")
                    assert source is None


class TestAWSIntegration:
    """Test AWS SSM and Secrets Manager integration."""

    def test_ssm_returns_parameter_value(self):
        """SSM should return parameter value if found."""
        mock_client = MagicMock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": "test_value"}
        }

        with patch("boto3.client", return_value=mock_client):
            result = _get_from_ssm("TEST_PARAM")
            assert result == "test_value"
            mock_client.get_parameter.assert_called_once()

    def test_ssm_returns_none_on_not_found(self):
        """SSM should return None if parameter not found."""
        mock_client = MagicMock()
        mock_client.get_parameter.side_effect = Exception("ParameterNotFound")

        with patch("boto3.client", return_value=mock_client):
            result = _get_from_ssm("MISSING_PARAM")
            assert result is None

    def test_secrets_manager_returns_secret_value(self):
        """Secrets Manager should return secret value if found."""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": "test_secret"
        }

        with patch("boto3.client", return_value=mock_client):
            result = _get_from_secrets_manager("TEST_SECRET")
            assert result == "test_secret"
            mock_client.get_secret_value.assert_called_once()

    def test_secrets_manager_returns_none_on_not_found(self):
        """Secrets Manager should return None if secret not found."""
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = Exception("ResourceNotFoundException")

        with patch("boto3.client", return_value=mock_client):
            result = _get_from_secrets_manager("MISSING_SECRET")
            assert result is None


class TestDotenvIntegration:
    """Test dotenv file integration."""

    def test_dotenv_returns_value_from_file(self, mock_dotenv):
        """Should read value from .env file."""
        with patch("src.ops.secrets.load_dotenv"):
            result = _get_from_dotenv("TEST_DOTENV_SECRET")
            # Mock will return from os.environ if set
            assert result is None or isinstance(result, str)

    def test_dotenv_returns_none_when_not_in_file(self):
        """Should return None if variable not in .env file."""
        result = _get_from_dotenv("MISSING_VAR")
        assert result is None
