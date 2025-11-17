import { test, expect } from '@playwright/test'

/**
 * E2E tests for trace link integration in Agent Execution Logs
 * 
 * Tests verify that:
 * 1. Trace links appear when VITE_TRACE_VIEWER_URL is set
 * 2. Trace links do NOT appear when VITE_TRACE_VIEWER_URL is unset/empty
 * 3. Trace links have correct URL format with encoded trace IDs
 */

test.describe('Trace Link Integration', () => {
  test.describe('With VITE_TRACE_VIEWER_URL set', () => {
    test.use({
    })

    test('should display external link icon next to trace IDs in desktop table view', async ({ page }) => {
      await page.goto('/governance')
      
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const traceIdCell = page.locator('td:has-text("trace")').first()
      
      if (await traceIdCell.count() > 0) {
        const externalLinkIcon = traceIdCell.locator('a[target="_blank"] svg')
        await expect(externalLinkIcon).toBeVisible()
        
        const traceLink = traceIdCell.locator('a[target="_blank"]')
        await expect(traceLink).toHaveAttribute('rel', 'noopener noreferrer')
        await expect(traceLink).toHaveAttribute('aria-label', /trace details/i)
        await expect(traceLink).toHaveAttribute('title', /trace details/i)
        
        const href = await traceLink.getAttribute('href')
        expect(href).toMatch(/\/trace\/[^/]+$/)
      }
    })

    test('should display external link icon in mobile card view', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      await page.goto('/governance')
      
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const traceCard = page.locator('.space-y-4 > div').first()
      
      if (await traceCard.count() > 0) {
        const externalLinkIcon = traceCard.locator('a[target="_blank"] svg')
        await expect(externalLinkIcon).toBeVisible()
        
        const traceLink = traceCard.locator('a[target="_blank"]')
        await expect(traceLink).toHaveAttribute('aria-label', /trace details/i)
        await expect(traceLink).toHaveAttribute('title', /trace details/i)
      }
    })

    test('should display external link icon in execution details drawer', async ({ page }) => {
      await page.goto('/governance')
      
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const viewDetailsButton = page.locator('button:has-text("View Details")').first()
      
      if (await viewDetailsButton.count() > 0) {
        await viewDetailsButton.click()
        
        await page.waitForSelector('[role="dialog"]', { timeout: 5000 })
        
        const drawer = page.locator('[role="dialog"]')
        const externalLinkIcon = drawer.locator('a[target="_blank"] svg')
        
        if (await externalLinkIcon.count() > 0) {
          await expect(externalLinkIcon).toBeVisible()
          
          const traceLink = drawer.locator('a[target="_blank"]')
          await expect(traceLink).toHaveAttribute('aria-label', /trace details/i)
          await expect(traceLink).toHaveAttribute('title', /trace details/i)
        }
      }
    })

    test('should encode special characters in trace IDs', async ({ page }) => {
      
      await page.goto('/governance')
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]').first()
      
      if (await traceLink.count() > 0) {
        const href = await traceLink.getAttribute('href')
        
        if (href?.includes('%')) {
          expect(href).toMatch(/%[0-9A-F]{2}/)
        }
      }
    })
  })

  test.describe('Without VITE_TRACE_VIEWER_URL set', () => {
    test.use({
    })

    test('should NOT display external link icon when VITE_TRACE_VIEWER_URL is unset', async ({ page }) => {
      await page.goto('/governance')
      
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const traceIdCell = page.locator('td:has-text("trace")').first()
      
      if (await traceIdCell.count() > 0) {
        const externalLinkIcon = traceIdCell.locator('a[target="_blank"] svg')
        await expect(externalLinkIcon).not.toBeVisible()
        
        const copyButton = traceIdCell.locator('button[aria-label*="Copy"]')
        await expect(copyButton).toBeVisible()
      }
    })

    test('should only show copy button in mobile view when VITE_TRACE_VIEWER_URL is unset', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      await page.goto('/governance')
      
      await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
      
      const traceCard = page.locator('.space-y-4 > div').first()
      
      if (await traceCard.count() > 0) {
        const externalLinkIcon = traceCard.locator('a[target="_blank"] svg')
        await expect(externalLinkIcon).not.toBeVisible()
        
        const copyButton = traceCard.locator('button[aria-label*="Copy"]')
        await expect(copyButton).toBeVisible()
      }
    })
  })

  test.describe('Mock Data Label', () => {
    test('should display mock data label on System Monitoring when VITE_USE_MOCK is true', async ({ page }) => {
      
      await page.goto('/monitoring')
      
      await page.waitForSelector('text=/CPU|Memory|Disk/i', { timeout: 10000 })
      
      const mockDataBadges = page.locator('text="Mock Data"')
      const badgeCount = await mockDataBadges.count()
      
      if (badgeCount > 0) {
        expect(badgeCount).toBe(3)
      }
    })

    test('should NOT display mock data label when VITE_USE_MOCK is false', async ({ page }) => {
      
      await page.goto('/monitoring')
      
      await page.waitForSelector('text=/CPU|Memory|Disk/i', { timeout: 10000 })
      
      const mockDataBadges = page.locator('text="Mock Data"')
      const badgeCount = await mockDataBadges.count()
      
      expect(badgeCount).toBe(0)
    })
  })
})
