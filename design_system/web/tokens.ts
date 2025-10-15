/**
 * Kearney Design System - TypeScript Tokens
 *
 * Auto-generated from design_system/tokens.json
 * DO NOT EDIT MANUALLY - use token generation script
 */

// Core Color Palette
export const CHARCOAL = '#1E1E1E';
export const SILVER = '#A5A5A5';
export const PURPLE = '#7823DC';
export const GREY_200 = '#D2D2D2';
export const GREY_500 = '#787878';
export const GREY_700 = '#4B4B4B';
export const VIOLET_1 = '#E6D2FA';
export const VIOLET_2 = '#C8A5F0';
export const VIOLET_3 = '#AF7DEB';
export const VIOLET_4 = '#9150E1';

// Extended Palette
export const WHITE = '#FFFFFF';
export const BLACK = '#000000';
export const GREY_100 = '#F5F5F5';
export const GREY_300 = '#BEBEBE';
export const GREY_600 = '#5A5A5A';
export const GREY_800 = '#2D2D2D';
export const GREY_900 = '#1A1A1A';

// Theme Colors
export interface ThemeColors {
  background: string;
  surface: string;
  surfaceElevated: string;
  text: string;
  textMuted: string;
  textInverse: string;
  border: string;
  emphasis: string;
  emphasisHover: string;
  success: string;
  successTint: string;
  warning: string;
  warningTint: string;
  error: string;
  errorTint: string;
  spotColor: string;
  chartMuted: string;
  chartHighlight: string;
}

export const LIGHT_THEME: ThemeColors = {
  background: '#FFFFFF',
  surface: '#F5F5F5',
  surfaceElevated: '#FFFFFF',
  text: '#1E1E1E',
  textMuted: '#787878',
  textInverse: '#FFFFFF',
  border: '#D2D2D2',
  emphasis: '#7823DC',
  emphasisHover: '#9150E1',
  success: '#2E7D32',
  successTint: '#E8F5E9',
  warning: '#ED6C02',
  warningTint: '#FFF3E0',
  error: '#D32F2F',
  errorTint: '#FFEBEE',
  spotColor: '#7823DC',
  chartMuted: '#A5A5A5',
  chartHighlight: '#7823DC',
};

export const DARK_THEME: ThemeColors = {
  background: '#000000',
  surface: '#1E1E1E',
  surfaceElevated: '#2D2D2D',
  text: '#FFFFFF',
  textMuted: '#A5A5A5',
  textInverse: '#1E1E1E',
  border: '#4B4B4B',
  emphasis: '#AF7DEB',
  emphasisHover: '#C8A5F0',
  success: '#66BB6A',
  successTint: '#1B5E20',
  warning: '#FFA726',
  warningTint: '#E65100',
  error: '#EF5350',
  errorTint: '#B71C1C',
  spotColor: '#AF7DEB',
  chartMuted: '#787878',
  chartHighlight: '#C8A5F0',
};

// Typography
export const FONT_FAMILY_PRIMARY = 'Inter, Arial, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif';
export const FONT_FAMILY_MONO = '"SF Mono", "Roboto Mono", "Courier New", monospace';

export const FONT_WEIGHT = {
  light: 300,
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const FONT_SIZE = {
  xs: '0.64rem',
  sm: '0.8rem',
  base: '1rem',
  md: '1.25rem',
  lg: '1.563rem',
  xl: '1.953rem',
  '2xl': '2.441rem',
  '3xl': '3.052rem',
  '4xl': '3.815rem',
} as const;

export const LINE_HEIGHT = {
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.75,
  loose: 2,
} as const;

export const LETTER_SPACING = {
  tighter: '-0.02em',
  tight: '-0.01em',
  normal: '0',
  wide: '0.01em',
  wider: '0.02em',
} as const;

// Spacing
export const SPACING = {
  0: '0',
  1: '0.25rem',
  2: '0.5rem',
  3: '0.75rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  8: '2rem',
  10: '2.5rem',
  12: '3rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
} as const;

// Border Radius
export const BORDER_RADIUS = {
  none: '0',
  sm: '0.125rem',
  base: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  '2xl': '1rem',
  full: '9999px',
} as const;

// Shadows
export const SHADOWS = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
} as const;

// Visualization Palettes
export const SEQUENTIAL_PURPLE = [
  '#E6D2FA',
  '#C8A5F0',
  '#AF7DEB',
  '#9150E1',
  '#7823DC',
  '#601FB5',
  '#4A188E',
  '#341167',
];

export const SEQUENTIAL_NEUTRAL = [
  '#F5F5F5',
  '#D2D2D2',
  '#A5A5A5',
  '#787878',
  '#5A5A5A',
  '#4B4B4B',
  '#2D2D2D',
  '#1E1E1E',
];

export const CATEGORICAL_PRIMARY = [
  '#7823DC',
  '#A5A5A5',
  '#9150E1',
  '#787878',
  '#AF7DEB',
  '#D2D2D2',
];

export const CATEGORICAL_EXTENDED = [
  '#7823DC',
  '#9150E1',
  '#AF7DEB',
  '#C8A5F0',
  '#E6D2FA',
  '#787878',
  '#A5A5A5',
  '#D2D2D2',
];

// Semantic Status Colors
export const STATUS_COLORS = {
  success: '#2E7D32',
  warning: '#ED6C02',
  error: '#D32F2F',
  info: '#7823DC',
} as const;

export const TREND_COLORS = {
  positive: '#2E7D32',
  negative: '#D32F2F',
  neutral: '#787878',
} as const;

// Theme Helper
export type Theme = 'light' | 'dark';

export function getThemeColors(theme: Theme): ThemeColors {
  return theme === 'light' ? LIGHT_THEME : DARK_THEME;
}

// Meta
export const META = {
  version: '1.0.0',
  source: 'Kearney brand guidelines',
  no_emojis: true,
  no_gridlines: true,
  label_first: true,
  spot_color_emphasis: true,
} as const;
