/**
 * Theme Manager
 *
 * Handles dark/light theme toggling with localStorage persistence.
 * Default theme: DARK
 * Button text: Shows what you'll GET (not current state)
 */

const THEME_KEY = 'metricsTheme';
const DEFAULT_THEME = 'dark';

class ThemeManager {
    constructor() {
        this.currentTheme = this.loadTheme();
        this.toggleButton = null;
    }

    /**
     * Initialize theme manager
     */
    init() {
        this.applyTheme(this.currentTheme);
        this.setupToggleButton();
        console.log(`Theme Manager initialized with theme: ${this.currentTheme}`);
    }

    /**
     * Load theme from localStorage or use default
     */
    loadTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        return savedTheme || DEFAULT_THEME;
    }

    /**
     * Save theme to localStorage
     */
    saveTheme(theme) {
        localStorage.setItem(THEME_KEY, theme);
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.updateToggleButtonText();

        // Emit custom event for chart updates
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme }
        }));
    }

    /**
     * Toggle between dark and light themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);
        console.log(`Theme toggled to: ${newTheme}`);
    }

    /**
     * Setup theme toggle button
     */
    setupToggleButton() {
        this.toggleButton = document.getElementById('theme-toggle');

        if (!this.toggleButton) {
            console.error('Theme toggle button not found');
            return;
        }

        this.updateToggleButtonText();

        this.toggleButton.addEventListener('click', () => {
            this.toggleTheme();
        });
    }

    /**
     * Update toggle button text
     * Shows what theme you'll GET (not current state)
     */
    updateToggleButtonText() {
        if (!this.toggleButton) return;

        if (this.currentTheme === 'dark') {
            this.toggleButton.textContent = 'Light Mode';
        } else {
            this.toggleButton.textContent = 'Dark Mode';
        }
    }

    /**
     * Get current theme
     */
    getTheme() {
        return this.currentTheme;
    }

    /**
     * Check if current theme is dark
     */
    isDark() {
        return this.currentTheme === 'dark';
    }
}

// Create singleton instance
const themeManager = new ThemeManager();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager.init();
    });
} else {
    themeManager.init();
}

// Export for use in other modules
export default themeManager;
