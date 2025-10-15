import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import L from 'leaflet';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors, SEQUENTIAL_PURPLE } from '../design-system/tokens';
import { labelStyle, spotOutline } from '../design-system/d3_theme';
import type { FeatureCollection, Feature, Polygon, MultiPolygon } from 'geojson';

export type D3OverlayProps = {
  map: L.Map | null;
  getFeatures: () => Promise<FeatureCollection>;
  labelAccessor?: (f: Feature) => string;
  spotPredicate?: (f: Feature) => boolean;
  onHover?: (f: Feature | null) => void;
  onClick?: (f: Feature | null) => void;
};

interface LabelData {
  text: string;
  x: number;
  y: number;
  feature: Feature;
  isSpot: boolean;
}

/**
 * LeafletD3Overlay - D3 SVG overlay on Leaflet map
 *
 * Renders GeoJSON features with:
 * - Brand-colored fills (sequential purple ramp)
 * - Collision-avoided labels using D3 force simulation
 * - Spot color highlighting for key features
 * - Theme-aware styling (light/dark)
 * - Re-syncs on map zoom/pan
 */
export function LeafletD3Overlay({
  map,
  getFeatures,
  labelAccessor = (f) => `${f.properties?.minutes || '?'} min`,
  spotPredicate = (f) => f.properties?.isMax === true,
  onHover,
  onClick,
}: D3OverlayProps) {
  const { theme } = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  const [features, setFeatures] = useState<FeatureCollection | null>(null);
  const [labels, setLabels] = useState<LabelData[]>([]);

  // Load features
  useEffect(() => {
    let mounted = true;

    getFeatures().then((data) => {
      if (mounted) {
        setFeatures(data);
      }
    });

    return () => {
      mounted = false;
    };
  }, [getFeatures]);

  // Render overlay
  useEffect(() => {
    if (!map || !svgRef.current || !features) return;

    const svg = d3.select(svgRef.current);
    const colors = getThemeColors(theme);

    // Clear previous render
    svg.selectAll('*').remove();

    // Get map bounds
    const bounds = map.getBounds();
    const topLeft = map.latLngToLayerPoint(bounds.getNorthWest());
    const bottomRight = map.latLngToLayerPoint(bounds.getSouthEast());
    const width = bottomRight.x - topLeft.x;
    const height = bottomRight.y - topLeft.y;

    // Position SVG
    svg
      .attr('width', width)
      .attr('height', height)
      .style('position', 'absolute')
      .style('left', `${topLeft.x}px`)
      .style('top', `${topLeft.y}px`)
      .style('pointer-events', 'none')
      .attr('role', 'img')
      .attr('aria-label', 'Isochrone overlay with labeled zones');

    // Create projection: lat/lng -> SVG coords
    const projectPoint = (lon: number, lat: number): [number, number] => {
      const point = map.latLngToLayerPoint([lat, lon]);
      return [point.x - topLeft.x, point.y - topLeft.y];
    };

    const geoPath = d3.geoPath().projection(
      d3.geoTransform({
        point: function (lon, lat) {
          const [x, y] = projectPoint(lon, lat);
          this.stream.point(x, y);
        },
      })
    );

    // Color scale based on feature index
    const colorScale = d3
      .scaleSequential(d3.interpolateRgbBasis(SEQUENTIAL_PURPLE))
      .domain([0, features.features.length - 1]);

    // Draw polygons
    const polygonGroup = svg.append('g').attr('class', 'polygons');

    polygonGroup
      .selectAll('path')
      .data(features.features)
      .join('path')
      .attr('d', (d) => geoPath(d as any))
      .attr('fill', (d, i) => colorScale(i))
      .attr('fill-opacity', 0.3)
      .attr('stroke', colors.border)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6)
      .style('pointer-events', 'auto')
      .style('cursor', onClick ? 'pointer' : 'default')
      .on('mouseenter', function (event, d) {
        d3.select(this).attr('fill-opacity', 0.5);
        onHover?.(d as Feature);
      })
      .on('mouseleave', function (event, d) {
        d3.select(this).attr('fill-opacity', 0.3);
        onHover?.(null);
      })
      .on('click', (event, d) => {
        onClick?.(d as Feature);
      });

    // Spot color outlines
    const spotFeatures = features.features.filter((f) => spotPredicate(f as Feature));
    if (spotFeatures.length > 0) {
      const spotGroup = svg.append('g').attr('class', 'spot-outlines');
      const spotStyle = spotOutline(theme);

      spotGroup
        .selectAll('path')
        .data(spotFeatures)
        .join('path')
        .attr('d', (d) => geoPath(d as any))
        .attr('stroke', spotStyle.stroke as string)
        .attr('stroke-width', spotStyle.strokeWidth as number)
        .attr('stroke-dasharray', spotStyle.strokeDasharray as string)
        .attr('fill', 'none')
        .attr('opacity', spotStyle.opacity as number)
        .style('pointer-events', 'none');
    }

    // Prepare labels with centroids
    const labelData: LabelData[] = features.features.map((f) => {
      const centroid = geoPath.centroid(f as any);
      return {
        text: labelAccessor(f as Feature),
        x: centroid[0],
        y: centroid[1],
        feature: f as Feature,
        isSpot: spotPredicate(f as Feature),
      };
    });

    // Filter out invalid centroids
    const validLabels = labelData.filter((l) => !isNaN(l.x) && !isNaN(l.y));

    // Collision avoidance using D3 force simulation
    if (validLabels.length > 0) {
      const nodes = validLabels.map((l) => ({
        ...l,
        fx: null as number | null,
        fy: null as number | null,
        vx: 0,
        vy: 0,
      }));

      const simulation = d3
        .forceSimulation(nodes as any)
        .force('collision', d3.forceCollide().radius(25))
        .force('x', d3.forceX((d: any) => d.x).strength(0.1))
        .force('y', d3.forceY((d: any) => d.y).strength(0.1))
        .stop();

      // Run simulation synchronously
      for (let i = 0; i < 100; i++) {
        simulation.tick();
      }

      // Filter labels within viewport
      const finalLabels = nodes.filter(
        (n) => n.x >= 0 && n.x <= width && n.y >= 0 && n.y <= height
      );

      setLabels(finalLabels as LabelData[]);

      // Render labels
      const labelGroup = svg.append('g').attr('class', 'labels');
      const labelStyles = labelStyle(theme);

      labelGroup
        .selectAll('text')
        .data(finalLabels)
        .join('text')
        .attr('x', (d) => d.x)
        .attr('y', (d) => d.y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .text((d) => d.text)
        .attr('font-family', labelStyles.fontFamily as string)
        .attr('font-size', labelStyles.fontSize as string)
        .attr('font-weight', labelStyles.fontWeight as string)
        .attr('fill', labelStyles.fill as string)
        .attr('paint-order', labelStyles.paintOrder as string)
        .attr('stroke', labelStyles.stroke as string)
        .attr('stroke-width', labelStyles.strokeWidth as string)
        .attr('stroke-linecap', labelStyles.strokeLinecap as string)
        .attr('stroke-linejoin', labelStyles.strokeLinejoin as string)
        .style('pointer-events', 'none')
        .append('title')
        .text((d) => `${d.text} (${d.feature.properties?.profile || 'zone'})`);
    }
  }, [map, features, theme, labelAccessor, spotPredicate, onHover, onClick]);

  // Re-render on map events
  useEffect(() => {
    if (!map) return;

    const handleUpdate = () => {
      // Trigger re-render by updating key state
      setLabels((prev) => [...prev]);
    };

    map.on('zoom', handleUpdate);
    map.on('move', handleUpdate);

    return () => {
      map.off('zoom', handleUpdate);
      map.off('move', handleUpdate);
    };
  }, [map]);

  return (
    <svg
      ref={svgRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 400,
      }}
    />
  );
}
