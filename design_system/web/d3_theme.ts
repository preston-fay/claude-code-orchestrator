/**
 * Kearney Design System - D3 Chart Helpers
 *
 * Enforces brand requirements:
 * - NO GRIDLINES (critical requirement)
 * - Label-first approach (prefer mark labels over axis labels)
 * - Spot color emphasis for key insights
 * - Minimal axes (top and right removed)
 */

import * as d3 from 'd3';
import {
  Theme,
  getThemeColors,
  CATEGORICAL_PRIMARY,
  SEQUENTIAL_PURPLE,
  FONT_FAMILY_PRIMARY,
} from './tokens';

export interface ChartConfig {
  theme: Theme;
  width: number;
  height: number;
  marginTop?: number;
  marginRight?: number;
  marginBottom?: number;
  marginLeft?: number;
}

/**
 * Apply Kearney theme to D3 chart SVG
 * CRITICAL: Enforces NO GRIDLINES requirement
 */
export function applyKearneyStyling(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  config: ChartConfig
): void {
  const colors = getThemeColors(config.theme);

  // Set background (usually transparent for embedding)
  svg.style('background-color', 'transparent');
  svg.style('font-family', FONT_FAMILY_PRIMARY);
  svg.style('font-size', '14px');

  // Style all text elements
  svg.selectAll('text')
    .style('fill', colors.text)
    .style('font-family', FONT_FAMILY_PRIMARY);

  // Style axis lines (but NO grid lines!)
  svg.selectAll('.domain')
    .style('stroke', colors.border)
    .style('stroke-width', '1px');

  svg.selectAll('.tick line')
    .style('stroke', colors.border)
    .style('stroke-width', '1px');

  // CRITICAL: Ensure NO grid lines are rendered
  svg.selectAll('.grid').remove();
  svg.selectAll('[class*="grid"]').remove();
}

/**
 * Create minimal axes with NO GRIDLINES
 */
export function createMinimalAxes(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  config: ChartConfig,
  xScale: d3.AxisScale<any>,
  yScale: d3.AxisScale<any>,
  xLabel?: string,
  yLabel?: string
): void {
  const colors = getThemeColors(config.theme);
  const { marginBottom = 40, marginLeft = 60, height } = config;

  // Bottom axis (x)
  const xAxis = d3.axisBottom(xScale)
    .tickSize(6)
    .tickPadding(8);

  const xAxisGroup = svg.append('g')
    .attr('transform', `translate(0, ${height - marginBottom})`)
    .call(xAxis);

  xAxisGroup.selectAll('text')
    .style('fill', colors.textMuted)
    .style('font-size', '12px');

  xAxisGroup.selectAll('line')
    .style('stroke', colors.border);

  xAxisGroup.select('.domain')
    .style('stroke', colors.border);

  // X-axis label
  if (xLabel) {
    svg.append('text')
      .attr('x', config.width / 2)
      .attr('y', height - 5)
      .attr('text-anchor', 'middle')
      .style('fill', colors.textMuted)
      .style('font-size', '13px')
      .style('font-weight', 500)
      .text(xLabel);
  }

  // Left axis (y)
  const yAxis = d3.axisLeft(yScale)
    .tickSize(6)
    .tickPadding(8);

  const yAxisGroup = svg.append('g')
    .attr('transform', `translate(${marginLeft}, 0)`)
    .call(yAxis);

  yAxisGroup.selectAll('text')
    .style('fill', colors.textMuted)
    .style('font-size', '12px');

  yAxisGroup.selectAll('line')
    .style('stroke', colors.border);

  yAxisGroup.select('.domain')
    .style('stroke', colors.border);

  // Y-axis label
  if (yLabel) {
    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -(height / 2))
      .attr('y', 15)
      .attr('text-anchor', 'middle')
      .style('fill', colors.textMuted)
      .style('font-size', '13px')
      .style('font-weight', 500)
      .text(yLabel);
  }

  // CRITICAL: Remove top and right axes (minimal style)
  // NO GRID LINES - this is enforced by not creating them in the first place
}

/**
 * Add direct mark label to data point (label-first approach)
 */
export function addMarkLabel(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  x: number,
  y: number,
  text: string,
  theme: Theme,
  anchor: 'start' | 'middle' | 'end' = 'start',
  offsetX: number = 0,
  offsetY: number = 0
): void {
  const colors = getThemeColors(theme);

  svg.append('text')
    .attr('x', x + offsetX)
    .attr('y', y + offsetY)
    .attr('text-anchor', anchor)
    .style('fill', colors.text)
    .style('font-size', '13px')
    .style('font-weight', 600)
    .style('pointer-events', 'none')
    .text(text);
}

/**
 * Add spot color highlight to emphasize key data point
 */
export function addSpotColorHighlight(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  x: number,
  yStart: number,
  yEnd: number,
  theme: Theme,
  label?: string
): void {
  const colors = getThemeColors(theme);

  // Vertical line at x position
  svg.append('line')
    .attr('x1', x)
    .attr('x2', x)
    .attr('y1', yStart)
    .attr('y2', yEnd)
    .style('stroke', colors.spotColor)
    .style('stroke-width', '2px')
    .style('stroke-dasharray', '4,4')
    .style('opacity', 0.7);

  // Optional label
  if (label) {
    svg.append('text')
      .attr('x', x)
      .attr('y', yStart - 10)
      .attr('text-anchor', 'middle')
      .style('fill', colors.spotColor)
      .style('font-size', '12px')
      .style('font-weight', 600)
      .text(label);
  }
}

/**
 * Get categorical color scale using Kearney palette
 */
export function getCategoricalColorScale(domain: string[]): d3.ScaleOrdinal<string, string> {
  return d3.scaleOrdinal<string>()
    .domain(domain)
    .range(CATEGORICAL_PRIMARY);
}

/**
 * Get sequential color scale using purple gradient
 */
export function getSequentialColorScale(
  domain: [number, number]
): d3.ScaleSequential<string> {
  return d3.scaleSequential<string>()
    .domain(domain)
    .interpolator(d3.interpolateRgbBasis(SEQUENTIAL_PURPLE));
}

/**
 * Format large numbers with K/M/B suffixes
 */
export function formatNumber(value: number): string {
  if (Math.abs(value) >= 1e9) {
    return `${(value / 1e9).toFixed(1)}B`;
  }
  if (Math.abs(value) >= 1e6) {
    return `${(value / 1e6).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1e3) {
    return `${(value / 1e3).toFixed(1)}K`;
  }
  return value.toFixed(0);
}

/**
 * Prevent label collisions using force simulation
 */
export function preventLabelCollisions(
  labels: d3.Selection<SVGTextElement, any, SVGSVGElement, unknown>,
  width: number,
  height: number
): void {
  const labelNodes = labels.nodes().map((node, i) => {
    const bbox = node.getBBox();
    return {
      node,
      x: bbox.x + bbox.width / 2,
      y: bbox.y + bbox.height / 2,
      width: bbox.width,
      height: bbox.height,
    };
  });

  const simulation = d3.forceSimulation(labelNodes as any)
    .force('collision', d3.forceCollide().radius((d: any) => Math.max(d.width, d.height) / 2 + 2))
    .force('x', d3.forceX((d: any) => d.x).strength(0.1))
    .force('y', d3.forceY((d: any) => d.y).strength(0.1))
    .stop();

  for (let i = 0; i < 100; i++) {
    simulation.tick();
  }

  labelNodes.forEach((d: any) => {
    d3.select(d.node)
      .attr('x', d.x)
      .attr('y', d.y);
  });
}

/**
 * Create responsive chart container
 */
export function createResponsiveSVG(
  container: HTMLElement,
  config: ChartConfig
): d3.Selection<SVGSVGElement, unknown, null, undefined> {
  const svg = d3.select(container)
    .append('svg')
    .attr('width', config.width)
    .attr('height', config.height)
    .attr('viewBox', `0 0 ${config.width} ${config.height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet')
    .style('max-width', '100%')
    .style('height', 'auto');

  applyKearneyStyling(svg, config);

  return svg;
}

/**
 * CRITICAL: Verify NO gridlines are present
 * Use this function after chart creation to double-check
 */
export function verifyNoGridlines(svg: d3.Selection<SVGSVGElement, unknown, null, undefined>): boolean {
  const gridElements = svg.selectAll('.grid, [class*="grid"]');
  const hasGridlines = !gridElements.empty();

  if (hasGridlines) {
    console.error('VIOLATION: Gridlines detected in chart. Removing...');
    gridElements.remove();
    return false;
  }

  return true;
}
