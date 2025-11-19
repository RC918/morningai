#!/usr/bin/env node

/**
 * Computed Style Verification
 * 
 * Verifies that critical CSS styles are correctly applied in production builds.
 * This prevents issues like the Tailwind v4 max-w-* bug where CSS specificity
 * or build ordering causes layout collapse.
 * 
 * Usage:
 *   node scripts/ux/check-computed-styles.mjs <app-name> <base-url>
 * 
 * Example:
 *   node scripts/ux/check-computed-styles.mjs owner-console http://localhost:4174
 */

import { chromium } from '@playwright/test';

const APP_NAME = process.argv[2];
const BASE_URL = process.argv[3] || 'http://localhost:4173';

if (!APP_NAME) {
  console.error('❌ Error: App name is required');
  console.error('Usage: node check-computed-styles.mjs <app-name> <base-url>');
  process.exit(1);
}

const STYLE_CHECKS = {
  'owner-console': [
    {
      name: 'Login Card Max-Width',
      selector: '[data-testid="login-card"]',
      property: 'maxWidth',
      expected: '448px',
      description: 'Verifies Tailwind v4 max-w-md override is applied correctly'
    }
  ],
  'frontend-dashboard': [
    // Add checks for frontend-dashboard if needed
  ]
};

async function checkComputedStyles() {
  console.log('🔍 Computed Style Verification');
  console.log(`App: ${APP_NAME}`);
  console.log(`Base URL: ${BASE_URL}`);
  console.log('');

  const checks = STYLE_CHECKS[APP_NAME] || [];
  
  if (checks.length === 0) {
    console.log(`ℹ️  No style checks configured for ${APP_NAME}`);
    process.exit(0);
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    serviceWorkers: 'block' // Prevent service worker from serving stale bundles
  });
  const page = await context.newPage();

  let allPassed = true;

  try {
    console.log(`📄 Loading ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    console.log('✅ Page loaded\n');

    for (const check of checks) {
      console.log(`🔬 ${check.name}`);
      console.log(`   Selector: ${check.selector}`);
      console.log(`   Property: ${check.property}`);
      console.log(`   Expected: ${check.expected}`);
      
      try {
        // Wait for element to be present
        await page.waitForSelector(check.selector, { timeout: 10000 });
        
        // Get computed style
        const computedValue = await page.$eval(
          check.selector,
          (el, prop) => getComputedStyle(el)[prop],
          check.property
        );

        console.log(`   Computed: ${computedValue}`);

        if (computedValue === check.expected) {
          console.log(`   ✅ PASS\n`);
        } else {
          console.log(`   ❌ FAIL - Expected ${check.expected}, got ${computedValue}\n`);
          allPassed = false;
        }
      } catch (error) {
        console.log(`   ❌ ERROR - ${error.message}\n`);
        allPassed = false;
      }
    }

    // Summary
    console.log('═══════════════════════════════════════');
    if (allPassed) {
      console.log('✅ All computed style checks passed!');
      console.log('═══════════════════════════════════════');
      process.exit(0);
    } else {
      console.log('❌ Some computed style checks failed!');
      console.log('═══════════════════════════════════════');
      console.log('');
      console.log('This indicates that CSS overrides are not being applied correctly.');
      console.log('Common causes:');
      console.log('  - CSS specificity issues');
      console.log('  - Build ordering problems');
      console.log('  - Missing !important declarations');
      console.log('  - Stale CDN/browser cache');
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

checkComputedStyles().catch(error => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});
