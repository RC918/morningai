#!/usr/bin/env node

/**
 * i18n Violation Baseline Check
 * 
 * This script enforces the i18n violation baseline by:
 * 1. Running ESLint on both frontend-dashboard and owner-console
 * 2. Counting i18next/no-literal-string violations
 * 3. Comparing against the baseline in scripts/i18n-baseline.json
 * 4. Failing if current violations exceed baseline for any app
 * 
 * This prevents regressions while allowing the team to gradually reduce violations.
 */

import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

const baselinePath = join(__dirname, 'i18n-baseline.json');
const baseline = JSON.parse(readFileSync(baselinePath, 'utf8'));

console.log('🔍 Checking i18n violations against baseline...\n');
console.log(`Baseline: ${baseline.baseline_commit} (${baseline.baseline_date})`);
console.log(`Baseline violations: frontend-dashboard=${baseline.violations['frontend-dashboard']}, owner-console=${baseline.violations['owner-console']}\n`);

const apps = [
  { name: 'frontend-dashboard', path: 'handoff/20250928/40_App/frontend-dashboard' },
  { name: 'owner-console', path: 'handoff/20250928/40_App/owner-console' }
];

let hasRegression = false;
const results = {};

for (const app of apps) {
  console.log(`Checking ${app.name}...`);
  
  try {
    const appPath = join(rootDir, app.path);
    
    // Use ESLint JSON formatter for reliable parsing
    const lintOutput = execSync('pnpm exec eslint "src/**/*.{js,jsx,ts,tsx}" --format json --no-color 2>&1', {
      cwd: appPath,
      encoding: 'utf8',
      stdio: 'pipe'
    });
    
    // Parse JSON output and count i18next/no-literal-string violations
    let violations = 0;
    try {
      const results = JSON.parse(lintOutput);
      violations = results.reduce((count, file) => {
        return count + file.messages.filter(msg => msg.ruleId === 'i18next/no-literal-string').length;
      }, 0);
    } catch (parseError) {
      // Fallback to grep if JSON parsing fails
      console.log(`  ⚠️  JSON parsing failed, falling back to grep method`);
      violations = (lintOutput.match(/i18next\/no-literal-string/g) || []).length;
    }
    
    const baselineCount = baseline.violations[app.name];
    results[app.name] = violations;
    
    console.log(`  Current: ${violations} violations`);
    console.log(`  Baseline: ${baselineCount} violations`);
    
    if (violations > baselineCount) {
      console.log(`  ❌ REGRESSION: ${violations - baselineCount} new violations!\n`);
      hasRegression = true;
    } else if (violations < baselineCount) {
      console.log(`  ✅ IMPROVEMENT: ${baselineCount - violations} violations fixed!\n`);
    } else {
      console.log(`  ✓ No change\n`);
    }
  } catch (error) {
    // ESLint exits with non-zero when there are violations
    const lintOutput = error.stdout || error.stderr || '';
    
    let violations = 0;
    try {
      const results = JSON.parse(lintOutput);
      violations = results.reduce((count, file) => {
        return count + file.messages.filter(msg => msg.ruleId === 'i18next/no-literal-string').length;
      }, 0);
    } catch (parseError) {
      // Fallback to grep if JSON parsing fails
      console.log(`  ⚠️  JSON parsing failed, falling back to grep method`);
      violations = (lintOutput.match(/i18next\/no-literal-string/g) || []).length;
    }
    
    const baselineCount = baseline.violations[app.name];
    results[app.name] = violations;
    
    console.log(`  Current: ${violations} violations`);
    console.log(`  Baseline: ${baselineCount} violations`);
    
    if (violations > baselineCount) {
      console.log(`  ❌ REGRESSION: ${violations - baselineCount} new violations!\n`);
      hasRegression = true;
    } else if (violations < baselineCount) {
      console.log(`  ✅ IMPROVEMENT: ${baselineCount - violations} violations fixed!\n`);
    } else {
      console.log(`  ✓ No change\n`);
    }
  }
}

console.log('─'.repeat(60));
console.log('\n📊 Summary:');
console.log(`  frontend-dashboard: ${results['frontend-dashboard']} / ${baseline.violations['frontend-dashboard']} (baseline)`);
console.log(`  owner-console: ${results['owner-console']} / ${baseline.violations['owner-console']} (baseline)`);
console.log(`  Total: ${results['frontend-dashboard'] + results['owner-console']} violations\n`);

if (hasRegression) {
  console.log('❌ BASELINE CHECK FAILED: New i18n violations detected!');
  console.log('\nTo fix:');
  console.log('1. Run `pnpm lint` in the affected app to see violations');
  console.log('2. Replace hardcoded strings with t() calls from react-i18next');
  console.log('3. Add translation keys to locale files (en-US.json, zh-TW.json)');
  console.log('\nSee CONTRIBUTING.md for i18n guidelines.\n');
  process.exit(1);
} else {
  console.log('✅ BASELINE CHECK PASSED: No new i18n violations!');
  
  const totalImprovement = 
    (baseline.violations['frontend-dashboard'] - results['frontend-dashboard']) +
    (baseline.violations['owner-console'] - results['owner-console']);
  
  if (totalImprovement > 0) {
    console.log(`\n🎉 Great work! ${totalImprovement} violations fixed since baseline.`);
    console.log('Consider updating the baseline: node scripts/update-i18n-baseline.js\n');
  } else {
    console.log('');
  }
  
  process.exit(0);
}
