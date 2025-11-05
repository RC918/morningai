import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * 
 * Tests the complete authentication flow including:
 * - Login with email/password
 * - Session persistence
 * - Logout
 * 
 * Note: These tests require a running backend with test credentials
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });
  
  test('should display login page', async ({ page }) => {
    await expect(page).toHaveTitle(/Owner Console/);
    
    await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /password/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible();
  });
  
  test('should show validation errors for empty form', async ({ page }) => {
    const loginButton = page.getByRole('button', { name: /login|sign in/i });
    await loginButton.click();
    
    await expect(page.getByText(/email.*required/i)).toBeVisible();
    await expect(page.getByText(/password.*required/i)).toBeVisible();
  });
  
  test('should show error for invalid credentials', async ({ page }) => {
    await page.getByRole('textbox', { name: /email/i }).fill('invalid@example.com');
    await page.getByRole('textbox', { name: /password/i }).fill('wrongpassword');
    await page.getByRole('button', { name: /login|sign in/i }).click();
    
    await expect(page.getByText(/invalid.*credentials|login failed/i)).toBeVisible();
  });
  
  test.skip('should login successfully with valid credentials', async ({ page }) => {
    const testEmail = process.env.TEST_OWNER_EMAIL || 'test@example.com';
    const testPassword = process.env.TEST_OWNER_PASSWORD || 'testpassword';
    
    await page.getByRole('textbox', { name: /email/i }).fill(testEmail);
    await page.getByRole('textbox', { name: /password/i }).fill(testPassword);
    await page.getByRole('button', { name: /login|sign in/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText(/dashboard|welcome/i)).toBeVisible();
  });
  
  test.skip('should logout successfully', async ({ page, context }) => {
    
    await page.goto('/dashboard');
    
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    await logoutButton.click();
    
    await expect(page).toHaveURL(/\/login/);
    
    const cookies = await context.cookies();
    const authCookies = cookies.filter(c => 
      c.name.includes('access_token') || c.name.includes('refresh_token')
    );
    expect(authCookies).toHaveLength(0);
  });
});
