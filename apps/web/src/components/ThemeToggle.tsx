import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getThemeColors } from '../design-system/tokens';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const colors = getThemeColors(theme);

  return (
    <button
      onClick={toggleTheme}
      className="rounded-lg px-4 py-2 font-medium transition-all"
      style={{
        backgroundColor: colors.surface,
        color: colors.text,
        border: `1px solid ${colors.border}`,
      }}
      aria-label="Toggle theme"
    >
      {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
    </button>
  );
}
