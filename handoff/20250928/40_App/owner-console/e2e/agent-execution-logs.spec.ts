import { test, expect } from '@playwright/test'
import { 
  mockExecutionLogsResponse, 
  mockExecutionLogsResponsePage2,
  mockExecutionLogsFilteredByStatus,
  grantClipboardPermissions,
  stubGovernanceEndpoints,
  addDiagnosticLogging
} from './utils/fixtures'

/**
 * E2E tests for AgentExecutionLogs component
 * 
 * NOTE: These tests require authenticated access to /governance route.
 * Authentication is handled by the setup project (auth.setup.ts) which runs before these tests.
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
  test.describe.configure({ mode: 'serial' })
  
  test.beforeEach(async ({ page }) => {
    await addDiagnosticLogging(page)
    await stubGovernanceEndpoints(page)
  })

  const navigateToExecutionLogs = async (page: any) => {
    await page.goto('/governance')
    await page.waitForLoadState('networkidle')
    
    await page.locator('[data-slot="tabs-list"]').waitFor({ timeout: 30000 })
    
    const executionLogsTab = page.getByRole('tab', { name: /execution logs/i })
    await executionLogsTab.waitFor({ state: 'visible', timeout: 10000 })
    
    const panelId = await executionLogsTab.getAttribute('aria-controls')
    
    if (!panelId) {
      console.warn('⚠️ Tab does not have aria-controls attribute, falling back to text-based panel selector')
      await Promise.all([
        page.waitForResponse(r => r.url().includes('/api/admin/agent-execution-logs') && (r.status() === 200 || r.status() === 500)),
        executionLogsTab.click()
      ])
      const tabPanel = page.getByRole('tabpanel', { name: /execution logs/i })
      await tabPanel.waitFor({ state: 'visible', timeout: 10000 })
    } else {
      console.log(`🔗 Tab aria-controls: ${panelId}`)
      
      // Wait for API response and tab click concurrently
      await Promise.all([
        page.waitForResponse(r => r.url().includes('/api/admin/agent-execution-logs') && (r.status() === 200 || r.status() === 500)),
        executionLogsTab.click()
      ])
      
      // Wait for tab to be selected
      await expect(executionLogsTab).toHaveAttribute('aria-selected', 'true', { timeout: 5000 })
      
      // Wait for panel to become active
      const panel = page.locator(`#${panelId}`)
      await expect(panel).toHaveAttribute('data-state', 'active', { timeout: 5000 })
      await panel.waitFor({ state: 'visible', timeout: 10000 })
    }
    
    await page.waitForSelector('[data-testid="agent-execution-logs"]', { timeout: 10000 })
  }

  test('1. should render summary statistics and table', async ({ page }) => {
    await navigateToExecutionLogs(page)
    
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
    await navigateToExecutionLogs(page)
    
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
    await navigateToExecutionLogs(page)
    
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
    await navigateToExecutionLogs(page)
    
    const agentTypeFilter = page.getByTestId('filter-agent-type')
    await agentTypeFilter.click()
    
    await page.locator('text=Dev Agent').first().click()
    
    await page.getByTestId('apply-filters').click()
    
    await page.waitForRequest(req => 
      req.url().includes('admin/agent-execution-logs') && req.url().includes('agent_type=dev_agent')
    )
  })

  test('5. should clear filters', async ({ page }) => {
    await navigateToExecutionLogs(page)
    
    const statusFilter = page.getByTestId('filter-status')
    await statusFilter.click()
    await page.locator('text=Completed').first().click()
    
    await page.getByTestId('clear-filters').click()
    
    await page.waitForRequest(req => 
      req.url().includes('admin/agent-execution-logs') && !req.url().includes('status=')
    )
  })

  test('6. should handle pagination', async ({ page }) => {
    await page.unroute('**/api/admin/agent-execution-logs*')
    
    await page.route('**/api/admin/agent-execution-logs*', route => {
      const url = route.request().url()
      console.log('[MOCK-TEST6] Pagination test intercepted:', url)
      if (url.includes('page=2')) {
        route.fulfill({ 
          json: {
            ...mockExecutionLogsResponsePage2,
            pagination: { total_items: 100, total_pages: 2, page: 2, page_size: 10 }
          }
        })
      } else {
        route.fulfill({ 
          json: {
            ...mockExecutionLogsResponse,
            pagination: { total_items: 100, total_pages: 2, page: 1, page_size: 10 }
          }
        })
      }
    })
    
    await navigateToExecutionLogs(page)
    
    // Wait for pagination to be visible using stable data-testid
    await page.getByTestId('pagination').waitFor({ state: 'visible', timeout: 10000 })
    
    // Verify pagination page indicator
    const pageIndicator = page.getByTestId('pagination-page')
    await expect(pageIndicator).toBeVisible()
    await expect(pageIndicator).toHaveAttribute('data-current', '1')
    await expect(pageIndicator).toHaveAttribute('data-total', '2')
    
    const nextButton = page.getByTestId('pagination-next')
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/admin/agent-execution-logs') && r.url().includes('page=2') && r.status() === 200),
      nextButton.click()
    ])
    
    // Verify we're on page 2
    await expect(pageIndicator).toHaveAttribute('data-current', '2')
  })

  test('7. should display trace links when TRACE_VIEWER_URL is set', async ({ page }) => {
    await page.addInitScript(() => {
      window.TRACE_VIEWER_URL = 'https://trace.example.com'
    })
    
    await navigateToExecutionLogs(page)
    
    // Wait for table to be visible
    await page.getByTestId('execution-table').waitFor({ state: 'visible', timeout: 10000 })
    
    const traceLinks = page.getByTestId('trace-link')
    const traceLinkCount = await traceLinks.count()
    
    if (traceLinkCount > 0) {
      const firstTraceLink = traceLinks.first()
      await expect(firstTraceLink).toBeVisible({ timeout: 10000 })
      await expect(firstTraceLink).toHaveAttribute('target', '_blank')
      await expect(firstTraceLink).toHaveAttribute('rel', 'noopener noreferrer')
      
      // Verify link URL format
      const href = await firstTraceLink.getAttribute('href')
      expect(href).toMatch(/\/trace\//)
    } else {
      const copyButtons = page.getByTestId('copy-trace-id')
      await expect(copyButtons.first()).toBeVisible({ timeout: 10000 })
    }
  })

  test('8. should copy trace ID to clipboard', async ({ page, context }) => {
    await grantClipboardPermissions(context)
    
    await navigateToExecutionLogs(page)
    
    // Wait for table to be visible
    await page.getByTestId('execution-table').waitFor({ state: 'visible', timeout: 10000 })
    
    const copyButton = page.getByTestId('copy-trace-id').first()
    await expect(copyButton).toBeVisible({ timeout: 10000 })
    await copyButton.click()
    
    await page.waitForTimeout(500)
    
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText())
    expect(clipboardText).toMatch(/trace-[a-f0-9-]{36}/)
  })

  test('9. should open details drawer and display full information', async ({ page }) => {
    await navigateToExecutionLogs(page)
    
    // Wait for table to be visible
    await page.getByTestId('execution-table').waitFor({ state: 'visible', timeout: 10000 })
    
    const viewDetailsButton = page.getByTestId('view-details').first()
    await expect(viewDetailsButton).toBeVisible({ timeout: 10000 })
    await viewDetailsButton.click()
    
    const drawer = page.getByTestId('details-drawer')
    await expect(drawer).toBeVisible({ timeout: 10000 })
    
    const detailsContent = page.getByTestId('details-content')
    await expect(detailsContent).toBeVisible({ timeout: 10000 })
    
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
    
    await page.unroute('**/api/admin/agent-execution-logs*')
    
    await page.route('**/api/admin/agent-execution-logs*', route => {
      callCount++
      console.log('[MOCK-TEST10] Error test intercepted, call count:', callCount)
      if (callCount === 1) {
        route.fulfill({ 
          status: 500, 
          json: { error: 'Internal server error' } 
        })
      } else {
        route.fulfill({ 
          status: 200,
          json: mockExecutionLogsResponse 
        })
      }
    })
    
    await navigateToExecutionLogs(page)
    
    const errorAlert = page.getByTestId('error-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })
    
    const retryButton = page.getByTestId('retry-button')
    await expect(retryButton).toBeVisible({ timeout: 10000 })
    
    await Promise.all([
      page.waitForResponse(r => r.url().includes('/api/admin/agent-execution-logs') && r.status() === 200),
      retryButton.click()
    ])
    
    // Wait for table to appear
    const table = page.getByTestId('execution-table')
    await expect(table).toBeVisible({ timeout: 10000 })
    
    await expect(errorAlert).not.toBeVisible()
  })
})
