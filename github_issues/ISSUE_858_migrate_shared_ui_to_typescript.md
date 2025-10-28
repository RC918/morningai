# Issue #858: Migrate shared-ui Package to TypeScript

## 🎯 Priority: HIGH

## 📋 Overview

Convert all 47 `.jsx` component files in `@morningai/shared-ui` to `.tsx` with proper TypeScript type definitions. This will enable proper type checking for shared-ui consumers and eliminate 400+ false positive type errors.

## 🔍 Background

### Current State
- **47 `.jsx` files** in `packages/shared-ui/src/components/ui/`
- **0 `.tsx` files**
- When tsup generates `.d.ts` from `.jsx`, it incorrectly marks all props (including `className`) as required
- This causes **441 TS2741 errors** in consuming applications

### Root Cause
```typescript
// Current: tsup generates from .jsx
declare function Card({ className, ...props }: {
    className: any;  // ❌ Required, type: any
    interactive?: boolean;
}): JSX.Element;

// Expected: proper TypeScript
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    className?: string;  // ✅ Optional, type: string
    interactive?: boolean;
}
declare function Card(props: CardProps): JSX.Element;
```

## 🎯 Acceptance Criteria

### 1. File Conversion
- [ ] All 47 `.jsx` files converted to `.tsx`
- [ ] No `.jsx` files remain in `src/components/ui/`
- [ ] All components compile without errors

### 2. Type Definitions
- [ ] All component props properly typed
- [ ] `className` is optional (`className?: string`)
- [ ] Components extend appropriate React HTML attribute types:
  - `React.ComponentPropsWithoutRef<'div'>` for div-based components
  - `React.ComponentPropsWithoutRef<'button'>` for button-based components
  - `React.ComponentPropsWithoutRef<'span'>` for span-based components
  - etc.

### 3. Build Configuration
- [ ] `package.json` build script includes `--dts` flag
- [ ] Build generates `dist/index.d.ts` and `dist/index.d.mts`
- [ ] `package.json` "types" field points to `dist/index.d.ts`

### 4. Type Safety Verification
- [ ] `pnpm run build` succeeds in shared-ui
- [ ] `pnpm run typecheck` in frontend-dashboard shows **≤19 errors** (baseline)
- [ ] No TS2741 "Property 'className' is missing" errors
- [ ] IDE autocomplete works for shared-ui components

### 5. Documentation
- [ ] Update shared-ui README with TypeScript usage examples
- [ ] Document prop types for commonly used components

## 📦 Affected Files

### Components to Convert (47 files)
```
src/components/ui/
├── accordion.jsx
├── alert-dialog.jsx
├── alert.jsx
├── aspect-ratio.jsx
├── avatar.jsx
├── badge.jsx
├── breadcrumb.jsx
├── button.jsx
├── calendar.jsx
├── card.jsx
├── carousel.jsx
├── chart.jsx
├── checkbox.jsx
├── collapsible.jsx
├── command.jsx
├── context-menu.jsx
├── dialog.jsx
├── drawer.jsx
├── dropdown-menu.jsx
├── form.jsx
├── hover-card.jsx
├── input-otp.jsx
├── input.jsx
├── label.jsx
├── menubar.jsx
├── navigation-menu.jsx
├── pagination.jsx
├── popover.jsx
├── progress.jsx
├── radio-group.jsx
├── resizable.jsx
├── scroll-area.jsx
├── select.jsx
├── separator.jsx
├── sheet.jsx
├── sidebar.jsx
├── skeleton.jsx
├── slider.jsx
├── sonner.jsx
├── switch.jsx
├── table.jsx
├── tabs.jsx
├── textarea.jsx
├── toaster.jsx
├── toggle-group.jsx
├── toggle.jsx
└── tooltip.jsx
```

### Configuration Files
- `packages/shared-ui/package.json` (build scripts)
- `packages/shared-ui/tsconfig.json` (already configured)

## 🔧 Implementation Strategy

### Batch 1: High-Frequency Components (Day 1) ✅ COMPLETED
**Priority: CRITICAL** - Most used across the application

Convert these 10 components first:
1. ✅ `card.jsx` → `card.tsx` (5 sub-components)
2. ✅ `button.jsx` → `button.tsx` (with CVA variants)
3. ✅ `badge.jsx` → `badge.tsx` (with CVA variants)
4. ✅ `input.jsx` → `input.tsx`
5. ✅ `label.jsx` → `label.tsx` (Radix UI)
6. ✅ `dialog.jsx` → `dialog.tsx` (10 sub-components, Radix UI)
7. ✅ `tabs.jsx` → `tabs.tsx` (4 sub-components, Radix UI)
8. ✅ `select.jsx` → `select.tsx` (10 sub-components, Radix UI)
9. ✅ `table.jsx` → `table.tsx` (8 sub-components)
10. ✅ `form.jsx` → `form.tsx` (6 sub-components, react-hook-form)

**Batch 1 Results:**
```bash
# Build Status: ✅ SUCCESS
cd packages/shared-ui
pnpm run build
# Output:
# - CJS dist/index.js 167.12 KB
# - ESM dist/index.mjs 145.27 KB
# - DTS dist/index.d.ts 51.01 KB
# - DTS dist/index.d.mts 51.01 KB

# Typecheck Status: ✅ SUCCESS
cd ../../handoff/20250928/40_App/frontend-dashboard
pnpm run typecheck
# Result: 0 className errors for Batch 1 components
# Remaining errors are from OTHER .jsx components (RadioGroup, Separator, etc.)
```

**Key Achievements:**
- All 10 Batch 1 components now have proper TypeScript interfaces
- `className` is optional (`className?: string`) in all converted components
- 0 TS2741 errors for Card, Button, Badge, Input, Label, Dialog, Tabs, Select, Table, Form
- Build generates correct .d.ts files with optional className
- Remaining 50+ className errors are from Batch 2/3 components (RadioGroup, Separator, Checkbox, Avatar, Switch, Skeleton, etc.)

### Batch 2: Medium-Frequency Components (Day 2)
**Priority: HIGH**

Convert these 15 components:
1. `accordion.jsx`
2. `alert.jsx`
3. `alert-dialog.jsx`
4. `avatar.jsx`
5. `checkbox.jsx`
6. `dropdown-menu.jsx`
7. `popover.jsx`
8. `progress.jsx`
9. `radio-group.jsx`
10. `scroll-area.jsx`
11. `separator.jsx`
12. `sheet.jsx`
13. `switch.jsx`
14. `textarea.jsx`
15. `tooltip.jsx`

### Batch 3: Low-Frequency Components (Day 3)
**Priority: MEDIUM**

Convert remaining 22 components:
1. `aspect-ratio.jsx`
2. `breadcrumb.jsx`
3. `calendar.jsx`
4. `carousel.jsx`
5. `chart.jsx`
6. `collapsible.jsx`
7. `command.jsx`
8. `context-menu.jsx`
9. `drawer.jsx`
10. `hover-card.jsx`
11. `input-otp.jsx`
12. `menubar.jsx`
13. `navigation-menu.jsx`
14. `pagination.jsx`
15. `resizable.jsx`
16. `sidebar.jsx`
17. `skeleton.jsx`
18. `slider.jsx`
19. `sonner.jsx`
20. `toaster.jsx`
21. `toggle-group.jsx`
22. `toggle.jsx`

## 📝 Example Conversion

### Before: `card.jsx`
```jsx
import * as React from "react"
import { cn } from "../../utils"

function Card({
  className,
  interactive = false,
  ...props
}) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        interactive && "card-hover cursor-pointer",
        className
      )}
      {...props} />
  );
}

function CardHeader({
  className,
  ...props
}) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6",
        className
      )}
      {...props} />
  );
}

export { Card, CardHeader }
```

### After: `card.tsx`
```tsx
import * as React from "react"
import { cn } from "../../utils"

interface CardProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
  interactive?: boolean;
}

function Card({
  className,
  interactive = false,
  ...props
}: CardProps) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        interactive && "card-hover cursor-pointer",
        className
      )}
      {...props} />
  );
}

interface CardHeaderProps extends React.ComponentPropsWithoutRef<'div'> {
  className?: string;
}

function CardHeader({
  className,
  ...props
}: CardHeaderProps) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-1.5 px-6",
        className
      )}
      {...props} />
  );
}

export { Card, CardHeader }
export type { CardProps, CardHeaderProps }
```

## 🧪 Testing Strategy

### After Each Batch
1. **Build shared-ui**
   ```bash
   cd packages/shared-ui
   pnpm run build
   ```

2. **Verify .d.ts generation**
   ```bash
   ls -lh dist/
   # Should see: index.d.ts and index.d.mts
   ```

3. **Run typecheck in consumer**
   ```bash
   cd ../../handoff/20250928/40_App/frontend-dashboard
   pnpm run typecheck
   ```

4. **Verify error reduction**
   - Track TS2741 error count
   - Ensure no new errors introduced

### Final Verification
```bash
# 1. Clean build
cd packages/shared-ui
rm -rf dist
pnpm run build

# 2. Verify outputs
ls -lh dist/
# Expected:
# - index.js (CJS)
# - index.mjs (ESM)
# - index.d.ts (TypeScript declarations)
# - index.d.mts (TypeScript declarations for ESM)

# 3. Full typecheck
cd ../../handoff/20250928/40_App/frontend-dashboard
pnpm run typecheck
# Expected: ≤19 errors (baseline)
# Expected: 0 TS2741 "className is missing" errors
```

## 📊 Success Metrics

### Before Migration
- ✅ 19 errors (baseline, without .d.ts)
- ❌ 441 errors (with incorrect .d.ts from .jsx)
- ❌ 47 .jsx files
- ❌ No type safety for shared-ui consumers

### After Migration
- ✅ ≤19 errors (baseline maintained)
- ✅ 0 .jsx files
- ✅ 47 .tsx files with proper types
- ✅ Full type safety for shared-ui consumers
- ✅ IDE autocomplete works correctly
- ✅ className is optional across all components

## 🔗 Related Issues

- **Issue #854**: Fix shared-ui module resolution (Stage 1 ✅ Complete)
- **Issue #852**: Fix hook signatures (can proceed in parallel)
- **Issue #853**: Fix toast props (can proceed in parallel)
- **Issue #856**: Fix animation property types (can proceed in parallel)

## ⚠️ Important Notes

### Do NOT
- ❌ Add `className` to hundreds of call sites in consuming apps
- ❌ Remove type checking or disable strict mode
- ❌ Use `any` types as a workaround
- ❌ Skip testing after each batch

### DO
- ✅ Fix types at the source (shared-ui)
- ✅ Use proper React HTML attribute base types
- ✅ Make className optional where appropriate
- ✅ Test incrementally (batch by batch)
- ✅ Verify .d.ts generation after each batch

## 📅 Timeline

- **Day 1**: Batch 1 (10 high-frequency components)
- **Day 2**: Batch 2 (15 medium-frequency components)
- **Day 3**: Batch 3 (22 low-frequency components)

**Total Estimated Time**: 2-3 days

## 🎓 Learning Resources

- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [ComponentPropsWithoutRef vs ComponentPropsWithRef](https://react-typescript-cheatsheet.netlify.app/docs/basic/getting-started/forward_and_create_ref/)
- [tsup Documentation](https://tsup.egoist.dev/)

## ✅ Definition of Done

1. All 47 .jsx files converted to .tsx
2. Build succeeds with .d.ts generation
3. Typecheck shows ≤19 errors (baseline)
4. No TS2741 className errors
5. IDE autocomplete works for shared-ui
6. Documentation updated
7. PR created and CI passes
