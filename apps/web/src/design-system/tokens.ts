/**
 * Kearney Design System - TypeScript Tokens
 *
 * Generated from design_system/tokens.json (v1.1.0)
 * Brand principle: White + slate + purple accent
 * NO green, red, orange, or blue
 */

// Core Color Palette
export const CHARCOAL = '#1E1E1E';
export const SILVER = '#A5A5A5';
export const PURPLE = '#7823DC';

// Complete Grey Scale
export const GREY_100 = '#F5F5F5';
export const GREY_150 = '#E6E6E6';
export const GREY_200 = '#D2D2D2';
export const GREY_250 = '#C8C8C8';
export const GREY_350 = '#B9B9B9';
export const GREY_500 = '#A5A5A5';
export const GREY_550 = '#8C8C8C';
export const GREY_600 = '#787878';
export const GREY_650 = '#5F5F5F';
export const GREY_700 = '#4B4B4B';
export const GREY_850 = '#323232';

// Primary Violet Scale
export const VIOLET_1 = '#E6D2FA';
export const VIOLET_2 = '#C8A5F0';
export const VIOLET_3 = '#AF7DEB';
export const VIOLET_4 = '#9150E1';
export const VIOLET_5 = '#7823DC';

// Secondary Violet Scale (Alternate)
export const VIOLET_1_ALT = '#D7BEF5';
export const VIOLET_2_ALT = '#B991EB';
export const VIOLET_3_ALT = '#A064E6';
export const VIOLET_4_ALT = '#8737E1';

// Extended Palette
export const WHITE = '#FFFFFF';
export const BLACK = '#000000';
export const GREY_800 = '#2D2D2D';
export const GREY_900 = '#1A1A1A';
export const FAINT = '#FAFAFA';

// Theme Colors Interface - NO success/warning/error (use positive/negative/neutral)
export interface ThemeColors {
  background: string;
  surface: string;
  surfaceElevated: string;
  text: string;
  textMuted: string;
  textInverse: string;
  border: string;
  borderSubtle: string;
  borderMedium: string;
  emphasis: string;
  emphasisHover: string;
  emphasisLight: string;
  positive: string;
  positiveTint: string;
  negative: string;
  negativeTint: string;
  neutral: string;
  neutralTint: string;
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
  borderSubtle: '#E6E6E6',
  borderMedium: '#C8C8C8',
  emphasis: '#7823DC',
  emphasisHover: '#9150E1',
  emphasisLight: '#E6D2FA',
  positive: '#7823DC',
  positiveTint: '#E6D2FA',
  negative: '#4B4B4B',
  negativeTint: '#F5F5F5',
  neutral: '#787878',
  neutralTint: '#F5F5F5',
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
  borderSubtle: '#323232',
  borderMedium: '#5F5F5F',
  emphasis: '#AF7DEB',
  emphasisHover: '#C8A5F0',
  emphasisLight: '#8737E1',
  positive: '#AF7DEB',
  positiveTint: '#323232',
  negative: '#787878',
  negativeTint: '#1E1E1E',
  neutral: '#A5A5A5',
  neutralTint: '#1E1E1E',
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
};

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
};

export const LINE_HEIGHT = {
  tight: 1.2,
  normal: 1.5,
  relaxed: 1.75,
  loose: 2,
};

export const LETTER_SPACING = {
  tighter: '-0.02em',
  tight: '-0.01em',
  normal: '0',
  wide: '0.01em',
  wider: '0.02em',
};

// Categorical Color Palette (for charts)
export const CATEGORICAL_PRIMARY = [
  PURPLE,     // Primary purple
  SILVER,     // Silver grey
  VIOLET_4,   // Lighter purple
  GREY_600,   // Mid grey
  VIOLET_3,   // Even lighter purple
  GREY_200,   // Light grey
];

// Helper function to get theme colors
export function getThemeColors(theme: 'light' | 'dark'): ThemeColors {
  return theme === 'dark' ? DARK_THEME : LIGHT_THEME;
}

// Brand Metadata
export const BRAND_META = {
  version: '1.1.0',
  principle: 'White + slate + purple accent',
  forbidden: 'NO green, red, orange, or blue',
  noEmojis: true,
  noGridlines: true,
  labelFirst: true,
  spotColorEmphasis: true,
  generousWhitespace: true,
};
