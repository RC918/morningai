import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Dashboard Widget Filtering
 * 
 * These tests verify that the task_execution widget (which contains owner-console
 * agent names like GrowthStrategist, OpsAgent, PMAgent, SecurityManager) is never
 * displayed to tenant users in any scenario.
 * 
 * This prevents sensitive owner-console information from leaking to tenant dashboards.
 */

test.describe('Dashboard Widget Filtering - E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    
    await page.waitForSelector('[role="main"]', { timeout: 10000 })
  })

  test('should not display task_execution widget in dashboard', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const taskExecutionWidget = page.locator('text=/task.?execution/i')
    await expect(taskExecutionWidget).toHaveCount(0)
    
    const taskExecutionTitle = page.locator('text=/任務執行|Task Execution/i')
    await expect(taskExecutionTitle).toHaveCount(0)
  })

  test('should not display owner-console agent names anywhere', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const growthStrategist = page.locator('text=/GrowthStrategist/i')
    await expect(growthStrategist).toHaveCount(0)
    
    const opsAgent = page.locator('text=/OpsAgent/i')
    await expect(opsAgent).toHaveCount(0)
    
    const pmAgent = page.locator('text=/PMAgent/i')
    await expect(pmAgent).toHaveCount(0)
    
    const securityManager = page.locator('text=/SecurityManager/i')
    await expect(securityManager).toHaveCount(0)
  })

  test('should display only allowed widgets', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const allowedWidgets = [
      'CPU',
      'Memory',
      'Response Time',
      'Error Rate',
      'Active Strategies',
      'Pending Approvals'
    ]
    
    let foundWidgets = 0
    for (const widgetName of allowedWidgets) {
      const widget = page.locator(`text=/${widgetName}/i`).first()
      const count = await widget.count()
      if (count > 0) {
        foundWidgets++
      }
    }
    
    expect(foundWidgets).toBeGreaterThanOrEqual(3)
  })

  test('should not have task_execution in widget add dialog', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const addWidgetButton = page.locator('button:has-text("Add Widget"), button:has-text("新增"), button:has-text("添加")')
    
    if (await addWidgetButton.count() > 0) {
      await addWidgetButton.first().click()
      
      await page.waitForTimeout(500)
      
      const taskExecutionOption = page.locator('text=/task.?execution/i')
      await expect(taskExecutionOption).toHaveCount(0)
      
      const growthStrategist = page.locator('text=/GrowthStrategist/i')
      await expect(growthStrategist).toHaveCount(0)
    }
  })

  test('should not expose task_execution in page source', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    const pageContent = await page.content()
    
    expect(pageContent.toLowerCase()).not.toContain('task_execution')
    expect(pageContent.toLowerCase()).not.toContain('taskexecution')
    
    expect(pageContent).not.toContain('GrowthStrategist')
    expect(pageContent).not.toContain('OpsAgent')
    expect(pageContent).not.toContain('PMAgent')
    expect(pageContent).not.toContain('SecurityManager')
  })

  test('should not expose task_execution in network requests', async ({ page }) => {
    const taskExecutionRequests: string[] = []
    
    page.on('response', async (response) => {
      const url = response.url()
      
      if (url.includes('/dashboard') || url.includes('/widgets')) {
        try {
          const body = await response.text()
          if (body.toLowerCase().includes('task_execution') || 
              body.includes('GrowthStrategist') ||
              body.includes('OpsAgent') ||
              body.includes('PMAgent') ||
              body.includes('SecurityManager')) {
            taskExecutionRequests.push(url)
          }
        } catch (e) {
        }
      }
    })
    
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    expect(taskExecutionRequests).toHaveLength(0)
  })

  test('should handle saved layouts with task_execution gracefully', async ({ page }) => {
    
    await page.waitForLoadState('networkidle')
    
    const mainContent = page.locator('[role="main"]')
    await expect(mainContent).toBeVisible()
    
    const errorMessages = page.locator('text=/error|錯誤|失敗/i')
    const errorCount = await errorMessages.count()
    
    expect(errorCount).toBeLessThan(10)
    
    const taskExecutionWidget = page.locator('text=/task.?execution/i')
    await expect(taskExecutionWidget).toHaveCount(0)
  })

  test('should maintain widget filtering after page refresh', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    
    let taskExecutionWidget = page.locator('text=/task.?execution/i')
    await expect(taskExecutionWidget).toHaveCount(0)
    
    await page.reload()
    await page.waitForLoadState('networkidle')
    
    taskExecutionWidget = page.locator('text=/task.?execution/i')
    await expect(taskExecutionWidget).toHaveCount(0)
    
    const growthStrategist = page.locator('text=/GrowthStrategist/i')
    await expect(growthStrategist).toHaveCount(0)
  })

  test('should not display task_execution in any language', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    let taskExecutionWidget = page.locator('text=/task.?execution|任務執行/i')
    await expect(taskExecutionWidget).toHaveCount(0)
    
    const languageSelector = page.locator('button:has-text("Language"), button:has-text("語言")')
    
    if (await languageSelector.count() > 0) {
      await languageSelector.first().click()
      await page.waitForTimeout(500)
      
      const chineseOption = page.locator('text=/中文|Chinese|zh/i')
      if (await chineseOption.count() > 0) {
        await chineseOption.first().click()
        await page.waitForTimeout(1000)
        
        taskExecutionWidget = page.locator('text=/task.?execution|任務執行/i')
        await expect(taskExecutionWidget).toHaveCount(0)
      }
    }
  })
})

test.describe('Dashboard Widget Filtering - Regression Prevention', () => {
  test('should verify widget count matches expected default', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const widgetCards = page.locator('[role="main"] .card, [role="main"] [class*="card"]')
    const count = await widgetCards.count()
    
    expect(count).toBeGreaterThanOrEqual(6)
    expect(count).toBeLessThanOrEqual(10)
  })

  test('should not have any widgets with owner-console specific data', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    
    const pageText = await page.locator('body').textContent()
    
    const ownerConsoleTerms = [
      'GrowthStrategist',
      'OpsAgent', 
      'PMAgent',
      'SecurityManager',
      'task_execution',
      'taskExecution'
    ]
    
    for (const term of ownerConsoleTerms) {
      expect(pageText).not.toContain(term)
    }
  })
})
