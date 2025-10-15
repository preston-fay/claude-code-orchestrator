"""Folium map helpers with Kearney design tokens.

Provides helper functions to create brand-compliant Folium maps with:
- Light/dark theme support
- Kearney color palette
- Label-first markers
- Isochrone visualization
"""

import folium
import json
from pathlib import Path
from typing import Literal, Dict, Any, List, Optional, Tuple
from branca.element import MacroElement
from jinja2 import Template


# Kearney color palettes
KEARNEY_COLORS = {
    "light": {
        "background": "#FFFFFF",
        "surface": "#F5F5F5",
        "text": "#1A1A1A",
        "text_secondary": "#666666",
        "emphasis": "#E63946",  # Red
        "border": "#D1D5DB",
    },
    "dark": {
        "background": "#1A1A1A",
        "surface": "#2D2D2D",
        "text": "#FFFFFF",
        "text_secondary": "#A3A3A3",
        "emphasis": "#EF476F",  # Pink
        "border": "#404040",
    }
}

# Isochrone zone colors (light to dark)
ISOCHRONE_COLORS = {
    "light": ["#FEE2E2", "#FECACA", "#FCA5A5", "#F87171"],  # Red scale
    "dark": ["#7F1D1D", "#991B1B", "#B91C1C", "#DC2626"],   # Dark red scale
}


def kearney_folium_map(
    center: Tuple[float, float],
    zoom: int = 12,
    theme: Literal["light", "dark"] = "light",
    title: Optional[str] = None,
    tiles: str = "cartodbpositron",
) -> folium.Map:
    """
    Create a Kearney-branded Folium map.

    Args:
        center: (lat, lon) tuple for map center
        zoom: Initial zoom level
        theme: "light" or "dark"
        title: Optional title displayed in top-right corner
        tiles: Base tiles (cartodbpositron for light, cartodbdark_matter for dark)

    Returns:
        Configured Folium map instance

    Example:
        >>> m = kearney_folium_map(
        ...     center=(45.5231, -122.6765),
        ...     zoom=12,
        ...     theme="light",
        ...     title="Portland Service Area"
        ... )
        >>> m.save("map.html")
    """
    colors = KEARNEY_COLORS[theme]

    # Select appropriate tiles for theme
    if theme == "dark" and tiles == "cartodbpositron":
        tiles = "cartodbdark_matter"

    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=tiles,
        attr="© OpenStreetMap contributors | Kearney",
        control_scale=True,
    )

    # Add custom CSS for Kearney branding
    css_template = Template("""
        <style>
            /* Kearney theme: {{ theme }} */
            .leaflet-container {
                background-color: {{ colors.background }};
                font-family: Inter, Arial, sans-serif;
            }

            .leaflet-control-zoom a,
            .leaflet-control-layers,
            .leaflet-bar {
                background-color: {{ colors.surface }} !important;
                color: {{ colors.text }} !important;
                border-color: {{ colors.border }} !important;
            }

            .leaflet-control-zoom a:hover {
                background-color: {{ colors.emphasis }} !important;
                color: white !important;
            }

            /* Label-first markers */
            .kearney-marker {
                background-color: {{ colors.surface }};
                border: 2px solid {{ colors.emphasis }};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
                color: {{ colors.text }};
                white-space: nowrap;
            }

            /* Title card */
            .kearney-title {
                position: absolute;
                top: 10px;
                right: 60px;
                background-color: {{ colors.surface }};
                border-left: 4px solid {{ colors.emphasis }};
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: {{ colors.text }};
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                z-index: 1000;
            }

            /* Attribution */
            .leaflet-control-attribution {
                background-color: {{ colors.surface }} !important;
                color: {{ colors.text_secondary }} !important;
                font-size: 11px;
            }
        </style>
    """)

    css = css_template.render(theme=theme, colors=colors)

    class KearneyCSSElement(MacroElement):
        def __init__(self, css_str):
            super().__init__()
            self._template = Template(css_str)

        def render(self, **kwargs):
            return self._template.render(**kwargs)

    m.get_root().html.add_child(KearneyCSSElement(css))

    # Add title if provided
    if title:
        title_html = f"""
            <div class="kearney-title">
                {title}
            </div>
        """
        m.get_root().html.add_child(folium.Element(title_html))

    return m


def add_isochrones(
    map_obj: folium.Map,
    isochrones: Dict[str, Any],
    theme: Literal["light", "dark"] = "light",
    show_labels: bool = True,
    label_position: Literal["center", "top", "bottom"] = "center",
) -> folium.Map:
    """
    Add isochrone polygons to a Folium map.

    Args:
        map_obj: Folium map instance
        isochrones: GeoJSON FeatureCollection from isochrone API
        theme: "light" or "dark" for color selection
        show_labels: Whether to show time labels on polygons
        label_position: Where to position labels relative to polygon

    Returns:
        Updated Folium map instance

    Example:
        >>> from src.server.iso_providers import get_isochrones_stub
        >>> m = kearney_folium_map((45.5231, -122.6765), theme="light")
        >>> isochrones = get_isochrones_stub(45.5231, -122.6765, 30, 3, "driving")
        >>> add_isochrones(m, isochrones, theme="light")
        >>> m.save("map_with_isochrones.html")
    """
    colors_palette = ISOCHRONE_COLORS[theme]
    kearney_colors = KEARNEY_COLORS[theme]

    features = isochrones.get("features", [])

    # Sort features by time descending (largest first for correct layering)
    features_sorted = sorted(
        features,
        key=lambda f: f.get("properties", {}).get("time", 0),
        reverse=True
    )

    for i, feature in enumerate(features_sorted):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        time_minutes = properties.get("time", (i + 1) * 10)
        range_value = properties.get("range", time_minutes)

        # Select color from palette
        color_idx = min(i, len(colors_palette) - 1)
        fill_color = colors_palette[color_idx]

        # Create polygon
        folium.GeoJson(
            feature,
            style_function=lambda x, fc=fill_color: {
                "fillColor": fc,
                "color": kearney_colors["emphasis"],
                "weight": 2,
                "fillOpacity": 0.3,
                "opacity": 0.8,
            },
            tooltip=f"{time_minutes} min travel time",
        ).add_to(map_obj)

        # Add label if requested
        if show_labels and geometry.get("type") == "Polygon":
            coords = geometry.get("coordinates", [[]])[0]

            if coords and len(coords) > 0:
                # Calculate centroid (simple average)
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                centroid_lon = sum(lons) / len(lons)
                centroid_lat = sum(lats) / len(lats)

                # Adjust label position
                if label_position == "top":
                    centroid_lat += 0.01
                elif label_position == "bottom":
                    centroid_lat -= 0.01

                # Add label marker
                folium.Marker(
                    location=[centroid_lat, centroid_lon],
                    icon=folium.DivIcon(
                        html=f'<div class="kearney-marker">{time_minutes} min</div>'
                    ),
                ).add_to(map_obj)

    return map_obj


def add_point_of_interest(
    map_obj: folium.Map,
    location: Tuple[float, float],
    label: str,
    theme: Literal["light", "dark"] = "light",
    popup: Optional[str] = None,
) -> folium.Map:
    """
    Add a labeled point of interest to the map.

    Args:
        map_obj: Folium map instance
        location: (lat, lon) tuple
        label: Label text displayed on map
        theme: "light" or "dark"
        popup: Optional popup text on click

    Returns:
        Updated Folium map instance

    Example:
        >>> m = kearney_folium_map((45.5231, -122.6765))
        >>> add_point_of_interest(m, (45.5231, -122.6765), "Store #123")
    """
    colors = KEARNEY_COLORS[theme]

    # Create custom marker with label
    icon = folium.DivIcon(
        html=f"""
            <div style="
                background-color: {colors['surface']};
                border: 3px solid {colors['emphasis']};
                border-radius: 50%;
                width: 16px;
                height: 16px;
                margin-left: -8px;
                margin-top: -8px;
            "></div>
            <div class="kearney-marker" style="
                position: absolute;
                top: -30px;
                left: 10px;
                background-color: {colors['surface']};
                border: 2px solid {colors['emphasis']};
                padding: 4px 8px;
                border-radius: 4px;
                white-space: nowrap;
                font-size: 12px;
                font-weight: 600;
                color: {colors['text']};
            ">{label}</div>
        """
    )

    marker = folium.Marker(
        location=location,
        icon=icon,
    )

    if popup:
        marker.add_child(folium.Popup(popup, max_width=300))

    marker.add_to(map_obj)

    return map_obj


def save_map_as_png(
    map_obj: folium.Map,
    output_path: Path,
    width: int = 1200,
    height: int = 800,
) -> None:
    """
    Save Folium map as PNG using selenium.

    Args:
        map_obj: Folium map instance
        output_path: Path to save PNG
        width: Image width in pixels
        height: Image height in pixels

    Note:
        Requires selenium and a webdriver (chromedriver or geckodriver)

    Example:
        >>> m = kearney_folium_map((45.5231, -122.6765))
        >>> save_map_as_png(m, Path("map_light.png"))
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import time
    except ImportError:
        raise ImportError(
            "selenium is required for PNG export. Install with: pip install selenium"
        )

    # Save map to temporary HTML
    temp_html = output_path.parent / f"temp_{output_path.stem}.html"
    map_obj.save(str(temp_html))

    # Configure headless browser
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"--window-size={width},{height}")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        try:
            driver = webdriver.Firefox(options=options)
        except Exception as e:
            raise RuntimeError(
                f"Could not initialize webdriver: {e}. "
                "Install chromedriver or geckodriver."
            )

    try:
        # Load map
        driver.get(f"file://{temp_html.absolute()}")
        time.sleep(2)  # Wait for tiles to load

        # Take screenshot
        driver.save_screenshot(str(output_path))
    finally:
        driver.quit()
        temp_html.unlink(missing_ok=True)


def get_design_tokens(theme: Literal["light", "dark"] = "light") -> Dict[str, str]:
    """
    Get Kearney design tokens for the specified theme.

    Args:
        theme: "light" or "dark"

    Returns:
        Dictionary of token names to color values

    Example:
        >>> tokens = get_design_tokens("dark")
        >>> tokens["emphasis"]
        '#EF476F'
    """
    return KEARNEY_COLORS[theme].copy()


def get_isochrone_colors(
    theme: Literal["light", "dark"] = "light"
) -> List[str]:
    """
    Get isochrone color palette for the specified theme.

    Args:
        theme: "light" or "dark"

    Returns:
        List of hex color strings (light to dark)

    Example:
        >>> colors = get_isochrone_colors("light")
        >>> len(colors)
        4
    """
    return ISOCHRONE_COLORS[theme].copy()
