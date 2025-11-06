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

  console.log('🔐 Setting up authentication...');
  
  // Try primary credentials first, then fallback to mock credentials
  const credentialSets = [
    { username: QA_TEST_EMAIL, password: QA_TEST_PASSWORD, label: 'Primary credentials' },
    { username: 'admin', password: 'admin123', label: 'Mock credentials (admin/admin123)' }
  ];
  
  for (const creds of credentialSets) {
    try {
      console.log(`   Attempting login with ${creds.label}...`);
      
      // Navigate to login page
      await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' });
      
      // Wait for form to be visible
      await page.waitForSelector('input[name="username"]', { state: 'visible', timeout: 10000 });
      
      // Fill in credentials using attribute-based selectors
      await page.fill('input[name="username"]', creds.username);
      await page.fill('input[name="password"]', creds.password);
      
      // Submit form by pressing Enter on password field (more reliable than clicking button)
      await page.press('input[name="password"]', 'Enter');
      
      console.log('   Waiting for authenticated shell (Sidebar) to appear...');
      
      // Wait for the Sidebar to appear (proves authentication succeeded and React state updated)
      // The sidebar is ONLY rendered when isAuthenticated === true
      // Check for either role="navigation" OR aria-label containing "navigation"
      const sidebarLocator = page.locator('nav[role="navigation"], nav[aria-label*="navigation"]').first();
      
      try {
        await sidebarLocator.waitFor({ state: 'visible', timeout: 12000 });
        console.log('   ✓ Sidebar appeared - authentication successful!');
      } catch (timeoutError) {
        console.log(`   Authentication check failed with ${creds.label} - sidebar did not appear`);
        continue; // Try next credential set
      }
      
      // Now navigate to dashboard using SPA client-side routing (preserves React state)
      // Click the dashboard link in the sidebar instead of using page.goto()
      console.log('   Navigating to /dashboard via SPA link...');
      const dashboardLink = page.locator('a[href="/dashboard"]').first();
      await dashboardLink.click();
      
      // Wait for dashboard route to load
      await page.waitForURL(/\/dashboard(\/|$)/, { timeout: 5000 });
      
      // Verify we're still authenticated (sidebar should still be visible)
      const stillAuthenticated = await sidebarLocator.isVisible().catch(() => false);
      
      if (stillAuthenticated) {
        console.log(`✅ Authentication successful with ${creds.label}\n`);
        return true;
      } else {
        console.log(`   Authentication lost after navigation with ${creds.label}`);
      }
    } catch (error) {
      console.log(`   Authentication attempt failed with ${creds.label}: ${error.message}`);
    }
  }
  
  console.error('❌ All authentication attempts failed\n');
  return false;
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
  
  // Split pages into public and authenticated
  const publicPages = pages.filter(p => !p.requiresAuth);
  const authenticatedPages = pages.filter(p => p.requiresAuth);
  
  // PHASE 1: Capture public pages using page.goto()
  console.log('📸 Phase 1: Capturing public pages...\n');
  for (const pageConfig of publicPages.slice(0, config.BUDGET.maxPagesPerApp)) {
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
  
  // PHASE 2: Setup authentication if needed
  let isAuthenticated = false;
  if (authenticatedPages.length > 0) {
    console.log('\n🔐 Phase 2: Setting up authentication...\n');
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
  
  // PHASE 3: Capture authenticated pages using SPA navigation (NO page.goto!)
  if (authenticatedPages.length > 0) {
    console.log('📸 Phase 3: Capturing authenticated pages...\n');
    
    if (!isAuthenticated) {
      console.log('⏭️  Skipping authenticated pages (authentication failed)\n');
      for (const pageConfig of authenticatedPages) {
        capturedPages.push({
          name: pageConfig.name,
          path: pageConfig.path,
          error: 'Requires authentication (credentials not provided)',
          skipped: true,
        });
      }
    } else {
      // We're already on /dashboard after setupAuth(), capture it first
      const sidebarLocator = page.locator('nav[role="navigation"], nav[aria-label*="navigation"]').first();
      
      for (const pageConfig of authenticatedPages.slice(0, config.BUDGET.maxPagesPerApp - publicPages.length)) {
        console.log(`Capturing: ${pageConfig.name} (${pageConfig.path})`);

        try {
          const url = `${BASE_URL}${pageConfig.path}`;
          
          // If not already on this page, navigate via SPA (click sidebar link)
          const currentUrl = page.url();
          if (!currentUrl.includes(pageConfig.path)) {
            console.log(`   Navigating to ${pageConfig.path} via SPA link...`);
            const navLink = page.locator(`a[href="${pageConfig.path}"]`).first();
            await navLink.click();
            await page.waitForURL(new RegExp(pageConfig.path.replace('/', '\\/')), { timeout: 5000 });
          }
          
          // Verify we're still authenticated
          const stillAuthenticated = await sidebarLocator.isVisible().catch(() => false);
          if (!stillAuthenticated) {
            throw new Error('Authentication lost during navigation');
          }
          
          // Scroll to top to ensure above-the-fold content is captured
          await page.evaluate(() => window.scrollTo(0, 0));
          
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
