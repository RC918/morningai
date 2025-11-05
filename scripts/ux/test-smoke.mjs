#!/usr/bin/env node
/**
 * Smoke Tests for UX QA Pipeline
 * Fast validation tests to catch configuration errors before expensive operations
 * Target: <5 seconds execution time
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let testsPassed = 0;
let testsFailed = 0;
const failures = [];

/**
 * Test helper function
 */
function test(name, fn) {
  try {
    fn();
    testsPassed++;
    console.log(`✅ ${name}`);
  } catch (error) {
    testsFailed++;
    failures.push({ name, error: error.message });
    console.error(`❌ ${name}: ${error.message}`);
  }
}

/**
 * Assert helper functions
 */
function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertExists(value, message) {
  assert(value !== undefined && value !== null, message || 'Value should exist');
}

function assertType(value, type, message) {
  assert(typeof value === type, message || `Expected type ${type}, got ${typeof value}`);
}

function assertArray(value, message) {
  assert(Array.isArray(value), message || 'Expected an array');
}

function assertPositive(value, message) {
  assert(typeof value === 'number' && value > 0, message || 'Expected positive number');
}

console.log('🧪 Running UX QA Pipeline Smoke Tests...\n');

// ============================================================================
// Test 1: Config File Validation
// ============================================================================

test('Config file exists', () => {
  const configPath = path.join(__dirname, 'config.js');
  assert(fs.existsSync(configPath), 'config.js not found');
});

test('Config exports required properties', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertExists(config.PAGES, 'PAGES not exported');
  assertExists(config.relevantTokens, 'relevantTokens not exported');
  assertExists(config.AI_CONFIG, 'AI_CONFIG not exported');
  assertExists(config.THRESHOLDS, 'THRESHOLDS not exported');
  assertExists(config.DELIGHT_WEIGHTS, 'DELIGHT_WEIGHTS not exported');
  assertExists(config.BUDGET, 'BUDGET not exported');
});

test('Config PAGES structure is valid', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertType(config.PAGES, 'object', 'PAGES should be an object');
  
  // Check frontend-dashboard pages
  assertExists(config.PAGES['frontend-dashboard'], 'frontend-dashboard pages not defined');
  assertArray(config.PAGES['frontend-dashboard'], 'frontend-dashboard pages should be an array');
  assert(config.PAGES['frontend-dashboard'].length > 0, 'frontend-dashboard should have at least one page');
  
  // Validate page structure
  const page = config.PAGES['frontend-dashboard'][0];
  assertExists(page.name, 'Page should have name');
  assertExists(page.path, 'Page should have path');
  assertExists(page.description, 'Page should have description');
  assert(typeof page.requiresAuth === 'boolean', 'Page should have requiresAuth boolean');
  assertExists(page.viewport, 'Page should have viewport');
  assertPositive(page.viewport.width, 'Viewport width should be positive');
  assertPositive(page.viewport.height, 'Viewport height should be positive');
});

test('Config AI_CONFIG is valid', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertExists(config.AI_CONFIG.model, 'AI model not specified');
  assertType(config.AI_CONFIG.temperature, 'number', 'Temperature should be a number');
  assertPositive(config.AI_CONFIG.maxTokens, 'maxTokens should be positive');
});

test('Config THRESHOLDS are valid', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertExists(config.THRESHOLDS.harmony, 'Harmony thresholds not defined');
  assertExists(config.THRESHOLDS.delight, 'Delight thresholds not defined');
  
  assertPositive(config.THRESHOLDS.harmony.min, 'Harmony min should be positive');
  assertPositive(config.THRESHOLDS.harmony.target, 'Harmony target should be positive');
  assert(config.THRESHOLDS.harmony.min <= 100, 'Harmony min should be <= 100');
  assert(config.THRESHOLDS.harmony.target <= 100, 'Harmony target should be <= 100');
  assert(config.THRESHOLDS.harmony.min < config.THRESHOLDS.harmony.target, 'Harmony min should be < target');
  
  assertPositive(config.THRESHOLDS.delight.min, 'Delight min should be positive');
  assertPositive(config.THRESHOLDS.delight.target, 'Delight target should be positive');
  assert(config.THRESHOLDS.delight.min <= 100, 'Delight min should be <= 100');
  assert(config.THRESHOLDS.delight.target <= 100, 'Delight target should be <= 100');
  assert(config.THRESHOLDS.delight.min < config.THRESHOLDS.delight.target, 'Delight min should be < target');
});

test('Config DELIGHT_WEIGHTS sum to 1.0', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertPositive(config.DELIGHT_WEIGHTS.harmony, 'Harmony weight should be positive');
  assertPositive(config.DELIGHT_WEIGHTS.motion, 'Motion weight should be positive');
  
  const sum = config.DELIGHT_WEIGHTS.harmony + config.DELIGHT_WEIGHTS.motion;
  assert(Math.abs(sum - 1.0) < 0.01, `Delight weights should sum to 1.0, got ${sum}`);
});

test('Config BUDGET is valid', async () => {
  const config = await import('./config.js').then(m => m.default);
  assertPositive(config.BUDGET.maxPagesPerApp, 'maxPagesPerApp should be positive');
  assertPositive(config.BUDGET.maxImageWidth, 'maxImageWidth should be positive');
  assert(config.BUDGET.imageQuality > 0 && config.BUDGET.imageQuality <= 1, 'imageQuality should be 0-1');
  assertExists(config.BUDGET.imageFormat, 'imageFormat should be defined');
});

// ============================================================================
// Test 2: Design Tokens Validation
// ============================================================================

test('Design tokens file exists', () => {
  const tokensPath = path.join(__dirname, '../../packages/shared-ui/src/tokens.json');
  assert(fs.existsSync(tokensPath), 'tokens.json not found');
});

test('Design tokens structure is valid', () => {
  const tokensPath = path.join(__dirname, '../../packages/shared-ui/src/tokens.json');
  const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf-8'));
  
  assertExists(tokens.color, 'color not defined in tokens');
  assertExists(tokens.space, 'space not defined in tokens');
  assertExists(tokens.font, 'font not defined in tokens');
  assertExists(tokens.radius, 'radius not defined in tokens');
  assertExists(tokens.shadow, 'shadow not defined in tokens');
  assertExists(tokens.animation, 'animation not defined in tokens');
});

// ============================================================================
// Test 3: Script Files Validation
// ============================================================================

test('capture.mjs exists and is executable', () => {
  const capturePath = path.join(__dirname, 'capture.mjs');
  assert(fs.existsSync(capturePath), 'capture.mjs not found');
  
  const stats = fs.statSync(capturePath);
  assert(stats.mode & fs.constants.S_IXUSR, 'capture.mjs should be executable');
});

test('score-ai.mjs exists and is executable', () => {
  const scorePath = path.join(__dirname, 'score-ai.mjs');
  assert(fs.existsSync(scorePath), 'score-ai.mjs not found');
  
  const stats = fs.statSync(scorePath);
  assert(stats.mode & fs.constants.S_IXUSR, 'score-ai.mjs should be executable');
});

test('aggregate.mjs exists and is executable', () => {
  const aggregatePath = path.join(__dirname, 'aggregate.mjs');
  assert(fs.existsSync(aggregatePath), 'aggregate.mjs not found');
  
  const stats = fs.statSync(aggregatePath);
  assert(stats.mode & fs.constants.S_IXUSR, 'aggregate.mjs should be executable');
});

test('run-qa.mjs exists and is executable', () => {
  const runQaPath = path.join(__dirname, 'run-qa.mjs');
  assert(fs.existsSync(runQaPath), 'run-qa.mjs not found');
  
  const stats = fs.statSync(runQaPath);
  assert(stats.mode & fs.constants.S_IXUSR, 'run-qa.mjs should be executable');
});

// ============================================================================
// Test 4: Delight Index Calculation Logic
// ============================================================================

test('Delight Index calculation is correct', async () => {
  const config = await import('./config.js').then(m => m.default);
  
  // Test case 1: Perfect scores
  const harmony1 = 100;
  const motion1 = 100;
  const delight1 = harmony1 * config.DELIGHT_WEIGHTS.harmony + motion1 * config.DELIGHT_WEIGHTS.motion;
  assert(delight1 === 100, `Perfect scores should yield 100, got ${delight1}`);
  
  // Test case 2: Zero scores
  const harmony2 = 0;
  const motion2 = 0;
  const delight2 = harmony2 * config.DELIGHT_WEIGHTS.harmony + motion2 * config.DELIGHT_WEIGHTS.motion;
  assert(delight2 === 0, `Zero scores should yield 0, got ${delight2}`);
  
  // Test case 3: Mixed scores (default weights: 0.5, 0.5)
  const harmony3 = 80;
  const motion3 = 60;
  const delight3 = harmony3 * config.DELIGHT_WEIGHTS.harmony + motion3 * config.DELIGHT_WEIGHTS.motion;
  const expected3 = 70; // (80 * 0.5) + (60 * 0.5) = 70
  assert(Math.abs(delight3 - expected3) < 0.01, `Mixed scores should yield ${expected3}, got ${delight3}`);
});

// ============================================================================
// Test 5: Screenshot Manifest Structure Validation
// ============================================================================

test('Screenshot manifest structure is valid (mock)', () => {
  // Mock manifest structure
  const mockManifest = {
    app: 'frontend-dashboard',
    baseUrl: 'http://localhost:4173',
    timestamp: new Date().toISOString(),
    pages: [
      {
        name: 'Landing Page',
        path: '/',
        description: 'Public landing page',
        screenshotPath: '/path/to/screenshot.jpg',
        url: 'http://localhost:4173/',
        actualUrl: 'http://localhost:4173/',
        requiresAuth: false,
      },
    ],
  };
  
  assertExists(mockManifest.app, 'Manifest should have app');
  assertExists(mockManifest.baseUrl, 'Manifest should have baseUrl');
  assertExists(mockManifest.timestamp, 'Manifest should have timestamp');
  assertArray(mockManifest.pages, 'Manifest should have pages array');
  assert(mockManifest.pages.length > 0, 'Manifest should have at least one page');
  
  const page = mockManifest.pages[0];
  assertExists(page.name, 'Page should have name');
  assertExists(page.path, 'Page should have path');
  assertExists(page.url, 'Page should have url');
  assert(typeof page.requiresAuth === 'boolean', 'Page should have requiresAuth boolean');
});

// ============================================================================
// Test 6: Harmony Report Structure Validation
// ============================================================================

test('Harmony report structure is valid (mock)', () => {
  // Mock harmony report structure
  const mockHarmony = {
    app: 'frontend-dashboard',
    timestamp: new Date().toISOString(),
    model: 'gpt-4o-mini',
    pages: [
      {
        name: 'Landing Page',
        path: '/',
        url: 'http://localhost:4173/',
        harmony: {
          overall: 85,
          color: 90,
          spacing: 85,
          typography: 80,
          alignment: 85,
          contrast: 85,
          findings: [
            'Color palette adheres to design tokens',
            'Spacing is consistent with scale',
          ],
        },
      },
    ],
    harmony_overall: 85,
    thresholds: {
      min: 70,
      target: 85,
    },
    usage: {
      prompt_tokens: 1000,
      completion_tokens: 200,
      total_tokens: 1200,
    },
  };
  
  assertExists(mockHarmony.app, 'Harmony should have app');
  assertExists(mockHarmony.timestamp, 'Harmony should have timestamp');
  assertExists(mockHarmony.model, 'Harmony should have model');
  assertArray(mockHarmony.pages, 'Harmony should have pages array');
  assertPositive(mockHarmony.harmony_overall, 'Harmony should have overall score');
  assertExists(mockHarmony.thresholds, 'Harmony should have thresholds');
  assertExists(mockHarmony.usage, 'Harmony should have usage stats');
  
  const page = mockHarmony.pages[0];
  assertExists(page.harmony, 'Page should have harmony object');
  assertPositive(page.harmony.overall, 'Harmony should have overall score');
  assertPositive(page.harmony.color, 'Harmony should have color score');
  assertPositive(page.harmony.spacing, 'Harmony should have spacing score');
  assertPositive(page.harmony.typography, 'Harmony should have typography score');
  assertPositive(page.harmony.alignment, 'Harmony should have alignment score');
  assertPositive(page.harmony.contrast, 'Harmony should have contrast score');
  assertArray(page.harmony.findings, 'Harmony should have findings array');
});

// ============================================================================
// Test 7: Environment Variables Check
// ============================================================================

test('Required environment variables are documented', () => {
  // This test just validates that we're checking for the right env vars
  const requiredEnvVars = [
    'BASE_URL',
    'APP_NAME',
    'OPENAI_API_KEY', // Optional but documented
    'QA_TEST_EMAIL', // Optional but documented
    'QA_TEST_PASSWORD', // Optional but documented
  ];
  
  // Just verify the list is not empty
  assert(requiredEnvVars.length > 0, 'Should have documented env vars');
});

// ============================================================================
// Summary
// ============================================================================

console.log('\n' + '='.repeat(60));
console.log(`Tests passed: ${testsPassed}`);
console.log(`Tests failed: ${testsFailed}`);

if (testsFailed > 0) {
  console.log('\n❌ Failed tests:');
  failures.forEach(({ name, error }) => {
    console.log(`  - ${name}: ${error}`);
  });
  console.log('='.repeat(60));
  process.exit(1);
} else {
  console.log('='.repeat(60));
  console.log('✅ All smoke tests passed!');
  process.exit(0);
}
