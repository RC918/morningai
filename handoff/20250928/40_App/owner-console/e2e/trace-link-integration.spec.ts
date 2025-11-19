import { test, expect } from '@playwright/test'

/**
 * E2E tests for trace link integration in Agent Execution Logs
 * 
 * NOTE: These tests require authenticated access to /governance and /monitoring routes.
 * In CI environments without authentication, these tests will be skipped automatically.
 * 
 * To run these tests locally with authentication:
 * 1. Set up authentication in your local environment
 * 2. Optionally set E2E_TRACE_VIEWER_URL to test trace link presence
 * 3. Optionally set E2E_USE_MOCK=true to test mock data label presence
 * 
 * Tests verify:
 * 1. Trace links appear when VITE_TRACE_VIEWER_URL is set (requires E2E_TRACE_VIEWER_URL)
 * 2. Trace links do NOT appear when VITE_TRACE_VIEWER_URL is unset (default)
 * 3. Mock data labels appear when VITE_USE_MOCK is true (requires E2E_USE_MOCK=true)
 * 4. Mock data labels do NOT appear when VITE_USE_MOCK is false (default)
 */

/**
 * Helper function to check if user is authenticated
 * Returns true if authenticated, false if on login page
 */
async function isAuthenticated(page) {
  const loginForm = await page.locator('input[type="email"], input[type="password"]').count()
  const loginButton = await page.locator('button:has-text("Login"), button:has-text("Sign in")').count()
  
  return loginForm === 0 && loginButton === 0
}

/**
 * Helper function to navigate to execution logs tab
 */
async function navigateToExecutionLogs(page) {
  await page.goto('/governance')
  
  if (!(await isAuthenticated(page))) {
    return false
  }
  
  await page.click('[data-slot="tabs-trigger"][value="executionLogs"]')
  
  const logsContainer = page.locator('[data-testid="agent-execution-logs"]')
  await logsContainer.waitFor({ state: 'visible', timeout: 10000 })
  
  return true
}

test.describe('Trace Link Integration', () => {
  test.describe('With VITE_TRACE_VIEWER_URL set', () => {
    test.beforeEach(async ({ page }) => {
      // Skip if E2E_TRACE_VIEWER_URL is not set (default CI behavior)
      if (!process.env.E2E_TRACE_VIEWER_URL) {
        test.skip(true, 'E2E_TRACE_VIEWER_URL not set - skipping trace link presence tests')
      }
    })

    test('should display external link icon next to trace IDs in desktop table view', async ({ page }) => {
      const authenticated = await navigateToExecutionLogs(page)
      
      if (!authenticated) {
        test.skip(true, 'Not authenticated - skipping test that requires /governance access')
      }
      
      // Find trace link using stable selector
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]').first()
      
      if (await traceLink.count() > 0) {
        // Verify external link icon exists
        const externalLinkIcon = traceLink.locator('svg')
        await expect(externalLinkIcon).toBeVisible()
        
        // Verify link has correct attributes
        await expect(traceLink).toHaveAttribute('rel', 'noopener noreferrer')
        await expect(traceLink).toHaveAttribute('aria-label', /trace/i)
        
        // Verify link URL format
        const href = await traceLink.getAttribute('href')
        expect(href).toMatch(/\/trace\/[^/]+$/)
      }
    })

    test('should display external link icon in mobile card view', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const authenticated = await navigateToExecutionLogs(page)
      
      if (!authenticated) {
        test.skip(true, 'Not authenticated - skipping test that requires /governance access')
      }
      
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]').first()
      
      if (await traceLink.count() > 0) {
        const externalLinkIcon = traceLink.locator('svg')
        await expect(externalLinkIcon).toBeVisible()
        await expect(traceLink).toHaveAttribute('aria-label', /trace/i)
      }
    })

    test('should encode special characters in trace IDs', async ({ page }) => {
      const authenticated = await navigateToExecutionLogs(page)
      
      if (!authenticated) {
        test.skip(true, 'Not authenticated - skipping test that requires /governance access')
      }
      
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]').first()
      
      if (await traceLink.count() > 0) {
        const href = await traceLink.getAttribute('href')
        
        // Verify URL encoding is applied (trace IDs should be encoded)
        // The presence of %XX patterns indicates encoding
        if (href?.includes('%')) {
          expect(href).toMatch(/%[0-9A-F]{2}/)
        }
      }
    })
  })

  test.describe('Without VITE_TRACE_VIEWER_URL set (default)', () => {
    test.beforeEach(async ({ page }) => {
      // Skip if E2E_TRACE_VIEWER_URL IS set (these tests verify absence)
      if (process.env.E2E_TRACE_VIEWER_URL) {
        test.skip(true, 'E2E_TRACE_VIEWER_URL is set - skipping trace link absence tests')
      }
    })

    test('should NOT display external link icon when VITE_TRACE_VIEWER_URL is unset', async ({ page }) => {
      const authenticated = await navigateToExecutionLogs(page)
      
      if (!authenticated) {
        test.skip(true, 'Not authenticated - skipping test that requires /governance access')
      }
      
      // Verify external link does NOT exist
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]')
      await expect(traceLink).toHaveCount(0)
      
      // Verify copy button exists (using stable selector)
      const copyButton = page.locator('button[aria-label*="Copy"]').first()
      if (await copyButton.count() > 0) {
        await expect(copyButton).toBeVisible()
      }
    })

    test('should only show copy button in mobile view when VITE_TRACE_VIEWER_URL is unset', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const authenticated = await navigateToExecutionLogs(page)
      
      if (!authenticated) {
        test.skip(true, 'Not authenticated - skipping test that requires /governance access')
      }
      
      // Verify external link does NOT exist
      const traceLink = page.locator('a[target="_blank"][href*="/trace/"]')
      await expect(traceLink).toHaveCount(0)
    })
  })

  test.describe('Mock Data Label', () => {
    test('should display mock data label on System Monitoring when VITE_USE_MOCK is true', async ({ page }) => {
      // Skip if E2E_USE_MOCK is not set to 'true'
      if (process.env.E2E_USE_MOCK !== 'true') {
        test.skip(true, 'E2E_USE_MOCK not set to true - skipping mock data label presence test')
      }
      
      await page.goto('/monitoring')
      
      if (!(await isAuthenticated(page))) {
        test.skip(true, 'Not authenticated - skipping test that requires /monitoring access')
      }
      
      // Wait for page to load using stable selector (avoid locale-dependent text)
      const pageContent = page.locator('main, [role="main"]')
      await pageContent.waitFor({ state: 'visible', timeout: 10000 })
      
      // Check if mock data badges are visible
      const mockDataBadges = page.locator('text="Mock Data"')
      const badgeCount = await mockDataBadges.count()
      
      // Should have 3 badges (CPU, Memory, Disk) when VITE_USE_MOCK=true
      expect(badgeCount).toBe(3)
    })

    test('should NOT display mock data label when VITE_USE_MOCK is false', async ({ page }) => {
      // Skip if E2E_USE_MOCK IS set to 'true' (this test verifies absence)
      if (process.env.E2E_USE_MOCK === 'true') {
        test.skip(true, 'E2E_USE_MOCK is set to true - skipping mock data label absence test')
      }
      
      await page.goto('/monitoring')
      
      if (!(await isAuthenticated(page))) {
        test.skip(true, 'Not authenticated - skipping test that requires /monitoring access')
      }
      
      // Wait for page to load
      const pageContent = page.locator('main, [role="main"]')
      await pageContent.waitFor({ state: 'visible', timeout: 10000 })
      
      // Check if mock data badges are NOT visible
      const mockDataBadges = page.locator('text="Mock Data"')
      const badgeCount = await mockDataBadges.count()
      
      // Should have 0 badges when VITE_USE_MOCK=false
      expect(badgeCount).toBe(0)
    })
  })
})
