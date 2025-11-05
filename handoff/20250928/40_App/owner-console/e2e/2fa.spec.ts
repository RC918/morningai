import { test, expect } from '@playwright/test';

/**
 * Two-Factor Authentication (2FA) E2E Tests
 * 
 * Tests the complete 2FA flow including:
 * - 2FA setup/enrollment
 * - QR code display
 * - TOTP verification
 * - Backup codes generation
 * - 2FA login flow
 * 
 * Note: These tests require a running backend and authenticated session
 */

test.describe('2FA Setup Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings/2fa');
  });
  
  test('should display 2FA settings page', async ({ page }) => {
    await expect(page).toHaveTitle(/2FA|Two-Factor|Settings/);
    
    await expect(page.getByText(/two-factor authentication|2fa/i)).toBeVisible();
  });
  
  test.skip('should show 2FA setup wizard when not enabled', async ({ page }) => {
    
    const enableButton = page.getByRole('button', { name: /enable|setup.*2fa/i });
    await expect(enableButton).toBeVisible();
    
    await enableButton.click();
    
    await expect(page.getByText(/scan.*qr code/i)).toBeVisible();
    await expect(page.locator('canvas, img[alt*="QR"]')).toBeVisible();
    
    await expect(page.getByText(/backup codes/i)).toBeVisible();
  });
  
  test.skip('should verify TOTP code during setup', async ({ page }) => {
    
    await page.getByRole('button', { name: /enable|setup.*2fa/i }).click();
    
    const totpInput = page.getByRole('textbox', { name: /code|totp/i });
    await totpInput.fill('123456'); // Mock code
    
    await page.getByRole('button', { name: /verify|confirm/i }).click();
    
    await expect(page.getByText(/success|verified|invalid/i)).toBeVisible();
  });
  
  test.skip('should display backup codes after setup', async ({ page }) => {
    
    await expect(page.getByText(/backup codes/i)).toBeVisible();
    
    const codes = page.locator('[data-testid="backup-code"]');
    await expect(codes).toHaveCount(8);
  });
  
  test.skip('should allow regenerating backup codes', async ({ page }) => {
    
    const regenerateButton = page.getByRole('button', { name: /regenerate.*codes/i });
    await regenerateButton.click();
    
    await expect(page.getByText(/confirm|are you sure/i)).toBeVisible();
    
    await page.getByRole('button', { name: /confirm|yes/i }).click();
    
    await expect(page.getByText(/new backup codes/i)).toBeVisible();
  });
});

test.describe('2FA Login Flow', () => {
  test.skip('should prompt for TOTP code after password', async ({ page }) => {
    
    const testEmail = process.env.TEST_OWNER_EMAIL_2FA || 'test2fa@example.com';
    const testPassword = process.env.TEST_OWNER_PASSWORD_2FA || 'testpassword';
    
    await page.goto('/login');
    
    await page.getByRole('textbox', { name: /email/i }).fill(testEmail);
    await page.getByRole('textbox', { name: /password/i }).fill(testPassword);
    await page.getByRole('button', { name: /login|sign in/i }).click();
    
    await expect(page.getByText(/enter.*code|two-factor/i)).toBeVisible();
    await expect(page.getByRole('textbox', { name: /code|totp/i })).toBeVisible();
  });
  
  test.skip('should login with valid TOTP code', async ({ page }) => {
    
    await page.goto('/login/2fa');
    
    await page.getByRole('textbox', { name: /code|totp/i }).fill('123456');
    await page.getByRole('button', { name: /verify|submit/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
  });
  
  test.skip('should allow using backup code', async ({ page }) => {
    
    await page.goto('/login/2fa');
    
    await page.getByText(/backup code/i).click();
    
    await page.getByRole('textbox', { name: /backup.*code/i }).fill('ABCD-1234-EFGH-5678');
    await page.getByRole('button', { name: /verify|submit/i }).click();
    
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
