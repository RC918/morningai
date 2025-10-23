/**
 * E2E tests for Path Tracking
 * Tests real user journeys with path tracking in browser environment
 */

import { test, expect } from '@playwright/test'

test.describe('Path Tracking E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
      window.sentryMessages = []
      window.sentryExceptions = []
      
      window.Sentry = window.Sentry || {}
      window.Sentry.captureMessage = (message, context) => {
        window.sentryMessages.push({ message, context })
      }
      window.Sentry.captureException = (error, context) => {
        window.sentryExceptions.push({ error: error.message, context })
      }
    })
  })

  test.describe('Login Path Tracking', () => {
    test('should track successful login journey', async ({ page }) => {
      await page.goto('/login')
      
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      
      await page.click('button[type="submit"]')
      
      await page.waitForURL('/', { timeout: 5000 })
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const loginMessage = sentryMessages.find(msg => 
        msg.message.includes('user_login') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(loginMessage).toBeDefined()
      expect(loginMessage.context.extra.pathName).toBe('user_login')
      expect(loginMessage.context.extra.duration).toBeGreaterThan(0)
    })

    test('should track failed login attempt', async ({ page }) => {
      await page.goto('/login')
      
      await page.fill('input[name="username"]', 'wronguser')
      await page.fill('input[name="password"]', 'wrongpass')
      
      await page.click('button[type="submit"]')
      
      await page.waitForSelector('.error-message', { timeout: 5000 })
      
      const sentryExceptions = await page.evaluate(() => window.sentryExceptions)
      
      const loginError = sentryExceptions.find(exc => 
        exc.context.extra.pathName === 'user_login'
      )
      
      expect(loginError).toBeDefined()
      expect(loginError.context.extra.pathName).toBe('user_login')
    })

    test('should trigger TTV event on first login', async ({ page }) => {
      await page.goto('/login')
      
      let ttvEventFired = false
      await page.evaluate(() => {
        window.addEventListener('first-value-operation', (e) => {
          if (e.detail.operation === 'user_login') {
            window.ttvEventFired = true
          }
        })
      })
      
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      
      await page.waitForURL('/', { timeout: 5000 })
      
      ttvEventFired = await page.evaluate(() => window.ttvEventFired)
      expect(ttvEventFired).toBe(true)
    })
  })

  test.describe('Dashboard Path Tracking', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login')
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/', { timeout: 5000 })
      
      await page.evaluate(() => {
        window.sentryMessages = []
      })
    })

    test('should track dashboard save layout', async ({ page }) => {
      await page.click('button:has-text("儲存佈局"), button:has-text("Save Layout")')
      
      await page.waitForSelector('.success-message, .toast-success', { timeout: 5000 })
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const saveMessage = sentryMessages.find(msg => 
        msg.message.includes('dashboard_save_layout') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(saveMessage).toBeDefined()
      expect(saveMessage.context.extra.pathName).toBe('dashboard_save_layout')
      expect(saveMessage.context.extra.duration).toBeGreaterThan(0)
    })

    test('should trigger TTV event on dashboard save', async ({ page }) => {
      let ttvEventFired = false
      await page.evaluate(() => {
        window.addEventListener('first-value-operation', (e) => {
          if (e.detail.operation === 'dashboard_save_layout') {
            window.ttvEventFired = true
          }
        })
      })
      
      await page.click('button:has-text("儲存佈局"), button:has-text("Save Layout")')
      
      await page.waitForSelector('.success-message, .toast-success', { timeout: 5000 })
      
      ttvEventFired = await page.evaluate(() => window.ttvEventFired)
      expect(ttvEventFired).toBe(true)
    })
  })

  test.describe('Decision Approval Path Tracking', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login')
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/', { timeout: 5000 })
      
      await page.click('a[href="/decisions"], nav >> text=決策審批')
      await page.waitForURL('/decisions', { timeout: 5000 })
      
      await page.evaluate(() => {
        window.sentryMessages = []
      })
    })

    test('should track decision approval', async ({ page }) => {
      await page.click('button:has-text("批准"), button:has-text("Approve")').first()
      
      await page.waitForSelector('.toast-success, .success-message', { timeout: 5000 })
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const approveMessage = sentryMessages.find(msg => 
        msg.message.includes('decision_approve') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(approveMessage).toBeDefined()
      expect(approveMessage.context.extra.pathName).toBe('decision_approve')
    })

    test('should track decision rejection', async ({ page }) => {
      await page.click('button:has-text("拒絕"), button:has-text("Reject")').first()
      
      await page.fill('textarea[placeholder*="理由"], textarea[placeholder*="reason"]', 'Not aligned with strategy')
      
      await page.click('button:has-text("確認"), button:has-text("Confirm")')
      
      await page.waitForSelector('.toast-success, .success-message', { timeout: 5000 })
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const rejectMessage = sentryMessages.find(msg => 
        msg.message.includes('decision_reject') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(rejectMessage).toBeDefined()
      expect(rejectMessage.context.extra.pathName).toBe('decision_reject')
    })

    test('should trigger TTV event on decision approval', async ({ page }) => {
      let ttvEventFired = false
      await page.evaluate(() => {
        window.addEventListener('first-value-operation', (e) => {
          if (e.detail.operation === 'decision_approve') {
            window.ttvEventFired = true
          }
        })
      })
      
      await page.click('button:has-text("批准"), button:has-text("Approve")').first()
      
      await page.waitForSelector('.toast-success, .success-message', { timeout: 5000 })
      
      ttvEventFired = await page.evaluate(() => window.ttvEventFired)
      expect(ttvEventFired).toBe(true)
    })
  })

  test.describe('Cost Analysis Path Tracking', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login')
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/', { timeout: 5000 })
      
      await page.evaluate(() => {
        window.sentryMessages = []
      })
    })

    test('should track cost analysis view', async ({ page }) => {
      await page.click('a[href="/cost-analysis"], nav >> text=成本分析')
      
      await page.waitForURL('/cost-analysis', { timeout: 5000 })
      
      await page.waitForTimeout(1000)
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const viewMessage = sentryMessages.find(msg => 
        msg.message.includes('cost_analysis_view') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(viewMessage).toBeDefined()
      expect(viewMessage.context.extra.pathName).toBe('cost_analysis_view')
    })

    test('should trigger TTV event on cost analysis view', async ({ page }) => {
      let ttvEventFired = false
      await page.evaluate(() => {
        window.addEventListener('first-value-operation', (e) => {
          if (e.detail.operation === 'cost_analysis_view') {
            window.ttvEventFired = true
          }
        })
      })
      
      await page.click('a[href="/cost-analysis"], nav >> text=成本分析')
      
      await page.waitForURL('/cost-analysis', { timeout: 5000 })
      await page.waitForTimeout(1000)
      
      ttvEventFired = await page.evaluate(() => window.ttvEventFired)
      expect(ttvEventFired).toBe(true)
    })
  })

  test.describe('Strategy Management Path Tracking', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/login')
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      await page.waitForURL('/', { timeout: 5000 })
      
      await page.evaluate(() => {
        window.sentryMessages = []
      })
    })

    test('should track strategy management view', async ({ page }) => {
      await page.click('a[href="/strategy-management"], nav >> text=策略管理')
      
      await page.waitForURL('/strategy-management', { timeout: 5000 })
      
      await page.waitForTimeout(1000)
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const viewMessage = sentryMessages.find(msg => 
        msg.message.includes('strategy_management_view') && 
        msg.context.extra.status === 'completed'
      )
      
      expect(viewMessage).toBeDefined()
      expect(viewMessage.context.extra.pathName).toBe('strategy_management_view')
    })

    test('should trigger TTV event on strategy management view', async ({ page }) => {
      let ttvEventFired = false
      await page.evaluate(() => {
        window.addEventListener('first-value-operation', (e) => {
          if (e.detail.operation === 'strategy_management_view') {
            window.ttvEventFired = true
          }
        })
      })
      
      await page.click('a[href="/strategy-management"], nav >> text=策略管理')
      
      await page.waitForURL('/strategy-management', { timeout: 5000 })
      await page.waitForTimeout(1000)
      
      ttvEventFired = await page.evaluate(() => window.ttvEventFired)
      expect(ttvEventFired).toBe(true)
    })
  })

  test.describe('Complete User Journey', () => {
    test('should track full user journey from login to multiple operations', async ({ page }) => {
      await page.goto('/login')
      
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      
      await page.waitForURL('/', { timeout: 5000 })
      
      await page.click('button:has-text("儲存佈局"), button:has-text("Save Layout")')
      await page.waitForSelector('.success-message, .toast-success', { timeout: 5000 })
      
      await page.click('a[href="/decisions"], nav >> text=決策審批')
      await page.waitForURL('/decisions', { timeout: 5000 })
      
      await page.click('button:has-text("批准"), button:has-text("Approve")').first()
      await page.waitForSelector('.toast-success, .success-message', { timeout: 5000 })
      
      await page.click('a[href="/cost-analysis"], nav >> text=成本分析')
      await page.waitForURL('/cost-analysis', { timeout: 5000 })
      await page.waitForTimeout(1000)
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      
      const loginMessage = sentryMessages.find(msg => msg.message.includes('user_login'))
      const dashboardMessage = sentryMessages.find(msg => msg.message.includes('dashboard_save_layout'))
      const decisionMessage = sentryMessages.find(msg => msg.message.includes('decision_approve'))
      const costMessage = sentryMessages.find(msg => msg.message.includes('cost_analysis_view'))
      
      expect(loginMessage).toBeDefined()
      expect(dashboardMessage).toBeDefined()
      expect(decisionMessage).toBeDefined()
      expect(costMessage).toBeDefined()
      
      expect(sentryMessages.length).toBeGreaterThanOrEqual(4)
    })
  })

  test.describe('Concurrent Operations', () => {
    test('should handle multiple concurrent path tracking', async ({ page, context }) => {
      const page2 = await context.newPage()
      
      await page.goto('/login')
      await page2.goto('/login')
      
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      
      await page2.fill('input[name="username"]', 'admin')
      await page2.fill('input[name="password"]', 'admin123')
      
      await Promise.all([
        page.click('button[type="submit"]'),
        page2.click('button[type="submit"]')
      ])
      
      await Promise.all([
        page.waitForURL('/', { timeout: 5000 }),
        page2.waitForURL('/', { timeout: 5000 })
      ])
      
      const sentryMessages1 = await page.evaluate(() => window.sentryMessages)
      const sentryMessages2 = await page2.evaluate(() => window.sentryMessages)
      
      expect(sentryMessages1.length).toBeGreaterThan(0)
      expect(sentryMessages2.length).toBeGreaterThan(0)
      
      await page2.close()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle localStorage errors gracefully', async ({ page }) => {
      await page.goto('/login')
      
      await page.evaluate(() => {
        const originalSetItem = localStorage.setItem
        localStorage.setItem = () => {
          throw new DOMException('QuotaExceededError')
        }
      })
      
      await page.fill('input[name="username"]', 'admin')
      await page.fill('input[name="password"]', 'admin123')
      await page.click('button[type="submit"]')
      
      await page.waitForURL('/', { timeout: 5000 })
      
      const sentryMessages = await page.evaluate(() => window.sentryMessages)
      const loginMessage = sentryMessages.find(msg => msg.message.includes('user_login'))
      
      expect(loginMessage).toBeDefined()
    })
  })
})
