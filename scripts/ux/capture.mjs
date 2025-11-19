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
const AUTH_STORAGE_PATH = path.join(OUTPUT_DIR, 'auth-storage.json');

// Authentication credentials from environment
const QA_TEST_EMAIL = process.env.QA_TEST_EMAIL;
const QA_TEST_PASSWORD = process.env.QA_TEST_PASSWORD;

/**
 * Setup authentication by logging in with test credentials
 * @param {Page} page - Playwright page instance
 * @returns {Promise<boolean>} - True if authentication succeeded
 */
async function setupAuth(page) {
  if (!QA_TEST_EMAIL || !QA_TEST_PASSWORD) {
    console.log('⚠️  No test credentials provided (QA_TEST_EMAIL, QA_TEST_PASSWORD)');
    console.log('   Skipping authentication - only public pages will be captured\n');
    return false;
  }

  // Get app-specific authentication configuration
  const authConfig = config.AUTH_CONFIG?.[APP_NAME];
  if (!authConfig) {
    console.log(`⚠️  No auth config for ${APP_NAME}`);
    console.log('   Using default selectors (may not work)\n');
    return false;
  }

  console.log('🔐 Setting up authentication...');
  
  try {
    // Navigate to login page
    await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
    
    // Wait for form to be visible (use app-specific selector)
    await page.waitForSelector(authConfig.usernameField, { state: 'visible', timeout: 10000 });
    
    // Fill in credentials using app-specific selectors
    await page.fill(authConfig.usernameField, QA_TEST_EMAIL);
    await page.fill(authConfig.passwordField, QA_TEST_PASSWORD);
    
    // Submit form by pressing Enter on password field (more reliable than clicking button)
    await page.press(authConfig.passwordField, 'Enter');
    
    // Wait for navigation to dashboard after successful login (use app-specific URL pattern)
    await page.waitForURL(authConfig.successUrl, { timeout: 15000 });
    
    // Verify authentication by checking for authenticated-only elements (use app-specific selector)
    const isAuthenticated = await page.locator(authConfig.successSelector).isVisible().catch(() => false);
    
    if (isAuthenticated) {
      console.log('✅ Authentication successful\n');
      return true;
    } else {
      console.log('❌ Authentication failed - no authenticated elements found\n');
      return false;
    }
  } catch (error) {
    console.error(`❌ Authentication error: ${error.message}\n`);
    return false;
  }
}

async function captureScreenshots() {
  console.log(`📸 Capturing screenshots for ${APP_NAME}...`);
  console.log(`Base URL: ${BASE_URL}\n`);

  // Create output directories
  if (!fs.existsSync(SCREENSHOTS_DIR)) {
    fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  
  // Check if we have saved auth state
  let contextOptions = {
    viewport: { width: 1366, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light', // Force light theme for consistency
    locale: 'en-US', // Force en-US locale
  };
  
  // Try to load saved auth state if it exists
  if (fs.existsSync(AUTH_STORAGE_PATH)) {
    try {
      contextOptions.storageState = AUTH_STORAGE_PATH;
      console.log('📂 Loaded saved authentication state\n');
    } catch (error) {
      console.log('⚠️  Could not load saved auth state, will authenticate fresh\n');
    }
  }
  
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();

  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(10000);

  const pages = config.PAGES[APP_NAME] || [];
  const capturedPages = [];
  
  // Determine if we need authentication
  const requiresAuth = pages.some(p => p.requiresAuth);
  let isAuthenticated = false;
  
  if (requiresAuth) {
    // Attempt authentication
    isAuthenticated = await setupAuth(page);
    
    // Save auth state for future runs
    if (isAuthenticated) {
      try {
        await context.storageState({ path: AUTH_STORAGE_PATH });
        console.log(`💾 Saved authentication state to ${AUTH_STORAGE_PATH}\n`);
      } catch (error) {
        console.log(`⚠️  Could not save auth state: ${error.message}\n`);
      }
    }
  }

  for (const pageConfig of pages.slice(0, config.BUDGET.maxPagesPerApp)) {
    // Skip authenticated pages if not authenticated
    if (pageConfig.requiresAuth && !isAuthenticated) {
      console.log(`⏭️  Skipping: ${pageConfig.name} (requires authentication)`);
      capturedPages.push({
        name: pageConfig.name,
        path: pageConfig.path,
        error: 'Requires authentication (credentials not provided)',
        skipped: true,
      });
      continue;
    }
    console.log(`Capturing: ${pageConfig.name} (${pageConfig.path})`);

    try {
      const url = `${BASE_URL}${pageConfig.path}`;
      await page.goto(url, { waitUntil: 'networkidle' });

      // Wait for page to stabilize
      await page.waitForTimeout(500);
      
      // Record actual URL after navigation (to detect redirects)
      const actualUrl = page.url();

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
        actualUrl, // Record actual URL to detect redirects
        requiresAuth: pageConfig.requiresAuth || false,
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
