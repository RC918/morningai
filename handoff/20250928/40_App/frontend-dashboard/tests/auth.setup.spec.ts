/**
 * Playwright Authentication Setup for Lighthouse CI
 * 
 * This test:
 * 1. Logs in to the application using mock credentials
 * 2. Saves the authenticated session state (including localStorage)
 * 3. Allows Lighthouse CI to reuse this session for testing protected pages
 * 
 * Environment variables required:
 * - VITE_SUPABASE_URL: Supabase project URL (optional, falls back to mock auth)
 * - VITE_SUPABASE_ANON_KEY: Supabase anonymous key (optional, falls back to mock auth)
 * - TEST_EMAIL: Test account email (optional, uses admin for mock auth)
 * - TEST_PASSWORD: Test account password (optional, uses admin123 for mock auth)
 */

import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const authDir = path.join(__dirname, '../playwright/.auth');
const authFile = path.join(authDir, 'storageState.json');

setup('authenticate', async ({ page }) => {
  console.log('🔐 Starting authentication setup...');
  
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
    console.log(`✅ Created auth directory: ${authDir}`);
  }

  const username = process.env.TEST_EMAIL || 'admin';
  const password = process.env.TEST_PASSWORD || 'admin123';
  console.log(`   Using credentials: ${username}/${password.replace(/./g, '*')}`);

  await page.goto('http://localhost:4173/login');
  console.log('   Navigated to login page');

  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  console.log('   Cleared browser storage');

  await page.reload();
  console.log('   Reloaded page after clearing storage');

  await page.waitForLoadState('domcontentloaded');
  
  const url = page.url();
  const title = await page.title();
  console.log(`   Current URL: ${url}`);
  console.log(`   Page title: ${title}`);

  await page.addStyleTag({ 
    content: '*, *::before, *::after { animation: none !important; transition: none !important; }' 
  });
  console.log('   Disabled animations');

  const usernameCount = await page.locator('#username').count();
  const passwordCount = await page.locator('#password').count();
  const inputCount = await page.locator('input').count();
  console.log(`   Found ${usernameCount} username input(s) and ${passwordCount} password input(s)`);
  console.log(`   Total input elements: ${inputCount}`);

  if (usernameCount === 0) {
    const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
    console.log(`   Page body text: ${bodyText}`);
  }

  await page.waitForSelector('#username', { state: 'visible', timeout: 30000 });
  console.log('   Username input is visible');

  await page.fill('#username', username);
  await page.fill('#password', password);
  console.log('   Filled in credentials');

  await page.click('button[type="submit"]');
  console.log('   Submitted login form');

  await page.waitForURL(/\/(dashboard|home|\/)/, { timeout: 15000 });

  const currentUrl = page.url();
  console.log(`✅ Authentication successful, current URL: ${currentUrl}`);

  await page.context().storageState({ path: authFile });

  console.log(`✅ Session saved to: ${authFile}`);
  
  if (fs.existsSync(authFile)) {
    const state = JSON.parse(fs.readFileSync(authFile, 'utf8'));
    const localStorageCount = state.origins?.reduce((sum: number, origin: any) => 
      sum + (origin.localStorage?.length || 0), 0) || 0;
    console.log(`✅ Storage state contains ${localStorageCount} localStorage items`);
  }
});
