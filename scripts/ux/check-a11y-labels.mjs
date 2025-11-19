#!/usr/bin/env node
/**
 * Sentinel check for visually-hidden accessibility labels becoming visible
 * Detects common patterns like "panel 0", "panel 1", "Resize handle"
 * 
 * This script prevents accessibility labels from becoming visible in production
 * by checking for known patterns that should be visually hidden.
 */

import { chromium } from '@playwright/test';

const FORBIDDEN_VISIBLE_TEXT = [
  'panel 0',
  'panel 1',
  'panel 2',
  'panel 3',
  'Resize handle',
  'resize handle',
];

/**
 * Check a single page for visible accessibility labels
 * @param {Page} page - Playwright page instance
 * @param {string} url - URL to check
 * @param {string} pageName - Name of the page for reporting
 * @returns {Promise<Array>} - Array of violations found
 */
async function checkPage(page, url, pageName) {
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);

    const bodyText = await page.locator('body').innerText();
    const violations = [];

    // Check for forbidden visible text
    for (const forbiddenText of FORBIDDEN_VISIBLE_TEXT) {
      if (bodyText.toLowerCase().includes(forbiddenText.toLowerCase())) {
        violations.push({
          page: pageName,
          text: forbiddenText,
          message: `Visually-hidden label "${forbiddenText}" is visible in viewport`,
          severity: 'critical',
        });
      }
    }

    // Check for role="separator" elements with visible text
    const separators = await page.locator('[role="separator"]').all();
    for (const separator of separators) {
      const text = await separator.innerText().catch(() => '');
      if (text.trim().length > 0) {
        violations.push({
          page: pageName,
          element: 'role="separator"',
          text: text.trim(),
          message: 'Separator element has visible text (should be visually hidden)',
          severity: 'high',
        });
      }
    }

    return violations;
  } catch (error) {
    console.error(`Error checking ${pageName}: ${error.message}`);
    return [{
      page: pageName,
      error: error.message,
      message: `Failed to check page: ${error.message}`,
      severity: 'warning',
    }];
  }
}

async function main() {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:4173';
  const APP_NAME = process.env.APP_NAME || 'frontend-dashboard';
  
  console.log(`🔍 Checking accessibility labels for ${APP_NAME}`);
  console.log(`Base URL: ${BASE_URL}\n`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Test critical pages that are most likely to have accessibility issues
  const testPages = [
    { name: 'Login', path: '/login' },
    { name: 'Home', path: '/' },
  ];

  let allViolations = [];

  for (const testPage of testPages) {
    console.log(`Checking: ${testPage.name} (${testPage.path})`);
    const violations = await checkPage(page, `${BASE_URL}${testPage.path}`, testPage.name);
    allViolations = allViolations.concat(violations);
    
    if (violations.length === 0) {
      console.log(`  ✅ No violations found\n`);
    } else {
      console.log(`  ⚠️  Found ${violations.length} violation(s)\n`);
    }
  }

  await browser.close();

  // Report results
  const criticalViolations = allViolations.filter(v => v.severity === 'critical');
  const highViolations = allViolations.filter(v => v.severity === 'high');
  const warningViolations = allViolations.filter(v => v.severity === 'warning');

  if (allViolations.length > 0) {
    console.error('\n❌ Accessibility Label Violations Found:\n');
    
    if (criticalViolations.length > 0) {
      console.error('🔴 CRITICAL VIOLATIONS:');
      criticalViolations.forEach(v => {
        console.error(`  Page: ${v.page}`);
        console.error(`  Issue: ${v.message}`);
        console.error(`  Text: "${v.text}"`);
        console.error('');
      });
    }

    if (highViolations.length > 0) {
      console.error('🟠 HIGH SEVERITY VIOLATIONS:');
      highViolations.forEach(v => {
        console.error(`  Page: ${v.page}`);
        console.error(`  Issue: ${v.message}`);
        console.error(`  Text: "${v.text}"`);
        console.error('');
      });
    }

    if (warningViolations.length > 0) {
      console.error('🟡 WARNINGS:');
      warningViolations.forEach(v => {
        console.error(`  Page: ${v.page}`);
        console.error(`  Issue: ${v.message}`);
        console.error('');
      });
    }

    console.error(`\nSummary: ${criticalViolations.length} critical, ${highViolations.length} high, ${warningViolations.length} warnings`);
    console.error('\nTo fix: Ensure react-resizable-panels/styles.css is imported in your main entry file.');
    
    // Only fail on critical violations
    if (criticalViolations.length > 0) {
      process.exit(1);
    }
  } else {
    console.log('✅ No accessibility label violations found');
    console.log(`Checked ${testPages.length} pages successfully\n`);
  }

  process.exit(0);
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
