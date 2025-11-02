# Storybook Coverage Expansion Plan - P1 Task

**Date**: November 2, 2025  
**Scope**: Expand Storybook coverage for all 47 shared-ui components  
**Target**: 100% story coverage for @morningai/shared-ui

---

## Executive Summary

**Current State**:
- Total shared-ui components: 47
- Existing story files: 21 (in frontend-dashboard)
- Current coverage: ~45% (estimated)

**Target State**:
- Story coverage: 100% (all 47 components)
- Stories location: packages/shared-ui/.storybook/
- Documentation: Complete with usage examples

**Estimated Effort**: 15-20 hours (30-40 minutes per component)

---

## Component Inventory

### Shared-UI Components (47 total)

Based on `packages/shared-ui/src/components/ui/`:

1. accordion.tsx
2. alert.tsx
3. alert-dialog.tsx
4. aspect-ratio.tsx
5. avatar.tsx
6. badge.tsx
7. breadcrumb.tsx
8. button.tsx
9. calendar.tsx
10. card.tsx
11. carousel.tsx
12. chart.tsx
13. checkbox.tsx
14. collapsible.tsx
15. command.tsx
16. context-menu.tsx
17. dialog.tsx
18. drawer.tsx
19. dropdown-menu.tsx
20. form.tsx
21. hover-card.tsx
22. input.tsx
23. input-otp.tsx
24. label.tsx
25. menubar.tsx
26. navigation-menu.tsx
27. pagination.tsx
28. popover.tsx
29. progress.tsx
30. radio-group.tsx
31. resizable.tsx
32. scroll-area.tsx
33. select.tsx
34. separator.tsx
35. sheet.tsx
36. sidebar.tsx
37. sidebar-variants.tsx
38. skeleton.tsx
39. slider.tsx
40. sonner.tsx
41. switch.tsx
42. table.tsx
43. tabs.tsx
44. textarea.tsx
45. toaster.tsx
46. toggle.tsx
47. toggle-group.tsx
48. tooltip.tsx
49. use-sidebar.tsx (hook, not component)

**Actual Components**: 47 (excluding use-sidebar hook)

---

## Current Story Coverage

### Existing Stories (21 files in frontend-dashboard)

Stories currently exist in `handoff/20250928/40_App/frontend-dashboard/`:

1. apple-action-sheet.stories.tsx
2. apple-button.stories.tsx
3. apple-control-center.stories.tsx
4. apple-input.stories.tsx
5. apple-live-activity.stories.tsx
6. apple-modal.stories.tsx
7. apple-picker.stories.tsx
8. apple-segmented-control.stories.tsx
9. apple-sheet.stories.tsx
10. apple-spotlight.stories.tsx
11. apple-tab-bar.stories.tsx
12. apple-toast.stories.tsx
13. color-system.stories.tsx
14. lazy-image.stories.tsx
15. material-system.stories.tsx
16. micro-interactions.stories.tsx
17. shadow-system.stories.tsx
18. spacing-system.stories.tsx
19. spring-animation.stories.tsx
20. theme-toggle.stories.tsx
21. typography-system.stories.tsx

**Note**: These are for local components and design system documentation, NOT for shared-ui components.

### Missing Stories

**All 47 shared-ui components** need stories created in `packages/shared-ui/`.

---

## Implementation Plan

### Phase 1: Setup Storybook in shared-ui (Week 1)

**Effort**: 2-3 hours

**Tasks**:
1. Create `.storybook/` directory in `packages/shared-ui/`
2. Configure Storybook for shared-ui package
3. Set up Tailwind CSS in Storybook
4. Configure design tokens
5. Create story template

**Deliverables**:
- `packages/shared-ui/.storybook/main.ts`
- `packages/shared-ui/.storybook/preview.ts`
- `packages/shared-ui/.storybook/manager.ts`
- Story template file

**Configuration Example**:
```ts
// packages/shared-ui/.storybook/main.ts
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx|mdx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
};

export default config;
```

---

### Phase 2: Create Stories - Priority 1 (Week 1-2)

**High-Usage Components** (15 components)  
**Effort**: 7-8 hours (30 minutes each)

Priority based on typical usage frequency:

1. **button.tsx** - Most used component
2. **input.tsx** - Form foundation
3. **card.tsx** - Layout component
4. **dialog.tsx** - Modal interactions
5. **sheet.tsx** - Side panels
6. **form.tsx** - Form wrapper
7. **label.tsx** - Form labels
8. **checkbox.tsx** - Form input
9. **select.tsx** - Form input
10. **tabs.tsx** - Navigation
11. **badge.tsx** - Status indicators
12. **alert.tsx** - Notifications
13. **tooltip.tsx** - Help text
14. **dropdown-menu.tsx** - Menus
15. **table.tsx** - Data display

**Story Template**:
```tsx
// packages/shared-ui/src/components/ui/button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: {
    children: 'Button',
  },
};

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
};

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex gap-4">
      <Button variant="default">Default</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
    </div>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};

export const WithIcon: Story = {
  render: () => (
    <Button>
      <svg className="mr-2 h-4 w-4" /* ... */>
      Button with Icon
    </Button>
  ),
};
```

---

### Phase 3: Create Stories - Priority 2 (Week 3)

**Medium-Usage Components** (16 components)  
**Effort**: 8 hours (30 minutes each)

16. avatar.tsx
17. breadcrumb.tsx
18. switch.tsx
19. textarea.tsx
20. progress.tsx
21. separator.tsx
22. skeleton.tsx
23. slider.tsx
24. toggle.tsx
25. toggle-group.tsx
26. radio-group.tsx
27. popover.tsx
28. hover-card.tsx
29. alert-dialog.tsx
30. context-menu.tsx
31. menubar.tsx

---

### Phase 4: Create Stories - Priority 3 (Week 4)

**Specialized Components** (16 components)  
**Effort**: 8 hours (30 minutes each)

32. accordion.tsx
33. aspect-ratio.tsx
34. calendar.tsx
35. carousel.tsx
36. chart.tsx
37. collapsible.tsx
38. command.tsx
39. drawer.tsx
40. input-otp.tsx
41. navigation-menu.tsx
42. pagination.tsx
43. resizable.tsx
44. scroll-area.tsx
45. sidebar.tsx
46. sidebar-variants.tsx
47. sonner.tsx
48. toaster.tsx

---

## Story Requirements

### Minimum Requirements for Each Story

1. **Meta Configuration**:
   - Title (e.g., 'Components/Button')
   - Component reference
   - Tags: ['autodocs']
   - ArgTypes for all props

2. **Default Story**:
   - Basic usage example
   - Default props

3. **Variant Stories**:
   - One story per variant
   - All variants showcase

4. **Interactive Stories**:
   - User interaction examples
   - State management examples

5. **Accessibility Notes**:
   - Keyboard navigation
   - Screen reader support
   - ARIA attributes

6. **Usage Documentation**:
   - When to use
   - Best practices
   - Common patterns

---

## Automation Opportunities

### Story Generator Script

Create a script to generate story boilerplate:

```bash
#!/bin/bash
# generate-story.sh

COMPONENT_NAME=$1
COMPONENT_FILE="packages/shared-ui/src/components/ui/${COMPONENT_NAME}.tsx"
STORY_FILE="packages/shared-ui/src/components/ui/${COMPONENT_NAME}.stories.tsx"

if [ ! -f "$COMPONENT_FILE" ]; then
  echo "Component file not found: $COMPONENT_FILE"
  exit 1
fi

# Extract component name (PascalCase)
COMPONENT_PASCAL=$(echo $COMPONENT_NAME | sed -r 's/(^|-)([a-z])/\U\2/g')

# Generate story template
cat > "$STORY_FILE" << EOF
import type { Meta, StoryObj } from '@storybook/react';
import { ${COMPONENT_PASCAL} } from './${COMPONENT_NAME}';

const meta: Meta<typeof ${COMPONENT_PASCAL}> = {
  title: 'Components/${COMPONENT_PASCAL}',
  component: ${COMPONENT_PASCAL},
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ${COMPONENT_PASCAL}>;

export const Default: Story = {
  args: {
    // Add default props
  },
};
EOF

echo "✅ Created story: $STORY_FILE"
```

**Usage**:
```bash
./generate-story.sh button
./generate-story.sh input
# ... etc
```

---

## Success Metrics

| Metric | Current | Target (Week 2) | Target (Week 4) |
|--------|---------|-----------------|-----------------|
| Story coverage | 0% | 32% (15/47) | 100% (47/47) |
| Components with docs | 0 | 15 | 47 |
| Accessibility notes | 0 | 15 | 47 |
| Interactive examples | 0 | 15 | 47 |

---

## Integration with CI/CD

### Storybook Build in CI

Add to `.github/workflows/frontend.yml`:

```yaml
- name: Build Storybook
  run: |
    cd packages/shared-ui
    pnpm run build-storybook

- name: Upload Storybook
  uses: actions/upload-artifact@v4
  with:
    name: storybook-static
    path: packages/shared-ui/storybook-static
```

### Storybook Deployment

Deploy to Vercel or Chromatic:

```yaml
- name: Deploy Storybook
  run: |
    cd packages/shared-ui
    pnpm run chromatic --project-token=${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

---

## Visual Regression Testing

### Playwright VRT Integration

Add VRT tests for each story:

```ts
// packages/shared-ui/src/components/ui/button.vrt.test.ts
import { test, expect } from '@playwright/test';

test.describe('Button Visual Regression', () => {
  test('default variant', async ({ page }) => {
    await page.goto('http://localhost:6006/?path=/story/components-button--default');
    await expect(page).toHaveScreenshot('button-default.png');
  });

  test('all variants', async ({ page }) => {
    await page.goto('http://localhost:6006/?path=/story/components-button--all-variants');
    await expect(page).toHaveScreenshot('button-all-variants.png');
  });
});
```

---

## Timeline Summary

| Week | Tasks | Deliverables |
|------|-------|--------------|
| Week 1 | Setup + Priority 1 (8 components) | Storybook config + 8 stories |
| Week 2 | Priority 1 completion (7 components) | 15 stories total |
| Week 3 | Priority 2 (16 components) | 31 stories total |
| Week 4 | Priority 3 (16 components) | 47 stories total (100%) |

**Total Effort**: 15-20 hours over 4 weeks

---

## Next Steps

1. **Immediate** (This PR):
   - ✅ Document Storybook expansion plan (DONE)
   - [ ] Create GitHub issue for Storybook setup
   - [ ] Create GitHub issues for story creation (by priority)

2. **Week 1**:
   - [ ] Set up Storybook in shared-ui package
   - [ ] Create story generator script
   - [ ] Create first 8 stories (Priority 1)

3. **Week 2-4**:
   - [ ] Complete remaining stories
   - [ ] Add VRT tests
   - [ ] Deploy Storybook to Chromatic/Vercel

---

**Appendix: Component Checklist**

Track progress with this checklist:

**Priority 1** (15):
- [ ] button
- [ ] input
- [ ] card
- [ ] dialog
- [ ] sheet
- [ ] form
- [ ] label
- [ ] checkbox
- [ ] select
- [ ] tabs
- [ ] badge
- [ ] alert
- [ ] tooltip
- [ ] dropdown-menu
- [ ] table

**Priority 2** (16):
- [ ] avatar
- [ ] breadcrumb
- [ ] switch
- [ ] textarea
- [ ] progress
- [ ] separator
- [ ] skeleton
- [ ] slider
- [ ] toggle
- [ ] toggle-group
- [ ] radio-group
- [ ] popover
- [ ] hover-card
- [ ] alert-dialog
- [ ] context-menu
- [ ] menubar

**Priority 3** (16):
- [ ] accordion
- [ ] aspect-ratio
- [ ] calendar
- [ ] carousel
- [ ] chart
- [ ] collapsible
- [ ] command
- [ ] drawer
- [ ] input-otp
- [ ] navigation-menu
- [ ] pagination
- [ ] resizable
- [ ] scroll-area
- [ ] sidebar
- [ ] sidebar-variants
- [ ] sonner
- [ ] toaster
