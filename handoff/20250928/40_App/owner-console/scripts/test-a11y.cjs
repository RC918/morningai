#!/usr/bin/env node
/**
 * Accessibility Testing Script with axe-core
 * Automated runtime a11y testing using Playwright + axe-core
 * Part of UX Ops Pipeline - Follow-up PR
 */

const { chromium } = require('@playwright/test');
const { injectAxe } = require('@axe-core/playwright');
const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, '../a11y-test-results');
const BASE_URL = process.env.BASE_URL || 'http://localhost:4173';

const PAGES_TO_TEST = [
  { name: 'Home', url: '/' },
  { name: 'Dashboard', url: '/dashboard' },
  { name: 'Login', url: '/login' }
];

async function checkServer() {
  try {
    const response = await fetch(BASE_URL);
    return response.ok;
  } catch {
    return false;
  }
}

async function runA11yTests() {
  console.log('♿ Starting Accessibility Tests with axe-core...\n');
  
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();
  
  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(10000);
  
  const results = [];
  let allTestsPassed = true;
  let totalViolations = 0;
  
  for (const testPage of PAGES_TO_TEST) {
    console.log(`Testing: ${testPage.name} (${testPage.url})`);
    
    try {
      await page.goto(`${BASE_URL}${testPage.url}`, { 
        waitUntil: 'domcontentloaded',
        timeout: 10000 
      });
      
      await injectAxe(page);
      
      const violations = await page.evaluate(async () => {
        const axe = window.axe;
        const results = await axe.run();
        return results.violations;
      });
      
      const criticalViolations = violations.filter(v => 
        v.impact === 'critical' || v.impact === 'serious'
      );
      
      const passed = criticalViolations.length === 0;
      
      if (!passed) {
        allTestsPassed = false;
      }
      
      totalViolations += violations.length;
      
      const result = {
        name: testPage.name,
        url: testPage.url,
        passed,
        violations: violations.length,
        critical: violations.filter(v => v.impact === 'critical').length,
        serious: violations.filter(v => v.impact === 'serious').length,
        moderate: violations.filter(v => v.impact === 'moderate').length,
        minor: violations.filter(v => v.impact === 'minor').length,
        details: violations.map(v => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          help: v.help,
          helpUrl: v.helpUrl,
          nodes: v.nodes.length
        }))
      };
      
      results.push(result);
      
      console.log(`  Total violations: ${violations.length}`);
      console.log(`  Critical: ${result.critical}, Serious: ${result.serious}`);
      console.log(`  Moderate: ${result.moderate}, Minor: ${result.minor}`);
      console.log(`  Status: ${passed ? '✅ PASS' : '❌ FAIL'}\n`);
      
      if (!passed) {
        console.log('  Critical/Serious violations:');
        criticalViolations.forEach(v => {
          console.log(`    - ${v.id}: ${v.description}`);
          console.log(`      Impact: ${v.impact}, Nodes: ${v.nodes.length}`);
          console.log(`      Help: ${v.helpUrl}\n`);
        });
      }
      
    } catch (error) {
      console.error(`  ❌ Error: ${error.message}\n`);
      results.push({
        name: testPage.name,
        url: testPage.url,
        error: error.message,
        passed: false
      });
      allTestsPassed = false;
    }
  }
  
  await browser.close();
  
  const reportPath = path.join(RESULTS_DIR, 'a11y-test-report.json');
  fs.writeFileSync(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    passed: allTestsPassed,
    totalViolations,
    results
  }, null, 2));
  
  console.log(`\n📊 Results saved to: ${reportPath}`);
  console.log(`\n${allTestsPassed ? '✅ All a11y tests PASSED' : '❌ Some a11y tests FAILED'}`);
  console.log(`Total violations found: ${totalViolations}`);
  
  process.exit(allTestsPassed ? 0 : 1);
}

(async () => {
  const serverRunning = await checkServer();
  
  if (!serverRunning) {
    console.error(`❌ Error: Development server not running on ${BASE_URL}`);
    console.error('Please start the server with: pnpm run preview');
    process.exit(1);
  }
  
  await runA11yTests();
})();
