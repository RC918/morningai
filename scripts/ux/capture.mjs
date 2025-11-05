#!/usr/bin/env node
/**
 * Screenshot Capture Script for AI Perceptual QA
 * Captures screenshots of key pages for visual harmony analysis
 */

import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const config = await import('./config.js').then(m => m.default);

const BASE_URL = process.env.BASE_URL || 'http://localhost:4173';
const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
const OUTPUT_DIR = path.join(__dirname, '../../ux-qa-results');
const SCREENSHOTS_DIR = path.join(OUTPUT_DIR, 'screenshots', APP_NAME);

async function captureScreenshots() {
  console.log(`📸 Capturing screenshots for ${APP_NAME}...`);
  console.log(`Base URL: ${BASE_URL}\n`);

  // Create output directories
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1366, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light', // Force light theme for consistency
    locale: 'en-US', // Force en-US locale
  });
  const page = await context.newPage();

  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(10000);

  const pages = config.PAGES[APP_NAME] || [];
  const capturedPages = [];

  for (const pageConfig of pages.slice(0, config.BUDGET.maxPagesPerApp)) {
    console.log(`Capturing: ${pageConfig.name} (${pageConfig.path})`);

    try {
      const url = `${BASE_URL}${pageConfig.path}`;
      await page.goto(url, { waitUntil: 'networkidle' });

      // Wait for page to stabilize
      await page.waitForTimeout(500);

      // Hide dynamic elements that could cause variance
      await page.addStyleTag({
        content: `
          [data-testid="timestamp"],
          .timestamp,
          .live-indicator,
          .pulse-animation {
            visibility: hidden !important;
          }
        `,
      });

      // Take screenshot
      const screenshotPath = path.join(
        SCREENSHOTS_DIR,
        `${pageConfig.name.toLowerCase().replace(/\s+/g, '-')}.jpg`
      );

      await page.screenshot({
        path: screenshotPath,
        type: 'jpeg',
        quality: Math.round(config.BUDGET.imageQuality * 100),
        fullPage: false, // Only capture viewport
      });

      console.log(`  ✅ Saved: ${path.basename(screenshotPath)}`);

      capturedPages.push({
        name: pageConfig.name,
        path: pageConfig.path,
        description: pageConfig.description,
        screenshotPath,
        url,
      });
    } catch (error) {
      console.error(`  ❌ Error capturing ${pageConfig.name}: ${error.message}`);
      capturedPages.push({
        name: pageConfig.name,
        path: pageConfig.path,
        error: error.message,
      });
    }
  }

  await browser.close();

  // Save manifest
  const manifestPath = path.join(OUTPUT_DIR, `${APP_NAME}-screenshots.json`);
  fs.writeFileSync(
    manifestPath,
    JSON.stringify(
      {
        app: APP_NAME,
        baseUrl: BASE_URL,
        timestamp: new Date().toISOString(),
        pages: capturedPages,
      },
      null,
      2
    )
  );

  console.log(`\n📊 Manifest saved: ${manifestPath}`);
  console.log(`✅ Captured ${capturedPages.filter(p => !p.error).length}/${pages.length} pages\n`);

  return capturedPages;
}

// Check if server is running
async function checkServer() {
  try {
    const response = await fetch(BASE_URL);
    return response.ok || response.status === 404; // 404 is ok, means server is running
  } catch {
    return false;
  }
}

// Main execution
(async () => {
  const serverRunning = await checkServer();

  if (!serverRunning) {
    console.error(`❌ Error: Development server not running on ${BASE_URL}`);
    console.error('Please start the server with: pnpm run preview');
    process.exit(1);
  }

  await captureScreenshots();
})();
