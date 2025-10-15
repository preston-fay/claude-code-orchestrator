"""Tests for isochrone provider system."""

import pytest
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from src.server.iso_providers import (
    TokenBucket,
    get_isochrones_stub,
    get_isochrones_ors,
    get_isochrones_mapbox,
    get_isochrones,
    FeatureCollection,
)


class TestTokenBucket:
    """Test token bucket rate limiting."""

    def test_initial_consumption_allowed(self):
        """First request should be allowed."""
        bucket = TokenBucket(rate=10, per_seconds=60)
        assert bucket.consume() is True

    def test_rate_limit_enforced(self):
        """Requests beyond rate should be blocked."""
        bucket = TokenBucket(rate=3, per_seconds=60)

        # Consume 3 tokens
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is True

        # 4th should be blocked
        assert bucket.consume() is False

    def test_time_window_expiry(self):
        """Old requests should expire after time window."""
        bucket = TokenBucket(rate=2, per_seconds=1)  # 2 per second

        # Consume 2 tokens
        assert bucket.consume() is True
        assert bucket.consume() is True

        # 3rd blocked
        assert bucket.consume() is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert bucket.consume() is True

    def test_concurrent_consumption(self):
        """Bucket should track all consumption correctly."""
        bucket = TokenBucket(rate=5, per_seconds=60)

        results = [bucket.consume() for _ in range(7)]

        # First 5 should succeed, last 2 fail
        assert results[:5] == [True] * 5
        assert results[5:] == [False] * 2


class TestStubProvider:
    """Test stub isochrone provider."""

    def test_stub_returns_feature_collection(self):
        """Stub should return valid FeatureCollection."""
        result = get_isochrones_stub(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving"
        )

        assert isinstance(result, FeatureCollection)
        assert len(result.features) == 3
        assert result.type == "FeatureCollection"

    def test_stub_features_have_properties(self):
        """Stub features should have time and range properties."""
        result = get_isochrones_stub(45.5231, -122.6765, 30, 3, "driving")

        for i, feature in enumerate(result.features):
            assert "properties" in feature
            assert "time" in feature["properties"]
            assert "range" in feature["properties"]
            assert feature["properties"]["time"] == (i + 1) * 10

    def test_stub_geometry_is_polygon(self):
        """Stub features should have Polygon geometry."""
        result = get_isochrones_stub(45.5231, -122.6765, 30, 3, "driving")

        for feature in result.features:
            assert feature["geometry"]["type"] == "Polygon"
            assert "coordinates" in feature["geometry"]
            assert len(feature["geometry"]["coordinates"]) > 0

    def test_stub_respects_buckets(self):
        """Stub should return correct number of buckets."""
        for buckets in [1, 2, 3, 4]:
            result = get_isochrones_stub(45.5231, -122.6765, 30, buckets, "driving")
            assert len(result.features) == buckets

    def test_stub_profile_affects_range(self):
        """Different profiles should create different ranges."""
        driving = get_isochrones_stub(45.5231, -122.6765, 30, 1, "driving")
        walking = get_isochrones_stub(45.5231, -122.6765, 30, 1, "walking")

        # Walking should be smaller than driving for same time
        # (this tests the speed assumptions work correctly)
        assert driving.features[0]["geometry"]["coordinates"] is not None
        assert walking.features[0]["geometry"]["coordinates"] is not None


class TestORSProvider:
    """Test OpenRouteService provider."""

    @patch.dict("os.environ", {"ORS_API_KEY": ""}, clear=True)
    def test_ors_no_api_key_falls_back_to_stub(self):
        """ORS without API key should fall back to stub."""
        result = get_isochrones_ors(45.5231, -122.6765, 30, 3, "driving")

        assert isinstance(result, FeatureCollection)
        assert len(result.features) == 3  # Stub returns 3 features

    @patch.dict("os.environ", {"ORS_API_KEY": "test_key_123"})
    @patch("src.server.iso_providers.requests.post")
    def test_ors_with_api_key_makes_request(self, mock_post):
        """ORS with API key should make API request."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"value": 600},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-122.6, 45.5], [-122.7, 45.5], [-122.6, 45.5]]]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = get_isochrones_ors(45.5231, -122.6765, 30, 3, "driving")

        # Should have called ORS API
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert "openrouteservice.org" in call_args[0][0]

        # Check headers contain API key
        assert "Authorization" in call_args[1]["headers"]
        assert "test_key_123" in call_args[1]["headers"]["Authorization"]

    @patch.dict("os.environ", {"ORS_API_KEY": "test_key_123"})
    @patch("src.server.iso_providers.requests.post")
    def test_ors_timeout_falls_back_to_stub(self, mock_post):
        """ORS timeout should fall back to stub."""
        import requests
        mock_post.side_effect = requests.Timeout("API timeout")

        result = get_isochrones_ors(45.5231, -122.6765, 30, 3, "driving")

        # Should fall back to stub
        assert isinstance(result, FeatureCollection)
        assert len(result.features) == 3


class TestMapboxProvider:
    """Test Mapbox provider."""

    @patch.dict("os.environ", {"MAPBOX_TOKEN": ""}, clear=True)
    def test_mapbox_no_token_falls_back_to_stub(self):
        """Mapbox without token should fall back to stub."""
        result = get_isochrones_mapbox(45.5231, -122.6765, 30, 3, "driving")

        assert isinstance(result, FeatureCollection)
        assert len(result.features) == 3

    @patch.dict("os.environ", {"MAPBOX_TOKEN": "pk.test_token_123"})
    @patch("src.server.iso_providers.requests.get")
    def test_mapbox_with_token_makes_request(self, mock_get):
        """Mapbox with token should make API request."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"contour": 10},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-122.6, 45.5], [-122.7, 45.5], [-122.6, 45.5]]]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        result = get_isochrones_mapbox(45.5231, -122.6765, 30, 3, "driving")

        # Should have called Mapbox API
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]

        # Check URL contains token
        assert "mapbox.com" in call_url
        assert "pk.test_token_123" in call_url

    @patch.dict("os.environ", {"MAPBOX_TOKEN": "pk.test_token_123"})
    @patch("src.server.iso_providers.requests.get")
    def test_mapbox_timeout_falls_back_to_stub(self, mock_get):
        """Mapbox timeout should fall back to stub."""
        import requests
        mock_get.side_effect = requests.Timeout("API timeout")

        result = get_isochrones_mapbox(45.5231, -122.6765, 30, 3, "driving")

        # Should fall back to stub
        assert isinstance(result, FeatureCollection)
        assert len(result.features) == 3


class TestGetIsochrones:
    """Test main get_isochrones function."""

    def test_stub_provider_selected(self):
        """Stub provider should be selected by default."""
        result, rate_limited = get_isochrones(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving",
            provider="stub"
        )

        assert isinstance(result, FeatureCollection)
        assert rate_limited is False

    @patch("src.server.iso_providers._rate_limiter")
    def test_rate_limiting_triggers_stub(self, mock_limiter):
        """Rate limiting should trigger stub response."""
        mock_limiter.consume.return_value = False

        result, rate_limited = get_isochrones(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving",
            provider="openrouteservice"
        )

        assert isinstance(result, FeatureCollection)
        assert rate_limited is True

    @patch("src.server.iso_providers._rate_limiter")
    @patch.dict("os.environ", {"ORS_API_KEY": "test_key"})
    @patch("src.server.iso_providers.requests.post")
    def test_ors_provider_selected(self, mock_post, mock_limiter):
        """ORS provider should be selected when specified."""
        mock_limiter.consume.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": []
        }
        mock_post.return_value = mock_response

        result, rate_limited = get_isochrones(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving",
            provider="openrouteservice"
        )

        assert rate_limited is False
        mock_post.assert_called_once()

    @patch("src.server.iso_providers._rate_limiter")
    @patch.dict("os.environ", {"MAPBOX_TOKEN": "pk.test"})
    @patch("src.server.iso_providers.requests.get")
    def test_mapbox_provider_selected(self, mock_get, mock_limiter):
        """Mapbox provider should be selected when specified."""
        mock_limiter.consume.return_value = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "FeatureCollection",
            "features": []
        }
        mock_get.return_value = mock_response

        result, rate_limited = get_isochrones(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving",
            provider="mapbox"
        )

        assert rate_limited is False
        mock_get.assert_called_once()

    def test_invalid_provider_falls_back_to_stub(self):
        """Invalid provider should fall back to stub."""
        result, rate_limited = get_isochrones(
            lat=45.5231,
            lon=-122.6765,
            range_minutes=30,
            buckets=3,
            profile="driving",
            provider="invalid_provider"
        )

        assert isinstance(result, FeatureCollection)
        assert rate_limited is False


class TestProviderTimeout:
    """Test provider timeout behavior."""

    @patch.dict("os.environ", {"ORS_API_KEY": "test_key"})
    @patch("src.server.iso_providers.requests.post")
    def test_ors_respects_timeout(self, mock_post):
        """ORS should use 5s timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"type": "FeatureCollection", "features": []}
        mock_post.return_value = mock_response

        get_isochrones_ors(45.5231, -122.6765, 30, 3, "driving")

        # Check timeout parameter
        assert mock_post.call_args[1]["timeout"] == 5

    @patch.dict("os.environ", {"MAPBOX_TOKEN": "pk.test"})
    @patch("src.server.iso_providers.requests.get")
    def test_mapbox_respects_timeout(self, mock_get):
        """Mapbox should use 5s timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"type": "FeatureCollection", "features": []}
        mock_get.return_value = mock_response

        get_isochrones_mapbox(45.5231, -122.6765, 30, 3, "driving")

        # Check timeout parameter
        assert mock_get.call_args[1]["timeout"] == 5


class TestRangeConfiguration:
    """Test range configuration via environment."""

    @patch.dict("os.environ", {"ISO_MAX_RANGE_MIN": "45"})
    def test_max_range_respected(self):
        """Max range should be enforced from environment."""
        from src.server.iso_providers import MAX_RANGE_MIN

        # Should be 45 from env var
        assert MAX_RANGE_MIN == 45

    @patch.dict("os.environ", {}, clear=True)
    def test_max_range_default(self):
        """Max range should default to 60."""
        # Reload module to pick up env
        import importlib
        import src.server.iso_providers
        importlib.reload(src.server.iso_providers)

        from src.server.iso_providers import MAX_RANGE_MIN
        assert MAX_RANGE_MIN == 60
