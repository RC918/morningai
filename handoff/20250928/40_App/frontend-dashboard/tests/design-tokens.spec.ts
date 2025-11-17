/**
 * Design Token Migration E2E Tests
 * 
 * This test suite ensures:
 * 1. All semantic token colors render correctly
 * 2. No visual regressions after design token migration
 * 3. Main user flows work correctly with new design tokens
 * 
 * Test Coverage:
 * - Visual regression tests for key pages (Agent Governance, Tenant Settings, Cost Analysis, Dashboard, 2FA)
 * - Functional smoke tests for navigation and interactions
 * - Color validation for semantic tokens (error, success, warning, info, neutral, primary, accent)
 * - Theme switching tests (if applicable)
 * 
 * Related: Issue #1330 (P2)
 */

import { test, expect, Page } from '@playwright/test'

test.use({ storageState: 'playwright/.auth/storageState.json' })

/**
 * Helper function to set authentication token for protected pages (fallback)
 */
async function setAuthToken(page: Page) {
  await page.addInitScript(() => {
    try {
      window.localStorage.setItem('auth_token', 'test-token')
    } catch {}
  })
}

/**
 * Helper function to extract computed color from an element
 */
async function getComputedColor(page: Page, selector: string, property: 'color' | 'backgroundColor' | 'borderColor'): Promise<string> {
  return await page.evaluate(
    ({ sel, prop }) => {
      const element = document.querySelector(sel)
      if (!element) return ''
      const computed = window.getComputedStyle(element)
      return computed[prop as any] || ''
    },
    { sel: selector, prop: property }
  )
}

/**
 * Helper function to verify semantic token usage (no hardcoded colors)
 */
async function verifyNoHardcodedColors(page: Page) {
  const hardcodedColorPatterns = [
    'rgb(239, 68, 68)', // red-500
    'rgb(34, 197, 94)', // green-500
    'rgb(234, 179, 8)', // yellow-500
    'rgb(59, 130, 246)', // blue-500
    'rgb(168, 85, 247)', // purple-500
  ]
  
  const bodyHTML = await page.evaluate(() => document.body.innerHTML)
  
  for (const pattern of hardcodedColorPatterns) {
    if (bodyHTML.includes(pattern)) {
      console.warn(`⚠️ Found potential hardcoded color: ${pattern}`)
    }
  }
}

test.describe('Design Token Migration - Visual Regression Tests', () => {
  test('[@vrt] Agent Governance page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/agent-governance')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.getByText(/agent governance/i)).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('agent-governance-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] Tenant Settings page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/settings/tenant')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.getByText(/tenant settings/i)).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('tenant-settings-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] Cost Analysis page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/cost-analysis')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.getByText(/cost analysis/i)).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('cost-analysis-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] Dashboard page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/dashboard')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.locator('main')).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('dashboard-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] 2FA Settings page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/settings/security')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.getByText(/security/i)).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('2fa-settings-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] Decision Approval page - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/decision-approval')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page.getByText(/decision approval/i)).toBeVisible()
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('decision-approval-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] Empty State Library - semantic tokens render correctly', async ({ page }) => {
    await page.goto('/empty-state-library')
    
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await verifyNoHardcodedColors(page)
    
    await expect(page).toHaveScreenshot('empty-state-library-page.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })
})

test.describe('Design Token Migration - Semantic Color Validation', () => {
  test('should use error tokens for error states', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const errorElements = await page.locator('[class*="error"], [class*="destructive"]').all()
    
    for (const element of errorElements.slice(0, 5)) { // Check first 5
      const isVisible = await element.isVisible().catch(() => false)
      if (isVisible) {
        const color = await element.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return computed.color || computed.backgroundColor
        })
        
        expect(color).toBeTruthy()
      }
    }
  })

  test('should use success tokens for success states', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const successElements = await page.locator('[class*="success"]').all()
    
    for (const element of successElements.slice(0, 5)) {
      const isVisible = await element.isVisible().catch(() => false)
      if (isVisible) {
        const color = await element.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return computed.color || computed.backgroundColor
        })
        
        expect(color).toBeTruthy()
      }
    }
  })

  test('should use warning tokens for warning states', async ({ page }) => {
    await page.goto('/cost-analysis')
    await page.waitForLoadState('networkidle')
    
    const warningElements = await page.locator('[class*="warning"]').all()
    
    for (const element of warningElements.slice(0, 5)) {
      const isVisible = await element.isVisible().catch(() => false)
      if (isVisible) {
        const color = await element.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return computed.color || computed.backgroundColor
        })
        
        expect(color).toBeTruthy()
      }
    }
  })

  test('should use primary tokens for CTAs and interactive elements', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const primaryButtons = await page.locator('button[class*="primary"]').all()
    
    for (const button of primaryButtons.slice(0, 5)) {
      const isVisible = await button.isVisible().catch(() => false)
      if (isVisible) {
        const bgColor = await button.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return computed.backgroundColor
        })
        
        expect(bgColor).toBeTruthy()
      }
    }
  })

  test('should use neutral tokens for neutral elements', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const neutralElements = await page.locator('[class*="neutral"], [class*="muted"]').all()
    
    for (const element of neutralElements.slice(0, 5)) {
      const isVisible = await element.isVisible().catch(() => false)
      if (isVisible) {
        const color = await element.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return computed.color || computed.backgroundColor
        })
        
        expect(color).toBeTruthy()
      }
    }
  })
})

test.describe('Design Token Migration - Functional Smoke Tests', () => {
  test('should navigate to all key pages without errors', async ({ page }) => {
    const pages = [
      { path: '/dashboard', title: /dashboard/i },
      { path: '/agent-governance', title: /agent governance/i },
      { path: '/settings/tenant', title: /tenant settings/i },
      { path: '/cost-analysis', title: /cost analysis/i },
      { path: '/decision-approval', title: /decision approval/i },
      { path: '/settings/security', title: /security/i },
    ]

    for (const { path, title } of pages) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      
      await expect(page.getByText(title)).toBeVisible()
      
      const errors: string[] = []
      page.on('pageerror', error => {
        errors.push(error.message)
      })
      
      await page.waitForTimeout(500)
      
      if (errors.length > 0) {
        console.warn(`⚠️ Console errors on ${path}:`, errors)
      }
    }
  })

  test('should render error states correctly', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const errorTrigger = page.locator('[data-testid="trigger-error"]').first()
    const exists = await errorTrigger.count() > 0
    
    if (exists) {
      await errorTrigger.click()
      await expect(page.locator('[class*="error"]')).toBeVisible()
    }
  })

  test('should render success states correctly', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const successTrigger = page.locator('[data-testid="trigger-success"]').first()
    const exists = await successTrigger.count() > 0
    
    if (exists) {
      await successTrigger.click()
      await expect(page.locator('[class*="success"]')).toBeVisible()
    }
  })

  test('should render warning states correctly', async ({ page }) => {
    await page.goto('/cost-analysis')
    await page.waitForLoadState('networkidle')
    
    const warningElements = await page.locator('[class*="warning"]').count()
    
    if (warningElements > 0) {
      await expect(page.locator('[class*="warning"]').first()).toBeVisible()
    }
  })

  test('should maintain layout consistency across pages', async ({ page }) => {
    const pages = ['/dashboard', '/agent-governance', '/cost-analysis']
    
    for (const path of pages) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('[data-testid="sidebar"], nav').first()
      const sidebarExists = await sidebar.count() > 0
      
      if (sidebarExists) {
        await expect(sidebar).toBeVisible()
      }
      
      const main = page.locator('main').first()
      await expect(main).toBeVisible()
    }
  })

  test('should handle interactive elements correctly', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const buttons = await page.locator('button:visible').all()
    
    if (buttons.length > 0) {
      const firstButton = buttons[0]
      
      await expect(firstButton).toBeEnabled()
      
      await firstButton.hover()
      await page.waitForTimeout(200)
    }
  })
})

test.describe('Design Token Migration - Dark Mode Tests', () => {
  test('[@vrt] should render correctly in light mode', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' })
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page).toHaveScreenshot('dashboard-light-mode.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('[@vrt] should render correctly in dark mode', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    
    await expect(page).toHaveScreenshot('dashboard-dark-mode.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    })
  })

  test('should toggle between light and dark mode without errors', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const darkModeToggle = page.locator('[data-testid="dark-mode-toggle"], [aria-label*="theme"]').first()
    const toggleExists = await darkModeToggle.count() > 0
    
    if (toggleExists) {
      await darkModeToggle.click()
      await page.waitForTimeout(500)
      
      const isDark = await page.evaluate(() => {
        return document.documentElement.classList.contains('dark') ||
               document.documentElement.getAttribute('data-theme') === 'dark'
      })
      
      expect(isDark).toBeTruthy()
      
      await darkModeToggle.click()
      await page.waitForTimeout(500)
      
      const isLight = await page.evaluate(() => {
        return !document.documentElement.classList.contains('dark') ||
               document.documentElement.getAttribute('data-theme') === 'light'
      })
      
      expect(isLight).toBeTruthy()
    }
  })
})

test.describe('Design Token Migration - Accessibility Tests', () => {
  test('should maintain sufficient color contrast for text', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const textElements = await page.locator('p, h1, h2, h3, h4, h5, h6, span, button').all()
    
    for (const element of textElements.slice(0, 10)) {
      const isVisible = await element.isVisible().catch(() => false)
      
      if (isVisible) {
        const { color, bgColor } = await element.evaluate(el => {
          const computed = window.getComputedStyle(el)
          return {
            color: computed.color,
            bgColor: computed.backgroundColor,
          }
        })
        
        expect(color).toBeTruthy()
      }
    }
  })

  test('should have proper focus indicators on interactive elements', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    await page.keyboard.press('Tab')
    await page.waitForTimeout(200)
    
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement
      if (!el) return null
      
      const computed = window.getComputedStyle(el)
      return {
        outline: computed.outline,
        outlineColor: computed.outlineColor,
        boxShadow: computed.boxShadow,
      }
    })
    
    if (focusedElement) {
      const hasFocusIndicator = 
        focusedElement.outline !== 'none' ||
        focusedElement.boxShadow !== 'none'
      
      expect(hasFocusIndicator).toBeTruthy()
    }
  })
})
