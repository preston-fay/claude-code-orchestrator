#!/usr/bin/env ts-node
/**
 * Export the Orchestrator Overview HTML to a branded PDF.
 *
 * Usage:
 *   npx ts-node scripts/export_overview_pdf.ts
 */

import puppeteer from 'puppeteer';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const HTML_PATH = join(__dirname, '..', 'docs', 'ORCHESTRATOR_OVERVIEW.html');
const OUTPUT_DIR = join(__dirname, '..', 'docs');
const OUTPUT_FILE = 'ORCHESTRATOR_OVERVIEW.pdf';

// PDF options with Kearney branding
const PDF_OPTIONS: puppeteer.PDFOptions = {
  format: 'Letter',
  margin: {
    top: '15mm',
    right: '15mm',
    bottom: '20mm',
    left: '15mm',
  },
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: `
    <div style="font-family: Arial, sans-serif; font-size: 9px; width: 100%; padding: 0 15mm; display: flex; justify-content: space-between; color: #787878;">
      <span>Claude Code Orchestrator</span>
      <span style="font-weight: 600; color: #7823DC;">Kearney Confidential</span>
    </div>
  `,
  footerTemplate: `
    <div style="font-family: Arial, sans-serif; font-size: 9px; width: 100%; padding: 0 15mm; display: flex; justify-content: space-between; color: #787878;">
      <span class="date"></span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>
  `,
};

async function main(): Promise<void> {
  console.log('Kearney PDF Export - Orchestrator Overview');
  console.log('==========================================\n');

  // Create output directory
  await mkdir(OUTPUT_DIR, { recursive: true });

  // Launch browser
  console.log('Launching headless browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    const page = await browser.newPage();

    // Load HTML file
    const fileUrl = `file://${HTML_PATH}`;
    console.log(`Loading: ${fileUrl}`);

    await page.goto(fileUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });

    // Generate PDF
    const outputPath = join(OUTPUT_DIR, OUTPUT_FILE);
    console.log(`Generating PDF: ${outputPath}`);

    await page.pdf({
      ...PDF_OPTIONS,
      path: outputPath,
    });

    console.log('\n==========================================');
    console.log(`PDF exported successfully!`);
    console.log(`Output: ${outputPath}`);
  } catch (error) {
    console.error('\nExport failed:', error);
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

export { main };
