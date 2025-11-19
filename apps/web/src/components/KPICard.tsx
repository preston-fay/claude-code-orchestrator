import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../design-system/tokens';

export type TrendDirection = 'up' | 'down' | 'neutral';

export interface KPICardProps {
  title: string;
  value: string | number;
  trend?: {
    direction: TrendDirection;
    value: string;
  };
  insight?: string;
  className?: string;
}

/**
 * KPI Card Component
 *
 * Displays a large number with optional trend indicator and concise insight.
 * No emojis - uses text indicators only.
 * Fully theme-aware.
 */
export function KPICard({
  title,
  value,
  trend,
  insight,
  className = '',
}: KPICardProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const getTrendColor = (direction: TrendDirection): string => {
    // Use neutral greys only - NO green/red (Kearney brand compliance)
    // Direction is conveyed by symbol (▲/▼/─), not color
    switch (direction) {
      case 'up':
        return colors.textMuted;  // Neutral grey (#787878)
      case 'down':
        return colors.textMuted;  // Neutral grey (#787878)
      case 'neutral':
        return colors.textMuted;  // Neutral grey (#787878)
    }
  };

  const getTrendSymbol = (direction: TrendDirection): string => {
    switch (direction) {
      case 'up':
        return '▲';
      case 'down':
        return '▼';
      case 'neutral':
        return '─';
    }
  };

  return (
    <div
      className={`rounded-lg p-6 shadow-md transition-all ${className}`}
      style={{
        backgroundColor: colors.surface,
        borderLeft: `4px solid ${colors.emphasis}`,
      }}
    >
      {/* Title */}
      <div
        className="text-sm font-medium mb-2"
        style={{ color: colors.textMuted }}
      >
        {title}
      </div>

      {/* Big Number */}
      <div
        className="text-4xl font-bold mb-3"
        style={{ color: colors.text }}
      >
        {value}
      </div>

      {/* Trend Indicator */}
      {trend && (
        <div className="flex items-center gap-2 mb-2">
          <span
            className="inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-semibold"
            style={{
              backgroundColor: `${getTrendColor(trend.direction)}15`,
              color: getTrendColor(trend.direction),
            }}
          >
            <span>{getTrendSymbol(trend.direction)}</span>
            <span>{trend.value}</span>
          </span>
        </div>
      )}

      {/* Concise Insight */}
      {insight && (
        <div
          className="text-sm leading-relaxed"
          style={{ color: colors.textMuted }}
        >
          {insight}
        </div>
      )}
    </div>
  );
}
