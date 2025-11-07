/**
 * AI Review Impact Charts
 *
 * Visualizations for AI code review metrics:
 * - Review Coverage Over Time
 * - Suggestions Per PR
 * - Acceptance Rate Trend
 * - Response Time Distribution
 */

import { getLineChartConfig, getBarChartConfig, COLORS, formatNumber, formatPercentage, formatDuration } from '../chart-config.js';
import { createTimeSeriesData, aggregateByWeek, bucketValues, lastN } from './data-utils.js';

/**
 * Create Review Coverage Chart
 * Shows percentage of PRs receiving AI review over time
 */
export function createReviewCoverageChart(canvas, metricsData, isDark) {
    const reviews = metricsData.aiReview?.reviews || [];

    if (reviews.length === 0) {
        const coverage = metricsData.aiReview?.summary?.review_coverage || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Current Coverage: ${formatPercentage(coverage)}</p>`;
        return null;
    }

    // Aggregate by week: count PRs with reviews
    const weekData = aggregateByWeek(reviews, 'reviewed_at', 'pr_number', 'count');

    // Take last 12 weeks
    const recentLabels = lastN(weekData.labels, 12);
    const recentData = lastN(weekData.data, 12);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'PRs Reviewed',
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
                        return `${context.parsed.y} PRs reviewed`;
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
                    text: 'PRs Reviewed per Week'
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
 * Create Suggestions Per PR Chart
 * Shows distribution of suggestions across PRs
 */
export function createSuggestionsPerPRChart(canvas, metricsData, isDark) {
    const reviews = metricsData.aiReview?.reviews || [];

    if (reviews.length === 0) {
        const avgSuggestions = metricsData.aiReview?.summary?.avg_suggestions_per_pr || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Average: ${formatNumber(avgSuggestions, 1)} suggestions/PR</p>`;
        return null;
    }

    // Get suggestion counts
    const suggestionCounts = reviews.map(r => r.issues_found?.length || 0);

    // Bucket into ranges
    const buckets = [
        { min: 0, max: 3, label: '0-2' },
        { min: 3, max: 6, label: '3-5' },
        { min: 6, max: 11, label: '6-10' },
        { min: 11, max: 21, label: '11-20' },
        { min: 21, max: Infinity, label: '20+' }
    ];

    const bucketedData = bucketValues(suggestionCounts, buckets);

    const config = getBarChartConfig(isDark);

    const chartData = {
        labels: bucketedData.labels,
        datasets: [{
            label: 'Number of PRs',
            data: bucketedData.counts,
            backgroundColor: COLORS.purple,
            borderColor: COLORS.purpleDark,
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
                        return `${context.parsed.y} PRs`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            x: {
                ...config.options.scales.x,
                title: {
                    display: true,
                    text: 'Suggestions per PR'
                }
            },
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of PRs'
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
 * Create Acceptance Rate Trend Chart
 * Shows how acceptance rate changes over time
 */
export function createAcceptanceRateTrendChart(canvas, metricsData, isDark) {
    const reviews = metricsData.aiReview?.reviews || [];

    if (reviews.length === 0) {
        const avgAcceptance = metricsData.aiReview?.summary?.avg_acceptance_rate || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Average Acceptance: ${formatPercentage(avgAcceptance)}</p>`;
        return null;
    }

    // Filter reviews with acceptance rate data
    const reviewsWithAcceptance = reviews.filter(r => r.acceptance_rate !== null && r.acceptance_rate !== undefined);

    if (reviewsWithAcceptance.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No acceptance data available yet</p>';
        return null;
    }

    // Create time series
    const seriesData = createTimeSeriesData(reviewsWithAcceptance, 'reviewed_at', 'acceptance_rate');

    // Take last 20 data points
    const recentLabels = lastN(seriesData.labels, 20);
    const recentData = lastN(seriesData.data, 20);

    const config = getLineChartConfig(isDark);

    const chartData = {
        labels: recentLabels,
        datasets: [{
            label: 'Acceptance Rate',
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
                    text: 'Acceptance Rate %'
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
 * Create Response Time Distribution Chart
 * Shows histogram of response times
 */
export function createResponseTimeDistributionChart(canvas, metricsData, isDark) {
    const reviews = metricsData.aiReview?.reviews || [];

    if (reviews.length === 0) {
        const avgResponseTime = metricsData.aiReview?.summary?.avg_response_time_hours || 0;
        canvas.parentElement.innerHTML = `<p class="no-data">Average: ${formatDuration(avgResponseTime)}</p>`;
        return null;
    }

    // Filter reviews with response time data
    const reviewsWithResponseTime = reviews.filter(r => r.response_time_hours !== null && r.response_time_hours !== undefined);

    if (reviewsWithResponseTime.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No response time data available yet</p>';
        return null;
    }

    // Get response times
    const responseTimes = reviewsWithResponseTime.map(r => r.response_time_hours);

    // Bucket into time ranges
    const buckets = [
        { min: 0, max: 1, label: '< 1h' },
        { min: 1, max: 4, label: '1-4h' },
        { min: 4, max: 8, label: '4-8h' },
        { min: 8, max: 24, label: '8-24h' },
        { min: 24, max: Infinity, label: '> 24h' }
    ];

    const bucketedData = bucketValues(responseTimes, buckets);

    const config = getBarChartConfig(isDark);

    const chartData = {
        labels: bucketedData.labels,
        datasets: [{
            label: 'Number of Reviews',
            data: bucketedData.counts,
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
                        return `${context.parsed.y} reviews`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            x: {
                ...config.options.scales.x,
                title: {
                    display: true,
                    text: 'Response Time'
                }
            },
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of Reviews'
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
