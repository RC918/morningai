import { test, expect } from '@playwright/test';

/**
 * Regression test for Tailwind v4 max-w-* utilities
 * 
 * Context: PR #1303 fixed a layout collapse issue where Tailwind v4 incorrectly
 * mapped max-w-md to var(--spacing-md) (16px) instead of 28rem (448px).
 * 
 * This test ensures the fix remains effective and prevents future regressions.
 * 
 * Related:
 * - PR #1303: https://github.com/RC918/morningai/pull/1303
 * - Root cause: theme.css --spacing-* tokens being used for max-width utilities
 * - Solution: Defined separate --max-width-* tokens in theme.css
 */

test.describe('Tailwind v4 max-w-* utilities regression tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('max-w-md should resolve to 28rem (448px), not 16px', async ({ page }) => {
    const container = page.locator('.max-w-md').first();
    
    await expect(container).toBeVisible();
    
    const maxWidth = await container.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.maxWidth;
    });
    
    const maxWidthPx = parseFloat(maxWidth);
    
    expect(maxWidthPx).toBeGreaterThanOrEqual(400);
    
    expect(maxWidthPx).toBeGreaterThanOrEqual(440);
    expect(maxWidthPx).toBeLessThanOrEqual(460);
  });

  test('max-w-md container should have proper width, not collapsed', async ({ page }) => {
    const container = page.locator('.max-w-md').first();
    
    const boundingBox = await container.boundingBox();
    
    expect(boundingBox).not.toBeNull();
    
    if (boundingBox) {
      expect(boundingBox.width).toBeGreaterThan(300);
      
      expect(boundingBox.width).toBeLessThanOrEqual(460);
    }
  });

  test('login form should be horizontally centered and properly sized', async ({ page }) => {
    const container = page.locator('.max-w-md').first();
    
    const viewportSize = page.viewportSize();
    expect(viewportSize).not.toBeNull();
    
    if (viewportSize) {
      const boundingBox = await container.boundingBox();
      expect(boundingBox).not.toBeNull();
      
      if (boundingBox) {
        const containerCenter = boundingBox.x + boundingBox.width / 2;
        const viewportCenter = viewportSize.width / 2;
        
        expect(Math.abs(containerCenter - viewportCenter)).toBeLessThan(50);
        
        expect(boundingBox.width).toBeGreaterThan(300);
      }
    }
  });

  test('all max-w-* utilities should use correct rem values', async ({ page }) => {
    await page.evaluate(() => {
      const testContainer = document.createElement('div');
      testContainer.id = 'max-w-test-container';
      testContainer.style.position = 'absolute';
      testContainer.style.top = '-9999px';
      
      const sizes = ['sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl'];
      const expectedWidths = {
        'sm': 384,   // 24rem
        'md': 448,   // 28rem
        'lg': 512,   // 32rem
        'xl': 576,   // 36rem
        '2xl': 672,  // 42rem
        '3xl': 768,  // 48rem
        '4xl': 896,  // 56rem
        '5xl': 1024, // 64rem
        '6xl': 1152, // 72rem
        '7xl': 1280  // 80rem
      };
      
      sizes.forEach(size => {
        const el = document.createElement('div');
        el.className = `max-w-${size}`;
        el.setAttribute('data-size', size);
        el.setAttribute('data-expected', expectedWidths[size].toString());
        testContainer.appendChild(el);
      });
      
      document.body.appendChild(testContainer);
    });
    
    const sizes = ['sm', 'md', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl'];
    
    for (const size of sizes) {
      const element = page.locator(`[data-size="${size}"]`);
      const expected = await element.getAttribute('data-expected');
      
      const maxWidth = await element.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return parseFloat(styles.maxWidth);
      });
      
      expect(maxWidth).toBeGreaterThanOrEqual(parseFloat(expected!) - 5);
      expect(maxWidth).toBeLessThanOrEqual(parseFloat(expected!) + 5);
    }
    
    await page.evaluate(() => {
      const container = document.getElementById('max-w-test-container');
      if (container) container.remove();
    });
  });
});
