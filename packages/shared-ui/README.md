# @morningai/shared-ui

Shared UI component library for MorningAI monorepo, featuring Apple-level design system with 47 production-ready components.

## Features

- 🎨 **Apple-level Design System** - iOS-inspired materials, spring animations, and polished interactions
- 🧩 **48 Shared Components** - Extracted from frontend-dashboard and owner-console (including StatusBadge)
- 🎭 **Radix UI Foundation** - Built on top of Radix UI primitives for accessibility
- 🎬 **Framer Motion 12.15** - Smooth spring-based animations with reduced motion support
- 🎯 **Design Tokens** - Centralized color, typography, spacing, and animation tokens
- 📦 **Tree-shakeable** - ESM and CJS builds with TypeScript support
- ♿ **Accessible** - WCAG AAA compliant (7:1 color contrast)
- 📚 **Storybook** - Interactive component documentation and visual testing

## Components Extracted

### Layout & Structure (5)
- `Card` - Container with elevation and rounded corners
- `Separator` - Horizontal or vertical divider
- `AspectRatio` - Maintain aspect ratio for media
- `ScrollArea` - Custom scrollable area
- `Resizable` - Resizable panels

### Navigation (7)
- `Tabs` - Tab navigation
- `Accordion` - Collapsible content sections
- `Breadcrumb` - Navigation breadcrumbs
- `NavigationMenu` - Complex navigation menus
- `Menubar` - Application menu bar
- `Sidebar` - Collapsible sidebar navigation
- `Pagination` - Page navigation

### Forms & Inputs (11)
- `Input` - Text input field
- `Textarea` - Multi-line text input
- `Checkbox` - Checkbox input
- `RadioGroup` - Radio button group
- `Switch` - Toggle switch
- `Slider` - Range slider
- `Select` - Dropdown select
- `InputOTP` - One-time password input
- `Calendar` - Date picker calendar
- `Form` - Form wrapper with validation
- `Label` - Form label

### Buttons & Actions (3)
- `Button` - Primary action button
- `Toggle` - Toggle button
- `ToggleGroup` - Group of toggle buttons

### Status & Indicators (1)
- `StatusBadge` - Status indicator with semantic colors (completed, running, failed, queued, assigned, cancelled)

### Feedback & Overlays (14)
- `Dialog` - Modal dialog
- `AlertDialog` - Confirmation dialog
- `Sheet` - Slide-in panel
- `Drawer` - Bottom drawer (mobile)
- `Popover` - Floating popover
- `Tooltip` - Hover tooltip
- `HoverCard` - Rich hover card
- `ContextMenu` - Right-click context menu
- `DropdownMenu` - Dropdown menu
- `Command` - Command palette (Cmd+K)
- `Alert` - Alert message
- `Toast` / `Sonner` - Toast notifications
- `Progress` - Progress indicator
- `Skeleton` - Loading skeleton

### Data Display (7)
- `Table` - Data table
- `Badge` - Status badge
- `Avatar` - User avatar
- `Chart` - Data visualization (recharts)
- `Carousel` - Image carousel
- `Collapsible` - Collapsible content

## Installation

This package is part of the monorepo workspace. It's automatically available to other workspace packages.

```bash
# In your workspace package
pnpm add @morningai/shared-ui@workspace:*
```

## Usage

### Basic Components

```tsx
import { Button, Card, Input } from '@morningai/shared-ui'

function MyComponent() {
  return (
    <Card>
      <Input placeholder="Enter text..." />
      <Button>Submit</Button>
    </Card>
  )
}
```

### With Animations

```tsx
import { motion } from 'framer-motion'
import { fadeIn, slideUp, buttonPress } from '@morningai/shared-ui/animations'
import { Button } from '@morningai/shared-ui'

function AnimatedComponent() {
  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible">
      <motion.div variants={slideUp}>
        <Button {...buttonPress}>Click me</Button>
      </motion.div>
    </motion.div>
  )
}
```

### Design Tokens

```tsx
import tokens from '@morningai/shared-ui/tokens.json'

// Access design tokens
const primaryColor = tokens.color.primary[500]
const spacing = tokens.space.md
const springEasing = tokens.animation.easing.spring
```

## Development

### Build

```bash
pnpm run build
```

### Development Mode

```bash
pnpm run dev
```

### Storybook

View and interact with components in isolation:

```bash
pnpm run storybook
```

Build Storybook for deployment:

```bash
pnpm run build-storybook
```

### Type Checking

```bash
pnpm run type-check
```

### Testing

```bash
# Run tests
pnpm run test

# Run tests in watch mode
pnpm run test:watch

# Run tests with coverage
pnpm run test:coverage
```

## Animation System

### Spring-based Animations

All animations use spring physics for natural, Apple-like motion:

```tsx
import { getSpringTransition, hoverScale, tapScale } from '@morningai/shared-ui/animations'

const springConfig = getSpringTransition(300, 30) // stiffness, damping
```

### Animation Variants

Pre-built animation variants for common patterns:

- `fadeIn` - Fade in animation
- `slideUp` - Slide up from bottom
- `scale` - Scale in animation
- `staggerContainer` - Stagger children animations
- `buttonPress` - Button hover and tap animations

### Reduced Motion Support

All animations respect `prefers-reduced-motion`:

```tsx
import { withReducedMotion, fadeIn } from '@morningai/shared-ui/animations'

<motion.div variants={withReducedMotion(fadeIn)}>
  Content
</motion.div>
```

## Design Tokens

### Color System

- **Primary**: Blue scale (50-900)
- **Accent**: Purple and Orange scales
- **Semantic**: Success, Error, Warning, Info
- **Neutral**: Gray scale (50-900)
- **Background**: Base, Surface, Overlay

### Typography

- **Font Families**: Inter (primary), IBM Plex Sans (secondary), IBM Plex Mono (mono)
- **Font Sizes**: 7 levels from caption (12px) to display (48px)
- **Font Weights**: Regular (400), Medium (500), Semibold (600), Bold (700)

### Spacing

8-point grid system: `xs` (4px), `sm` (8px), `md` (16px), `lg` (24px), `xl` (32px), `2xl` (48px), `3xl` (64px), `4xl` (96px)

### Shadows

5-level shadow system: `sm`, `md`, `lg`, `xl`, `2xl`

### Animation

- **Durations**: instant (50ms), fast (150ms), normal (300ms), slow (500ms)
- **Easing**: linear, easeIn, easeOut, easeInOut, spring (Apple-style)

## Architecture

```
packages/shared-ui/
├── src/
│   ├── components/
│   │   └── ui/           # 47 UI components
│   ├── lib/
│   │   └── animations.ts # Animation utilities
│   ├── tokens.json       # Design tokens
│   ├── utils.ts          # Utility functions
│   └── index.ts          # Main export
├── package.json
├── tsconfig.json
└── README.md
```

## Dependencies

### Peer Dependencies
- `react` ^18.0.0
- `react-dom` ^18.0.0

### Main Dependencies
- Radix UI components (dialog, dropdown, popover, etc.)
- `class-variance-authority` - Component variants
- `clsx` + `tailwind-merge` - Utility classes
- `lucide-react` - Icons
- `framer-motion` - Animations
- `react-i18next` - Internationalization

## Benefits

### Code Reduction
- **Before**: 166 components (111 frontend-dashboard + 55 owner-console)
- **After**: 119 components (72 unique + 47 shared)
- **Reduction**: 28% (47 components eliminated)

### File Size
- Estimated 200-250KB of duplicated code removed
- 15-20% bundle size reduction per application

### Maintenance
- Single source of truth for UI components
- Easier to maintain consistency
- Faster bug fixes (fix once, apply everywhere)
- Better type safety with shared types
- Unified design system across all apps

## Current Status

✅ **Phase 1 Complete**: Component Extraction
- 48 components extracted (including StatusBadge)
- Apple-level design system integrated
- Animation utilities added
- Design tokens centralized
- Package structure created
- Dependencies configured

✅ **Phase 2 Complete**: Storybook & Documentation
- Storybook 8 configured with Vite
- Interactive component stories
- Design tokens preview decorator
- Unit tests for StatusBadge
- Component documentation

⏳ **Phase 3 Pending**: Application Migration
- Migrate frontend-dashboard to use shared components
- Migrate owner-console to use shared components
- Remove duplicate files

## Migration Guide

### From Local Components

Replace local component imports with shared-ui imports:

```tsx
// Before
import { Button } from '@/components/ui/button'

// After
import { Button } from '@morningai/shared-ui'
```

### Utility Functions

Update utility imports:

```tsx
// Before
import { cn } from '@/lib/utils'

// After
import { cn } from '@morningai/shared-ui/utils'
```

## Related Documentation

- [UI/UX Quick Start Guide](../../docs/UI_UX_QUICKSTART.md)
- [UI/UX Cheat Sheet](../../docs/UI_UX_CHEATSHEET.md)
- [Design System Guidelines](../../DESIGN_SYSTEM_GUIDELINES.md)
- [Apple-level UI/UX Optimization Report](../../APPLE_LEVEL_UI_UX_OPTIMIZATION_REPORT.md)
- [CODE_DUPLICATION_ANALYSIS.md](../../CODE_DUPLICATION_ANALYSIS.md)
- [SHARED_COMPONENT_MIGRATION_PLAN.md](../../SHARED_COMPONENT_MIGRATION_PLAN.md)

## Contributing

When adding new shared components:

1. Ensure the component is used in at least 2 apps
2. Follow the existing component structure
3. Use Design Tokens for styling
4. Add animation support with reduced motion
5. Ensure WCAG AAA accessibility
6. Update this README

## License

MIT
