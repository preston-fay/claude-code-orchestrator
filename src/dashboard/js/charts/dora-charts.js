/**
 * DORA Metrics Charts
 *
 * Visualizations for DORA metrics:
 * - Deployment Frequency
 * - Lead Time for Changes
 * - Mean Time to Recovery
 * - Change Failure Rate
 */

import { getLineChartConfig, getBarChartConfig, COLORS, formatDuration, formatPercentage } from '../chart-config.js';
import { createTimeSeriesData, aggregateByWeek, lastN } from './data-utils.js';

/**
 * Create Deployment Frequency Chart
 */
export function createDeploymentFrequencyChart(canvas, metricsData, isDark) {
    const deployments = metricsData.dora?.deployments?.deployments || [];

    if (deployments.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No deployment data available</p>';
        return null;
    }

    // Aggregate deployments by week
    const weekData = aggregateByWeek(deployments, 'timestamp', 'version', 'count');

    // Take last 12 weeks
    const recentLabels = lastN(weekData.labels, 12);
    const recentData = lastN(weekData.data, 12);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'Deploys per Week',
            data: recentData,
            borderColor: COLORS.purple,
            backgroundColor: COLORS.purple20,
            fill: true,
            tension: 0.3
        }]
    };

    const options = {
        ...config.options,
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        return `${context.parsed.y} deploys`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Deploys per Week'
                }
            }
        }
    };

    return new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: options
    });
}

/**
 * Create Lead Time Chart
 */
export function createLeadTimeChart(canvas, metricsData, isDark) {
    const leadTimes = metricsData.dora?.leadTime?.lead_times || [];

    if (leadTimes.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No lead time data available. Requires multiple deployments.</p>';
        return null;
    }

    const seriesData = createTimeSeriesData(leadTimes, 'committed_at', 'lead_time_hours');

    // Take last 20 data points
    const recentLabels = lastN(seriesData.labels, 20);
    const recentData = lastN(seriesData.data, 20);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'Lead Time',
            data: recentData,
            borderColor: COLORS.purpleLight,
            backgroundColor: COLORS.purple20,
            fill: false,
            tension: 0.3
        }]
    };

    const options = {
        ...config.options,
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        return `${formatDuration(context.parsed.y)}`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Hours'
                }
            }
        }
    };

    return new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: options
    });
}

/**
 * Create MTTR Chart
 */
export function createMTTRChart(canvas, metricsData, isDark) {
    const incidents = metricsData.dora?.mttr?.incidents || [];

    if (incidents.length === 0) {
        // Show "elite" status when no incidents
        canvas.parentElement.innerHTML = '<p class="no-data">No incidents recorded (Elite DORA rating)</p>';
        return null;
    }

    // Sort by detection date
    const sorted = [...incidents].sort((a, b) => {
        return new Date(a.detected_at) - new Date(b.detected_at);
    });

    const labels = sorted.map((incident, i) => `Incident ${i + 1}`);
    const data = sorted.map(incident => incident.resolution_time_hours || 0);

    const config = getBarChartConfig(isDark);

    const chartData = {
        labels: labels,
        datasets: [{
            label: 'Resolution Time',
            data: data,
            backgroundColor: COLORS.purpleDark,
            borderColor: COLORS.purple,
            borderWidth: 1
        }]
    };

    const options = {
        ...config.options,
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        return `${formatDuration(context.parsed.y)}`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Resolution Time (hours)'
                }
            }
        }
    };

    return new Chart(canvas, {
        type: 'bar',
        data: chartData,
        options: options
    });
}

/**
 * Create Change Failure Rate Chart
 */
export function createChangeFailureRateChart(canvas, metricsData, isDark) {
    const failures = metricsData.dora?.changeFailureRate?.failures || [];

    if (failures.length === 0) {
        // Show current failure rate from summary
        const failureRate = metricsData.dora?.changeFailureRate?.summary?.failure_rate || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Current Failure Rate: ${formatPercentage(failureRate)}</p>`;
        return null;
    }

    // Create time series from failures
    const seriesData = createTimeSeriesData(failures, 'detected_at', 'failure_rate');

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: seriesData.labels,
        datasets: [{
            label: 'Failure Rate',
            data: seriesData.data,
            borderColor: COLORS.purple,
            backgroundColor: COLORS.purple20,
            fill: true,
            tension: 0.3
        }]
    };

    const options = {
        ...config.options,
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        return `${formatPercentage(context.parsed.y)}`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                max: 100,
                title: {
                    display: true,
                    text: 'Failure Rate %'
                }
            }
        }
    };

    return new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: options
    });
}
