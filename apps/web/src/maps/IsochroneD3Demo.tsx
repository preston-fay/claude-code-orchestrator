import { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { LeafletD3Overlay } from './LeafletD3Overlay';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../design-system/tokens';
import type { FeatureCollection, Feature } from 'geojson';

type Provider = 'stub' | 'openrouteservice' | 'mapbox';
type Profile = 'driving' | 'walking' | 'cycling';

/**
 * IsochroneD3Demo - Interactive isochrone map with D3 overlay
 *
 * Features:
 * - Provider selection (stub, ORS, Mapbox)
 * - Range and buckets controls
 * - Profile selection (driving, walking, cycling)
 * - D3 overlay with branded labels and spot color
 * - Theme-aware tiles and styling
 */
export function IsochroneD3Demo() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const mapRef = useRef<L.Map | null>(null);

  const [provider, setProvider] = useState<Provider>('stub');
  const [range, setRange] = useState(30);
  const [buckets, setBuckets] = useState(3);
  const [profile, setProfile] = useState<Profile>('driving');
  const [center, setCenter] = useState<[number, number]>([51.505, -0.09]);
  const [hoveredFeature, setHoveredFeature] = useState<Feature | null>(null);

  // Generate stub isochrone data
  const getStubFeatures = (): FeatureCollection => {
    const features: Feature[] = [];
    const step = range / buckets;

    for (let i = 0; i < buckets; i++) {
      const minutes = (i + 1) * step;
      const radius = 0.01 * (i + 1);

      // Create polygon ring around center
      const points: [number, number][] = [];
      const segments = 32;
      for (let j = 0; j <= segments; j++) {
        const angle = (j / segments) * 2 * Math.PI;
        const lng = center[1] + radius * Math.cos(angle);
        const lat = center[0] + radius * Math.sin(angle);
        points.push([lng, lat]);
      }

      features.push({
        type: 'Feature',
        properties: {
          minutes: Math.round(minutes),
          profile,
          isMax: i === buckets - 1,
          area: Math.PI * radius * radius,
        },
        geometry: {
          type: 'Polygon',
          coordinates: [points],
        },
      });
    }

    return {
      type: 'FeatureCollection',
      features: features.reverse(), // Largest first for proper rendering
    };
  };

  // Fetch isochrones from API (stub implementation)
  const getFeatures = async (): Promise<FeatureCollection> => {
    if (provider === 'stub') {
      return getStubFeatures();
    }

    // Real API would fetch here
    // For now, return stub data
    console.log(`Fetching from ${provider}: range=${range}, buckets=${buckets}, profile=${profile}`);
    return getStubFeatures();
  };

  // Get tile layer URL based on theme
  const getTileUrl = () => {
    if (theme === 'dark') {
      return 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    }
    return 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
  };

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: colors.background }}>
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: colors.border }}>
        <h1 className="text-2xl font-bold mb-2" style={{ color: colors.text }}>
          Isochrone Map with D3 Overlay
        </h1>
        <p className="text-sm" style={{ color: colors.textMuted }}>
          Brand-compliant isochrone visualization with collision-avoided labels and spot color emphasis
        </p>
      </div>

      {/* Controls */}
      <div
        className="p-4 border-b flex flex-wrap gap-4 items-center"
        style={{ borderColor: colors.border, backgroundColor: colors.surface }}
      >
        {/* Provider */}
        <label className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: colors.text }}>
            Provider:
          </span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
            className="px-3 py-1 rounded border"
            style={{
              backgroundColor: colors.background,
              color: colors.text,
              borderColor: colors.border,
            }}
          >
            <option value="stub">Stub (Demo)</option>
            <option value="openrouteservice">OpenRouteService</option>
            <option value="mapbox">Mapbox</option>
          </select>
        </label>

        {/* Profile */}
        <label className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: colors.text }}>
            Profile:
          </span>
          <select
            value={profile}
            onChange={(e) => setProfile(e.target.value as Profile)}
            className="px-3 py-1 rounded border"
            style={{
              backgroundColor: colors.background,
              color: colors.text,
              borderColor: colors.border,
            }}
          >
            <option value="driving">Driving</option>
            <option value="walking">Walking</option>
            <option value="cycling">Cycling</option>
          </select>
        </label>

        {/* Range */}
        <label className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: colors.text }}>
            Range: {range} min
          </span>
          <input
            type="range"
            min="10"
            max="60"
            step="5"
            value={range}
            onChange={(e) => setRange(Number(e.target.value))}
            className="w-32"
          />
        </label>

        {/* Buckets */}
        <label className="flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: colors.text }}>
            Buckets: {buckets}
          </span>
          <input
            type="range"
            min="1"
            max="4"
            step="1"
            value={buckets}
            onChange={(e) => setBuckets(Number(e.target.value))}
            className="w-24"
          />
        </label>

        {/* Legend */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-sm font-medium" style={{ color: colors.text }}>
            Legend:
          </span>
          <div className="flex gap-1">
            {Array.from({ length: buckets }, (_, i) => {
              const minutes = Math.round(((i + 1) * range) / buckets);
              return (
                <div
                  key={i}
                  className="px-2 py-1 rounded text-xs"
                  style={{
                    backgroundColor: colors.spotColor,
                    color: colors.textInverse,
                    opacity: 0.5 + (i / buckets) * 0.5,
                  }}
                >
                  {minutes}m
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={center}
          zoom={13}
          style={{ width: '100%', height: '100%' }}
          ref={(map) => {
            if (map) {
              mapRef.current = map;
            }
          }}
        >
          <TileLayer
            url={getTileUrl()}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <LeafletD3Overlay
            map={mapRef.current}
            getFeatures={getFeatures}
            labelAccessor={(f) => `${f.properties?.minutes || '?'} min`}
            spotPredicate={(f) => f.properties?.isMax === true}
            onHover={setHoveredFeature}
            onClick={(f) => {
              if (f) {
                console.log('Clicked feature:', f.properties);
              }
            }}
          />
        </MapContainer>

        {/* Hover info */}
        {hoveredFeature && (
          <div
            className="absolute top-4 right-4 p-3 rounded shadow-lg"
            style={{
              backgroundColor: colors.surfaceElevated,
              borderLeft: `4px solid ${colors.spotColor}`,
            }}
          >
            <div className="text-sm font-semibold" style={{ color: colors.text }}>
              {hoveredFeature.properties?.minutes} minutes
            </div>
            <div className="text-xs" style={{ color: colors.textMuted }}>
              {hoveredFeature.properties?.profile || profile}
            </div>
          </div>
        )}
      </div>

      {/* Footer note */}
      <div
        className="p-2 text-center text-xs border-t"
        style={{ borderColor: colors.border, color: colors.textMuted }}
      >
        No gridlines • Label-first • Spot color emphasis • Collision-avoided labels
      </div>
    </div>
  );
}
