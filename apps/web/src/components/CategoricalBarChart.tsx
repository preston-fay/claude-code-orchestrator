import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useTheme } from '../contexts/ThemeContext';
import {
  createResponsiveSVG,
  addMarkLabel,
  verifyNoGridlines,
  formatNumber,
  ChartConfig,
} from '../design-system/d3_theme';
import { getThemeColors, CATEGORICAL_PRIMARY } from '../design-system/tokens';

export interface CategoricalDataPoint {
  category: string;
  value: number;
  highlight?: boolean;
}

export interface CategoricalBarChartProps {
  data: CategoricalDataPoint[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
  width?: number;
  height?: number;
  horizontal?: boolean;
  sorted?: boolean;
  className?: string;
}

/**
 * Categorical Bar Chart Component
 *
 * CRITICAL BRAND REQUIREMENTS:
 * - NO GRIDLINES (verified programmatically)
 * - Labels directly on bars (label-first approach)
 * - Ranked/sorted by default
 * - Minimal axes (top and right removed)
 * - Spot color for highlighted categories
 */
export function CategoricalBarChart({
  data,
  title,
  xLabel,
  yLabel,
  width = 800,
  height = 400,
  horizontal = false,
  sorted = true,
  className = '',
}: CategoricalBarChartProps) {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const colors = getThemeColors(theme);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    // Clear previous chart
    d3.select(containerRef.current).selectAll('*').remove();

    // Sort data if requested
    const chartData = sorted
      ? [...data].sort((a, b) => b.value - a.value)
      : data;

    // Configuration
    const config: ChartConfig = {
      theme,
      width,
      height,
      marginTop: 40,
      marginRight: 40,
      marginBottom: horizontal ? 60 : 80,
      marginLeft: horizontal ? 120 : 70,
    };

    // Create SVG
    const svg = createResponsiveSVG(containerRef.current, config);

    if (horizontal) {
      // Horizontal bar chart
      const xScale = d3
        .scaleLinear()
        .domain([0, d3.max(chartData, (d) => d.value) || 0])
        .nice()
        .range([config.marginLeft!, width - config.marginRight!]);

      const yScale = d3
        .scaleBand()
        .domain(chartData.map((d) => d.category))
        .range([config.marginTop!, height - config.marginBottom!])
        .padding(0.2);

      // Draw bars
      svg
        .selectAll('rect')
        .data(chartData)
        .join('rect')
        .attr('x', config.marginLeft!)
        .attr('y', (d) => yScale(d.category)!)
        .attr('width', (d) => xScale(d.value) - config.marginLeft!)
        .attr('height', yScale.bandwidth())
        .attr('fill', (d, i) =>
          d.highlight ? colors.spotColor : CATEGORICAL_PRIMARY[i % CATEGORICAL_PRIMARY.length]
        )
        .attr('opacity', (d) => (d.highlight ? 1 : 0.8));

      // Add value labels on bars
      svg
        .selectAll('.bar-label')
        .data(chartData)
        .join('text')
        .attr('class', 'bar-label')
        .attr('x', (d) => xScale(d.value) + 5)
        .attr('y', (d) => yScale(d.category)! + yScale.bandwidth() / 2)
        .attr('dominant-baseline', 'middle')
        .style('fill', colors.text)
        .style('font-size', '13px')
        .style('font-weight', 600)
        .text((d) => formatNumber(d.value));

      // Draw Y axis (categories)
      const yAxis = d3.axisLeft(yScale).tickSize(0);

      svg
        .append('g')
        .attr('transform', `translate(${config.marginLeft}, 0)`)
        .call(yAxis)
        .selectAll('text')
        .style('fill', colors.textMuted)
        .style('font-size', '13px')
        .style('font-weight', 500);

      svg.select('.domain').remove();

      // X axis label
      if (xLabel) {
        svg
          .append('text')
          .attr('x', width / 2)
          .attr('y', height - 10)
          .attr('text-anchor', 'middle')
          .style('fill', colors.textMuted)
          .style('font-size', '13px')
          .style('font-weight', 500)
          .text(xLabel);
      }
    } else {
      // Vertical bar chart
      const xScale = d3
        .scaleBand()
        .domain(chartData.map((d) => d.category))
        .range([config.marginLeft!, width - config.marginRight!])
        .padding(0.2);

      const yScale = d3
        .scaleLinear()
        .domain([0, d3.max(chartData, (d) => d.value) || 0])
        .nice()
        .range([height - config.marginBottom!, config.marginTop!]);

      // Draw bars
      svg
        .selectAll('rect')
        .data(chartData)
        .join('rect')
        .attr('x', (d) => xScale(d.category)!)
        .attr('y', (d) => yScale(d.value))
        .attr('width', xScale.bandwidth())
        .attr('height', (d) => height - config.marginBottom! - yScale(d.value))
        .attr('fill', (d, i) =>
          d.highlight ? colors.spotColor : CATEGORICAL_PRIMARY[i % CATEGORICAL_PRIMARY.length]
        )
        .attr('opacity', (d) => (d.highlight ? 1 : 0.8));

      // Add value labels on top of bars
      svg
        .selectAll('.bar-label')
        .data(chartData)
        .join('text')
        .attr('class', 'bar-label')
        .attr('x', (d) => xScale(d.category)! + xScale.bandwidth() / 2)
        .attr('y', (d) => yScale(d.value) - 5)
        .attr('text-anchor', 'middle')
        .style('fill', colors.text)
        .style('font-size', '13px')
        .style('font-weight', 600)
        .text((d) => formatNumber(d.value));

      // Draw X axis (categories)
      const xAxis = d3.axisBottom(xScale).tickSize(0);

      svg
        .append('g')
        .attr('transform', `translate(0, ${height - config.marginBottom!})`)
        .call(xAxis)
        .selectAll('text')
        .style('fill', colors.textMuted)
        .style('font-size', '12px')
        .style('font-weight', 500)
        .attr('transform', 'rotate(-45)')
        .attr('text-anchor', 'end');

      svg.select('.domain').remove();

      // Y axis label
      if (yLabel) {
        svg
          .append('text')
          .attr('transform', 'rotate(-90)')
          .attr('x', -(height / 2))
          .attr('y', 15)
          .attr('text-anchor', 'middle')
          .style('fill', colors.textMuted)
          .style('font-size', '13px')
          .style('font-weight', 500)
          .text(yLabel);
      }
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
      console.warn('Gridlines were detected and removed from CategoricalBarChart');
    }

    // Cleanup
    return () => {
      d3.select(containerRef.current).selectAll('*').remove();
    };
  }, [data, theme, title, xLabel, yLabel, width, height, horizontal, sorted]);

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
