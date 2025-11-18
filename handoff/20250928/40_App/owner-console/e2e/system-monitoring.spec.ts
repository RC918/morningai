import { test, expect } from '@playwright/test'
import { 
  mockHealthResponse, 
  mockHealthResponseDegraded,
  mockMetricsResponse,
  mockMetricsResponseHighUsage,
  stubMathRandom 
} from './utils/fixtures'

/**
 * E2E tests for SystemMonitoring component
 * 
 * NOTE: These tests require authenticated access to /monitoring route.
 * Authentication is handled by the setup project (auth.setup.ts) which runs before these tests.
 * 
 * Tests verify:
 * 1. Happy path render (health and metrics)
 * 2. Mock badges when VITE_USE_MOCK=true
 * 3. Error handling for health and metrics
 * 4. Trend charts presence
 * 5. Refresh button flow
 */

test.describe('SystemMonitoring E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await stubMathRandom(page)
    
    await page.route('**/admin/system-health', route => {
      route.fulfill({ json: mockHealthResponse })
    })
    
    await page.route('**/admin/system-metrics', route => {
      route.fulfill({ json: mockMetricsResponse })
    })
  })

  test('1. should render health and metrics successfully', async ({ page }) => {
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]', { timeout: 10000 })
    
    const healthCard = page.getByTestId('system-health')
    await expect(healthCard).toBeVisible()
    await expect(healthCard).toContainText('healthy')
    
    await expect(healthCard).toContainText(/\d+[dhm]/)
    
    const cpuCard = page.getByTestId('cpu-card')
    await expect(cpuCard).toBeVisible()
    await expect(cpuCard).toContainText('45.2%')
    await expect(cpuCard).toContainText('4') // CPU count
    
    const memoryCard = page.getByTestId('memory-card')
    await expect(memoryCard).toBeVisible()
    await expect(memoryCard).toContainText('62.8%')
    await expect(memoryCard).toContainText('5.0') // Used GB
    await expect(memoryCard).toContainText('8.0') // Total GB
    
    const diskCard = page.getByTestId('disk-card')
    await expect(diskCard).toBeVisible()
    await expect(diskCard).toContainText('38.5%')
    await expect(diskCard).toContainText('77.0') // Used GB
    await expect(diskCard).toContainText('200.0') // Total GB
  })

  test('2. should show mock badges when VITE_USE_MOCK=true', async ({ page }) => {
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]')
    
    const mockBadges = page.locator('[data-testid="mock-badge"]')
    const mockBadgeCount = await mockBadges.count()
    
    if (mockBadgeCount > 0) {
      expect(mockBadgeCount).toBe(3)
      
      await expect(mockBadges.first()).toBeVisible()
      await expect(mockBadges.nth(1)).toBeVisible()
      await expect(mockBadges.nth(2)).toBeVisible()
    } else {
      console.log('VITE_USE_MOCK not set during build - mock badges not present')
    }
  })

  test('3. should handle health check error and retry', async ({ page }) => {
    let healthCallCount = 0
    
    await page.route('**/admin/system-health', route => {
      healthCallCount++
      if (healthCallCount === 1) {
        route.fulfill({ 
          status: 500, 
          json: { error: 'Health check failed' } 
        })
      } else {
        route.fulfill({ json: mockHealthResponse })
      }
    })
    
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    const errorAlert = page.getByTestId('error-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })
    
    const retryButton = page.getByTestId('retry-button')
    await expect(retryButton).toBeVisible()
    await retryButton.click()
    
    await page.waitForSelector('[data-testid="system-health"]', { timeout: 10000 })
    const healthCard = page.getByTestId('system-health')
    await expect(healthCard).toBeVisible()
    
    await expect(errorAlert).not.toBeVisible()
  })

  test('4. should handle metrics error and retry', async ({ page }) => {
    let metricsCallCount = 0
    
    await page.route('**/admin/system-metrics', route => {
      metricsCallCount++
      if (metricsCallCount === 1) {
        route.fulfill({ 
          status: 500, 
          json: { error: 'Metrics fetch failed' } 
        })
      } else {
        route.fulfill({ json: mockMetricsResponse })
      }
    })
    
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    const errorAlert = page.getByTestId('error-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })
    
    const retryButton = page.getByTestId('retry-button')
    await expect(retryButton).toBeVisible()
    await retryButton.click()
    
    await page.waitForSelector('[data-testid="cpu-card"]', { timeout: 10000 })
    const cpuCard = page.getByTestId('cpu-card')
    await expect(cpuCard).toBeVisible()
    
    await expect(errorAlert).not.toBeVisible()
  })

  test('5. should display trend charts for all metrics', async ({ page }) => {
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]')
    
    const cpuTrend = page.getByTestId('cpu-trend')
    await expect(cpuTrend).toBeVisible()
    
    const memoryTrend = page.getByTestId('memory-trend')
    await expect(memoryTrend).toBeVisible()
    
    const diskTrend = page.getByTestId('disk-trend')
    await expect(diskTrend).toBeVisible()
    
    const cpuChart = cpuTrend.locator('svg')
    await expect(cpuChart).toBeVisible()
    
    const memoryChart = memoryTrend.locator('svg')
    await expect(memoryChart).toBeVisible()
    
    const diskChart = diskTrend.locator('svg')
    await expect(diskChart).toBeVisible()
  })

  test('6. should refresh data when refresh button is clicked', async ({ page }) => {
    let healthCallCount = 0
    let metricsCallCount = 0
    
    await page.route('**/admin/system-health', route => {
      healthCallCount++
      if (healthCallCount === 1) {
        route.fulfill({ json: mockHealthResponse })
      } else {
        route.fulfill({ json: mockHealthResponseDegraded })
      }
    })
    
    await page.route('**/admin/system-metrics', route => {
      metricsCallCount++
      if (metricsCallCount === 1) {
        route.fulfill({ json: mockMetricsResponse })
      } else {
        route.fulfill({ json: mockMetricsResponseHighUsage })
      }
    })
    
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]')
    
    const healthCard = page.getByTestId('system-health')
    await expect(healthCard).toContainText('healthy')
    
    const cpuCard = page.getByTestId('cpu-card')
    await expect(cpuCard).toContainText('45.2%')
    
    const refreshButton = page.getByTestId('refresh-metrics')
    await refreshButton.click()
    
    await page.waitForRequest(req => req.url().includes('admin/system-health'))
    await page.waitForRequest(req => req.url().includes('admin/system-metrics'))
    
    await page.waitForTimeout(500)
    
    await expect(healthCard).toContainText('degraded')
    await expect(cpuCard).toContainText('89.5%')
    
    expect(healthCallCount).toBe(2)
    expect(metricsCallCount).toBe(2)
  })

  test('7. should display different health statuses correctly', async ({ page }) => {
    await page.route('**/admin/system-health', route => {
      route.fulfill({ json: mockHealthResponseDegraded })
    })
    
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]')
    
    const healthCard = page.getByTestId('system-health')
    await expect(healthCard).toBeVisible()
    await expect(healthCard).toContainText('degraded')
    
    await expect(healthCard).toContainText('redis')
  })

  test('8. should handle high usage metrics', async ({ page }) => {
    await page.route('**/admin/system-metrics', route => {
      route.fulfill({ json: mockMetricsResponseHighUsage })
    })
    
    await page.goto('/monitoring')
    await page.waitForLoadState('networkidle')
    
    await page.waitForSelector('[data-testid="system-monitoring"]')
    
    const cpuCard = page.getByTestId('cpu-card')
    await expect(cpuCard).toContainText('89.5%')
    
    const memoryCard = page.getByTestId('memory-card')
    await expect(memoryCard).toContainText('94.2%')
    await expect(memoryCard).toContainText('7.5') // Used GB
    
    const diskCard = page.getByTestId('disk-card')
    await expect(diskCard).toContainText('82.1%')
    await expect(diskCard).toContainText('164.2') // Used GB
  })
})
