"""
Tests for platform health webhook module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import urllib.request
import urllib.error

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from lifecycle.health_webhook import (
    format_slack_payload,
    format_teams_payload,
    format_generic_payload,
    post_webhook
)


def test_format_generic_payload_valid():
    """Test generic payload formatting with valid data."""
    report_data = {
        "timestamp": "2025-10-15T12:00:00Z",
        "scores": {
            "security": 95.0,
            "ops": 92.0,
            "governance": 88.0,
            "reliability": 97.0
        },
        "status": "healthy",
        "recommendations": ["All systems nominal"]
    }

    payload = format_generic_payload(report_data)

    assert "timestamp" in payload
    assert "scores" in payload
    assert "status" in payload
    assert "release" in payload

    assert payload["scores"]["security"] == 95
    assert payload["scores"]["ops"] == 92
    assert payload["scores"]["governance"] == 88
    assert payload["scores"]["reliability"] == 97
    assert payload["status"] == "healthy"


def test_format_slack_payload_excellent_status():
    """Test Slack payload formatting with excellent status."""
    report_data = {
        "scores": {
            "security": 98.0,
            "ops": 96.0,
            "governance": 97.0,
            "reliability": 99.0
        },
        "status": "healthy",
        "recommendations": ["Continue monitoring"]
    }

    payload = format_slack_payload(report_data)

    assert "text" in payload
    assert "attachments" in payload
    assert len(payload["attachments"]) > 0

    # Should use "good" color for excellent scores (avg >= 95)
    assert payload["attachments"][0]["color"] == "good"

    # Check that scores are formatted in blocks
    blocks = payload["attachments"][0]["blocks"]
    assert any("Security" in str(block) for block in blocks)


def test_format_slack_payload_poor_status():
    """Test Slack payload formatting with poor status."""
    report_data = {
        "scores": {
            "security": 65.0,
            "ops": 60.0,
            "governance": 55.0,
            "reliability": 62.0
        },
        "status": "poor",
        "recommendations": ["Urgent: Address critical issues"]
    }

    payload = format_slack_payload(report_data)

    # Should use "danger" color for poor scores (avg < 70)
    assert payload["attachments"][0]["color"] == "danger"


def test_format_teams_payload_valid():
    """Test Teams payload formatting with valid data."""
    report_data = {
        "scores": {
            "security": 90.0,
            "ops": 85.0,
            "governance": 88.0,
            "reliability": 92.0
        },
        "status": "healthy"
    }

    payload = format_teams_payload(report_data)

    assert "@type" in payload
    assert payload["@type"] == "MessageCard"
    assert "themeColor" in payload
    assert payload["themeColor"] == "7823DC"  # Kearney purple

    # Check facts section
    assert "sections" in payload
    assert len(payload["sections"]) > 0
    facts = payload["sections"][0]["facts"]
    assert len(facts) == 4  # 4 score categories

    # Verify all scores are present
    fact_names = [f["name"] for f in facts]
    assert "Security" in fact_names
    assert "Operations" in fact_names
    assert "Governance" in fact_names
    assert "Reliability" in fact_names


@patch('urllib.request.urlopen')
def test_post_webhook_success(mock_urlopen):
    """Test successful webhook posting."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    mock_urlopen.return_value = mock_response

    config = {
        "webhook": {
            "retry_count": 3,
            "retry_backoff": 2,
            "timeout": 10
        }
    }

    payload = {"test": "data"}
    result = post_webhook("https://example.com/webhook", payload, config)

    assert result is True
    mock_urlopen.assert_called_once()


@patch('urllib.request.urlopen')
def test_post_webhook_http_error_retry(mock_urlopen):
    """Test webhook posting with HTTP error and retry logic."""
    # Mock HTTP error
    mock_urlopen.side_effect = urllib.error.HTTPError(
        "https://example.com/webhook",
        500,
        "Internal Server Error",
        {},
        None
    )

    config = {
        "webhook": {
            "retry_count": 2,
            "retry_backoff": 1,  # Short backoff for test
            "timeout": 10
        }
    }

    payload = {"test": "data"}
    result = post_webhook("https://example.com/webhook", payload, config)

    assert result is False
    # Should retry 2 times
    assert mock_urlopen.call_count == 2


@patch('urllib.request.urlopen')
def test_post_webhook_url_error(mock_urlopen):
    """Test webhook posting with URL error."""
    # Mock URL error (e.g., DNS failure)
    mock_urlopen.side_effect = urllib.error.URLError("Name or service not known")

    config = {
        "webhook": {
            "retry_count": 1,
            "retry_backoff": 1,
            "timeout": 10
        }
    }

    payload = {"test": "data"}
    result = post_webhook("https://invalid-domain-xyz.com/webhook", payload, config)

    assert result is False


@patch('urllib.request.urlopen')
def test_post_webhook_success_after_retry(mock_urlopen):
    """Test webhook succeeds after initial failure."""
    # First call fails, second succeeds
    mock_error_response = Mock(side_effect=urllib.error.HTTPError(
        "https://example.com/webhook",
        503,
        "Service Unavailable",
        {},
        None
    ))

    mock_success_response = MagicMock()
    mock_success_response.status = 200
    mock_success_response.__enter__ = Mock(return_value=mock_success_response)
    mock_success_response.__exit__ = Mock(return_value=False)

    mock_urlopen.side_effect = [mock_error_response, mock_success_response]

    config = {
        "webhook": {
            "retry_count": 3,
            "retry_backoff": 1,
            "timeout": 10
        }
    }

    payload = {"test": "data"}
    result = post_webhook("https://example.com/webhook", payload, config)

    assert result is True
    assert mock_urlopen.call_count == 2


def test_format_generic_payload_missing_scores():
    """Test generic payload formatting handles missing scores."""
    report_data = {
        "status": "unknown",
        "recommendations": []
    }

    payload = format_generic_payload(report_data)

    # Should handle missing scores gracefully
    assert payload["scores"]["security"] == 0
    assert payload["scores"]["ops"] == 0
    assert payload["scores"]["governance"] == 0
    assert payload["scores"]["reliability"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
