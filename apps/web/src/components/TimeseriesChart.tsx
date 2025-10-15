import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useTheme } from '../contexts/ThemeContext';
import {
  createResponsiveSVG,
  createMinimalAxes,
  addMarkLabel,
  addSpotColorHighlight,
  verifyNoGridlines,
  ChartConfig,
} from '../design-system/d3_theme';
import { getThemeColors } from '../design-system/tokens';

export interface TimeseriesDataPoint {
  date: Date;
  value: number;
  label?: string;
}

export interface TimeseriesChartProps {
  data: TimeseriesDataPoint[];
  highlightData?: TimeseriesDataPoint[];
  spotHighlight?: {
    date: Date;
    label: string;
  };
  title?: string;
  xLabel?: string;
  yLabel?: string;
  width?: number;
  height?: number;
  className?: string;
}

/**
 * Timeseries Chart Component (NYT-style)
 *
 * CRITICAL BRAND REQUIREMENTS:
 * - NO GRIDLINES (verified programmatically)
 * - Muted series for context + spot color for highlight
 * - Direct mark labels (label-first approach)
 * - Minimal axes (top and right removed)
 */
export function TimeseriesChart({
  data,
  highlightData,
  spotHighlight,
  title,
  xLabel,
  yLabel,
  width = 800,
  height = 400,
  className = '',
}: TimeseriesChartProps) {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const colors = getThemeColors(theme);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    // Clear previous chart
    d3.select(containerRef.current).selectAll('*').remove();

    // Configuration
    const config: ChartConfig = {
      theme,
      width,
      height,
      marginTop: 40,
      marginRight: 40,
      marginBottom: 60,
      marginLeft: 70,
    };

    // Create SVG
    const svg = createResponsiveSVG(containerRef.current, config);

    // Scales
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(data, (d) => d.date) as [Date, Date])
      .range([config.marginLeft!, width - config.marginRight!]);

    const allValues = [
      ...data.map((d) => d.value),
      ...(highlightData || []).map((d) => d.value),
    ];
    const yScale = d3
      .scaleLinear()
      .domain([0, d3.max(allValues) || 0])
      .nice()
      .range([height - config.marginBottom!, config.marginTop!]);

    // Create axes (NO GRIDLINES!)
    createMinimalAxes(svg, config, xScale, yScale, xLabel, yLabel);

    // Line generator
    const line = d3
      .line<TimeseriesDataPoint>()
      .x((d) => xScale(d.date))
      .y((d) => yScale(d.value))
      .curve(d3.curveMonotoneX);

    // Draw muted context series (main data)
    svg
      .append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', colors.chartMuted)
      .attr('stroke-width', 2)
      .attr('d', line);

    // Draw highlighted series if provided
    if (highlightData && highlightData.length > 0) {
      svg
        .append('path')
        .datum(highlightData)
        .attr('fill', 'none')
        .attr('stroke', colors.spotColor)
        .attr('stroke-width', 3)
        .attr('d', line);

      // Add mark labels to highlight series
      highlightData.forEach((point) => {
        if (point.label) {
          addMarkLabel(
            svg,
            xScale(point.date),
            yScale(point.value),
            point.label,
            theme,
            'middle',
            0,
            -10
          );
        }
      });
    }

    // Add spot color highlight if specified
    if (spotHighlight) {
      addSpotColorHighlight(
        svg,
        xScale(spotHighlight.date),
        config.marginTop!,
        height - config.marginBottom!,
        theme,
        spotHighlight.label
      );
    }

    // Add title if provided
    if (title) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', 20)
        .attr('text-anchor', 'middle')
        .style('fill', colors.text)
        .style('font-size', '18px')
        .style('font-weight', 600)
        .text(title);
    }

    // CRITICAL: Verify NO gridlines are present
    const noGridlines = verifyNoGridlines(svg);
    if (!noGridlines) {
      console.warn('Gridlines were detected and removed from TimeseriesChart');
    }

    // Cleanup
    return () => {
      d3.select(containerRef.current).selectAll('*').remove();
    };
  }, [data, highlightData, spotHighlight, theme, title, xLabel, yLabel, width, height]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        backgroundColor: colors.surface,
        borderRadius: '8px',
        padding: '16px',
      }}
    />
  );
}
