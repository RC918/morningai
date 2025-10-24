# Storybook Documentation

This directory contains the Storybook configuration for the frontend-dashboard application.

## Overview

Storybook is a tool for developing UI components in isolation. It allows you to browse a component library, view the different states of each component, and interactively develop and test components.

## Configuration Files

- **main.ts**: Main Storybook configuration
  - Defines story locations
  - Configures addons
  - Sets up Vite integration
  - Filters out PWA plugin to avoid build conflicts

- **preview.ts**: Preview configuration
  - Imports global styles (Tailwind CSS)
  - Configures controls and actions
  - Sets up background themes

## Running Storybook

### Development Mode

Start Storybook in development mode with hot reload:

```bash
npm run storybook
```

This will start Storybook on http://localhost:6006

### Build Static Version

Build a static version of Storybook for deployment:

```bash
npm run build-storybook
```

The output will be in the `storybook-static` directory.

## Addons

The following Storybook addons are configured:

- **@storybook/addon-essentials**: Essential addons including:
  - Controls: Interactive controls for component props
  - Actions: Log component events
  - Docs: Auto-generated documentation
  - Viewport: Test responsive designs
  - Backgrounds: Change background colors
  - Toolbars: Custom toolbar items

- **@storybook/addon-interactions**: Test user interactions

- **@storybook/addon-links**: Link between stories

- **@storybook/addon-a11y**: Accessibility testing

## Writing Stories

Stories are located alongside components in `src/components/ui/*.stories.tsx`.

### Basic Story Structure

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline'],
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Button',
  },
};
```

### Story Naming Convention

- Use PascalCase for story names
- Use descriptive names that indicate the state or variant
- Examples: `Default`, `WithIcon`, `Disabled`, `LongContent`

## Documented Components

The following UI components have Storybook documentation:

1. **Button** (`button.stories.tsx`)
   - All variants: default, destructive, outline, secondary, ghost, link
   - All sizes: default, sm, lg, icon
   - States: disabled, with click handler

2. **Card** (`card.stories.tsx`)
   - Basic card structure
   - With/without header and footer
   - Different content types
   - Various widths

3. **Input** (`input.stories.tsx`)
   - All input types: text, email, password, number, search, file
   - With labels and helper text
   - Error states
   - Disabled state

4. **Badge** (`badge.stories.tsx`)
   - All variants: default, secondary, destructive, outline
   - With icons
   - Different sizes
   - Status indicators

5. **Dialog** (`dialog.stories.tsx`)
   - Basic dialog
   - With forms
   - Confirmation dialogs
   - Long content with scrolling
   - Multiple action buttons

## Best Practices

1. **Autodocs**: Use the `autodocs` tag to automatically generate documentation from your stories

2. **Controls**: Define argTypes to provide interactive controls for component props

3. **Layout**: Use appropriate layout settings:
   - `centered`: For small components like buttons, badges
   - `padded`: For components that need some spacing
   - `fullscreen`: For page-level components

4. **Accessibility**: Test components with the a11y addon to ensure they meet accessibility standards

5. **Responsive Testing**: Use the viewport addon to test components at different screen sizes

## Troubleshooting

### Build Failures

If you encounter build failures:

1. Check that all component imports are correct
2. Ensure Tailwind CSS is properly configured
3. Verify that the PWA plugin is filtered out in `main.ts`

### Missing Styles

If components don't have proper styling:

1. Verify that `../src/index.css` is imported in `preview.ts`
2. Check that Tailwind CSS is configured correctly
3. Ensure all necessary CSS files are included

## Deployment

Storybook can be deployed to various platforms:

- **Vercel**: Connect your repository and set the build command to `npm run build-storybook`
- **Netlify**: Similar to Vercel, use `npm run build-storybook` as the build command
- **GitHub Pages**: Use the `storybook-static` directory as the source

## Resources

- [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)
- [Storybook Addons](https://storybook.js.org/addons)
- [Writing Stories](https://storybook.js.org/docs/react/writing-stories/introduction)
