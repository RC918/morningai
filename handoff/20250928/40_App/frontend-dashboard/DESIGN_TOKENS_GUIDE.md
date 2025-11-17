# Design Tokens Usage Guide

## Overview

This guide explains how to use semantic design tokens in the MorningAI frontend applications. Design tokens provide a consistent, maintainable approach to styling by replacing hardcoded color values with semantic tokens that convey meaning and intent.

## Why Design Tokens?

**Benefits:**
- **Consistency**: Ensures uniform styling across the application
- **Maintainability**: Change colors globally by updating token definitions
- **Semantic Clarity**: Token names convey purpose (e.g., `error-600` vs `red-600`)
- **Accessibility**: Tokens are designed with WCAG contrast requirements
- **Theme Support**: Easy to implement dark mode and custom themes
- **Type Safety**: Prevents typos and invalid color combinations

## Semantic Token Mapping

### Color Categories

| Semantic Token | Use Case | Replaces | Example |
|---------------|----------|----------|---------|
| `error-*` | Error states, destructive actions, validation failures | `red-*` | Delete buttons, error messages |
| `success-*` | Success states, confirmations, positive feedback | `green-*` | Success toasts, checkmarks |
| `warning-*` | Warning states, cautions, important notices | `yellow-*`, `amber-*` | Warning banners, alerts |
| `info-*` | Informational content, hints, tooltips | `blue-*` (non-CTA) | Info badges, help text |
| `neutral-*` | Neutral elements, disabled states, borders | `gray-*` | Dividers, disabled inputs |
| `primary-*` | Primary CTAs, interactive elements, brand colors | `blue-*` (CTA) | Primary buttons, links |
| `accent-*` | Accent elements, highlights, secondary brand | `purple-*` | Badges, highlights |

### Shade Guidelines

Each semantic token has 11 shades (50-950) following Tailwind's convention:

- **50-100**: Very light backgrounds, subtle highlights
- **200-300**: Light backgrounds, hover states
- **400-500**: Medium contrast, secondary text
- **600-700**: Primary text, strong borders (most common)
- **800-900**: Dark text, strong emphasis
- **950**: Darkest shade, maximum contrast

## Usage Examples

### ❌ Before (Hardcoded Colors)

```tsx
// Error state
<div className="text-red-600 bg-red-100 border-red-300">
  Error: Invalid input
</div>

// Success state
<button className="bg-green-600 hover:bg-green-700 text-white">
  Save Changes
</button>

// Info badge
<span className="bg-blue-100 text-blue-800">
  New Feature
</span>

// Disabled input
<input className="bg-gray-100 text-gray-400 border-gray-300" disabled />
```

### ✅ After (Semantic Tokens)

```tsx
// Error state
<div className="text-error-600 bg-error-100 border-error-300">
  Error: Invalid input
</div>

// Success state
<button className="bg-success-600 hover:bg-success-700 text-white">
  Save Changes
</button>

// Info badge
<span className="bg-info-100 text-info-800">
  New Feature
</span>

// Disabled input
<input className="bg-neutral-100 text-neutral-400 border-neutral-300" disabled />
```

## Context-Dependent Blue Mapping

Blue colors require context-aware mapping:

### Primary (CTAs and Interactive Elements)

Use `primary-*` for:
- Primary action buttons
- Active navigation items
- Selected states
- Interactive links
- Focus indicators

```tsx
// ✅ Correct
<button className="bg-primary-600 hover:bg-primary-700">
  Get Started
</button>

<a className="text-primary-600 hover:text-primary-700">
  Learn More
</a>
```

### Info (Informational Content)

Use `info-*` for:
- Informational badges
- Help tooltips
- Status indicators (non-interactive)
- Informational alerts
- Documentation hints

```tsx
// ✅ Correct
<div className="bg-info-100 text-info-800 border-info-300">
  💡 Tip: You can use keyboard shortcuts
</div>

<span className="bg-info-100 text-info-700 px-2 py-1 rounded">
  Beta
</span>
```

## Component Patterns

### Buttons

```tsx
// Primary action
<button className="bg-primary-600 hover:bg-primary-700 text-white">
  Submit
</button>

// Destructive action
<button className="bg-error-600 hover:bg-error-700 text-white">
  Delete
</button>

// Secondary action
<button className="bg-neutral-200 hover:bg-neutral-300 text-neutral-900">
  Cancel
</button>
```

### Alerts and Notifications

```tsx
// Error alert
<div className="bg-error-100 border-error-300 text-error-800">
  <AlertCircle className="text-error-600" />
  <p>Failed to save changes</p>
</div>

// Success alert
<div className="bg-success-100 border-success-300 text-success-800">
  <CheckCircle className="text-success-600" />
  <p>Changes saved successfully</p>
</div>

// Warning alert
<div className="bg-warning-100 border-warning-300 text-warning-800">
  <AlertTriangle className="text-warning-600" />
  <p>Your session will expire soon</p>
</div>

// Info alert
<div className="bg-info-100 border-info-300 text-info-800">
  <Info className="text-info-600" />
  <p>New features are available</p>
</div>
```

### Badges and Tags

```tsx
// Status badges
<span className="bg-success-100 text-success-700">Active</span>
<span className="bg-error-100 text-error-700">Inactive</span>
<span className="bg-warning-100 text-warning-700">Pending</span>
<span className="bg-info-100 text-info-700">Draft</span>

// Category tags
<span className="bg-accent-100 text-accent-700">Premium</span>
<span className="bg-neutral-100 text-neutral-700">Standard</span>
```

### Form Elements

```tsx
// Input with error
<input 
  className="border-error-300 focus:ring-error-500 text-error-900"
  aria-invalid="true"
/>
<p className="text-error-600">Email is required</p>

// Input with success
<input 
  className="border-success-300 focus:ring-success-500"
  aria-invalid="false"
/>
<p className="text-success-600">Email is valid</p>

// Disabled input
<input 
  className="bg-neutral-100 border-neutral-300 text-neutral-400"
  disabled
/>
```

## Allowed Non-Semantic Colors

Some colors are allowed for specific use cases:

- **`gray-*`**: Allowed for neutral UI elements (equivalent to `neutral-*`)
- **`white`**: Pure white backgrounds
- **`black`**: Pure black text (rare, use `neutral-900` instead)
- **`transparent`**: Transparent backgrounds
- **`current`**: Inherits current text color
- **`inherit`**: Inherits parent color

## ESLint Rule

An ESLint rule (`custom/no-hardcoded-colors`) automatically detects hardcoded Tailwind color utilities and suggests semantic tokens.

### Rule Behavior

```tsx
// ❌ Error: Hardcoded color detected
<div className="text-red-600">Error</div>
// Suggestion: Use text-error-600 instead

// ✅ Allowed: Semantic token
<div className="text-error-600">Error</div>

// ✅ Allowed: Neutral colors
<div className="bg-white text-gray-600">Content</div>
```

### Pre-commit Hook

The pre-commit hook automatically runs ESLint on staged files, preventing hardcoded colors from being committed:

```bash
# This will fail if hardcoded colors are detected
git commit -m "Add new feature"

# Fix the violations, then commit again
git commit -m "Add new feature"
```

## Token Definitions

Semantic color tokens are defined in `src/index.css` using Tailwind v4's `@theme` directive:

```css
@theme {
  /* Error colors (red) */
  --color-error-50: #fef2f2;
  --color-error-600: #dc2626;
  /* ... more shades ... */

  /* Success colors (green) */
  --color-success-50: #f0fdf4;
  --color-success-600: #16a34a;
  /* ... more shades ... */

  /* Warning colors (yellow/amber) */
  --color-warning-50: #fffbeb;
  --color-warning-600: #d97706;
  /* ... more shades ... */

  /* Info colors (blue) */
  --color-info-50: #eff6ff;
  --color-info-600: #2563eb;
  /* ... more shades ... */

  /* Neutral colors (gray) */
  --color-neutral-50: #f9fafb;
  --color-neutral-600: #4b5563;
  /* ... more shades ... */

  /* Primary colors (blue) */
  --color-primary-50: #eff6ff;
  --color-primary-600: #2563eb;
  /* ... more shades ... */

  /* Accent colors (purple) */
  --color-accent-50: #faf5ff;
  --color-accent-600: #9333ea;
  /* ... more shades ... */
}
```

## Migration Checklist

When migrating existing components:

1. **Identify the intent**: What is the purpose of this color?
   - Error/validation? → `error-*`
   - Success/confirmation? → `success-*`
   - Warning/caution? → `warning-*`
   - Information/hint? → `info-*`
   - Neutral/disabled? → `neutral-*`
   - Primary CTA? → `primary-*`
   - Accent/highlight? → `accent-*`

2. **Choose the appropriate shade**: Match the contrast level
   - Light backgrounds: 50-100
   - Medium contrast: 400-500
   - Primary text/borders: 600-700
   - Dark text: 800-900

3. **Test accessibility**: Verify WCAG contrast requirements
   - Text on background: minimum 4.5:1 (AA)
   - Large text: minimum 3:1 (AA)

4. **Run ESLint**: Verify no hardcoded colors remain
   ```bash
   pnpm eslint src/
   ```

5. **Test visually**: Ensure colors look correct in context

## Common Mistakes

### ❌ Using hardcoded colors

```tsx
<div className="text-red-600">Error</div>
```

### ❌ Using wrong semantic token

```tsx
// Using error for informational content
<span className="bg-error-100 text-error-700">New</span>
```

### ❌ Inconsistent shade usage

```tsx
// Mixing shades without purpose
<div className="bg-error-50 text-error-900 border-error-300">
  Error message
</div>
```

### ✅ Correct usage

```tsx
// Semantic token with consistent shades
<div className="bg-error-100 text-error-800 border-error-300">
  <AlertCircle className="text-error-600" />
  <p>Error message</p>
</div>
```

## Dark Mode Support

Semantic tokens are designed to work with dark mode. When implementing dark mode:

```tsx
// Tokens automatically adjust for dark mode
<div className="bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100">
  Content adapts to theme
</div>
```

## Resources

- **Token Definitions**: `src/index.css` (lines 17-107)
- **ESLint Rule**: `eslint-rules/no-hardcoded-colors.js`
- **ESLint Config**: `eslint.config.js`
- **Pre-commit Hook**: `.husky/pre-commit`
- **Issue Tracker**: GitHub Issue #1327 (Color Migration)

## Questions?

If you have questions about which semantic token to use:

1. Check this guide for similar examples
2. Look at existing components for patterns
3. Consider the user's intent and context
4. When in doubt, ask the team

## Version History

- **v1.0.0** (2025-11-17): Initial guide with all semantic tokens
  - Added error, success, warning, info, neutral, primary, accent tokens
  - Documented ESLint rule and pre-commit hook
  - Provided comprehensive examples and patterns
