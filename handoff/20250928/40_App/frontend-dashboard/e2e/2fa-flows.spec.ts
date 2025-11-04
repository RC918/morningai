import { test, expect } from '@playwright/test';

test.describe('2FA Complete User Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('2FA Setup Flow', () => {
    test('should complete full 2FA setup flow', async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[name="email"]', 'test@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.waitForURL('/dashboard');
      
      await page.goto('/settings/security');
      
      const enableButton = page.getByRole('button', { name: /enable 2fa/i });
      await enableButton.click();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button:has-text("Continue")');
      
      await expect(page.locator('img[alt*="QR"]')).toBeVisible();
      
      const secret = await page.locator('[data-testid="totp-secret"]').textContent();
      expect(secret).toBeTruthy();
      
      const backupCodes = await page.locator('[data-testid="backup-code"]').allTextContents();
      expect(backupCodes).toHaveLength(8);
      backupCodes.forEach(code => {
        expect(code).toMatch(/^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
      });
      
      await page.click('button:has-text("Copy All")');
      await expect(page.getByText('Copied!')).toBeVisible();
      
      await page.click('button:has-text("Download")');
      
      await page.click('button:has-text("I\'ve Saved My Backup Codes")');
      
      await page.fill('input[data-testid="totp-input-0"]', '1');
      await page.fill('input[data-testid="totp-input-1"]', '2');
      await page.fill('input[data-testid="totp-input-2"]', '3');
      await page.fill('input[data-testid="totp-input-3"]', '4');
      await page.fill('input[data-testid="totp-input-4"]', '5');
      await page.fill('input[data-testid="totp-input-5"]', '6');
      
      await expect(page.getByText(/2FA Enabled Successfully/i)).toBeVisible();
      
      const statusBadge = page.locator('[data-testid="2fa-status"]');
      await expect(statusBadge).toContainText('Enabled');
    });

    test('should show error for invalid TOTP code during setup', async ({ page }) => {
      await page.goto('/settings/security');
      
      const enableButton = page.getByRole('button', { name: /enable 2fa/i });
      await enableButton.click();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button:has-text("Continue")');
      
      await page.click('button:has-text("I\'ve Saved My Backup Codes")');
      
      await page.fill('input[data-testid="totp-input-0"]', '0');
      await page.fill('input[data-testid="totp-input-1"]', '0');
      await page.fill('input[data-testid="totp-input-2"]', '0');
      await page.fill('input[data-testid="totp-input-3"]', '0');
      await page.fill('input[data-testid="totp-input-4"]', '0');
      await page.fill('input[data-testid="totp-input-5"]', '0');
      
      await expect(page.getByText(/invalid.*code/i)).toBeVisible();
    });

    test('should require password confirmation for setup', async ({ page }) => {
      await page.goto('/settings/security');
      
      const enableButton = page.getByRole('button', { name: /enable 2fa/i });
      await enableButton.click();
      
      await page.click('button:has-text("Continue")');
      
      await expect(page.getByText(/password.*required/i)).toBeVisible();
    });
  });

  test.describe('2FA Login Flow', () => {
    test('should require TOTP code when 2FA is enabled', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await expect(page.getByText(/enter.*verification code/i)).toBeVisible();
      
      const totpInputs = page.locator('input[data-testid^="totp-input-"]');
      await expect(totpInputs).toHaveCount(6);
    });

    test('should login successfully with valid TOTP code', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.fill('input[data-testid="totp-input-0"]', '1');
      await page.fill('input[data-testid="totp-input-1"]', '2');
      await page.fill('input[data-testid="totp-input-2"]', '3');
      await page.fill('input[data-testid="totp-input-3"]', '4');
      await page.fill('input[data-testid="totp-input-4"]', '5');
      await page.fill('input[data-testid="totp-input-5"]', '6');
      
      await page.waitForURL('/dashboard');
      await expect(page).toHaveURL('/dashboard');
    });

    test('should show error for invalid TOTP code during login', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.fill('input[data-testid="totp-input-0"]', '0');
      await page.fill('input[data-testid="totp-input-1"]', '0');
      await page.fill('input[data-testid="totp-input-2"]', '0');
      await page.fill('input[data-testid="totp-input-3"]', '0');
      await page.fill('input[data-testid="totp-input-4"]', '0');
      await page.fill('input[data-testid="totp-input-5"]', '0');
      
      await expect(page.getByText(/invalid.*code/i)).toBeVisible();
    });

    test('should allow login with backup code', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.click('button:has-text("Use backup code")');
      
      await expect(page.locator('input[name="backupCode"]')).toBeVisible();
      
      await page.fill('input[name="backupCode"]', 'ABCD-EFGH-IJKL-MNOP');
      await page.click('button[type="submit"]');
      
      await page.waitForURL('/dashboard');
      await expect(page).toHaveURL('/dashboard');
    });

    test('should show warning when backup codes are low', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.click('button:has-text("Use backup code")');
      await page.fill('input[name="backupCode"]', 'LAST-CODE-HERE-XXXX');
      await page.click('button[type="submit"]');
      
      await expect(page.getByText(/backup codes remaining/i)).toBeVisible();
      await expect(page.getByText(/regenerate/i)).toBeVisible();
    });

    test('should remember device when checkbox is checked', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      await page.check('input[name="rememberDevice"]');
      
      await page.fill('input[data-testid="totp-input-0"]', '1');
      await page.fill('input[data-testid="totp-input-1"]', '2');
      await page.fill('input[data-testid="totp-input-2"]', '3');
      await page.fill('input[data-testid="totp-input-3"]', '4');
      await page.fill('input[data-testid="totp-input-4"]', '5');
      await page.fill('input[data-testid="totp-input-5"]', '6');
      
      await page.waitForURL('/dashboard');
      
      await page.goto('/settings/security');
      const trustedDevices = page.locator('[data-testid="trusted-device"]');
      await expect(trustedDevices).toHaveCount(1);
    });
  });

  test.describe('2FA Disable Flow', () => {
    test('should disable 2FA with password and TOTP code', async ({ page }) => {
      await page.goto('/settings/security');
      
      const disableButton = page.getByRole('button', { name: /disable 2fa/i });
      await disableButton.click();
      
      await expect(page.getByText(/warning/i)).toBeVisible();
      await expect(page.getByText(/less secure/i)).toBeVisible();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      
      await page.fill('input[data-testid="totp-input-0"]', '1');
      await page.fill('input[data-testid="totp-input-1"]', '2');
      await page.fill('input[data-testid="totp-input-2"]', '3');
      await page.fill('input[data-testid="totp-input-3"]', '4');
      await page.fill('input[data-testid="totp-input-4"]', '5');
      await page.fill('input[data-testid="totp-input-5"]', '6');
      
      await page.click('button:has-text("Disable 2FA")');
      
      await expect(page.getByText(/2FA.*disabled/i)).toBeVisible();
      
      const statusBadge = page.locator('[data-testid="2fa-status"]');
      await expect(statusBadge).toContainText('Disabled');
    });

    test('should require both password and TOTP code to disable', async ({ page }) => {
      await page.goto('/settings/security');
      
      const disableButton = page.getByRole('button', { name: /disable 2fa/i });
      await disableButton.click();
      
      await page.click('button:has-text("Disable 2FA")');
      
      await expect(page.getByText(/required/i)).toBeVisible();
    });

    test('should show error for invalid TOTP code when disabling', async ({ page }) => {
      await page.goto('/settings/security');
      
      const disableButton = page.getByRole('button', { name: /disable 2fa/i });
      await disableButton.click();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      
      await page.fill('input[data-testid="totp-input-0"]', '0');
      await page.fill('input[data-testid="totp-input-1"]', '0');
      await page.fill('input[data-testid="totp-input-2"]', '0');
      await page.fill('input[data-testid="totp-input-3"]', '0');
      await page.fill('input[data-testid="totp-input-4"]', '0');
      await page.fill('input[data-testid="totp-input-5"]', '0');
      
      await page.click('button:has-text("Disable 2FA")');
      
      await expect(page.getByText(/invalid.*code/i)).toBeVisible();
    });
  });

  test.describe('Backup Codes Management', () => {
    test('should regenerate backup codes', async ({ page }) => {
      await page.goto('/settings/security');
      
      const regenerateButton = page.getByRole('button', { name: /regenerate/i });
      await regenerateButton.click();
      
      await expect(page.getByText(/warning/i)).toBeVisible();
      await expect(page.getByText(/old.*codes.*no longer work/i)).toBeVisible();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button:has-text("Regenerate Codes")');
      
      const newBackupCodes = await page.locator('[data-testid="backup-code"]').allTextContents();
      expect(newBackupCodes).toHaveLength(8);
      
      await page.click('button:has-text("Copy All")');
      await expect(page.getByText('Copied!')).toBeVisible();
    });

    test('should require password to regenerate backup codes', async ({ page }) => {
      await page.goto('/settings/security');
      
      const regenerateButton = page.getByRole('button', { name: /regenerate/i });
      await regenerateButton.click();
      
      await page.click('button:has-text("Regenerate Codes")');
      
      await expect(page.getByText(/password.*required/i)).toBeVisible();
    });

    test('should show backup codes count', async ({ page }) => {
      await page.goto('/settings/security');
      
      const codesRemaining = page.locator('[data-testid="backup-codes-remaining"]');
      await expect(codesRemaining).toBeVisible();
      await expect(codesRemaining).toContainText(/\d+ codes remaining/i);
    });
  });

  test.describe('Trusted Devices Management', () => {
    test('should display list of trusted devices', async ({ page }) => {
      await page.goto('/settings/security');
      
      const trustedDevicesSection = page.locator('[data-testid="trusted-devices"]');
      await expect(trustedDevicesSection).toBeVisible();
      
      const devices = page.locator('[data-testid="trusted-device"]');
      const deviceCount = await devices.count();
      
      if (deviceCount > 0) {
        const firstDevice = devices.first();
        await expect(firstDevice).toContainText(/last used/i);
        await expect(firstDevice).toContainText(/expires/i);
      }
    });

    test('should revoke trusted device', async ({ page }) => {
      await page.goto('/settings/security');
      
      const devices = page.locator('[data-testid="trusted-device"]');
      const initialCount = await devices.count();
      
      if (initialCount > 0) {
        const revokeButton = devices.first().locator('button:has-text("Revoke")');
        await revokeButton.click();
        
        await expect(page.getByText(/device.*revoked/i)).toBeVisible();
        
        const newCount = await devices.count();
        expect(newCount).toBe(initialCount - 1);
      }
    });

    test('should show expiry warning for expiring devices', async ({ page }) => {
      await page.goto('/settings/security');
      
      const expiringDevices = page.locator('[data-testid="trusted-device"]:has-text("expiring soon")');
      const count = await expiringDevices.count();
      
      if (count > 0) {
        await expect(expiringDevices.first()).toContainText(/expiring soon/i);
      }
    });
  });

  test.describe('2FA Status Display', () => {
    test('should show 2FA status on settings page', async ({ page }) => {
      await page.goto('/settings/security');
      
      const statusCard = page.locator('[data-testid="2fa-status-card"]');
      await expect(statusCard).toBeVisible();
      
      const status = page.locator('[data-testid="2fa-status"]');
      await expect(status).toBeVisible();
      await expect(status).toContainText(/(enabled|disabled)/i);
    });

    test('should show enabled date when 2FA is enabled', async ({ page }) => {
      await page.goto('/settings/security');
      
      const status = page.locator('[data-testid="2fa-status"]');
      const statusText = await status.textContent();
      
      if (statusText?.toLowerCase().includes('enabled')) {
        await expect(page.getByText(/enabled on/i)).toBeVisible();
      }
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels on TOTP inputs', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      for (let i = 0; i < 6; i++) {
        const input = page.locator(`input[data-testid="totp-input-${i}"]`);
        await expect(input).toHaveAttribute('aria-label', new RegExp(`digit ${i + 1}`, 'i'));
      }
    });

    test('should be keyboard navigable', async ({ page }) => {
      await page.goto('/settings/security');
      
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      const enableButton = page.getByRole('button', { name: /enable 2fa/i });
      await expect(enableButton).toBeFocused();
      
      await page.keyboard.press('Enter');
      
      await expect(page.locator('input[name="password"]')).toBeVisible();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle network errors gracefully', async ({ page }) => {
      await page.route('**/api/auth/v2/totp/setup', route => route.abort());
      
      await page.goto('/settings/security');
      
      const enableButton = page.getByRole('button', { name: /enable 2fa/i });
      await enableButton.click();
      
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button:has-text("Continue")');
      
      await expect(page.getByText(/error/i)).toBeVisible();
    });

    test('should handle rate limiting', async ({ page }) => {
      await page.goto('/login');
      
      await page.fill('input[name="email"]', 'user-with-2fa@example.com');
      await page.fill('input[name="password"]', 'TestPassword123!');
      await page.click('button[type="submit"]');
      
      for (let i = 0; i < 6; i++) {
        await page.fill('input[data-testid="totp-input-0"]', '0');
        await page.fill('input[data-testid="totp-input-1"]', '0');
        await page.fill('input[data-testid="totp-input-2"]', '0');
        await page.fill('input[data-testid="totp-input-3"]', '0');
        await page.fill('input[data-testid="totp-input-4"]', '0');
        await page.fill('input[data-testid="totp-input-5"]', '0');
        
        await page.waitForTimeout(500);
      }
      
      await expect(page.getByText(/too many attempts/i)).toBeVisible();
    });
  });
});
