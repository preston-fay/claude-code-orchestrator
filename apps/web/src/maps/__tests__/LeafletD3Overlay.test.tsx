import { describe, it, expect, vi } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { LeafletD3Overlay } from '../LeafletD3Overlay';
import { ThemeProvider } from '../../contexts/ThemeContext';
import L from 'leaflet';
import type { FeatureCollection } from 'geojson';

// Mock Leaflet map
const createMockMap = (): L.Map => {
  return {
    getBounds: () => ({
      getNorthWest: () => ({ lat: 51.54, lng: -0.14 }),
      getSouthEast: () => ({ lat: 51.46, lng: -0.06 }),
    }),
    latLngToLayerPoint: (latlng: any) => {
      // Handle both [lat, lng] array and {lat, lng} object
      const lat = Array.isArray(latlng) ? latlng[0] : latlng.lat;
      const lng = Array.isArray(latlng) ? latlng[1] : latlng.lng;
      // Increased scale factor for larger viewport
      return {
        x: (lng + 0.2) * 5000,
        y: (51.6 - lat) * 5000,
      };
    },
    on: vi.fn(),
    off: vi.fn(),
  } as any;
};

// Stub GeoJSON data
const stubFeatures: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { minutes: 10, isMax: false },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-0.1, 51.5],
            [-0.1, 51.51],
            [-0.09, 51.51],
            [-0.09, 51.5],
            [-0.1, 51.5],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { minutes: 20, isMax: false },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-0.11, 51.49],
            [-0.11, 51.52],
            [-0.08, 51.52],
            [-0.08, 51.49],
            [-0.11, 51.49],
          ],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { minutes: 30, isMax: true },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-0.12, 51.48],
            [-0.12, 51.53],
            [-0.07, 51.53],
            [-0.07, 51.48],
            [-0.12, 51.48],
          ],
        ],
      },
    },
  ],
};

describe('LeafletD3Overlay', () => {
  it('renders SVG overlay with correct attributes', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay map={mockMap} getFeatures={getFeatures} />
      </ThemeProvider>
    );

    await waitFor(() => {
      const svg = container.querySelector('svg');
      expect(svg).toBeTruthy();
      expect(svg?.getAttribute('role')).toBe('img');
      expect(svg?.getAttribute('aria-label')).toContain('Isochrone overlay');
    });
  });

  it('renders correct number of polygon paths', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay map={mockMap} getFeatures={getFeatures} />
      </ThemeProvider>
    );

    await waitFor(() => {
      const paths = container.querySelectorAll('.polygons path');
      expect(paths.length).toBe(3);
    });
  });

  it('applies spot color to features matching predicate', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay
          map={mockMap}
          getFeatures={getFeatures}
          spotPredicate={(f) => f.properties?.isMax === true}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      const spotOutlines = container.querySelectorAll('.spot-outlines path');
      expect(spotOutlines.length).toBe(1);
    });
  });

  it('renders labels with correct text', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay
          map={mockMap}
          getFeatures={getFeatures}
          labelAccessor={(f) => `${f.properties?.minutes} min`}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      const labels = container.querySelectorAll('.labels text');
      expect(labels.length).toBeGreaterThan(0);

      const labelTexts = Array.from(labels).map((l) => l.textContent || '');
      // Labels include title elements, so check if text starts with expected value
      expect(labelTexts.some(t => t.startsWith('10 min'))).toBe(true);
      expect(labelTexts.some(t => t.startsWith('20 min'))).toBe(true);
      expect(labelTexts.some(t => t.startsWith('30 min'))).toBe(true);
    });
  });

  it('calls onHover callback when hovering polygons', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;
    const onHover = vi.fn();

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay map={mockMap} getFeatures={getFeatures} onHover={onHover} />
      </ThemeProvider>
    );

    await waitFor(() => {
      const paths = container.querySelectorAll('.polygons path');
      expect(paths.length).toBe(3);

      // Simulate hover
      const firstPath = paths[0] as SVGPathElement;
      firstPath.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));

      expect(onHover).toHaveBeenCalled();
    });
  });

  it('registers map event listeners for zoom and move', () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    render(
      <ThemeProvider>
        <LeafletD3Overlay map={mockMap} getFeatures={getFeatures} />
      </ThemeProvider>
    );

    expect(mockMap.on).toHaveBeenCalledWith('zoom', expect.any(Function));
    expect(mockMap.on).toHaveBeenCalledWith('move', expect.any(Function));
  });

  it('verifies no gridlines are present (brand compliance)', async () => {
    const mockMap = createMockMap();
    const getFeatures = async () => stubFeatures;

    const { container } = render(
      <ThemeProvider>
        <LeafletD3Overlay map={mockMap} getFeatures={getFeatures} />
      </ThemeProvider>
    );

    await waitFor(() => {
      const gridElements = container.querySelectorAll('.grid, [class*="grid"]');
      expect(gridElements.length).toBe(0);
    });
  });
});
