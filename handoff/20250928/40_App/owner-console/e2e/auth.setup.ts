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

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  const username = process.env.TEST_EMAIL || 'admin@morningai.com';
  const password = process.env.TEST_PASSWORD || 'admin123';
  
  console.log(`🔐 Authenticating as: ${username}`);
  
  await page.goto('/login');
  
  await expect(page.locator('[data-testid="login-card"]')).toBeVisible({ timeout: 10000 });
  
  await page.fill('#email', username);
  await page.fill('#password', password);
  
  await page.click('button[type="submit"]');
  
  await expect(page).not.toHaveURL(/\/login(\?|$)/, { timeout: 15000 });
  
  await expect(page).toHaveURL(/\/(dashboard|home)(\?|$)/, { timeout: 5000 });
  
  console.log('✅ Authentication successful');
  
  await page.context().storageState({ path: authFile });
  
  console.log(`💾 Saved authentication state to ${authFile}`);
});
