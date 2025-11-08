#!/usr/bin/env node
/**
 * Enhanced i18n Coverage Testing Script
 * Week 4 Improvements:
 * - ICU/pluralization support detection
 * - Ignore list for intentional untranslated strings
 * - Per-namespace statistics
 * - Flexible threshold validation
 * 
 * Part of UX Ops Pipeline - Week 4
 */

const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, '../i18n-test-results');
const LOCALES_DIR = path.join(__dirname, '../src/locales');
const CONFIG_PATH = path.join(__dirname, '../i18n-coverage-config.json');

// Default configuration
const DEFAULT_CONFIG = {
  primaryLocale: 'en-US',
  secondaryLocales: ['zh-TW'],
  thresholds: {
    global: 95,
    perNamespace: {
      // Can specify different thresholds per namespace
      // e.g., "common": 100, "errors": 98
    }
  },
  ignorePatterns: [
    // Patterns for keys that should be ignored in coverage calculation
    // e.g., "debug.*", "test.*"
  ],
  ignoreKeys: [
    // Specific keys to ignore
    // e.g., "common.appName", "common.version"
  ],
  detectPluralization: true,
  detectICU: true
};

/**
 * Load configuration from file or use defaults
 */
function loadConfig() {
  if (fs.existsSync(CONFIG_PATH)) {
    try {
      const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
      return { ...DEFAULT_CONFIG, ...config };
    } catch (error) {
      console.warn(`⚠️  Failed to load config from ${CONFIG_PATH}, using defaults`);
      return DEFAULT_CONFIG;
    }
  }
  return DEFAULT_CONFIG;
}

/**
 * Check if a key matches any ignore pattern
 */
function shouldIgnoreKey(key, config) {
  // Check exact matches
  if (config.ignoreKeys.includes(key)) {
    return true;
  }
  
  // Check pattern matches
  for (const pattern of config.ignorePatterns) {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    if (regex.test(key)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Detect if a key uses ICU MessageFormat syntax
 * Examples: {count, plural, one {# item} other {# items}}
 */
function detectICUFormat(value) {
  if (typeof value !== 'string') return false;
  
  // ICU MessageFormat patterns
  const icuPatterns = [
    /\{[^}]+,\s*plural,/,  // plural: {count, plural, one {...} other {...}}
    /\{[^}]+,\s*select,/,  // select: {gender, select, male {...} female {...}}
    /\{[^}]+,\s*selectordinal,/,  // selectordinal
    /\{[^}]+,\s*number,/,  // number formatting
    /\{[^}]+,\s*date,/,    // date formatting
    /\{[^}]+,\s*time,/     // time formatting
  ];
  
  return icuPatterns.some(pattern => pattern.test(value));
}

/**
 * Detect if a key uses i18next pluralization suffix
 * Examples: key_one, key_other, key_zero, key_two, key_few, key_many
 */
function detectI18nextPluralization(key) {
  const pluralSuffixes = ['_zero', '_one', '_two', '_few', '_many', '_other'];
  return pluralSuffixes.some(suffix => key.endsWith(suffix));
}

/**
 * Get namespace from key (first segment before dot)
 */
function getNamespace(key) {
  const parts = key.split('.');
  return parts.length > 1 ? parts[0] : 'root';
}

/**
 * Recursively get all keys from a nested object with metadata
 */
function getAllKeys(obj, prefix = '', config = DEFAULT_CONFIG) {
  const keys = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      keys.push(...getAllKeys(value, fullKey, config));
    } else {
      const metadata = {
        key: fullKey,
        namespace: getNamespace(fullKey),
        ignored: shouldIgnoreKey(fullKey, config),
        hasICU: config.detectICU && detectICUFormat(value),
        hasPluralization: config.detectPluralization && detectI18nextPluralization(fullKey),
        value: value
      };
      keys.push(metadata);
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
 * Group keys by namespace
 */
function groupByNamespace(keys) {
  const namespaces = {};
  
  for (const keyMeta of keys) {
    const ns = keyMeta.namespace;
    if (!namespaces[ns]) {
      namespaces[ns] = [];
    }
    namespaces[ns].push(keyMeta);
  }
  
  return namespaces;
}

/**
 * Calculate coverage for a set of keys
 */
function calculateCoverage(primaryKeys, secondaryKeys, config) {
  // Filter out ignored keys
  const relevantPrimaryKeys = primaryKeys.filter(k => !k.ignored);
  const secondaryKeySet = new Set(secondaryKeys.map(k => k.key));
  
  const covered = relevantPrimaryKeys.filter(k => secondaryKeySet.has(k.key)).length;
  const total = relevantPrimaryKeys.length;
  
  return {
    covered,
    total,
    percentage: total > 0 ? (covered / total) * 100 : 0
  };
}

/**
 * Compare keys and find differences
 */
function compareKeys(primaryKeys, secondaryKeys, config) {
  const primaryKeySet = new Set(primaryKeys.map(k => k.key));
  const secondaryKeySet = new Set(secondaryKeys.map(k => k.key));
  
  // Filter out ignored keys for comparison
  const relevantPrimaryKeys = primaryKeys.filter(k => !k.ignored);
  
  const missing = relevantPrimaryKeys.filter(k => !secondaryKeySet.has(k.key));
  const extra = secondaryKeys.filter(k => !primaryKeySet.has(k.key) && !k.ignored);
  
  return { missing, extra };
}

/**
 * Get threshold for a namespace
 */
function getThresholdForNamespace(namespace, config) {
  if (config.thresholds.perNamespace && config.thresholds.perNamespace[namespace]) {
    return config.thresholds.perNamespace[namespace];
  }
  return config.thresholds.global;
}

/**
 * Analyze namespace coverage
 */
function analyzeNamespaceCoverage(primaryNamespaces, secondaryNamespaces, config) {
  const namespaceResults = {};
  
  for (const [ns, primaryKeys] of Object.entries(primaryNamespaces)) {
    const secondaryKeys = secondaryNamespaces[ns] || [];
    const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);
    const { missing, extra } = compareKeys(primaryKeys, secondaryKeys, config);
    const threshold = getThresholdForNamespace(ns, config);
    
    namespaceResults[ns] = {
      totalKeys: primaryKeys.length,
      relevantKeys: primaryKeys.filter(k => !k.ignored).length,
      ignoredKeys: primaryKeys.filter(k => k.ignored).length,
      coverage: Math.round(coverage.percentage * 100) / 100,
      covered: coverage.covered,
      missing: missing.length,
      extra: extra.length,
      threshold,
      passed: coverage.percentage >= threshold && extra.length === 0,
      missingKeys: missing.slice(0, 10).map(k => k.key),
      extraKeys: extra.slice(0, 10).map(k => k.key),
      icuKeys: primaryKeys.filter(k => k.hasICU).length,
      pluralKeys: primaryKeys.filter(k => k.hasPluralization).length
    };
  }
  
  return namespaceResults;
}

async function runI18nTests() {
  console.log('🌍 Starting Enhanced i18n Coverage Tests...\n');
  
  const config = loadConfig();
  console.log(`Configuration:`);
  console.log(`  Primary locale: ${config.primaryLocale}`);
  console.log(`  Secondary locales: ${config.secondaryLocales.join(', ')}`);
  console.log(`  Global threshold: ${config.thresholds.global}%`);
  console.log(`  Ignore patterns: ${config.ignorePatterns.length}`);
  console.log(`  Ignore keys: ${config.ignoreKeys.length}`);
  console.log(`  Detect ICU: ${config.detectICU}`);
  console.log(`  Detect pluralization: ${config.detectPluralization}\n`);
  
  if (!fs.existsSync(RESULTS_DIR)) {
    fs.mkdirSync(RESULTS_DIR, { recursive: true });
  }
  
  try {
    // Load primary locale
    console.log(`Loading primary locale: ${config.primaryLocale}`);
    const primaryData = loadLocale(config.primaryLocale);
    const primaryKeys = getAllKeys(primaryData, '', config);
    const primaryNamespaces = groupByNamespace(primaryKeys);
    
    const relevantPrimaryKeys = primaryKeys.filter(k => !k.ignored);
    const ignoredPrimaryKeys = primaryKeys.filter(k => k.ignored);
    
    console.log(`  Total keys: ${primaryKeys.length}`);
    console.log(`  Relevant keys: ${relevantPrimaryKeys.length}`);
    console.log(`  Ignored keys: ${ignoredPrimaryKeys.length}`);
    console.log(`  Namespaces: ${Object.keys(primaryNamespaces).length}`);
    
    if (config.detectICU) {
      const icuKeys = primaryKeys.filter(k => k.hasICU);
      console.log(`  ICU format keys: ${icuKeys.length}`);
    }
    
    if (config.detectPluralization) {
      const pluralKeys = primaryKeys.filter(k => k.hasPluralization);
      console.log(`  Pluralization keys: ${pluralKeys.length}`);
    }
    
    console.log();
    
    const results = {
      primary: {
        locale: config.primaryLocale,
        totalKeys: primaryKeys.length,
        relevantKeys: relevantPrimaryKeys.length,
        ignoredKeys: ignoredPrimaryKeys.length,
        namespaces: Object.keys(primaryNamespaces).length,
        icuKeys: primaryKeys.filter(k => k.hasICU).length,
        pluralKeys: primaryKeys.filter(k => k.hasPluralization).length
      },
      secondary: [],
      config: {
        thresholds: config.thresholds,
        ignorePatterns: config.ignorePatterns,
        ignoreKeys: config.ignoreKeys
      }
    };
    
    let allTestsPassed = true;
    
    // Check each secondary locale
    for (const locale of config.secondaryLocales) {
      console.log(`Checking locale: ${locale}`);
      
      try {
        const secondaryData = loadLocale(locale);
        const secondaryKeys = getAllKeys(secondaryData, '', config);
        const secondaryNamespaces = groupByNamespace(secondaryKeys);
        
        const { missing, extra } = compareKeys(primaryKeys, secondaryKeys, config);
        const coverage = calculateCoverage(primaryKeys, secondaryKeys, config);
        const namespaceResults = analyzeNamespaceCoverage(primaryNamespaces, secondaryNamespaces, config);
        
        // Check if all namespaces pass their thresholds
        const allNamespacesPassed = Object.values(namespaceResults).every(ns => ns.passed);
        const passed = coverage.percentage >= config.thresholds.global && extra.length === 0 && allNamespacesPassed;
        
        if (!passed) {
          allTestsPassed = false;
        }
        
        const result = {
          locale,
          totalKeys: secondaryKeys.length,
          relevantKeys: secondaryKeys.filter(k => !k.ignored).length,
          coverage: Math.round(coverage.percentage * 100) / 100,
          covered: coverage.covered,
          missing: missing.length,
          extra: extra.length,
          passed,
          missingKeys: missing.slice(0, 10).map(k => k.key),
          extraKeys: extra.slice(0, 10).map(k => k.key),
          namespaces: namespaceResults,
          icuKeys: secondaryKeys.filter(k => k.hasICU).length,
          pluralKeys: secondaryKeys.filter(k => k.hasPluralization).length
        };
        
        results.secondary.push(result);
        
        console.log(`  Total keys: ${secondaryKeys.length}`);
        console.log(`  Coverage: ${result.coverage}% (threshold: ${config.thresholds.global}%)`);
        console.log(`  Missing keys: ${missing.length}`);
        console.log(`  Extra keys: ${extra.length}`);
        console.log(`  Status: ${passed ? '✅ PASS' : '⚠️  WARNING'}\n`);
        
        // Show namespace breakdown
        console.log(`  Namespace breakdown:`);
        for (const [ns, nsResult] of Object.entries(namespaceResults)) {
          const status = nsResult.passed ? '✅' : '⚠️';
          console.log(`    ${status} ${ns}: ${nsResult.coverage}% (${nsResult.covered}/${nsResult.relevantKeys}, threshold: ${nsResult.threshold}%)`);
        }
        console.log();
        
        if (missing.length > 0) {
          console.log(`  First missing keys:`);
          missing.slice(0, 5).forEach(k => {
            console.log(`    - ${k.key} (${k.namespace})`);
          });
          if (missing.length > 5) {
            console.log(`    ... and ${missing.length - 5} more`);
          }
          console.log();
        }
        
        if (extra.length > 0) {
          console.log(`  Extra keys (not in ${config.primaryLocale}):`);
          extra.slice(0, 5).forEach(k => {
            console.log(`    - ${k.key} (${k.namespace})`);
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
    const reportPath = path.join(RESULTS_DIR, 'i18n-test-report-enhanced.json');
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
    console.error(error.stack);
    process.exit(1);
  }
}

runI18nTests();
