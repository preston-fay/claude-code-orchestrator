"""
Isochrone provider adapters for OpenRouteService, Mapbox, and stub implementation.

Features:
- Rate limiting (token bucket, 10 req/min default)
- Timeout protection (5s default)
- Fallback to stub on failure
- Environment variable configuration
"""

import os
import time
import math
from typing import Dict, List, Optional, Tuple
from collections import deque
import requests
from geojson import FeatureCollection, Feature, Polygon

# Configuration from environment
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
ISO_MAX_RANGE_MIN = int(os.getenv("ISO_MAX_RANGE_MIN", "60"))
ISO_RATE_LIMIT = int(os.getenv("ISO_RATE_LIMIT", "10"))  # requests per minute
PROVIDER_TIMEOUT = int(os.getenv("PROVIDER_TIMEOUT", "5"))  # seconds


class TokenBucket:
    """Simple in-memory token bucket for rate limiting."""

    def __init__(self, rate: int, per_seconds: int = 60):
        """
        Initialize token bucket.

        Args:
            rate: Number of tokens per time period
            per_seconds: Time period in seconds (default 60 = 1 minute)
        """
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_update = time.time()
        self.requests = deque()

    def consume(self) -> bool:
        """
        Try to consume one token.

        Returns:
            True if token consumed, False if rate limit exceeded
        """
        now = time.time()

        # Remove requests older than time window
        while self.requests and self.requests[0] < now - self.per_seconds:
            self.requests.popleft()

        # Check rate limit
        if len(self.requests) >= self.rate:
            return False

        # Consume token
        self.requests.append(now)
        return True


# Global rate limiter
_rate_limiter = TokenBucket(rate=ISO_RATE_LIMIT, per_seconds=60)


def get_isochrones_stub(
    lat: float,
    lon: float,
    range_minutes: int,
    buckets: int = 3,
    profile: str = "driving"
) -> FeatureCollection:
    """
    Generate stub isochrone polygons using circular buffers.

    Args:
        lat: Latitude of starting point
        lon: Longitude of starting point
        range_minutes: Maximum travel time in minutes
        buckets: Number of isochrone zones (default 3)
        profile: Travel profile (driving, walking, cycling)

    Returns:
        GeoJSON FeatureCollection with polygon features
    """
    # Speed assumptions (km/h)
    speeds = {
        "driving": 50,
        "walking": 5,
        "cycling": 15,
    }
    speed_kmh = speeds.get(profile, 50)

    features = []
    step = range_minutes / buckets

    for i in range(buckets):
        minutes = (i + 1) * step
        # Distance = speed * time
        distance_km = (speed_kmh * minutes) / 60
        # Convert to degrees (rough approximation)
        # 1 degree lat ~ 111 km, 1 degree lon ~ 111km * cos(lat)
        radius_deg = distance_km / 111.0

        # Create circular polygon
        segments = 32
        coords = []
        for j in range(segments + 1):
            angle = (j / segments) * 2 * math.pi
            point_lon = lon + radius_deg * math.cos(angle) / math.cos(math.radians(lat))
            point_lat = lat + radius_deg * math.sin(angle)
            coords.append([point_lon, point_lat])

        features.append(Feature(
            geometry=Polygon([coords]),
            properties={
                "minutes": round(minutes),
                "profile": profile,
                "isMax": i == buckets - 1,
                "area": math.pi * (distance_km ** 2),
                "provider": "stub"
            }
        ))

    # Reverse so largest is first (for proper rendering)
    return FeatureCollection(features=list(reversed(features)))


def get_isochrones_ors(
    lat: float,
    lon: float,
    range_minutes: int,
    buckets: int = 3,
    profile: str = "driving"
) -> FeatureCollection:
    """
    Fetch isochrones from OpenRouteService API.

    Args:
        lat: Latitude of starting point
        lon: Longitude of starting point
        range_minutes: Maximum travel time in minutes
        buckets: Number of isochrone zones
        profile: Travel profile (driving-car, foot-walking, cycling-regular)

    Returns:
        GeoJSON FeatureCollection or stub data on failure

    Env:
        ORS_API_KEY: OpenRouteService API key
    """
    if not ORS_API_KEY:
        print("ORS_API_KEY not set, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)

    # Map profile names
    profile_map = {
        "driving": "driving-car",
        "walking": "foot-walking",
        "cycling": "cycling-regular"
    }
    ors_profile = profile_map.get(profile, "driving-car")

    # Build range array
    step = range_minutes / buckets
    ranges = [int((i + 1) * step * 60) for i in range(buckets)]  # Convert to seconds

    url = f"https://api.openrouteservice.org/v2/isochrones/{ors_profile}"
    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "locations": [[lon, lat]],
        "range": ranges,
        "range_type": "time"
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=PROVIDER_TIMEOUT)
        response.raise_for_status()

        geojson = response.json()

        # Add metadata to features
        for i, feature in enumerate(geojson.get("features", [])):
            feature["properties"]["minutes"] = ranges[i] // 60
            feature["properties"]["profile"] = profile
            feature["properties"]["isMax"] = i == len(ranges) - 1
            feature["properties"]["provider"] = "openrouteservice"

        return FeatureCollection(features=geojson.get("features", []))

    except requests.Timeout:
        print(f"ORS API timeout after {PROVIDER_TIMEOUT}s, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)

    except Exception as e:
        print(f"ORS API error: {e}, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)


def get_isochrones_mapbox(
    lat: float,
    lon: float,
    range_minutes: int,
    buckets: int = 3,
    profile: str = "driving"
) -> FeatureCollection:
    """
    Fetch isochrones from Mapbox Isochrone API.

    Args:
        lat: Latitude of starting point
        lon: Longitude of starting point
        range_minutes: Maximum travel time in minutes
        buckets: Number of isochrone zones
        profile: Travel profile (driving, walking, cycling)

    Returns:
        GeoJSON FeatureCollection or stub data on failure

    Env:
        MAPBOX_TOKEN: Mapbox access token
    """
    if not MAPBOX_TOKEN:
        print("MAPBOX_TOKEN not set, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)

    # Map profile names
    profile_map = {
        "driving": "driving",
        "walking": "walking",
        "cycling": "cycling"
    }
    mapbox_profile = profile_map.get(profile, "driving")

    # Mapbox only supports single contour per request, so we'll just use the max range
    # For multiple buckets, would need multiple requests (not implemented to save quota)
    contour_minutes = range_minutes

    url = f"https://api.mapbox.com/isochrone/v1/mapbox/{mapbox_profile}/{lon},{lat}"
    params = {
        "contours_minutes": contour_minutes,
        "polygons": "true",
        "access_token": MAPBOX_TOKEN
    }

    try:
        response = requests.get(url, params=params, timeout=PROVIDER_TIMEOUT)
        response.raise_for_status()

        geojson = response.json()

        # Add metadata
        for feature in geojson.get("features", []):
            feature["properties"]["minutes"] = contour_minutes
            feature["properties"]["profile"] = profile
            feature["properties"]["isMax"] = True
            feature["properties"]["provider"] = "mapbox"

        # If buckets > 1, fill with stub data for smaller zones
        if buckets > 1:
            stub_data = get_isochrones_stub(lat, lon, range_minutes, buckets - 1, profile)
            features = stub_data["features"] + geojson.get("features", [])
            return FeatureCollection(features=features)

        return FeatureCollection(features=geojson.get("features", []))

    except requests.Timeout:
        print(f"Mapbox API timeout after {PROVIDER_TIMEOUT}s, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)

    except Exception as e:
        print(f"Mapbox API error: {e}, falling back to stub")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile)


def get_isochrones(
    lat: float,
    lon: float,
    range_minutes: int,
    buckets: int = 3,
    profile: str = "driving",
    provider: str = "stub"
) -> Tuple[FeatureCollection, bool]:
    """
    Get isochrones from specified provider with rate limiting and fallback.

    Args:
        lat: Latitude
        lon: Longitude
        range_minutes: Max travel time in minutes
        buckets: Number of zones
        profile: Travel profile
        provider: Provider name (stub, openrouteservice, mapbox)

    Returns:
        Tuple of (FeatureCollection, rate_limited: bool)
    """
    # Check rate limit
    if not _rate_limiter.consume():
        print(f"Rate limit exceeded ({ISO_RATE_LIMIT} req/min)")
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile), True

    # Enforce max range
    range_minutes = min(range_minutes, ISO_MAX_RANGE_MIN)

    # Select provider
    if provider == "openrouteservice":
        return get_isochrones_ors(lat, lon, range_minutes, buckets, profile), False
    elif provider == "mapbox":
        return get_isochrones_mapbox(lat, lon, range_minutes, buckets, profile), False
    else:
        return get_isochrones_stub(lat, lon, range_minutes, buckets, profile), False
