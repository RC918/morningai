#!/usr/bin/env node
/**
 * Tolgee Locale File Structure Validator
 * 
 * Validates that locale files:
 * 1. Do not contain Tolgee demo data patterns
 * 2. Have proper nested structure (not flat)
 * 3. Contain expected keys for each app
 * 4. Only include allowed language files
 * 
 * Usage:
 *   node scripts/validate-tolgee-structure.js [path]
 *   
 * Exit codes:
 *   0 - All validations passed
 *   1 - Validation failed (corrupted or invalid data detected)
 */

const fs = require('fs');
const path = require('path');

const APPS = {
  'owner-console': {
    path: 'handoff/20250928/40_App/owner-console/src/locales',
    allowedLocales: ['en.json', 'en-US.json', 'zh-TW.json'],
    requiredKeys: ['dashboard', 'auth', 'settings'],
    forbiddenKeys: ['app-title', 'add-item-add-button', 'delete-item-button', 'add-item-input-placeholder']
  },
  'frontend-dashboard': {
    path: 'handoff/20250928/40_App/frontend-dashboard/src/i18n/locales',
    allowedLocales: ['en-US.json', 'zh-TW.json'],
    requiredKeys: [], // Frontend dashboard may have different structure
    forbiddenKeys: ['app-title', 'add-item-add-button', 'delete-item-button', 'add-item-input-placeholder']
  }
};

const DEMO_PATTERNS = [
  'What to pack',
  'Quoi emballer',
  'Was mitnehmen',
  'add-item-add-button',
  'delete-item-button',
  'add-item-input-placeholder',
  'app-title'
];

let hasErrors = false;

function error(message) {
  console.error(`❌ ERROR: ${message}`);
  hasErrors = true;
}

function warn(message) {
  console.warn(`⚠️  WARNING: ${message}`);
}

function info(message) {
  console.log(`ℹ️  ${message}`);
}

function success(message) {
  console.log(`✅ ${message}`);
}

/**
 * Check if a string contains any demo patterns
 */
function containsDemoPattern(str) {
  return DEMO_PATTERNS.some(pattern => str.includes(pattern));
}

/**
 * Check if an object has nested structure (depth > 1)
 */
function hasNestedStructure(obj, depth = 0) {
  if (typeof obj !== 'object' || obj === null) {
    return depth > 1;
  }
  
  for (const key in obj) {
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      return true; // Found nested object
    }
  }
  
  return false;
}

/**
 * Recursively check all string values in an object for demo patterns
 */
function checkForDemoData(obj, path = '') {
  const issues = [];
  
  for (const key in obj) {
    const currentPath = path ? `${path}.${key}` : key;
    const value = obj[key];
    
    if (containsDemoPattern(key)) {
      issues.push(`Key contains demo pattern: ${currentPath}`);
    }
    
    if (typeof value === 'string') {
      if (containsDemoPattern(value)) {
        issues.push(`Value contains demo pattern: ${currentPath} = "${value}"`);
      }
    } else if (typeof value === 'object' && value !== null) {
      issues.push(...checkForDemoData(value, currentPath));
    }
  }
  
  return issues;
}

/**
 * Validate a single locale file
 */
function validateLocaleFile(filePath, appConfig, fileName) {
  info(`Validating ${filePath}...`);
  
  if (!appConfig.allowedLocales.includes(fileName)) {
    error(`Unexpected locale file: ${fileName} (not in allowed list: ${appConfig.allowedLocales.join(', ')})`);
    return;
  }
  
  let data;
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    data = JSON.parse(content);
  } catch (err) {
    error(`Failed to parse JSON in ${filePath}: ${err.message}`);
    return;
  }
  
  const demoIssues = checkForDemoData(data);
  if (demoIssues.length > 0) {
    error(`Demo data detected in ${filePath}:`);
    demoIssues.forEach(issue => console.error(`  - ${issue}`));
    return;
  }
  
  const forbiddenFound = appConfig.forbiddenKeys.filter(key => key in data);
  if (forbiddenFound.length > 0) {
    error(`Forbidden keys found in ${filePath}: ${forbiddenFound.join(', ')}`);
    return;
  }
  
  if (fileName !== 'en.json' && !hasNestedStructure(data)) {
    warn(`${filePath} has flat structure (expected nested structure)`);
  }
  
  if (appConfig.requiredKeys.length > 0) {
    const missingKeys = appConfig.requiredKeys.filter(key => !(key in data));
    if (missingKeys.length > 0) {
      warn(`Missing expected keys in ${filePath}: ${missingKeys.join(', ')}`);
    }
  }
  
  success(`${filePath} passed validation`);
}

/**
 * Validate all locale files for an app
 */
function validateApp(appName, appConfig, basePath) {
  info(`\n=== Validating ${appName} ===`);
  
  const localesPath = path.join(basePath, appConfig.path);
  
  if (!fs.existsSync(localesPath)) {
    error(`Locales directory not found: ${localesPath}`);
    return;
  }
  
  const files = fs.readdirSync(localesPath).filter(f => f.endsWith('.json'));
  
  const unexpectedFiles = files.filter(f => !appConfig.allowedLocales.includes(f));
  if (unexpectedFiles.length > 0) {
    error(`Unexpected locale files in ${appName}: ${unexpectedFiles.join(', ')}`);
  }
  
  appConfig.allowedLocales.forEach(fileName => {
    const filePath = path.join(localesPath, fileName);
    if (fs.existsSync(filePath)) {
      validateLocaleFile(filePath, appConfig, fileName);
    } else {
      warn(`Expected locale file not found: ${filePath}`);
    }
  });
}

/**
 * Main validation function
 */
function main() {
  const basePath = process.argv[2] || process.cwd();
  
  console.log('🔍 Tolgee Locale File Structure Validator\n');
  info(`Base path: ${basePath}\n`);
  
  for (const [appName, appConfig] of Object.entries(APPS)) {
    validateApp(appName, appConfig, basePath);
  }
  
  console.log('\n' + '='.repeat(50));
  if (hasErrors) {
    console.error('\n❌ VALIDATION FAILED - Corrupted or invalid data detected!');
    console.error('Please fix the issues above before merging.\n');
    process.exit(1);
  } else {
    console.log('\n✅ ALL VALIDATIONS PASSED - Locale files are clean!\n');
    process.exit(0);
  }
}

if (require.main === module) {
  main();
}

module.exports = { validateApp, validateLocaleFile, checkForDemoData };
