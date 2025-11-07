/**
 * Dashboard Main Controller
 *
 * Orchestrates the metrics dashboard:
 * - Loads metrics data
 * - Initializes charts
 * - Handles theme changes
 * - Updates UI elements
 */

import themeManager from './theme-manager.js';
import { loadAllMetrics, getCollectionTimestamp } from './metrics-loader.js';
import { getThemeColors, updateChartTheme, formatNumber, formatPercentage, formatDuration } from './chart-config.js';
import { setupExportButton, setupChartDownloadButtons } from './exporters.js';

class Dashboard {
    constructor() {
        this.metrics = null;
        this.charts = {};
    }

    /**
     * Initialize dashboard
     */
    async init() {
        console.log('Initializing dashboard...');

        try {
            // Load metrics data
            this.metrics = await loadAllMetrics();

            // Update hero metrics
            this.updateHeroMetrics();

            // Update last updated timestamp
            this.updateLastUpdated();

            // Initialize all charts
            this.initializeCharts();

            // Setup theme change listener
            this.setupThemeListener();

            // Setup export button
            this.setupExportButton();

            // Setup chart download buttons
            setupChartDownloadButtons();

            console.log('Dashboard initialized successfully');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('Failed to load metrics data. Please refresh the page.');
        }
    }

    /**
     * Update hero metrics cards
     */
    updateHeroMetrics() {
        // DORA Rating
        const doraRating = this.metrics.dora.deployments?.summary?.rating || 'low';
        const doraRatingEl = document.getElementById('dora-rating');
        if (doraRatingEl) {
            doraRatingEl.querySelector('.hero-value').textContent = doraRating.toUpperCase();
            doraRatingEl.querySelector('.hero-label').textContent = 'DORA Rating';
        }

        // Deployment Frequency
        const deployFreq = this.metrics.dora.deployments?.summary?.deploys_per_week || 0;
        const deployFreqEl = document.getElementById('deploy-freq');
        if (deployFreqEl) {
            deployFreqEl.querySelector('.hero-value').textContent = formatNumber(deployFreq, 1);
            deployFreqEl.querySelector('.hero-label').textContent = 'deploys/week';
        }

        // AI Contribution
        const collaborativePercent = this.metrics.contributions?.summary?.collaborative_percentage || 0;
        const aiContribEl = document.getElementById('ai-contribution');
        if (aiContribEl) {
            aiContribEl.querySelector('.hero-value').textContent = formatNumber(collaborativePercent, 1);
            aiContribEl.querySelector('.hero-label').textContent = '% collaborative';
        }

        // Review Coverage
        const reviewCoverage = this.metrics.aiReview?.summary?.review_coverage || 0;
        const reviewCoverageEl = document.getElementById('review-coverage');
        if (reviewCoverageEl) {
            reviewCoverageEl.querySelector('.hero-value').textContent = formatNumber(reviewCoverage, 1);
            reviewCoverageEl.querySelector('.hero-label').textContent = '% PRs reviewed';
        }
    }

    /**
     * Update last updated timestamp
     */
    updateLastUpdated() {
        const timestamp = getCollectionTimestamp(this.metrics);
        const lastUpdatedEl = document.getElementById('last-updated');

        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = timestamp.toLocaleString('en-US', {
                dateStyle: 'medium',
                timeStyle: 'short'
            });
        }
    }

    /**
     * Setup theme change listener
     */
    setupThemeListener() {
        window.addEventListener('themeChanged', (event) => {
            const isDark = event.detail.theme === 'dark';
            console.log(`Theme changed to: ${event.detail.theme}`);

            // Update all charts
            Object.values(this.charts).forEach(chart => {
                if (chart) {
                    updateChartTheme(chart, isDark);
                }
            });
        });
    }

    /**
     * Setup export data button
     */
    setupExportButton() {
        const exportButton = document.getElementById('export-data');

        if (exportButton) {
            setupExportButton(exportButton, this.metrics);
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;

        const main = document.querySelector('.dashboard-main');
        if (main) {
            main.insertBefore(errorDiv, main.firstChild);
        }
    }

    /**
     * Initialize all charts
     */
    initializeCharts() {
        const isDark = themeManager.currentTheme === 'dark';

        // Import chart creation functions
        import('./charts/dora-charts.js').then(module => {
            this.charts['chart-deploy-frequency'] = module.createDeploymentFrequencyChart(
                document.getElementById('chart-deploy-frequency'),
                this.metrics,
                isDark
            );

            this.charts['chart-lead-time'] = module.createLeadTimeChart(
                document.getElementById('chart-lead-time'),
                this.metrics,
                isDark
            );

            this.charts['chart-mttr'] = module.createMTTRChart(
                document.getElementById('chart-mttr'),
                this.metrics,
                isDark
            );

            this.charts['chart-change-failure-rate'] = module.createChangeFailureRateChart(
                document.getElementById('chart-change-failure-rate'),
                this.metrics,
                isDark
            );
        });

        import('./charts/github-charts.js').then(module => {
            this.charts['chart-pr-cycle-time'] = module.createPRCycleTimeChart(
                document.getElementById('chart-pr-cycle-time'),
                this.metrics,
                isDark
            );

            this.charts['chart-merge-conflicts'] = module.createMergeConflictsChart(
                document.getElementById('chart-merge-conflicts'),
                this.metrics,
                isDark
            );

            this.charts['chart-feature-velocity'] = module.createFeatureVelocityChart(
                document.getElementById('chart-feature-velocity'),
                this.metrics,
                isDark
            );
        });

        import('./charts/contribution-charts.js').then(module => {
            this.charts['chart-attribution'] = module.createAttributionPieChart(
                document.getElementById('chart-attribution'),
                this.metrics,
                isDark
            );

            this.charts['chart-contribution-trend'] = module.createContributionTrendChart(
                document.getElementById('chart-contribution-trend'),
                this.metrics,
                isDark
            );

            this.charts['chart-commit-distribution'] = module.createCommitDistributionChart(
                document.getElementById('chart-commit-distribution'),
                this.metrics,
                isDark
            );
        });

        import('./charts/ai-review-charts.js').then(module => {
            this.charts['chart-review-coverage'] = module.createReviewCoverageChart(
                document.getElementById('chart-review-coverage'),
                this.metrics,
                isDark
            );

            this.charts['chart-suggestions-per-pr'] = module.createSuggestionsPerPRChart(
                document.getElementById('chart-suggestions-per-pr'),
                this.metrics,
                isDark
            );

            this.charts['chart-acceptance-rate'] = module.createAcceptanceRateTrendChart(
                document.getElementById('chart-acceptance-rate'),
                this.metrics,
                isDark
            );

            this.charts['chart-response-time'] = module.createResponseTimeDistributionChart(
                document.getElementById('chart-response-time'),
                this.metrics,
                isDark
            );
        });
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.init();

    // Make dashboard available globally for debugging
    window.dashboard = dashboard;
});
