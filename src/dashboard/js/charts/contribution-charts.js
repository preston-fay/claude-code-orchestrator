/**
 * AI Contribution Charts
 *
 * Visualizations for AI contribution metrics:
 * - Attribution Pie Chart
 * - Contribution Trend Stacked Area
 * - Commit Distribution Bar Chart
 */

import { getPieChartConfig, getStackedAreaConfig, getBarChartConfig, COLORS, formatNumber, formatPercentage } from '../chart-config.js';
import { groupByWeek, lastN } from './data-utils.js';

/**
 * Create Attribution Pie Chart
 * Shows distribution of human/ai/collaborative contributions
 */
export function createAttributionPieChart(canvas, metricsData, isDark) {
    const summary = metricsData.contributions?.summary;

    if (!summary || summary.total_commits === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No contribution data available</p>';
        return null;
    }

    const config = getPieChartConfig(isDark);

    const chartData = {
        labels: ['Human', 'AI', 'Collaborative'],
        datasets: [{
            label: 'Contribution Type',
            data: [
                summary.human_percentage || 0,
                summary.ai_percentage || 0,
                summary.collaborative_percentage || 0
            ],
            backgroundColor: [
                COLORS.purpleDark,
                COLORS.purple,
                COLORS.purpleLight
            ],
            borderWidth: 0
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
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        return `${label}: ${formatPercentage(value)}`;
                    }
                }
            }
        }
    };

    return new Chart(canvas, {
        type: 'doughnut',
        data: chartData,
        options: options
    });
}

/**
 * Create Contribution Trend Stacked Area Chart
 * Shows lines of code contributed over time by type
 */
export function createContributionTrendChart(canvas, metricsData, isDark) {
    const commits = metricsData.contributions?.commits || [];

    if (commits.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No commit data available</p>';
        return null;
    }

    // Group commits by week and sum lines_added by contributor_type
    const grouped = groupByWeek(commits, 'committed_at');
    const weeks = Array.from(grouped.keys()).sort();

    // Take last 12 weeks
    const recentWeeks = lastN(weeks, 12);

    const humanData = [];
    const aiData = [];
    const collaborativeData = [];

    recentWeeks.forEach(week => {
        const weekCommits = grouped.get(week) || [];

        const humanLines = weekCommits
            .filter(c => c.contributor_type === 'human')
            .reduce((sum, c) => sum + (c.lines_added || 0), 0);

        const aiLines = weekCommits
            .filter(c => c.contributor_type === 'ai')
            .reduce((sum, c) => sum + (c.lines_added || 0), 0);

        const collabLines = weekCommits
            .filter(c => c.contributor_type === 'collaborative')
            .reduce((sum, c) => sum + (c.lines_added || 0), 0);

        humanData.push(humanLines);
        aiData.push(aiLines);
        collaborativeData.push(collabLines);
    });

    const labels = recentWeeks.map(w => {
        const [year, week] = w.split('-W');
        return `Week ${week}`;
    });

    const config = getStackedAreaConfig(isDark);

    const chartData = {
        labels: labels,
        datasets: [
            {
                label: 'Human',
                data: humanData,
                borderColor: COLORS.purpleDark,
                backgroundColor: 'rgba(90, 26, 168, 0.6)',
                fill: true,
                tension: 0.3
            },
            {
                label: 'AI',
                data: aiData,
                borderColor: COLORS.purple,
                backgroundColor: COLORS.purple50,
                fill: true,
                tension: 0.3
            },
            {
                label: 'Collaborative',
                data: collaborativeData,
                borderColor: COLORS.purpleLight,
                backgroundColor: 'rgba(155, 81, 224, 0.4)',
                fill: true,
                tension: 0.3
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
                        return `${label}: ${formatNumber(value, 0)} lines`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            y: {
                ...config.options.scales.y,
                beginAtZero: true,
                stacked: true,
                title: {
                    display: true,
                    text: 'Lines Added'
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
 * Create Commit Distribution Bar Chart
 * Shows commit counts by contributor type
 */
export function createCommitDistributionChart(canvas, metricsData, isDark) {
    const commits = metricsData.contributions?.commits || [];

    if (commits.length === 0) {
        canvas.parentElement.innerHTML = '<p class="no-data">No commit data available</p>';
        return null;
    }

    // Count commits by type
    const humanCount = commits.filter(c => c.contributor_type === 'human').length;
    const aiCount = commits.filter(c => c.contributor_type === 'ai').length;
    const collabCount = commits.filter(c => c.contributor_type === 'collaborative').length;
    const total = commits.length;

    const config = getBarChartConfig(isDark);

    const chartData = {
        labels: ['Human', 'AI', 'Collaborative'],
        datasets: [{
            label: 'Commit Count',
            data: [humanCount, aiCount, collabCount],
            backgroundColor: [
                COLORS.purpleDark,
                COLORS.purple,
                COLORS.purpleLight
            ],
            borderWidth: 0
        }]
    };

    const options = {
        ...config.options,
        indexAxis: 'y', // Horizontal bars
        plugins: {
            ...config.options.plugins,
            tooltip: {
                ...config.options.plugins.tooltip,
                callbacks: {
                    label: (context) => {
                        const value = context.parsed.x || 0;
                        const percentage = total > 0 ? (value / total * 100) : 0;
                        return `${value} commits (${formatPercentage(percentage)})`;
                    }
                }
            }
        },
        scales: {
            ...config.options.scales,
            x: {
                ...config.options.scales.x,
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Number of Commits'
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
