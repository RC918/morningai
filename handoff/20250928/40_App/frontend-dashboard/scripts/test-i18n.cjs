#!/usr/bin/env node
/**
 * i18n Coverage Testing Script
 * Checks translation coverage and consistency across locales
 * Part of UX Ops Pipeline - Priority 3
 */

const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, '../i18n-test-results');
const LOCALES_DIR = path.join(__dirname, '../src/i18n/locales');

// Primary locale is the source of truth
const PRIMARY_LOCALE = 'en-US';
// Secondary locales to check coverage against
const SECONDARY_LOCALES = ['zh-TW'];

/**
 * Recursively get all keys from a nested object
 */
function getAllKeys(obj, prefix = '') {
  const keys = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      keys.push(...getAllKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  
  return keys;
}

/**
 * Load and parse a locale JSON file
 */
function loadLocale(locale) {
  const filePath = path.join(LOCALES_DIR, `${locale}.json`);
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`Locale file not found: ${filePath}`);
  }
  
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Failed to parse ${locale}.json: ${error.message}`);
  }
}

/**
 * Compare two sets of keys and find differences
 */
function compareKeys(primaryKeys, secondaryKeys) {
  const primarySet = new Set(primaryKeys);
  const secondarySet = new Set(secondaryKeys);
  
  const missing = primaryKeys.filter(key => !secondarySet.has(key));
  const extra = secondaryKeys.filter(key => !primarySet.has(key));
  
  return { missing, extra };
}

/**
 * Calculate coverage percentage
 */
function calculateCoverage(primaryKeys, secondaryKeys) {
  const primarySet = new Set(primaryKeys);
  const secondarySet = new Set(secondaryKeys);
  
  const covered = primaryKeys.filter(key => secondarySet.has(key)).length;
  const total = primaryKeys.length;
  
  return total > 0 ? (covered / total) * 100 : 0;
}

async function runI18nTests() {
  console.log('🌍 Starting i18n Coverage Tests...\n');
  
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }
  
  try {
    // Load primary locale
    console.log(`Loading primary locale: ${PRIMARY_LOCALE}`);
    const primaryData = loadLocale(PRIMARY_LOCALE);
    const primaryKeys = getAllKeys(primaryData);
    
    console.log(`  Total keys in ${PRIMARY_LOCALE}: ${primaryKeys.length}\n`);
    
    const results = {
      primary: {
        locale: PRIMARY_LOCALE,
        totalKeys: primaryKeys.length
      },
      secondary: []
    };
    
    let allTestsPassed = true;
    
    // Check each secondary locale
    for (const locale of SECONDARY_LOCALES) {
      console.log(`Checking locale: ${locale}`);
      
      try {
        const secondaryData = loadLocale(locale);
        const secondaryKeys = getAllKeys(secondaryData);
        
        const { missing, extra } = compareKeys(primaryKeys, secondaryKeys);
        const coverage = calculateCoverage(primaryKeys, secondaryKeys);
        
        // Pass if coverage >= 95% and no extra keys
        const passed = coverage >= 95 && extra.length === 0;
        
        if (!passed) {
          allTestsPassed = false;
        }
        
        const result = {
          locale,
          totalKeys: secondaryKeys.length,
          coverage: Math.round(coverage * 100) / 100,
          missing: missing.length,
          extra: extra.length,
          passed,
          missingKeys: missing.slice(0, 10), // First 10 for brevity
          extraKeys: extra.slice(0, 10) // First 10 for brevity
        };
        
        results.secondary.push(result);
        
        console.log(`  Total keys: ${secondaryKeys.length}`);
        console.log(`  Coverage: ${result.coverage}%`);
        console.log(`  Missing keys: ${missing.length}`);
        console.log(`  Extra keys: ${extra.length}`);
        console.log(`  Status: ${passed ? '✅ PASS' : '⚠️  WARNING'}\n`);
        
        if (missing.length > 0) {
          console.log(`  First missing keys:`);
          missing.slice(0, 5).forEach(key => {
            console.log(`    - ${key}`);
          });
          if (missing.length > 5) {
            console.log(`    ... and ${missing.length - 5} more`);
          }
          console.log();
        }
        
        if (extra.length > 0) {
          console.log(`  Extra keys (not in ${PRIMARY_LOCALE}):`);
          extra.slice(0, 5).forEach(key => {
            console.log(`    - ${key}`);
          });
          if (extra.length > 5) {
            console.log(`    ... and ${extra.length - 5} more`);
          }
          console.log();
        }
        
      } catch (error) {
        console.error(`  ❌ Error: ${error.message}\n`);
        results.secondary.push({
          locale,
          error: error.message,
          passed: false
        });
        allTestsPassed = false;
      }
    }
    
    // Save results
    const reportPath = path.join(RESULTS_DIR, 'i18n-test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify({
      timestamp: new Date().toISOString(),
      passed: allTestsPassed,
      results
    }, null, 2));
    
    console.log(`📊 Results saved to: ${reportPath}`);
    console.log(`\n${allTestsPassed ? '✅ All i18n tests PASSED' : '⚠️  Some i18n tests have WARNINGS'}`);
    
    // Note: We don't exit with error code for i18n warnings in warning mode
    // This is informational only during Phase 3
    process.exit(0);
    
  } catch (error) {
    console.error(`\n❌ Fatal error: ${error.message}`);
    process.exit(1);
  }
}

runI18nTests();
