/**
 * Accessibility Smoke Test Script
 * 
 * This script performs quick smoke tests on the 5 Apple components
 * to ensure basic accessibility features are working correctly.
 * 
 * Run with: node scripts/accessibility-smoke-test.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COMPONENTS_DIR = path.join(__dirname, '../src/components/ui');
const COMPONENTS = [
  'apple-live-activity',
  'apple-control-center',
  'apple-spotlight',
  'apple-action-sheet',
  'apple-picker'
];

const REQUIRED_ARIA_ATTRIBUTES = {
  'apple-live-activity': ['role="region"', 'aria-label', 'role="progressbar"', 'aria-valuenow'],
  'apple-control-center': ['role="dialog"', 'aria-modal', 'aria-label'],
  'apple-spotlight': ['role="dialog"', 'aria-modal', 'role="searchbox"', 'role="listbox"'],
  'apple-action-sheet': ['role="dialog"', 'aria-modal', 'aria-labelledby'],
  'apple-picker': ['role="listbox"', 'role="option"', 'aria-selected']
};

const REQUIRED_KEYBOARD_HANDLERS = ['onKeyDown', 'tabIndex'];

console.log('🧪 Starting Accessibility Smoke Test...\n');

let passed = 0;
let failed = 0;
const issues = [];

COMPONENTS.forEach(component => {
  console.log(`\n📦 Testing ${component}...`);
  
  const componentPath = path.join(COMPONENTS_DIR, `${component}.tsx`);
  
  if (!fs.existsSync(componentPath)) {
    console.log(`  ❌ Component file not found`);
    failed++;
    issues.push(`${component}: File not found`);
    return;
  }
  
  const content = fs.readFileSync(componentPath, 'utf-8');
  
  // Check for ARIA attributes
  const requiredAttrs = REQUIRED_ARIA_ATTRIBUTES[component] || [];
  const missingAttrs = [];
  
  requiredAttrs.forEach(attr => {
    if (!content.includes(attr)) {
      missingAttrs.push(attr);
    }
  });
  
  if (missingAttrs.length > 0) {
    console.log(`  ⚠️  Missing ARIA attributes: ${missingAttrs.join(', ')}`);
    issues.push(`${component}: Missing ${missingAttrs.join(', ')}`);
  } else {
    console.log(`  ✅ All required ARIA attributes present`);
  }
  
  // Check for keyboard handlers
  const hasKeyboardSupport = REQUIRED_KEYBOARD_HANDLERS.some(handler => 
    content.includes(handler)
  ) || content.includes('addEventListener') && (content.includes('keydown') || content.includes('keyup') || content.includes('keypress'));
  
  if (!hasKeyboardSupport) {
    console.log(`  ⚠️  No keyboard event handlers found`);
    issues.push(`${component}: Missing keyboard support`);
  } else {
    console.log(`  ✅ Keyboard support detected`);
  }
  
  // Check for screen reader announcements
  const hasScreenReaderSupport = content.includes('useScreenReaderAnnouncement') || 
                                   content.includes('announce');
  
  if (!hasScreenReaderSupport) {
    console.log(`  ⚠️  No screen reader announcements found`);
    issues.push(`${component}: Missing screen reader support`);
  } else {
    console.log(`  ✅ Screen reader support detected`);
  }
  
  // Check for accessibility test file
  const testPath = path.join(COMPONENTS_DIR, `${component}.a11y.test.tsx`);
  const hasA11yTests = fs.existsSync(testPath);
  
  if (!hasA11yTests) {
    console.log(`  ⚠️  No accessibility test file found`);
    issues.push(`${component}: Missing .a11y.test.tsx file`);
  } else {
    console.log(`  ✅ Accessibility test file exists`);
  }
  
  // Overall component status
  if (missingAttrs.length === 0 && hasKeyboardSupport && hasScreenReaderSupport && hasA11yTests) {
    console.log(`  ✨ ${component}: PASSED`);
    passed++;
  } else {
    console.log(`  ❌ ${component}: FAILED`);
    failed++;
  }
});

// Summary
console.log('\n' + '='.repeat(60));
console.log('📊 Smoke Test Summary');
console.log('='.repeat(60));
console.log(`✅ Passed: ${passed}/${COMPONENTS.length}`);
console.log(`❌ Failed: ${failed}/${COMPONENTS.length}`);

if (issues.length > 0) {
  console.log('\n⚠️  Issues Found:');
  issues.forEach(issue => {
    console.log(`  - ${issue}`);
  });
}

console.log('\n' + '='.repeat(60));

if (failed === 0) {
  console.log('🎉 All smoke tests passed!');
  process.exit(0);
} else {
  console.log('❌ Some smoke tests failed. Please review the issues above.');
  process.exit(1);
}
