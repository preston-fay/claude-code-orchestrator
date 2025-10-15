import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// Kearney Data Platform Documentation Portal
// Brand-locked: Inter->Arial, no emojis, no gridlines

const config: Config = {
  title: 'Kearney Data Platform',
  tagline: 'Unified documentation, APIs, and delivery portal',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://data-platform-docs.kearney.com',
  baseUrl: '/',

  organizationName: 'kearney',
  projectName: 'data-platform-docs',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: undefined,
          routeBasePath: '/',
          versions: {
            current: {
              label: 'Latest',
              path: '',
            },
          },
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/kearney-social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Kearney Data Platform',
      logo: {
        alt: 'Kearney Logo',
        src: 'img/logo.svg',
        srcDark: 'img/logo-dark.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'gettingStartedSidebar',
          position: 'left',
          label: 'Getting Started',
        },
        {
          type: 'docSidebar',
          sidebarId: 'apiSidebar',
          position: 'left',
          label: 'API Reference',
        },
        {
          type: 'docSidebar',
          sidebarId: 'cliSidebar',
          position: 'left',
          label: 'CLI',
        },
        {
          type: 'docSidebar',
          sidebarId: 'designSystemSidebar',
          position: 'left',
          label: 'Design System',
        },
        {
          type: 'docSidebar',
          sidebarId: 'opsSidebar',
          position: 'left',
          label: 'Operations',
        },
        {
          type: 'docSidebar',
          sidebarId: 'securitySidebar',
          position: 'left',
          label: 'Security',
        },
        {
          type: 'docsVersionDropdown',
          position: 'right',
          dropdownActiveClassDisabled: true,
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {
              label: 'Getting Started',
              to: '/getting-started',
            },
            {
              label: 'API Reference',
              to: '/api',
            },
            {
              label: 'CLI Reference',
              to: '/cli',
            },
          ],
        },
        {
          title: 'Platform',
          items: [
            {
              label: 'Design System',
              to: '/design-system',
            },
            {
              label: 'Data & Registry',
              to: '/data',
            },
            {
              label: 'Operations',
              to: '/ops',
            },
          ],
        },
        {
          title: 'Resources',
          items: [
            {
              label: 'Security',
              to: '/security',
            },
            {
              label: 'Runbooks',
              to: '/runbooks',
            },
            {
              label: 'Governance',
              to: '/governance',
            },
          ],
        },
      ],
      copyright: `Kearney Data Platform Documentation. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'json', 'yaml', 'typescript'],
    },
  } satisfies Preset.ThemeConfig,

  plugins: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['en'],
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
        docsRouteBasePath: '/',
      },
    ],
  ],
};

export default config;
