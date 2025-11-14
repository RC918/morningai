# Testing Guide for @morningai/shared-ui

This document explains how to test the shared-ui component library.

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Storybook Testing](#storybook-testing)
- [Accessibility Testing](#accessibility-testing)
- [Writing Tests](#writing-tests)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)

## Overview

The shared-ui package uses multiple testing approaches:

1. **Unit Tests** - Vitest for component logic testing
2. **Storybook Stories** - Visual documentation and manual testing
3. **Storybook Test Runner** - Automated story testing with accessibility checks
4. **Accessibility Tests** - Automated a11y validation using axe-core

## Running Tests

### Unit Tests (Vitest)

```bash
# Run all unit tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage

# Run tests with UI
pnpm test:ui
```

### Storybook Tests

```bash
# Start Storybook dev server
pnpm storybook

# Run Storybook test-runner (requires Storybook to be running)
# Terminal 1:
pnpm storybook

# Terminal 2:
pnpm test-storybook

# Run tests in CI mode (builds + serves + tests automatically)
pnpm test-storybook:ci
```

## Storybook Testing

### What is Storybook Test Runner?

The test-runner automatically:
- Renders each story in a real browser (Chromium via Playwright)
- Runs accessibility checks using axe-core
- Validates that stories render without errors
- Generates detailed reports for failures

### Current Story Coverage

**13 out of 48 components (27%)** have Storybook stories:

- ✅ Alert (3 stories)
- ✅ Badge (3 stories)
- ✅ Button (13 stories)
- ✅ Card (8 stories)
- ✅ Dialog (8 stories)
- ✅ Form (5 stories)
- ✅ Input (12 stories)
- ✅ Progress (9 stories)
- ✅ Select (8 stories)
- ✅ StatusBadge (1 story)
- ✅ Tabs (6 stories)

### Writing Stories

Create a `.stories.tsx` file next to your component:

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: {
    children: 'Click me',
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled',
    disabled: true,
  },
};
```

**Best Practices**:
- Cover all variants and sizes
- Include disabled states
- Show real-world use cases
- Add descriptions for complex props
- Use `tags: ['autodocs']` for automatic documentation

## Accessibility Testing

### Automated A11y Checks

Every story is automatically tested for accessibility violations using axe-core. The test-runner checks for:

- Color contrast issues
- Missing ARIA labels
- Keyboard navigation problems
- Screen reader compatibility
- Semantic HTML issues

### A11y Test Configuration

The test-runner config (`.storybook/test-runner.js`) automatically injects axe-core and runs checks on every story:

```javascript
// This runs automatically for every story
async postVisit(page) {
  await checkA11y(page, '#storybook-root', {
    detailedReport: true,
    detailedReportOptions: {
      html: true,
    },
  });
}
```

### Handling A11y Violations

If a story fails accessibility checks:

1. **Review the error message** - It will specify the exact issue (e.g., "Elements must have sufficient color contrast")
2. **Fix the component** - Update the component to meet WCAG standards
3. **Re-run tests** - Verify the fix resolves the issue
4. **Document exceptions** - If a violation is intentional, document why in the story

### Disabling A11y Checks (Not Recommended)

If you absolutely must disable a11y checks for a specific story:

```typescript
export const ProblematicStory: Story = {
  parameters: {
    a11y: {
      disable: true, // Only use if absolutely necessary
    },
  },
};
```

## Writing Tests

### Unit Test Example

```typescript
import { render, screen } from '@testing-library/react';
import { Button } from './button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    screen.getByText('Click me').click();
    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

### Story Test Example

Stories are automatically tested by the test-runner. No additional test files needed!

```typescript
// This story will be automatically tested
export const WithIcon: Story = {
  args: {
    children: (
      <>
        <Icon name="check" />
        Save
      </>
    ),
  },
};
```

## CI/CD

### GitHub Actions Workflow

The `Storybook A11y Tests` job runs on every PR:

1. Installs dependencies
2. Caches Playwright browsers (speeds up subsequent runs)
3. Builds Storybook static files
4. Serves Storybook on port 6006
5. Runs test-runner with accessibility checks
6. Reports failures with detailed logs

### CI Configuration

```yaml
storybook-a11y-tests:
  name: Storybook A11y Tests
  runs-on: ubuntu-latest
  steps:
    - name: Cache Playwright browsers
      uses: actions/cache@v4
      with:
        path: ~/.cache/ms-playwright
        key: playwright-${{ runner.os }}-${{ hashFiles('**/pnpm-lock.yaml') }}
    
    - name: Run Storybook accessibility tests
      run: pnpm run test-storybook:ci
```

### Performance Optimizations

- **Playwright Cache**: Browsers are cached between runs (~200MB saved)
- **maxWorkers=2**: Limits parallel tests to avoid CI resource exhaustion
- **Explicit URL**: `--url http://127.0.0.1:6006` avoids auto-detection issues

## Troubleshooting

### Test Runner Fails to Start

**Problem**: `Error: Cannot find module '.storybook/test-runner.js'`

**Solution**: Ensure the test-runner config exists and is in CommonJS format (`.js`, not `.ts`). The test-runner uses `require()` which doesn't support ES modules.

### Playwright Browser Installation Fails

**Problem**: `browserType.launch: Executable doesn't exist`

**Solution**: Run `pnpm exec playwright install --with-deps chromium` to install browsers.

### A11y Tests Fail Unexpectedly

**Problem**: Stories that look fine have accessibility violations

**Solution**: 
1. Review the specific axe-core rule that failed
2. Check [axe-core rule descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
3. Fix the component to meet WCAG standards
4. Consider if the violation is a false positive (rare)

### CI Tests Pass Locally But Fail in CI

**Problem**: Tests work on your machine but fail in GitHub Actions

**Solution**:
1. Check if you're using the same Node/pnpm versions as CI
2. Ensure `pnpm-lock.yaml` is committed
3. Run `pnpm test-storybook:ci` locally (mimics CI environment)
4. Check CI logs for specific error messages

### Slow Test Execution

**Problem**: Tests take too long to run

**Solution**:
- Use `--maxWorkers=2` to limit parallelization
- Cache Playwright browsers in CI
- Consider running only changed stories locally (not yet implemented)

## Additional Resources

- [Storybook Test Runner Documentation](https://storybook.js.org/docs/writing-tests/test-runner)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)

## Contributing

When adding new components:

1. ✅ Write unit tests for component logic
2. ✅ Create Storybook stories for all variants
3. ✅ Ensure stories pass accessibility checks
4. ✅ Run `pnpm test-storybook:ci` before submitting PR
5. ✅ Update this documentation if adding new testing patterns

---

**Current Test Coverage Goal**: Expand from 27% to 50%+ component story coverage.
