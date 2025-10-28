# Storybook Guide

## Overview

Storybook is an interactive component documentation and development environment for MorningAI. It allows developers and designers to view, test, and document UI components in isolation.

## Getting Started

### Running Storybook

```bash
cd frontend-dashboard-deploy
pnpm run storybook
```

Storybook will start on `http://localhost:6006`

### Building Storybook

```bash
pnpm run build-storybook
```

This creates a static build in `storybook-static/` directory.

## Project Structure

```
frontend-dashboard-deploy/
├── .storybook/
│   ├── main.js              # Storybook configuration
│   ├── preview.jsx          # Global decorators and parameters
│   └── vitest.setup.js      # Vitest integration setup
├── src/
│   └── components/
│       ├── Dashboard.stories.jsx
│       ├── LoginPage.stories.jsx
│       └── DecisionApproval.stories.jsx
```

## Writing Stories

### Basic Story Structure

```jsx
import ComponentName from './ComponentName';
import { MemoryRouter } from 'react-router-dom';

export default {
  title: 'Components/ComponentName',
  component: ComponentName,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Component description here.',
      },
    },
  },
  decorators: [
    (Story) => (
      <MemoryRouter>
        <Story />
      </MemoryRouter>
    ),
  ],
  tags: ['autodocs'],
};

export const Default = {
  name: 'Default State',
  parameters: {
    docs: {
      description: {
        story: 'Story description here.',
      },
    },
  },
};
```

### Interactive Stories with Play Functions

```jsx
import { within, userEvent, waitFor, expect } from '@storybook/test';

export const WithInteraction = {
  name: 'With User Interaction',
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    const button = await canvas.findByRole('button', { name: /submit/i });
    await userEvent.click(button);
    
    await waitFor(() => {
      expect(canvas.getByText(/success/i)).toBeInTheDocument();
    });
  },
};
```

### Mobile View Stories

```jsx
export const MobileView = {
  name: 'Mobile View',
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};
```

## Addons

### Installed Addons

1. **@storybook/addon-essentials**
   - Controls: Interactive component props
   - Actions: Event handler logging
   - Docs: Auto-generated documentation
   - Viewport: Responsive design testing
   - Backgrounds: Background color switching

2. **@storybook/addon-links**
   - Navigate between stories

3. **@storybook/addon-a11y**
   - Accessibility testing and reporting
   - WCAG compliance checking

4. **@storybook/experimental-addon-test**
   - Component testing with Vitest
   - Browser-based testing with Playwright

### Using the A11y Addon

The accessibility addon automatically checks stories for WCAG violations:

```jsx
export const AccessibilityTest = {
  name: 'Accessibility Test',
  parameters: {
    a11y: {
      config: {
        rules: [
          { id: 'label', enabled: true },
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
        ],
      },
    },
  },
};
```

## Design Token Integration

Storybook is configured to use MorningAI's design tokens automatically. The tokens are applied via the global decorator in `.storybook/preview.jsx`:

```jsx
import { applyDesignTokens } from '../src/lib/design-tokens';

if (typeof window !== 'undefined') {
  applyDesignTokens('morning-ai', '.theme-morning-ai');
}
```

All stories are wrapped in a `.theme-morning-ai` container, ensuring consistent styling.

## Testing with Storybook

### Running Component Tests

```bash
npx vitest --project=storybook
```

This runs all play functions as tests using Vitest.

### Writing Testable Stories

```jsx
export const FormValidation = {
  name: 'Form Validation',
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    // Test empty form submission
    const submitButton = await canvas.findByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);
    
    // Assert validation errors appear
    await waitFor(() => {
      const errorMessages = canvas.queryAllByRole('alert');
      expect(errorMessages.length).toBeGreaterThan(0);
    });
    
    // Fill form with valid data
    const emailInput = await canvas.findByLabelText(/email/i);
    await userEvent.type(emailInput, 'test@example.com');
    
    // Submit again
    await userEvent.click(submitButton);
    
    // Assert success
    await waitFor(() => {
      expect(canvas.getByText(/success/i)).toBeInTheDocument();
    });
  },
};
```

## Best Practices

### 1. Story Naming

- Use descriptive names: `WithValidation`, `LoadingState`, `ErrorState`
- Group related stories: `Components/Dashboard`, `Components/Forms/LoginForm`

### 2. Documentation

- Always add component descriptions
- Document each story variant
- Include usage examples in docs

### 3. Accessibility

- Test all interactive components with a11y addon
- Ensure keyboard navigation works
- Verify screen reader compatibility

### 4. Responsive Design

- Create mobile view stories for all components
- Test different viewport sizes
- Use viewport addon for testing

### 5. Path Tracking Integration

When documenting components with Path Tracking:

```jsx
export const WithPathTracking = {
  name: 'With Path Tracking',
  parameters: {
    docs: {
      description: {
        story: 'This component integrates Path Tracking to monitor user interactions and send analytics data to Sentry.',
      },
    },
  },
};
```

## Troubleshooting

### Common Issues

#### 1. Component Not Rendering

**Problem**: Component shows blank screen

**Solution**: Check if component requires router context. Add MemoryRouter decorator:

```jsx
decorators: [
  (Story) => (
    <MemoryRouter>
      <Story />
    </MemoryRouter>
  ),
],
```

#### 2. Import Errors

**Problem**: "No matching export" error

**Solution**: Check if component uses default export:

```jsx
// Correct
import ComponentName from './ComponentName';

// Incorrect (if component uses default export)
import { ComponentName } from './ComponentName';
```

#### 3. Styling Issues

**Problem**: Components look unstyled

**Solution**: Ensure `index.css` is imported in `.storybook/preview.jsx`:

```jsx
import '../src/index.css';
```

## Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Writing Stories](https://storybook.js.org/docs/writing-stories)
- [Testing with Storybook](https://storybook.js.org/docs/writing-tests)
- [Accessibility Testing](https://storybook.js.org/docs/writing-tests/accessibility-testing)

## Next Steps

1. Add more component stories
2. Create interaction tests for all forms
3. Document design patterns
4. Set up Chromatic for visual regression testing
5. Integrate with CI/CD pipeline
