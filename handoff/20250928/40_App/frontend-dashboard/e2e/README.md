# Frontend Dashboard E2E Tests

This directory contains documentation for end-to-end (E2E) tests for the frontend-dashboard application using Playwright.

**Note:** Test files are located in the `tests/` directory (per Playwright config). This directory contains documentation only.

## Test Suites

### 1. Design Token Migration Tests (`tests/design-tokens.spec.ts`)

Comprehensive E2E test suite to ensure the design token migration is successful and maintains visual consistency.

**Test Coverage:**
- Visual regression tests for key pages (Agent Governance, Tenant Settings, Cost Analysis, Dashboard, 2FA, Decision Approval, Empty State Library)
- Semantic color validation (error, success, warning, info, neutral, primary, accent tokens)
- Functional smoke tests for navigation and interactions
- Dark mode compatibility tests
- Accessibility tests (color contrast, focus indicators)

**Related Issue:** [#1330](https://github.com/RC918/morningai/issues/1330) (P2)

**Test Tags:**
- `@vrt` - Visual regression tests (screenshot comparison)

### 2. 2FA Flows Tests (`e2e/2fa-flows.spec.ts`)

Complete user flow tests for Two-Factor Authentication functionality.

### 3. Dashboard Widget Filtering Tests (`e2e/dashboard-widget-filtering.spec.ts`)

Tests for dashboard widget filtering and interaction functionality.

## Running Tests

### Run All E2E Tests
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run test:e2e
```

### Run Visual Regression Tests Only
```bash
pnpm run test:vrt
```

### Run Specific Test File
```bash
# Design token tests (in tests/ directory)
pnpm exec playwright test tests/design-tokens.spec.ts

# Other E2E tests (in e2e/ directory)
pnpm exec playwright test e2e/2fa-flows.spec.ts
```

### Run Tests in UI Mode (Interactive)
```bash
pnpm exec playwright test --ui
```

### Run Tests in Debug Mode
```bash
pnpm exec playwright test --debug
```

## Visual Regression Testing

Visual regression tests use Playwright's screenshot comparison feature to detect unintended visual changes.

### Establishing Baseline Screenshots

When running visual regression tests for the first time or after intentional visual changes:

```bash
# Update all baseline screenshots
pnpm exec playwright test --update-snapshots

# Update specific test baseline
pnpm exec playwright test tests/design-tokens.spec.ts --update-snapshots
```

### Screenshot Storage

Baseline screenshots are stored in:
```
tests/design-tokens.spec.ts-snapshots/
```

These screenshots are committed to the repository and used for comparison in CI.

### Handling Visual Differences

If a test fails due to visual differences:

1. **Review the diff**: Check the generated diff images in `test-results/`
2. **Verify the change is intentional**: If the visual change is expected, update the baseline
3. **Fix the issue**: If the change is unintended, fix the code causing the regression

## CI Integration

E2E tests run automatically on every pull request via GitHub Actions (`.github/workflows/frontend.yml`).

**CI Job:** `frontend-dashboard-e2e`

**Artifacts:**
- Playwright test reports (`playwright-report-frontend-dashboard`)
- Screenshots and traces (`playwright-screenshots-frontend-dashboard`)

## Test Configuration

Test configuration is defined in `playwright.config.ts`:

- **Test Directory:** `./tests` (for design token tests and auth setup), `./e2e` (for other E2E tests)
- **Base URL:** `http://localhost:4173` (preview server)
- **Timeout:** 30 seconds per test
- **Retries:** 2 retries in CI, 0 locally
- **Browser:** Chromium (Desktop Chrome)
- **Viewport:** 1280x736

## Writing New Tests

### Visual Regression Test Example

```typescript
test('[@vrt] My Page - visual baseline', async ({ page }) => {
  await page.goto('/my-page')
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1000) // Allow animations to settle
  
  await expect(page).toHaveScreenshot('my-page.png', {
    fullPage: true,
    animations: 'disabled',
    timeout: 10000,
  })
})
```

### Functional Test Example

```typescript
test('should navigate and interact correctly', async ({ page }) => {
  await page.goto('/dashboard')
  await page.waitForLoadState('networkidle')
  
  // Verify element visibility
  await expect(page.getByText(/dashboard/i)).toBeVisible()
  
  // Interact with elements
  await page.click('button:has-text("Click Me")')
  
  // Verify result
  await expect(page.getByText(/success/i)).toBeVisible()
})
```

## Best Practices

1. **Wait for Network Idle**: Always use `waitForLoadState('networkidle')` before taking screenshots
2. **Disable Animations**: Use `animations: 'disabled'` for consistent screenshots
3. **Add Timeouts**: Allow time for dynamic content to load before assertions
4. **Use Semantic Selectors**: Prefer `getByRole`, `getByText`, `getByLabel` over CSS selectors
5. **Tag Visual Tests**: Use `[@vrt]` tag for visual regression tests
6. **Test in Isolation**: Each test should be independent and not rely on other tests

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Ensure you're using the same browser version as CI
- Check viewport size matches CI configuration
- Verify environment variables are set correctly

### Visual Regression Tests Always Fail

- Update baseline screenshots: `pnpm exec playwright test --update-snapshots`
- Check for dynamic content (timestamps, random IDs) that changes between runs
- Ensure animations are disabled in test configuration

### Tests Timeout

- Increase timeout in test or config
- Check for network issues or slow API responses
- Verify the application is running correctly

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Design Token Migration Guide](../DESIGN_TOKENS_GUIDE.md)
