#!/usr/bin/env ts-node
/**
 * Export documentation pages as branded PDFs for client deliveries.
 *
 * Usage:
 *   ts-node scripts/export_pdfs.ts
 *   npm run docs-export
 */

import puppeteer from 'puppeteer';
import { readdir, mkdir } from 'fs/promises';
import { join, basename } from 'path';

const DOCS_BASE_URL = process.env.DOCS_BASE_URL || 'http://localhost:3000';
const OUTPUT_DIR = join(__dirname, '..', 'site', 'pdfs');

// Pages to export
const PAGES_TO_EXPORT = [
  {
    path: '/',
    filename: 'platform-overview.pdf',
    title: 'Kearney Data Platform - Overview',
  },
  {
    path: '/getting-started',
    filename: 'getting-started.pdf',
    title: 'Getting Started Guide',
  },
  {
    path: '/api',
    filename: 'api-reference.pdf',
    title: 'API Reference',
  },
  {
    path: '/cli',
    filename: 'cli-reference.pdf',
    title: 'CLI Reference',
  },
  {
    path: '/design-system',
    filename: 'design-system.pdf',
    title: 'Design System',
  },
  {
    path: '/security',
    filename: 'security-guide.pdf',
    title: 'Security Guide',
  },
  {
    path: '/ops',
    filename: 'operations-guide.pdf',
    title: 'Operations Guide',
  },
];

// PDF options with Kearney branding
const PDF_OPTIONS: puppeteer.PDFOptions = {
  format: 'A4',
  margin: {
    top: '20mm',
    right: '15mm',
    bottom: '20mm',
    left: '15mm',
  },
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: `
    <div style="font-family: Inter, Arial, sans-serif; font-size: 10px; width: 100%; padding: 0 15mm; display: flex; justify-content: space-between; color: #1E1E1E;">
      <span>Kearney Data Platform</span>
      <span style="font-weight: 600; color: #7823DC;">Confidential</span>
    </div>
  `,
  footerTemplate: `
    <div style="font-family: Inter, Arial, sans-serif; font-size: 9px; width: 100%; padding: 0 15mm; display: flex; justify-content: space-between; color: #787878;">
      <span class="date"></span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>
  `,
};

async function exportPage(
  browser: puppeteer.Browser,
  page: { path: string; filename: string; title: string }
): Promise<void> {
  const url = `${DOCS_BASE_URL}${page.path}`;
  console.log(`Exporting: ${url}`);

  const browserPage = await browser.newPage();

  try {
    // Navigate to page
    await browserPage.goto(url, {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });

    // Wait for content to load
    await browserPage.waitForSelector('.main-wrapper', { timeout: 10000 }).catch(() => {
      console.warn('Main content selector not found, continuing anyway...');
    });

    // Inject custom styles for PDF
    await browserPage.addStyleTag({
      content: `
        /* PDF-specific styles */
        @media print {
          /* Hide navigation */
          nav, .navbar, .sidebar, .pagination-nav, .theme-doc-toc-mobile {
            display: none !important;
          }

          /* Adjust main content */
          .main-wrapper {
            max-width: 100% !important;
          }

          /* Better page breaks */
          h1, h2, h3 {
            page-break-after: avoid;
          }

          pre, table {
            page-break-inside: avoid;
          }

          /* Brand colors */
          a {
            color: #7823DC !important;
          }

          code {
            background-color: #F5F5F5 !important;
            border: 1px solid #D2D2D2 !important;
          }
        }

        /* Cover page style */
        body.cover-page {
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #7823DC 0%, #AF7DEB 100%);
        }

        .cover-title {
          font-family: Inter, Arial, sans-serif;
          font-size: 48px;
          font-weight: 700;
          color: white;
          text-align: center;
          padding: 40px;
        }
      `,
    });

    // Generate PDF
    const outputPath = join(OUTPUT_DIR, page.filename);
    await browserPage.pdf({
      ...PDF_OPTIONS,
      path: outputPath,
    });

    console.log(`✓ Exported: ${page.filename}`);
  } catch (error) {
    console.error(`✗ Error exporting ${page.path}:`, error);
    throw error;
  } finally {
    await browserPage.close();
  }
}

async function generateCoverPage(browser: puppeteer.Browser): Promise<void> {
  console.log('Generating cover page...');

  const page = await browser.newPage();

  await page.setContent(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap" rel="stylesheet">
      <style>
        body {
          margin: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          background: linear-gradient(135deg, #7823DC 0%, #AF7DEB 100%);
          font-family: Inter, Arial, sans-serif;
        }

        .cover {
          text-align: center;
          color: white;
          padding: 60px;
        }

        .cover h1 {
          font-size: 52px;
          font-weight: 700;
          margin: 0 0 20px 0;
          letter-spacing: -0.02em;
        }

        .cover .subtitle {
          font-size: 20px;
          font-weight: 400;
          margin: 0 0 40px 0;
          opacity: 0.9;
        }

        .cover .date {
          font-size: 14px;
          font-weight: 500;
          margin: 40px 0 0 0;
          opacity: 0.8;
        }
      </style>
    </head>
    <body>
      <div class="cover">
        <h1>Kearney Data Platform</h1>
        <p class="subtitle">Complete Documentation Suite</p>
        <p class="date">${new Date().toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })}</p>
      </div>
    </body>
    </html>
  `);

  const outputPath = join(OUTPUT_DIR, 'cover.pdf');
  await page.pdf({
    format: 'A4',
    path: outputPath,
    printBackground: true,
  });

  console.log('✓ Cover page generated');
  await page.close();
}

async function main(): Promise<void> {
  console.log('Kearney Data Platform - PDF Export Tool');
  console.log('========================================\n');
  console.log(`Documentation URL: ${DOCS_BASE_URL}`);
  console.log(`Output directory: ${OUTPUT_DIR}\n`);

  // Create output directory
  await mkdir(OUTPUT_DIR, { recursive: true });

  // Launch browser
  console.log('Launching headless browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    // Generate cover page
    await generateCoverPage(browser);

    // Export each page
    console.log(`\nExporting ${PAGES_TO_EXPORT.length} pages...\n`);

    for (const page of PAGES_TO_EXPORT) {
      await exportPage(browser, page);
    }

    console.log('\n========================================');
    console.log('✓ All PDFs exported successfully!');
    console.log(`\nOutput files in: ${OUTPUT_DIR}`);
    console.log(`Total PDFs: ${PAGES_TO_EXPORT.length + 1} (including cover)`);
  } catch (error) {
    console.error('\n✗ Export failed:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export { exportPage, generateCoverPage, PAGES_TO_EXPORT };
