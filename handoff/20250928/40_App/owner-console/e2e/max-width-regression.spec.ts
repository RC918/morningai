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

  test('max-w-md utility class should use correct token value', async ({ page }) => {
    const container = page.locator('.max-w-md').first();
    
    const computedMaxWidth = await container.evaluate((el) => {
      return window.getComputedStyle(el).maxWidth;
    });
    
    const maxWidthPx = parseFloat(computedMaxWidth);
    
    expect(maxWidthPx).toBeGreaterThanOrEqual(440);
    expect(maxWidthPx).toBeLessThanOrEqual(460);
  });

  /**
   * P2 Enhancement: Responsive variants tests
   * 
   * Tests that responsive max-w-* utilities (sm:max-w-*, md:max-w-*, etc.)
   * work correctly at different viewport sizes. These variants use the same
   * --max-width-* tokens, so they should resolve to correct rem values.
   * 
   * Note: This is a P2 improvement to ensure comprehensive coverage of
   * responsive breakpoint variants, not just base utilities.
   */
  test.describe('Responsive variants (P2 - comprehensive coverage)', () => {
    test('sm:max-w-md should work at small viewport (640px)', async ({ page }) => {
      await page.setViewportSize({ width: 640, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const testElement = await page.evaluate(() => {
        const div = document.createElement('div');
        div.className = 'sm:max-w-md';
        div.style.width = '100%';
        document.body.appendChild(div);
        return window.getComputedStyle(div).maxWidth;
      });
      
      const maxWidthPx = parseFloat(testElement);
      expect(maxWidthPx).toBeGreaterThanOrEqual(440);
      expect(maxWidthPx).toBeLessThanOrEqual(460);
    });

    test('md:max-w-lg should work at medium viewport (768px)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const testElement = await page.evaluate(() => {
        const div = document.createElement('div');
        div.className = 'md:max-w-lg';
        div.style.width = '100%';
        document.body.appendChild(div);
        return window.getComputedStyle(div).maxWidth;
      });
      
      const maxWidthPx = parseFloat(testElement);
      expect(maxWidthPx).toBeGreaterThanOrEqual(500);
      expect(maxWidthPx).toBeLessThanOrEqual(520);
    });

    test('lg:max-w-xl should work at large viewport (1024px)', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const testElement = await page.evaluate(() => {
        const div = document.createElement('div');
        div.className = 'lg:max-w-xl';
        div.style.width = '100%';
        document.body.appendChild(div);
        return window.getComputedStyle(div).maxWidth;
      });
      
      const maxWidthPx = parseFloat(testElement);
      expect(maxWidthPx).toBeGreaterThanOrEqual(570);
      expect(maxWidthPx).toBeLessThanOrEqual(585);
    });

    test('xl:max-w-2xl should work at extra-large viewport (1280px)', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const testElement = await page.evaluate(() => {
        const div = document.createElement('div');
        div.className = 'xl:max-w-2xl';
        div.style.width = '100%';
        document.body.appendChild(div);
        return window.getComputedStyle(div).maxWidth;
      });
      
      const maxWidthPx = parseFloat(testElement);
      expect(maxWidthPx).toBeGreaterThanOrEqual(665);
      expect(maxWidthPx).toBeLessThanOrEqual(680);
    });

    test('2xl:max-w-4xl should work at 2xl viewport (1536px)', async ({ page }) => {
      await page.setViewportSize({ width: 1536, height: 800 });
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const testElement = await page.evaluate(() => {
        const div = document.createElement('div');
        div.className = '2xl:max-w-4xl';
        div.style.width = '100%';
        document.body.appendChild(div);
        return window.getComputedStyle(div).maxWidth;
      });
      
      const maxWidthPx = parseFloat(testElement);
      expect(maxWidthPx).toBeGreaterThanOrEqual(890);
      expect(maxWidthPx).toBeLessThanOrEqual(905);
    });

    test('all max-w-* sizes should use correct rem values', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      const results = await page.evaluate(() => {
        const sizes = {
          'sm': { class: 'max-w-sm', expected: 384 },   // 24rem
          'md': { class: 'max-w-md', expected: 448 },   // 28rem
          'lg': { class: 'max-w-lg', expected: 512 },   // 32rem
          'xl': { class: 'max-w-xl', expected: 576 },   // 36rem
          '2xl': { class: 'max-w-2xl', expected: 672 }, // 42rem
          '3xl': { class: 'max-w-3xl', expected: 768 }, // 48rem
          '4xl': { class: 'max-w-4xl', expected: 896 }, // 56rem
          '5xl': { class: 'max-w-5xl', expected: 1024 }, // 64rem
          '6xl': { class: 'max-w-6xl', expected: 1152 }, // 72rem
          '7xl': { class: 'max-w-7xl', expected: 1280 }  // 80rem
        };
        
        const results: Record<string, { actual: number; expected: number }> = {};
        
        for (const [size, config] of Object.entries(sizes)) {
          const div = document.createElement('div');
          div.className = config.class;
          div.style.width = '100%';
          document.body.appendChild(div);
          
          const computedMaxWidth = window.getComputedStyle(div).maxWidth;
          const actualPx = parseFloat(computedMaxWidth);
          
          results[size] = {
            actual: actualPx,
            expected: config.expected
          };
          
          document.body.removeChild(div);
        }
        
        return results;
      });
      
      for (const [size, { actual, expected }] of Object.entries(results)) {
        expect(actual, `max-w-${size} should be ~${expected}px`).toBeGreaterThanOrEqual(expected - 10);
        expect(actual, `max-w-${size} should be ~${expected}px`).toBeLessThanOrEqual(expected + 10);
      }
    });
  });
});
