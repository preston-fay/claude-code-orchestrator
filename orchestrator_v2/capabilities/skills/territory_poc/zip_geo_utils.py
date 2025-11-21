"""
ZIP Code Geography Utilities for Territory POC.

Provides ZIP to lat/lon mapping for IA, IL, IN states.
Uses a baked-in mapping for the POC to avoid external dependencies.
"""

import math
from typing import Optional

# Baked-in ZIP code centroids for IA, IL, IN
# Format: {zip_prefix: (lat, lon)}
# Using 3-digit ZIP prefixes for broader coverage
ZIP_CENTROIDS = {
    # Iowa (IA) - ZIP prefixes 500-528
    "500": (41.5868, -93.6250),  # Des Moines
    "501": (41.5868, -93.6250),  # Des Moines
    "502": (41.6611, -91.5302),  # Iowa City
    "503": (41.9779, -91.6656),  # Cedar Rapids
    "504": (42.4995, -96.4003),  # Sioux City
    "505": (42.0308, -93.6319),  # Ames
    "506": (42.8794, -91.6985),  # Waterloo
    "507": (40.8072, -91.1127),  # Burlington
    "508": (41.2619, -95.8608),  # Council Bluffs
    "509": (42.5006, -94.1669),  # Fort Dodge
    "510": (42.0308, -93.6319),  # Central IA
    "511": (42.0308, -93.6319),  # Central IA
    "512": (41.0534, -92.4077),  # Ottumwa
    "513": (40.4067, -91.4116),  # Keokuk
    "514": (41.4019, -90.5776),  # Davenport
    "515": (40.9856, -91.5436),  # Burlington area
    "516": (43.1536, -93.2011),  # Mason City
    "520": (42.5006, -90.6647),  # Dubuque
    "521": (42.0308, -93.6319),  # Decorah
    "522": (41.6611, -91.5302),  # Iowa City
    "523": (41.5868, -93.6250),  # Des Moines
    "524": (41.5868, -93.6250),  # Des Moines
    "525": (40.8072, -91.1127),  # Southeast IA
    "526": (41.5868, -93.6250),  # Central IA
    "527": (42.0308, -93.6319),  # Central IA
    "528": (43.1536, -93.2011),  # North IA

    # Illinois (IL) - ZIP prefixes 600-629
    "600": (41.8781, -87.6298),  # Chicago
    "601": (41.8781, -87.6298),  # Chicago
    "602": (41.8781, -87.6298),  # Chicago
    "603": (41.8781, -87.6298),  # Chicago
    "604": (41.8781, -87.6298),  # Chicago
    "605": (41.8781, -87.6298),  # Chicago
    "606": (41.8781, -87.6298),  # Chicago
    "607": (41.8781, -87.6298),  # Chicago
    "608": (41.8781, -87.6298),  # Chicago
    "609": (41.5250, -88.0817),  # Joliet
    "610": (41.5061, -90.5152),  # Rock Island
    "611": (41.5061, -90.5152),  # Moline
    "612": (41.4239, -88.8340),  # LaSalle
    "613": (41.4239, -88.8340),  # Ottawa
    "614": (40.6936, -89.5890),  # Peoria
    "615": (40.6936, -89.5890),  # Peoria
    "616": (40.6936, -89.5890),  # Peoria
    "617": (40.4842, -88.9937),  # Bloomington
    "618": (39.7817, -89.6501),  # Springfield
    "619": (39.7817, -89.6501),  # Springfield
    "620": (38.6270, -90.1994),  # East St. Louis
    "621": (38.6270, -90.1994),  # East St. Louis
    "622": (38.5254, -89.9875),  # Belleville
    "623": (38.3031, -88.9076),  # Mt. Vernon
    "624": (38.9206, -89.0828),  # Effingham
    "625": (40.1164, -88.2434),  # Champaign
    "626": (40.1164, -88.2434),  # Urbana
    "627": (39.7817, -89.6501),  # Central IL
    "628": (37.7273, -89.2168),  # Carbondale
    "629": (37.7273, -89.2168),  # Southern IL

    # Indiana (IN) - ZIP prefixes 460-479
    "460": (39.7684, -86.1581),  # Indianapolis
    "461": (39.7684, -86.1581),  # Indianapolis
    "462": (39.7684, -86.1581),  # Indianapolis
    "463": (41.0793, -85.1394),  # Fort Wayne
    "464": (41.4731, -87.0611),  # Gary
    "465": (41.6764, -86.2520),  # South Bend
    "466": (41.6764, -86.2520),  # South Bend
    "467": (40.4167, -86.8753),  # Lafayette
    "468": (40.4167, -86.8753),  # Lafayette
    "469": (40.1934, -85.3864),  # Muncie
    "470": (38.0406, -87.5342),  # Evansville
    "471": (38.0406, -87.5342),  # Evansville
    "472": (38.2542, -85.7594),  # New Albany
    "473": (39.1653, -86.5264),  # Bloomington
    "474": (39.1653, -86.5264),  # Bloomington
    "475": (39.4667, -87.4139),  # Terre Haute
    "476": (39.4667, -87.4139),  # Terre Haute
    "477": (38.0406, -87.5342),  # Southern IN
    "478": (39.4667, -87.4139),  # Western IN
    "479": (40.7478, -86.0670),  # Kokomo
}

# State centroids as fallback
STATE_CENTROIDS = {
    "IA": (41.8780, -93.0977),  # Iowa
    "IL": (40.6331, -89.3985),  # Illinois
    "IN": (40.2672, -86.1349),  # Indiana
}


def get_zip_centroid(zip_code: str, state: str = "") -> tuple[float, float]:
    """Get lat/lon centroid for a ZIP code.

    Args:
        zip_code: ZIP code (can be 5-digit or 3-digit prefix)
        state: State abbreviation (used as fallback)

    Returns:
        Tuple of (latitude, longitude)
    """
    if not zip_code:
        # Return state centroid or default
        return STATE_CENTROIDS.get(state, (40.0, -89.0))

    # Clean ZIP code
    zip_str = str(zip_code).strip().split("-")[0]  # Handle ZIP+4

    # Try exact 3-digit prefix match
    prefix = zip_str[:3]
    if prefix in ZIP_CENTROIDS:
        return ZIP_CENTROIDS[prefix]

    # Try 5-digit to find closest prefix
    if len(zip_str) >= 5:
        prefix = zip_str[:3]
        if prefix in ZIP_CENTROIDS:
            return ZIP_CENTROIDS[prefix]

    # Fallback to state centroid
    if state in STATE_CENTROIDS:
        return STATE_CENTROIDS[state]

    # Default fallback (central US)
    return (40.0, -89.0)


def add_coordinates_to_dataframe(df, zip_column: str = "zip", state_column: str = "state"):
    """Add lat/lon columns to a DataFrame based on ZIP codes.

    Args:
        df: pandas DataFrame with ZIP and state columns
        zip_column: Name of ZIP code column
        state_column: Name of state column

    Returns:
        DataFrame with 'lat' and 'lon' columns added
    """
    import pandas as pd

    lats = []
    lons = []

    for _, row in df.iterrows():
        zip_code = str(row.get(zip_column, ""))
        state = str(row.get(state_column, ""))
        lat, lon = get_zip_centroid(zip_code, state)
        lats.append(lat)
        lons.append(lon)

    df = df.copy()
    df["lat"] = lats
    df["lon"] = lons

    return df


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers.

    Uses Haversine formula.
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
