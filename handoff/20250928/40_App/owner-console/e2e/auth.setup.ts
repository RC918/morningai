/**
 * Authentication Setup for Playwright E2E Tests
 * 
 * This setup test runs before all other tests and authenticates with the backend.
 * It saves the authentication state to playwright/.auth/user.json which is then
 * reused by all other tests via the storageState configuration.
 * 
 * Related: Issue #1349 (P0.1: Enable CI Authentication for Owner Console E2E Tests)
 */

import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import { addDiagnosticLogging } from './utils/fixtures';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const authFile = path.resolve(__dirname, '../playwright/.auth/user.json');

setup('authenticate', async ({ page }) => {
  const username = process.env.TEST_EMAIL || 'admin@morningai.com';
  const password = process.env.TEST_PASSWORD || 'admin123';
  
  console.log(`🔐 Authenticating as: ${username}`);
  
  await addDiagnosticLogging(page);
  
  await page.goto('/login');
  
  await expect(page.locator('[data-testid="login-card"]')).toBeVisible({ timeout: 10000 });
  
  await page.fill('#email', username);
  await page.fill('#password', password);
  
  await page.click('button[type="submit"]');
  
  await expect(page).not.toHaveURL(/\/login(\?|$)/, { timeout: 15000 });
  
  await expect(page).toHaveURL(/\/(dashboard|home)(\?|$)/, { timeout: 5000 });
  
  await page.waitForFunction(() => {
    const tokenExpiry = localStorage.getItem('morningai_token_expiry');
    const user = localStorage.getItem('morningai_user');
    return tokenExpiry !== null && user !== null;
  }, { timeout: 10000 });
  
  const longLivedExpiry = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7 days from now
  await page.evaluate((expiry) => {
    localStorage.setItem('morningai_token_expiry', expiry.toString());
  }, longLivedExpiry);
  
  console.log('✅ Authentication successful');
  console.log(`🔒 Set long-lived token expiry: ${new Date(longLivedExpiry).toISOString()} (7 days from now)`);
  
  const storageState = await page.context().storageState({ path: authFile });
  
  console.log(`💾 Saved authentication state to ${authFile}`);
  console.log('📊 StorageState origins:', storageState.origins.map(o => o.origin));
  console.log('📊 Cookies count:', storageState.cookies.length);
  console.log('📊 Cookies for localhost:4173:', storageState.cookies.filter(c => c.domain.includes('localhost')).map(c => c.name));
  
  const localStorageKeys = await page.evaluate(() => {
    return {
      hasTokenExpiry: !!localStorage.getItem('morningai_token_expiry'),
      hasUser: !!localStorage.getItem('morningai_user'),
      hasAccessToken: !!localStorage.getItem('morningai_access_token'),
      tokenExpiry: localStorage.getItem('morningai_token_expiry'),
      tokenExpiryDate: new Date(parseInt(localStorage.getItem('morningai_token_expiry') || '0')).toISOString(),
    };
  });
  console.log('📊 localStorage keys:', localStorageKeys);
});
