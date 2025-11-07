/**
 * Export Utilities
 *
 * Functions for exporting metrics data:
 * - CSV export (all metrics)
 * - PNG export (individual charts)
 */

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Check if current theme is dark
 */
function isDarkTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

/**
 * Sanitize text for CSV (escape commas, quotes, newlines)
 */
function sanitizeCSV(text) {
    if (text === null || text === undefined) {
        return '';
    }

    const str = String(text);

    // If contains comma, quote, or newline, wrap in quotes and escape quotes
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
    }

    return str;
}

/**
 * Show temporary feedback on export button
 */
function showExportFeedback(button) {
    const originalText = button.textContent;

    button.textContent = 'Exporting...';
    button.disabled = true;

    setTimeout(() => {
        button.textContent = 'Exported!';

        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 1000);
    }, 500);
}

/**
 * Export all metrics to CSV
 */
export function exportToCSV(metricsData) {
    try {
        if (!metricsData) {
            console.error('No metrics data available for export');
            return;
        }

        const rows = [];
        const currentDate = formatDate(new Date());

        // CSV Header
        rows.push(['Date', 'Metric Category', 'Metric Name', 'Value', 'Unit']);

        // DORA Metrics
        if (metricsData.dora) {
            const dora = metricsData.dora;

            // Deployment Frequency
            if (dora.deployments?.summary) {
                const s = dora.deployments.summary;
                rows.push([currentDate, 'DORA', 'Total Deployments', s.total_deployments || 0, 'count']);
                rows.push([currentDate, 'DORA', 'Deploys per Week', s.deploys_per_week?.toFixed(1) || 0, 'deploys/week']);
                rows.push([currentDate, 'DORA', 'DORA Rating', s.rating || 'unknown', 'rating']);
            }

            // Lead Time
            if (dora.leadTime?.summary) {
                const s = dora.leadTime.summary;
                rows.push([currentDate, 'DORA', 'Median Lead Time', s.median_lead_time_hours?.toFixed(1) || 0, 'hours']);
                rows.push([currentDate, 'DORA', 'P95 Lead Time', s.p95_lead_time_hours?.toFixed(1) || 0, 'hours']);
            }

            // MTTR
            if (dora.mttr?.summary) {
                const s = dora.mttr.summary;
                rows.push([currentDate, 'DORA', 'Total Incidents', s.total_incidents || 0, 'count']);
                rows.push([currentDate, 'DORA', 'Median Resolution Time', s.median_resolution_time_hours?.toFixed(1) || 0, 'hours']);
            }

            // Change Failure Rate
            if (dora.changeFailureRate?.summary) {
                const s = dora.changeFailureRate.summary;
                rows.push([currentDate, 'DORA', 'Total Failures', s.total_failures || 0, 'count']);
                rows.push([currentDate, 'DORA', 'Failure Rate', s.failure_rate?.toFixed(1) || 0, '%']);
            }
        }

        // GitHub Metrics
        if (metricsData.github) {
            const github = metricsData.github;

            // Pull Requests
            if (github.pullRequests?.summary) {
                const s = github.pullRequests.summary;
                rows.push([currentDate, 'GitHub', 'Total PRs', s.total_prs || 0, 'count']);
                rows.push([currentDate, 'GitHub', 'Median Cycle Time', s.median_cycle_time_hours?.toFixed(1) || 0, 'hours']);
                rows.push([currentDate, 'GitHub', 'Open PRs', s.open_prs || 0, 'count']);
                rows.push([currentDate, 'GitHub', 'Merged PRs', s.merged_prs || 0, 'count']);
            }

            // Conflicts
            if (github.conflicts?.summary) {
                const s = github.conflicts.summary;
                rows.push([currentDate, 'GitHub', 'Total Conflicts', s.total_conflicts || 0, 'count']);
                rows.push([currentDate, 'GitHub', 'Conflict Rate', s.conflict_rate?.toFixed(1) || 0, '%']);
            }

            // Velocity
            if (github.velocity?.summary) {
                const s = github.velocity.summary;
                rows.push([currentDate, 'GitHub', 'Avg Features per Week', s.avg_features_per_week?.toFixed(1) || 0, 'features/week']);
                rows.push([currentDate, 'GitHub', 'Avg Bugs per Week', s.avg_bugs_per_week?.toFixed(1) || 0, 'bugs/week']);
            }
        }

        // Contribution Metrics
        if (metricsData.contributions?.summary) {
            const s = metricsData.contributions.summary;
            rows.push([currentDate, 'Contributions', 'Total Commits', s.total_commits || 0, 'count']);
            rows.push([currentDate, 'Contributions', 'Human Commits', s.human_percentage?.toFixed(1) || 0, '%']);
            rows.push([currentDate, 'Contributions', 'AI Commits', s.ai_percentage?.toFixed(1) || 0, '%']);
            rows.push([currentDate, 'Contributions', 'Collaborative Commits', s.collaborative_percentage?.toFixed(1) || 0, '%']);
            rows.push([currentDate, 'Contributions', 'Human Lines Added', s.human_lines_added || 0, 'lines']);
            rows.push([currentDate, 'Contributions', 'AI Lines Added', s.ai_lines_added || 0, 'lines']);
            rows.push([currentDate, 'Contributions', 'Collaborative Lines Added', s.collaborative_lines_added || 0, 'lines']);
        }

        // AI Review Metrics
        if (metricsData.aiReview?.summary) {
            const s = metricsData.aiReview.summary;
            rows.push([currentDate, 'AI Review', 'Review Coverage', s.review_coverage?.toFixed(1) || 0, '%']);
            rows.push([currentDate, 'AI Review', 'Avg Suggestions per PR', s.avg_suggestions_per_pr?.toFixed(1) || 0, 'suggestions/PR']);
            rows.push([currentDate, 'AI Review', 'Avg Acceptance Rate', s.avg_acceptance_rate?.toFixed(1) || 0, '%']);
            rows.push([currentDate, 'AI Review', 'Avg Response Time', s.avg_response_time_hours?.toFixed(1) || 0, 'hours']);
        }

        // Convert to CSV string
        const csvContent = rows.map(row => row.map(sanitizeCSV).join(','));
        const csvString = csvContent.join('\n');

        // Add UTF-8 BOM for Excel compatibility
        const bom = '\ufeff';
        const blob = new Blob([bom + csvString], { type: 'text/csv;charset=utf-8;' });

        // Create download link
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = `metrics_export_${currentDate}.csv`;

        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up
        URL.revokeObjectURL(url);

        console.log('CSV export successful');

    } catch (error) {
        console.error('CSV export failed:', error);
    }
}

/**
 * Export chart as PNG image
 */
export function exportChartAsPNG(chartId, chartName) {
    try {
        // Get chart instance
        const chart = Chart.getChart(chartId);

        if (!chart) {
            console.error('Chart not found:', chartId);
            return;
        }

        // Determine background color based on theme
        const bgColor = isDarkTheme()
            ? 'rgba(26, 26, 26, 1)'  // Dark background
            : 'rgba(255, 255, 255, 1)'; // Light background

        // Save original background
        const originalBgColor = chart.options.plugins.backgroundColor;

        // Set background color plugin
        chart.options.plugins.backgroundColor = {
            color: bgColor
        };

        // Register background color plugin if not already registered
        if (!Chart.registry.plugins.get('backgroundColor')) {
            Chart.register({
                id: 'backgroundColor',
                beforeDraw: (chart, args, options) => {
                    const { ctx, chartArea } = chart;
                    if (options.color) {
                        ctx.save();
                        ctx.fillStyle = options.color;
                        ctx.fillRect(0, 0, chart.width, chart.height);
                        ctx.restore();
                    }
                }
            });
        }

        // Update chart to apply background
        chart.update('none');

        // Export as base64 PNG
        const url = chart.toBase64Image('image/png', 1.0);

        // Restore original background
        chart.options.plugins.backgroundColor = originalBgColor;
        chart.update('none');

        // Create download link
        const link = document.createElement('a');
        link.href = url;
        link.download = `${chartName}_${formatDate(new Date())}.png`;

        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log('PNG export successful:', chartName);

    } catch (error) {
        console.error('PNG export failed for chart:', chartId, error);
    }
}

/**
 * Wire export button to CSV export
 */
export function setupExportButton(button, metricsData) {
    if (!button) {
        console.warn('Export button not found');
        return;
    }

    button.addEventListener('click', () => {
        exportToCSV(metricsData);
        showExportFeedback(button);
    });
}

/**
 * Wire chart download buttons
 */
export function setupChartDownloadButtons() {
    // Mapping of button IDs to chart canvas IDs and names
    const chartMappings = [
        // DORA Charts
        { btnId: 'download-deploy-frequency', chartId: 'chart-deploy-frequency', name: 'deployment_frequency' },
        { btnId: 'download-lead-time', chartId: 'chart-lead-time', name: 'lead_time' },
        { btnId: 'download-mttr', chartId: 'chart-mttr', name: 'mttr' },
        { btnId: 'download-change-failure-rate', chartId: 'chart-change-failure-rate', name: 'change_failure_rate' },

        // GitHub Charts
        { btnId: 'download-pr-cycle-time', chartId: 'chart-pr-cycle-time', name: 'pr_cycle_time' },
        { btnId: 'download-merge-conflicts', chartId: 'chart-merge-conflicts', name: 'merge_conflicts' },
        { btnId: 'download-feature-velocity', chartId: 'chart-feature-velocity', name: 'feature_velocity' },

        // Contribution Charts
        { btnId: 'download-attribution', chartId: 'chart-attribution', name: 'contribution_attribution' },
        { btnId: 'download-contribution-trend', chartId: 'chart-contribution-trend', name: 'contribution_trend' },
        { btnId: 'download-commit-distribution', chartId: 'chart-commit-distribution', name: 'commit_distribution' },

        // AI Review Charts
        { btnId: 'download-review-coverage', chartId: 'chart-review-coverage', name: 'review_coverage' },
        { btnId: 'download-suggestions-per-pr', chartId: 'chart-suggestions-per-pr', name: 'suggestions_per_pr' },
        { btnId: 'download-acceptance-rate', chartId: 'chart-acceptance-rate', name: 'acceptance_rate' },
        { btnId: 'download-response-time', chartId: 'chart-response-time', name: 'response_time' }
    ];

    chartMappings.forEach(({ btnId, chartId, name }) => {
        const button = document.getElementById(btnId);

        if (button) {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                exportChartAsPNG(chartId, name);
            });
        }
    });
}
