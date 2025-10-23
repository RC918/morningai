/**
 * Playwright Authentication Setup for Lighthouse CI
 * 
 * This test:
 * 1. Logs in to the application using Supabase credentials
 * 2. Saves the authenticated session state (including cookies)
 * 3. Allows Lighthouse CI to reuse this session for testing protected pages
 * 
 * Environment variables required:
 * - VITE_SUPABASE_URL: Supabase project URL
 * - VITE_SUPABASE_ANON_KEY: Supabase anonymous key
 * - TEST_EMAIL: Test account email
 * - TEST_PASSWORD: Test account password
 */

import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authFile = path.join(__dirname, '../playwright/.auth/storageState.json');

setup('authenticate', async ({ page }) => {
  const testEmail = process.env.TEST_EMAIL;
  const testPassword = process.env.TEST_PASSWORD;

  if (!testEmail || !testPassword) {
    throw new Error('TEST_EMAIL and TEST_PASSWORD environment variables are required');
  }

  console.log('🔐 Starting authentication setup...');
  console.log(`   Email: ${testEmail}`);

  await page.goto('http://localhost:4173/login');

  await page.waitForLoadState('networkidle');

  await page.fill('input[name="username"]', testEmail);
  await page.fill('input[name="password"]', testPassword);

  await page.click('button[type="submit"]');

  await page.waitForURL(/\/(dashboard|home|\/)/, { timeout: 15000 });

  const currentUrl = page.url();
  console.log(`✅ Authentication successful, current URL: ${currentUrl}`);

  await page.context().storageState({ path: authFile });

  console.log(`✅ Session saved to: ${authFile}`);
});
