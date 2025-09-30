#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🧪 Running Frontend Smoke Tests...');

const tests = [
  {
    name: 'CheckoutPage Component Exists',
    test: () => {
      const checkoutPath = path.join(__dirname, '../src/components/CheckoutPage.jsx');
      return fs.existsSync(checkoutPath);
    }
  },
  {
    name: 'Design Tokens File Exists',
    test: () => {
      const tokensPath = path.join(__dirname, '../public/tokens.json');
      return fs.existsSync(tokensPath);
    }
  },
  {
    name: 'Environment Configuration Exists',
    test: () => {
      const envProdPath = path.join(__dirname, '../.env.production');
      const envLocalPath = path.join(__dirname, '../.env.local');
      return fs.existsSync(envProdPath) && fs.existsSync(envLocalPath);
    }
  },
  {
    name: 'CheckoutPage Contains Billing API Integration',
    test: () => {
      const checkoutPath = path.join(__dirname, '../src/components/CheckoutPage.jsx');
      if (!fs.existsSync(checkoutPath)) return false;
      
      const content = fs.readFileSync(checkoutPath, 'utf8');
      return content.includes('/api/billing/plans') && 
             content.includes('/api/billing/checkout/session') &&
             content.includes('useMockData');
    }
  },
  {
    name: 'Build Directory Exists',
    test: () => {
      const distPath = path.join(__dirname, '../dist');
      return fs.existsSync(distPath);
    }
  }
];

let passed = 0;
let failed = 0;

tests.forEach(({ name, test }) => {
  try {
    if (test()) {
      console.log(`✅ ${name}`);
      passed++;
    } else {
      console.log(`❌ ${name}`);
      failed++;
    }
  } catch (error) {
    console.log(`❌ ${name} - Error: ${error.message}`);
    failed++;
  }
});

console.log(`\n📊 Smoke Test Results: ${passed} passed, ${failed} failed`);

if (failed > 0) {
  console.log('❌ Some smoke tests failed');
  process.exit(1);
} else {
  console.log('✅ All smoke tests passed');
  process.exit(0);
}
