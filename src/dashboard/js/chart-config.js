/**
 * Chart.js Configuration
 *
 * Base configurations for all charts following Kearney standards:
 * - Purple color palette (NO green)
 * - NO gridlines
 * - Theme-aware colors
 * - Responsive settings
 */

// Kearney Purple Color Palette (from design system)
export const COLORS = {
    purple: '#7823DC',
    purpleLight: '#9B51E0',
    purpleDark: '#5A1AA8',
    charcoal: '#1E1E1E',
    silver: '#A5A5A5',
    white: '#FFFFFF',

    // Additional purple shades for charts
    purple10: 'rgba(120, 35, 220, 0.1)',
    purple20: 'rgba(120, 35, 220, 0.2)',
    purple50: 'rgba(120, 35, 220, 0.5)',
    purple80: 'rgba(120, 35, 220, 0.8)',
};

/**
 * Get theme-aware colors based on current theme
 */
export function getThemeColors(isDark = true) {
    return {
        text: isDark ? COLORS.white : COLORS.charcoal,
        textMuted: COLORS.silver,
        background: isDark ? '#121212' : '#FFFFFF',
        surface: isDark ? '#1E1E1E' : '#F5F5F5',
        border: isDark ? '#333333' : '#E0E0E0'
    };
}

/**
 * Base chart configuration (NO gridlines per Kearney standard)
 */
export function getBaseConfig(isDark = true) {
    const themeColors = getThemeColors(isDark);

    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    color: themeColors.text,
                    font: {
                        family: 'Inter, Arial, sans-serif',
                        size: 12
                    },
                    padding: 16,
                    usePointStyle: true
                }
            },
            tooltip: {
                enabled: true,
                backgroundColor: themeColors.surface,
                titleColor: themeColors.text,
                bodyColor: themeColors.text,
                borderColor: themeColors.border,
                borderWidth: 1,
                padding: 12,
                displayColors: true,
                callbacks: {
                    // Custom formatting added per chart type
                }
            }
        },
        scales: {
            x: {
                display: true,
                grid: {
                    display: false  // NO GRIDLINES
                },
                ticks: {
                    color: themeColors.textMuted,
                    font: {
                        family: 'Inter, Arial, sans-serif',
                        size: 11
                    }
                },
                border: {
                    display: true,
                    color: themeColors.border
                }
            },
            y: {
                display: true,
                grid: {
                    display: false  // NO GRIDLINES
                },
                ticks: {
                    color: themeColors.textMuted,
                    font: {
                        family: 'Inter, Arial, sans-serif',
                        size: 11
                    }
                },
                border: {
                    display: true,
                    color: themeColors.border
                }
            }
        },
        animation: {
            duration: 750,
            easing: 'easeInOutQuart'
        }
    };
}

/**
 * Line chart configuration
 */
export function getLineChartConfig(isDark = true) {
    const base = getBaseConfig(isDark);

    return {
        ...base,
        type: 'line',
        options: {
            ...base,
            elements: {
                line: {
                    tension: 0.3,  // Slight curve
                    borderWidth: 2
                },
                point: {
                    radius: 4,
                    hoverRadius: 6,
                    hitRadius: 10
                }
            }
        }
    };
}

/**
 * Bar chart configuration
 */
export function getBarChartConfig(isDark = true) {
    const base = getBaseConfig(isDark);

    return {
        ...base,
        type: 'bar',
        options: {
            ...base,
            elements: {
                bar: {
                    borderWidth: 0,
                    borderRadius: 4
                }
            }
        }
    };
}

/**
 * Pie/Doughnut chart configuration
 */
export function getPieChartConfig(isDark = true) {
    const base = getBaseConfig(isDark);

    return {
        type: 'doughnut',
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: base.plugins.legend,
                tooltip: base.plugins.tooltip
            },
            cutout: '60%',  // Doughnut hole size
            animation: base.animation
        }
    };
}

/**
 * Stacked bar chart configuration
 */
export function getStackedBarConfig(isDark = true) {
    const config = getBarChartConfig(isDark);

    return {
        ...config,
        options: {
            ...config.options,
            scales: {
                ...config.options.scales,
                x: {
                    ...config.options.scales.x,
                    stacked: true
                },
                y: {
                    ...config.options.scales.y,
                    stacked: true
                }
            }
        }
    };
}

/**
 * Stacked area chart configuration
 */
export function getStackedAreaConfig(isDark = true) {
    const config = getLineChartConfig(isDark);

    return {
        ...config,
        options: {
            ...config.options,
            scales: {
                ...config.options.scales,
                y: {
                    ...config.options.scales.y,
                    stacked: true
                }
            },
            elements: {
                ...config.options.elements,
                line: {
                    ...config.options.elements.line,
                    fill: true
                }
            }
        }
    };
}

/**
 * Get color palette for multiple datasets
 */
export function getColorPalette(count = 3) {
    const palette = [
        COLORS.purple,
        COLORS.purpleLight,
        COLORS.purpleDark,
        COLORS.purple80,
        COLORS.purple50,
        COLORS.purple20
    ];

    return palette.slice(0, count);
}

/**
 * Update chart theme dynamically
 */
export function updateChartTheme(chart, isDark = true) {
    if (!chart) return;

    const themeColors = getThemeColors(isDark);
    const options = chart.options;

    // Update legend colors
    if (options.plugins?.legend?.labels) {
        options.plugins.legend.labels.color = themeColors.text;
    }

    // Update tooltip colors
    if (options.plugins?.tooltip) {
        options.plugins.tooltip.backgroundColor = themeColors.surface;
        options.plugins.tooltip.titleColor = themeColors.text;
        options.plugins.tooltip.bodyColor = themeColors.text;
        options.plugins.tooltip.borderColor = themeColors.border;
    }

    // Update scale colors
    if (options.scales) {
        Object.keys(options.scales).forEach(scaleKey => {
            const scale = options.scales[scaleKey];
            if (scale.ticks) {
                scale.ticks.color = themeColors.textMuted;
            }
            if (scale.border) {
                scale.border.color = themeColors.border;
            }
        });
    }

    chart.update('none');  // Update without animation
}

/**
 * Format number with units
 */
export function formatNumber(value, decimals = 1) {
    if (value === null || value === undefined) return '--';

    if (value >= 1000) {
        return (value / 1000).toFixed(decimals) + 'k';
    }

    return value.toFixed(decimals);
}

/**
 * Format time duration
 */
export function formatDuration(hours) {
    if (hours === null || hours === undefined) return '--';

    if (hours < 1) {
        return Math.round(hours * 60) + 'm';
    } else if (hours < 24) {
        return hours.toFixed(1) + 'h';
    } else {
        return (hours / 24).toFixed(1) + 'd';
    }
}

/**
 * Format percentage
 */
export function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined) return '--';
    return value.toFixed(decimals) + '%';
}
