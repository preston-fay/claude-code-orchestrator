/**
 * Metrics Loader
 *
 * Loads JSON metrics data from .claude/metrics/ directory.
 * Handles errors gracefully with fallback to empty data.
 */

const METRICS_BASE_PATH = '../../.claude/metrics';

/**
 * Load JSON file with error handling
 */
async function loadJSON(path) {
    try {
        const response = await fetch(path);

        if (!response.ok) {
            console.warn(`Failed to load ${path}: ${response.status}`);
            return null;
        }

        const data = await response.json();
        console.log(`Loaded: ${path}`);
        return data;

    } catch (error) {
        console.error(`Error loading ${path}:`, error);
        return null;
    }
}

/**
 * Load DORA metrics
 */
export async function loadDORAMetrics() {
    const deployments = await loadJSON(`${METRICS_BASE_PATH}/dora/deployments.json`);
    const leadTime = await loadJSON(`${METRICS_BASE_PATH}/dora/lead_time.json`);
    const mttr = await loadJSON(`${METRICS_BASE_PATH}/dora/mttr.json`);
    const changeFailureRate = await loadJSON(`${METRICS_BASE_PATH}/dora/change_failure_rate.json`);

    return {
        deployments: deployments || { summary: { total_deployments: 0, deploys_per_week: 0, rating: 'low' }, deployments: [] },
        leadTime: leadTime || { summary: { median_lead_time_hours: 0 }, lead_times: [] },
        mttr: mttr || { summary: { total_incidents: 0, median_resolution_time_hours: 0 }, incidents: [] },
        changeFailureRate: changeFailureRate || { summary: { failure_rate: 0 }, failures: [] }
    };
}

/**
 * Load GitHub collaboration metrics
 */
export async function loadGitHubMetrics() {
    const pullRequests = await loadJSON(`${METRICS_BASE_PATH}/github/pull_requests.json`);
    const conflicts = await loadJSON(`${METRICS_BASE_PATH}/github/conflicts.json`);
    const velocity = await loadJSON(`${METRICS_BASE_PATH}/github/velocity.json`);

    return {
        pullRequests: pullRequests || { summary: { median_cycle_time_hours: 0 }, pull_requests: [] },
        conflicts: conflicts || { summary: { total_conflicts: 0, conflict_rate: 0 }, conflicts: [] },
        velocity: velocity || { summary: { avg_features_per_week: 0, avg_bugs_per_week: 0 }, sprints: [] }
    };
}

/**
 * Load AI contribution metrics
 */
export async function loadContributionMetrics() {
    const data = await loadJSON(`${METRICS_BASE_PATH}/contributions/attribution.json`);

    return data || {
        summary: {
            total_commits: 0,
            human_percentage: 0,
            ai_percentage: 0,
            collaborative_percentage: 0,
            human_lines_added: 0,
            ai_lines_added: 0,
            collaborative_lines_added: 0
        },
        commits: []
    };
}

/**
 * Load AI review impact metrics
 */
export async function loadAIReviewMetrics() {
    const data = await loadJSON(`${METRICS_BASE_PATH}/ai_review/impact.json`);

    return data || {
        summary: {
            review_coverage: 0,
            avg_suggestions_per_pr: 0,
            avg_acceptance_rate: 0,
            avg_response_time_hours: 0
        },
        reviews: []
    };
}

/**
 * Load aggregated metrics (weekly/monthly summaries)
 */
export async function loadAggregatedMetrics() {
    const weekly = await loadJSON(`${METRICS_BASE_PATH}/aggregated/weekly_summary.json`);
    const monthly = await loadJSON(`${METRICS_BASE_PATH}/aggregated/monthly_summary.json`);
    const trends = await loadJSON(`${METRICS_BASE_PATH}/aggregated/trends.json`);

    return {
        weekly: weekly || [],
        monthly: monthly || [],
        trends: trends || {}
    };
}

/**
 * Load all metrics in parallel
 */
export async function loadAllMetrics() {
    console.log('Loading all metrics...');

    const [dora, github, contributions, aiReview, aggregated] = await Promise.all([
        loadDORAMetrics(),
        loadGitHubMetrics(),
        loadContributionMetrics(),
        loadAIReviewMetrics(),
        loadAggregatedMetrics()
    ]);

    console.log('All metrics loaded successfully');

    return {
        dora,
        github,
        contributions,
        aiReview,
        aggregated,
        lastUpdated: new Date().toISOString()
    };
}

/**
 * Get collection timestamp from metrics
 */
export function getCollectionTimestamp(metrics) {
    // Try to get timestamp from DORA metrics first
    if (metrics.dora?.deployments?.collection_timestamp) {
        return new Date(metrics.dora.deployments.collection_timestamp);
    }

    // Fallback to current time
    return new Date();
}
