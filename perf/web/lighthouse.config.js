/**
 * Lighthouse CI Configuration for Kearney Data Platform
 *
 * Performance thresholds for web application:
 * - Performance: ≥ 85
 * - Accessibility: ≥ 90
 * - Best Practices: ≥ 90
 * - SEO: ≥ 80 (optional)
 *
 * Usage:
 *   lighthouse http://localhost:5173 --config-path=perf/web/lighthouse.config.js --output=json --output-path=perf/web/report.json
 *   npm run lighthouse
 */

module.exports = {
  extends: 'lighthouse:default',

  settings: {
    // Run multiple passes for more accurate results
    throttling: {
      rttMs: 40,
      throughputKbps: 10 * 1024,
      cpuSlowdownMultiplier: 1,
    },

    // Screen emulation (desktop)
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false,
    },

    // Form factor
    formFactor: 'desktop',

    // Number of runs (for CI, use 1; for local testing, use 3-5)
    runs: 1,
  },

  // Categories and their minimum scores
  categories: {
    performance: {
      title: 'Performance',
      description: 'Performance metrics for page load and interactivity',
      auditRefs: [
        { id: 'first-contentful-paint', weight: 10 },
        { id: 'largest-contentful-paint', weight: 25 },
        { id: 'total-blocking-time', weight: 30 },
        { id: 'cumulative-layout-shift', weight: 25 },
        { id: 'speed-index', weight: 10 },
      ],
    },
    accessibility: {
      title: 'Accessibility',
      description: 'Accessibility checks for inclusive design',
    },
    'best-practices': {
      title: 'Best Practices',
      description: 'Web best practices compliance',
    },
    seo: {
      title: 'SEO',
      description: 'Search engine optimization checks',
    },
  },

  // Assertions for CI (used by Lighthouse CI)
  assertions: {
    'categories:performance': ['error', { minScore: 0.85 }],
    'categories:accessibility': ['error', { minScore: 0.90 }],
    'categories:best-practices': ['error', { minScore: 0.90 }],
    'categories:seo': ['warn', { minScore: 0.80 }],

    // Core Web Vitals thresholds
    'first-contentful-paint': ['warn', { maxNumericValue: 1800 }], // 1.8s
    'largest-contentful-paint': ['error', { maxNumericValue: 2500 }], // 2.5s
    'total-blocking-time': ['error', { maxNumericValue: 200 }], // 200ms
    'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }], // 0.1
    'speed-index': ['warn', { maxNumericValue: 3400 }], // 3.4s

    // Resource loading
    'interactive': ['warn', { maxNumericValue: 3800 }], // 3.8s
    'max-potential-fid': ['warn', { maxNumericValue: 130 }], // 130ms

    // Asset optimization
    'unused-javascript': ['warn', { maxNumericValue: 0 }],
    'modern-image-formats': ['warn', { maxNumericValue: 0 }],
    'offscreen-images': ['warn', { maxNumericValue: 0 }],

    // Best practices
    'uses-https': ['error', { minScore: 1 }],
    'no-vulnerable-libraries': ['error', { minScore: 1 }],
  },

  // Output configuration
  output: ['json', 'html'],

  // URL patterns to test
  // (Override via CLI: lighthouse <url>)
  url: 'http://localhost:5173',

  // Audits to skip (if needed)
  skipAudits: [
    // 'uses-http2',  // Uncomment if not using HTTP/2 in dev
  ],

  // Additional settings
  onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
};
