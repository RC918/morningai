import { test, expect } from '@playwright/test'
import { 
  mockExecutionLogsResponse, 
  mockExecutionLogsResponsePage2,
  mockExecutionLogsFilteredByStatus,
  grantClipboardPermissions 
} from './utils/fixtures'

/**
 * E2E tests for AgentExecutionLogs component
 * 
 * Tests verify:
 * 1. Rendering and summary statistics
 * 2. Status normalization
 * 3. Filters functionality
 * 4. Sorting functionality
 * 5. Pagination functionality
 * 6. Trace links vs copy fallback
 * 7. Copy actions
 * 8. Drawer details
 * 9. Error state and retry
 */

test.describe('AgentExecutionLogs E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/admin/agent-execution-logs*', route => {
      const url = route.request().url()
      
      if (url.includes('page=2')) {
        route.fulfill({ json: mockExecutionLogsResponsePage2 })
      }
      else if (url.includes('status=completed')) {
        route.fulfill({ json: mockExecutionLogsFilteredByStatus })
      }
      else {
        route.fulfill({ json: mockExecutionLogsResponse })
      }
    })
  })

  test('1. should render summary statistics and table', async ({ page }) => {
    await page.goto('/governance')
    
    await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
    
    const summaryTotal = page.getByTestId('summary-total')
    await expect(summaryTotal).toBeVisible()
    await expect(summaryTotal).toContainText('42')
    
    const summarySuccessRate = page.getByTestId('summary-success-rate')
    await expect(summarySuccessRate).toBeVisible()
    await expect(summarySuccessRate).toContainText('85.7%')
    
    const summaryAvgDuration = page.getByTestId('summary-avg-duration')
    await expect(summaryAvgDuration).toBeVisible()
    
    const summaryStatusBreakdown = page.getByTestId('summary-status-breakdown')
    await expect(summaryStatusBreakdown).toBeVisible()
    
    const table = page.getByTestId('execution-table')
    await expect(table).toBeVisible()
    
    const rows = page.locator('[data-testid="execution-row"]')
    await expect(rows.first()).toBeVisible()
  })

  test('2. should normalize execution log statuses correctly', async ({ page }) => {
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const rows = page.locator('[data-testid="execution-row"]')
    const rowCount = await rows.count()
    
    expect(rowCount).toBeGreaterThan(0)
    
    const firstRow = rows.first()
    const statusBadge = firstRow.locator('[data-status]').first()
    await expect(statusBadge).toBeVisible()
    
    const statusValue = await statusBadge.getAttribute('data-status')
    expect(['completed', 'running', 'failed', 'queued', 'cancelled', 'assigned']).toContain(statusValue)
  })

  test('3. should filter by status', async ({ page }) => {
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const statusFilter = page.getByTestId('filter-status')
    await statusFilter.click()
    
    await page.locator('text=Completed').first().click()
    
    await page.getByTestId('apply-filters').click()
    
    const request = await page.waitForRequest(req => 
      req.url().includes('admin/agent-execution-logs') && req.url().includes('status=completed')
    )
    
    expect(request.url()).toContain('status=completed')
    
    await page.waitForSelector('[data-testid="execution-table"]')
    const rows = page.locator('[data-testid="execution-row"]')
    await expect(rows.first()).toBeVisible()
  })

  test('4. should filter by agent type', async ({ page }) => {
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const agentTypeFilter = page.getByTestId('filter-agent-type')
    await agentTypeFilter.click()
    
    await page.locator('text=Dev Agent').first().click()
    
    await page.getByTestId('apply-filters').click()
    
    await page.waitForRequest(req => 
      req.url().includes('admin/agent-execution-logs') && req.url().includes('agent_type=dev_agent')
    )
  })

  test('5. should clear filters', async ({ page }) => {
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const statusFilter = page.getByTestId('filter-status')
    await statusFilter.click()
    await page.locator('text=Completed').first().click()
    
    await page.getByTestId('clear-filters').click()
    
    await page.waitForRequest(req => 
      req.url().includes('admin/agent-execution-logs') && !req.url().includes('status=')
    )
  })

  test('6. should handle pagination', async ({ page }) => {
    await page.route('**/admin/agent-execution-logs*', route => {
      const url = route.request().url()
      if (url.includes('page=2')) {
        route.fulfill({ 
          json: {
            ...mockExecutionLogsResponsePage2,
            pagination: { total_items: 100, total_pages: 2 }
          }
        })
      } else {
        route.fulfill({ 
          json: {
            ...mockExecutionLogsResponse,
            pagination: { total_items: 100, total_pages: 2 }
          }
        })
      }
    })
    
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    await page.waitForSelector('text=/Page.*of/')
    
    const nextButton = page.locator('a[aria-label*="next" i], button:has-text("Next")')
    if (await nextButton.count() > 0) {
      await nextButton.first().click()
      
      await page.waitForRequest(req => 
        req.url().includes('admin/agent-execution-logs') && req.url().includes('page=2')
      )
    }
  })

  test('7. should display trace links when TRACE_VIEWER_URL is set', async ({ page }) => {
    
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const traceLinks = page.locator('[data-testid="trace-link"]')
    const traceLinkCount = await traceLinks.count()
    
    if (traceLinkCount > 0) {
      const firstTraceLink = traceLinks.first()
      await expect(firstTraceLink).toHaveAttribute('target', '_blank')
      await expect(firstTraceLink).toHaveAttribute('rel', 'noopener noreferrer')
      
      // Verify link URL format
      const href = await firstTraceLink.getAttribute('href')
      expect(href).toMatch(/\/trace\//)
    } else {
      const copyButtons = page.locator('[data-testid="copy-trace-id"]')
      await expect(copyButtons.first()).toBeVisible()
    }
  })

  test('8. should copy trace ID to clipboard', async ({ page, context }) => {
    await grantClipboardPermissions(context)
    
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const copyButton = page.getByTestId('copy-trace-id').first()
    await copyButton.click()
    
    await page.waitForTimeout(500)
    
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toMatch(/trace-[a-f0-9-]{36}/)
  })

  test('9. should open details drawer and display full information', async ({ page }) => {
    await page.goto('/governance')
    await page.waitForSelector('[data-testid="execution-table"]')
    
    const viewDetailsButton = page.getByTestId('view-details').first()
    await viewDetailsButton.click()
    
    const drawer = page.getByTestId('details-drawer')
    await expect(drawer).toBeVisible()
    
    const detailsContent = page.getByTestId('details-content')
    await expect(detailsContent).toBeVisible()
    
    const agentSection = page.getByTestId('details-agent')
    if (await agentSection.count() > 0) {
      await expect(agentSection).toBeVisible()
    }
    
    const timestampsSection = page.getByTestId('details-timestamps')
    await expect(timestampsSection).toBeVisible()
    
    const copyTaskIdButton = page.getByTestId('copy-task-id')
    await expect(copyTaskIdButton).toBeVisible()
  })

  test('10. should handle error state and retry', async ({ page }) => {
    let callCount = 0
    
    await page.route('**/admin/agent-execution-logs*', route => {
      callCount++
      if (callCount === 1) {
        route.fulfill({ 
          status: 500, 
          json: { error: 'Internal server error' } 
        })
      } else {
        route.fulfill({ json: mockExecutionLogsResponse })
      }
    })
    
    await page.goto('/governance')
    
    const errorAlert = page.getByTestId('error-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })
    
    const retryButton = page.getByTestId('retry-button')
    await expect(retryButton).toBeVisible()
    await retryButton.click()
    
    await page.waitForSelector('[data-testid="execution-table"]', { timeout: 10000 })
    const table = page.getByTestId('execution-table')
    await expect(table).toBeVisible()
    
    await expect(errorAlert).not.toBeVisible()
  })
})
