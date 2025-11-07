/**
 * Data Transformation Utilities for Charts
 *
 * Common helper functions for transforming metrics data into Chart.js format.
 */

/**
 * Get ISO week string from date (YYYY-Wnn)
 */
function getWeekString(date) {
    const d = new Date(date);
    const oneJan = new Date(d.getFullYear(), 0, 1);
    const numberOfDays = Math.floor((d - oneJan) / (24 * 60 * 60 * 1000));
    const weekNumber = Math.ceil((numberOfDays + oneJan.getDay() + 1) / 7);
    return `${d.getFullYear()}-W${weekNumber.toString().padStart(2, '0')}`;
}

/**
 * Group items by week
 */
export function groupByWeek(items, dateField) {
    const grouped = new Map();

    items.forEach(item => {
        const date = item[dateField];
        if (!date) return;

        const weekKey = getWeekString(date);

        if (!grouped.has(weekKey)) {
            grouped.set(weekKey, []);
        }

        grouped.get(weekKey).push(item);
    });

    return grouped;
}

/**
 * Aggregate items by week
 */
export function aggregateByWeek(items, dateField, valueField, aggregateFn = 'sum') {
    const grouped = groupByWeek(items, dateField);
    const weeks = Array.from(grouped.keys()).sort();

    const data = weeks.map(week => {
        const weekItems = grouped.get(week);
        const values = weekItems.map(item => item[valueField] || 0);

        switch (aggregateFn) {
            case 'sum':
                return values.reduce((a, b) => a + b, 0);
            case 'avg':
                return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
            case 'count':
                return values.length;
            case 'max':
                return Math.max(...values, 0);
            case 'min':
                return Math.min(...values, 0);
            default:
                return 0;
        }
    });

    return {
        labels: weeks.map(w => formatWeekLabel(w)),
        data: data
    };
}

/**
 * Format week label for display
 */
function formatWeekLabel(weekString) {
    const [year, week] = weekString.split('-W');
    return `Week ${week}`;
}

/**
 * Create time series data from items
 */
export function createTimeSeriesData(items, dateField, valueField) {
    if (!items || items.length === 0) {
        return { labels: [], data: [] };
    }

    // Sort by date
    const sorted = [...items].sort((a, b) => {
        const dateA = new Date(a[dateField]);
        const dateB = new Date(b[dateField]);
        return dateA - dateB;
    });

    const labels = sorted.map(item => {
        const date = new Date(item[dateField]);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const data = sorted.map(item => item[valueField] || 0);

    return { labels, data };
}

/**
 * Bucket numeric values into ranges
 */
export function bucketValues(values, buckets) {
    const counts = new Array(buckets.length).fill(0);

    values.forEach(value => {
        for (let i = 0; i < buckets.length; i++) {
            const bucket = buckets[i];
            if (value >= bucket.min && value < bucket.max) {
                counts[i]++;
                break;
            }
            // Last bucket includes max value
            if (i === buckets.length - 1 && value >= bucket.min) {
                counts[i]++;
            }
        }
    });

    const labels = buckets.map(b => b.label);

    return { labels, counts };
}

/**
 * Calculate percentage distribution
 */
export function calculatePercentages(values) {
    const total = values.reduce((a, b) => a + b, 0);

    if (total === 0) {
        return values.map(() => 0);
    }

    return values.map(v => (v / total) * 100);
}

/**
 * Format date for chart label
 */
export function formatChartDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Get last N items from array
 */
export function lastN(arr, n) {
    if (!arr || arr.length === 0) return [];
    return arr.slice(Math.max(0, arr.length - n));
}

/**
 * Calculate moving average
 */
export function movingAverage(values, windowSize = 3) {
    if (!values || values.length < windowSize) return values;

    const result = [];

    for (let i = 0; i < values.length; i++) {
        const start = Math.max(0, i - Math.floor(windowSize / 2));
        const end = Math.min(values.length, start + windowSize);
        const window = values.slice(start, end);
        const avg = window.reduce((a, b) => a + b, 0) / window.length;
        result.push(avg);
    }

    return result;
}
