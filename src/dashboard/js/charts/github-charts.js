/**
 * GitHub Collaboration Charts
 *
 * Visualizations for GitHub collaboration metrics:
 * - PR Cycle Time Trend
 * - Merge Conflicts Over Time
 * - Feature Velocity (Stacked Bar)
 */

import { getLineChartConfig, getStackedBarConfig, COLORS, formatDuration, formatNumber } from '../chart-config.js';
import { createTimeSeriesData, aggregateByWeek, lastN } from './data-utils.js';

/**
 * Create PR Cycle Time Chart
 * Shows median PR cycle time (creation to merge) over time
 */
export function createPRCycleTimeChart(canvas, metricsData, isDark) {
    const pullRequests = metricsData.github?.pullRequests?.pull_requests || [];

    if (pullRequests.length === 0) {
        const medianCycleTime = metricsData.github?.pullRequests?.summary?.median_cycle_time_hours || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Median Cycle Time: ${formatDuration(medianCycleTime)}</p>`;
        return null;
    }

    // Filter merged PRs with cycle time data
    const mergedPRs = pullRequests.filter(pr =>
        pr.state === 'closed' &&
        pr.merged_at &&
        pr.cycle_time_hours !== null
    );

    if (mergedPRs.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No merged PRs with cycle time data yet</p>';
        return null;
    }

    // Create time series
    const seriesData = createTimeSeriesData(mergedPRs, 'merged_at', 'cycle_time_hours');

    // Take last 20 data points
    const recentLabels = lastN(seriesData.labels, 20);
    const recentData = lastN(seriesData.data, 20);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'Cycle Time',
            data: recentData,
            borderColor: COLORS.purple,
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
 * Create Merge Conflicts Chart
 * Shows number of merge conflicts detected over time
 */
export function createMergeConflictsChart(canvas, metricsData, isDark) {
    const conflicts = metricsData.github?.conflicts?.conflicts || [];

    if (conflicts.length === 0) {
        const conflictRate = metricsData.github?.conflicts?.summary?.conflict_rate || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Conflict Rate: ${formatNumber(conflictRate, 1)}%</p>`;
        return null;
    }

    // Aggregate by week
    const weekData = aggregateByWeek(conflicts, 'detected_at', 'pr_number', 'count');

    // Take last 12 weeks
    const recentLabels = lastN(weekData.labels, 12);
    const recentData = lastN(weekData.data, 12);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'Conflicts Detected',
            data: recentData,
            borderColor: COLORS.purpleDark,
            backgroundColor: 'rgba(90, 26, 168, 0.3)',
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
                        return `${context.parsed.y} conflicts`;
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
                    text: 'Conflicts per Week'
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
 * Create Feature Velocity Chart
 * Shows features vs bugs completed per week (stacked bar)
 */
export function createFeatureVelocityChart(canvas, metricsData, isDark) {
    const sprints = metricsData.github?.velocity?.sprints || [];

    if (sprints.length === 0) {
        const avgFeatures = metricsData.github?.velocity?.summary?.avg_features_per_week || 0;
        const avgBugs = metricsData.github?.velocity?.summary?.avg_bugs_per_week || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Avg: ${formatNumber(avgFeatures, 1)} features, ${formatNumber(avgBugs, 1)} bugs/week</p>`;
        return null;
    }

    // Sort by week
    const sorted = [...sprints].sort((a, b) => {
        return a.week_start.localeCompare(b.week_start);
    });

    // Take last 12 weeks
    const recent = lastN(sorted, 12);

    const labels = recent.map(sprint => {
        const date = new Date(sprint.week_start);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const featureData = recent.map(sprint => sprint.features_completed || 0);
    const bugData = recent.map(sprint => sprint.bugs_fixed || 0);

    const config = getStackedBarConfig(isDark);

    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Features',
                data: featureData,
                backgroundColor: COLORS.purple,
                borderWidth: 0
            },
            {
                label: 'Bugs',
                data: bugData,
                backgroundColor: COLORS.purpleLight,
                borderWidth: 0
            }
        ]
    };

    const options = {
        ...config.options,
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        const label = context.dataset.label || '';
                        const value = context.parsed.y || 0;
                        return `${label}: ${value}`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            x: {
                ...config.options.scales.x,
                stacked: true
            },
            y: {
                ...config.options.scales.y,
                stacked: true,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Items Completed'
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
