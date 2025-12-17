# Component Migration Phase 1 Plan - P1 Task

**Date**: November 2, 2025  
**Scope**: Migrate top 10 high-usage components from local to shared-ui  
**Target**: Reduce local component count and increase shared-ui adoption

---

## Executive Summary

**Current State**:
- Local components: 16 (frontend-dashboard)
- Shared-UI adoption: ~45%
- Identified migration candidates: 3 utility components

**Phase 1 Target**:
- Migrate 3 utility components (immediate)
- Evaluate 5 overlapping components (decision required)
- Document migration process

**Estimated Effort**: 10-15 hours

---

## Migration Strategy

### Immediate Migration (3 Components)

Based on COMPONENT_ANALYSIS_P0.md, these 3 utility components are **confirmed for migration**:

1. **lazy-image.tsx** → @morningai/shared-ui
2. **loading-states.tsx** → @morningai/shared-ui  
3. **theme-toggle.tsx** → @morningai/shared-ui

**Rationale**: Generic utilities with no app-specific logic, reusable across all applications.

---

## Phase 1: Immediate Migration

### Component 1: lazy-image.tsx

**Current Location**: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/lazy-image.tsx`

**Target Location**: `packages/shared-ui/src/components/ui/lazy-image.tsx`

**Features**:
- Lazy loading with Intersection Observer
- Placeholder support
- Error handling
- Responsive images

**Migration Steps**:

1. **Copy component to shared-ui**:
   ```bash
   cp handoff/20250928/40_App/frontend-dashboard/src/components/ui/lazy-image.tsx \
      packages/shared-ui/src/components/ui/lazy-image.tsx
   ```

2. **Update imports in shared-ui**:
   - Verify `@/lib/utils` import works
   - Update any app-specific imports

3. **Export from shared-ui index**:
   ```ts
   // packages/shared-ui/src/index.ts
   export { LazyImage } from './components/ui/lazy-image';
   ```

4. **Build shared-ui**:
   ```bash
   cd packages/shared-ui
   pnpm build
   ```

5. **Update imports in frontend-dashboard**:
   ```bash
   # Find all imports
   grep -r "from.*lazy-image" handoff/20250928/40_App/frontend-dashboard/src
   
   # Replace with shared-ui import
   # Before: import { LazyImage } from '@/components/ui/lazy-image'
   # After: import { LazyImage } from '@morningai/shared-ui'
   ```

6. **Remove local component**:
   ```bash
   git rm handoff/20250928/40_App/frontend-dashboard/src/components/ui/lazy-image.tsx
   git rm handoff/20250928/40_App/frontend-dashboard/src/components/ui/lazy-image.stories.tsx
   ```

7. **Test**:
   - Build frontend-dashboard
   - Run tests
   - Visual verification

**Estimated Effort**: 1-2 hours

---

### Component 2: loading-states.tsx

**Current Location**: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/loading-states.tsx`

**Target Location**: `packages/shared-ui/src/components/ui/spinner.tsx` (renamed for clarity)

**Features**:
- Multiple spinner sizes (sm, md, lg)
- Customizable colors
- Accessible loading states

**Migration Steps**:

1. **Copy and rename component**:
   ```bash
   cp handoff/20250928/40_App/frontend-dashboard/src/components/ui/loading-states.tsx \
      packages/shared-ui/src/components/ui/spinner.tsx
   ```

2. **Refactor component name**:
   ```tsx
   // Before: export const Spinner, LoadingDots, etc.
   // After: Consolidate into single Spinner component with variants
   ```

3. **Update shared-ui exports**:
   ```ts
   // packages/shared-ui/src/index.ts
   export { Spinner } from './components/ui/spinner';
   ```

4. **Build shared-ui**:
   ```bash
   cd packages/shared-ui
   pnpm build
   ```

5. **Update imports in frontend-dashboard**:
   ```bash
   # Find all imports
   grep -r "from.*loading-states" handoff/20250928/40_App/frontend-dashboard/src
   
   # Replace with shared-ui import
   # Before: import { Spinner } from '@/components/ui/loading-states'
   # After: import { Spinner } from '@morningai/shared-ui'
   ```

6. **Remove local component**:
   ```bash
   git rm handoff/20250928/40_App/frontend-dashboard/src/components/ui/loading-states.tsx
   ```

7. **Test**:
   - Build frontend-dashboard
   - Run tests
   - Visual verification

**Estimated Effort**: 2-3 hours (includes refactoring)

---

### Component 3: theme-toggle.tsx

**Current Location**: `handoff/20250928/40_App/frontend-dashboard/src/components/ui/theme-toggle.tsx`

**Target Location**: `packages/shared-ui/src/components/ui/theme-toggle.tsx`

**Features**:
- Dark/light mode toggle
- System preference detection
- Persistent theme storage
- Accessible toggle button

**Migration Steps**:

1. **Copy component to shared-ui**:
   ```bash
   cp handoff/20250928/40_App/frontend-dashboard/src/components/ui/theme-toggle.tsx \
      packages/shared-ui/src/components/ui/theme-toggle.tsx
   ```

2. **Review dependencies**:
   - Check for app-specific theme context
   - Ensure theme provider is compatible
   - Update any localStorage keys to be configurable

3. **Export from shared-ui**:
   ```ts
   // packages/shared-ui/src/index.ts
   export { ThemeToggle } from './components/ui/theme-toggle';
   ```

4. **Build shared-ui**:
   ```bash
   cd packages/shared-ui
   pnpm build
   ```

5. **Update imports in frontend-dashboard**:
   ```bash
   # Find all imports
   grep -r "from.*theme-toggle" handoff/20250928/40_App/frontend-dashboard/src
   
   # Replace with shared-ui import
   # Before: import { ThemeToggle } from '@/components/ui/theme-toggle'
   # After: import { ThemeToggle } from '@morningai/shared-ui'
   ```

6. **Remove local component**:
   ```bash
   git rm handoff/20250928/40_App/frontend-dashboard/src/components/ui/theme-toggle.tsx
   git rm handoff/20250928/40_App/frontend-dashboard/src/components/ui/theme-toggle.stories.tsx
   ```

7. **Test**:
   - Build frontend-dashboard
   - Test theme switching
   - Test persistence
   - Test system preference

**Estimated Effort**: 2-3 hours

---

## Phase 1.5: Evaluation Required (5 Components)

These components require **usage analysis and decision** before migration:

### 1. apple-button.tsx vs shared-ui/button.tsx

**Decision Required**: Consolidate or keep separate?

**Analysis Needed**:
```bash
# Count usage
grep -r "from.*apple-button" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
grep -r "from.*@morningai/shared-ui.*Button" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l

# Compare features
diff handoff/20250928/40_App/frontend-dashboard/src/components/ui/apple-button.tsx \
     packages/shared-ui/src/components/ui/button.tsx
```

**Options**:
- **A**: Add iOS variant to shared-ui Button, deprecate apple-button
- **B**: Keep apple-button as iOS-specific wrapper
- **C**: Merge features into shared-ui Button

**Recommendation**: Evaluate usage frequency before deciding

---

### 2. apple-input.tsx vs shared-ui/input.tsx

**Decision Required**: Extend shared-ui or keep separate?

**Analysis Needed**:
```bash
# Count usage
grep -r "from.*apple-input" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l

# Feature comparison
# apple-input: validation states, password toggle, animations
# shared-ui input: basic input component
```

**Options**:
- **A**: Add validation variant to shared-ui Input
- **B**: Keep apple-input as enhanced wrapper
- **C**: Create separate InputWithValidation component in shared-ui

**Recommendation**: Option A - Extend shared-ui Input with validation

---

### 3. apple-modal.tsx vs shared-ui/dialog.tsx

**Decision Required**: Consolidate or keep separate?

**Analysis Needed**:
```bash
# Count usage
grep -r "from.*apple-modal" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
grep -r "from.*@morningai/shared-ui.*Dialog" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
```

**Options**:
- **A**: Add iOS variant to shared-ui Dialog
- **B**: Keep apple-modal for iOS-specific interactions
- **C**: Use shared-ui Dialog for standard modals, apple-modal for iOS-specific

**Recommendation**: Option C - Document when to use each

---

### 4. apple-sheet.tsx vs shared-ui/sheet.tsx

**Decision Required**: Consolidate or keep separate?

**Analysis Needed**:
```bash
# Count usage
grep -r "from.*apple-sheet" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
grep -r "from.*@morningai/shared-ui.*Sheet" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l

# Feature comparison
# apple-sheet: swipe gestures, spring physics, drag indicators
# shared-ui sheet: standard sheet with positioning
```

**Options**:
- **A**: Add gesture support to shared-ui Sheet
- **B**: Keep apple-sheet for iOS-specific gestures
- **C**: Merge gesture features into shared-ui Sheet

**Recommendation**: Evaluate if shared-ui Sheet can support gestures

---

### 5. apple-toast.tsx vs shared-ui/sonner.tsx

**Decision Required**: Consolidate or keep separate?

**Analysis Needed**:
```bash
# Count usage
grep -r "from.*apple-toast" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
grep -r "from.*@morningai/shared-ui.*[Tt]oast" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
```

**Options**:
- **A**: Use shared-ui Sonner for all toasts
- **B**: Keep apple-toast for iOS-specific styling
- **C**: Add iOS variant to Sonner

**Recommendation**: Option B - Keep apple-toast for iOS-specific UX

---

## Migration Checklist Template

For each component migration:

### Pre-Migration
- [ ] Run usage analysis (count imports)
- [ ] Review component dependencies
- [ ] Check for app-specific logic
- [ ] Identify breaking changes
- [ ] Create migration branch

### Migration
- [ ] Copy component to shared-ui
- [ ] Update imports (remove app-specific)
- [ ] Add to shared-ui exports
- [ ] Build shared-ui package
- [ ] Update TypeScript types

### Integration
- [ ] Update imports in frontend-dashboard
- [ ] Update imports in owner-console (if used)
- [ ] Remove local component files
- [ ] Remove local test files
- [ ] Remove local story files

### Testing
- [ ] Build all packages
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Visual regression tests
- [ ] Accessibility tests

### Documentation
- [ ] Update component documentation
- [ ] Update migration guide
- [ ] Add usage examples
- [ ] Update Storybook

---

## Success Metrics

| Metric | Current | After Phase 1 | Target (90 days) |
|--------|---------|---------------|------------------|
| Local components | 16 | 13 | <10 |
| Shared-UI adoption | ~45% | ~55% | 75% |
| Migrated components | 0 | 3 | 8-10 |
| Component duplication | 5 | 2 | 0 |

---

## Timeline

### Week 1-2 (Immediate)
- [ ] Migrate lazy-image.tsx
- [ ] Migrate loading-states.tsx → spinner.tsx
- [ ] Migrate theme-toggle.tsx
- [ ] Update all imports
- [ ] Remove local files
- [ ] Test and verify

### Week 3-4 (Evaluation)
- [ ] Run usage analysis for 5 overlapping components
- [ ] Make consolidation decisions
- [ ] Document usage guidelines
- [ ] Create Phase 2 migration plan

---

## Risk Mitigation

### Breaking Changes

**Risk**: Migration breaks existing functionality

**Mitigation**:
- Comprehensive testing before removal
- Gradual rollout (one component at a time)
- Keep local files until verified
- Rollback plan ready

### Import Path Changes

**Risk**: Missed import updates cause build failures

**Mitigation**:
- Use grep to find all imports
- Update all at once
- Run TypeScript compiler to catch errors
- Test build before committing

### Feature Parity

**Risk**: Shared-ui version missing features

**Mitigation**:
- Feature comparison before migration
- Add missing features to shared-ui first
- Document feature differences
- Provide migration guide

---

## Rollback Plan

If migration causes issues:

1. **Revert shared-ui changes**:
   ```bash
   git revert <commit-hash>
   cd packages/shared-ui
   pnpm build
   ```

2. **Restore local component**:
   ```bash
   git checkout HEAD~1 -- handoff/20250928/40_App/frontend-dashboard/src/components/ui/<component>.tsx
   ```

3. **Revert import changes**:
   ```bash
   git checkout HEAD~1 -- handoff/20250928/40_App/frontend-dashboard/src
   ```

4. **Rebuild and test**:
   ```bash
   pnpm install
   pnpm build
   pnpm test
   ```

---

## Next Steps

### This PR (Documentation)
- ✅ Document migration plan (DONE)
- [ ] Create GitHub issues for each migration
- [ ] Assign to frontend team

### Week 1 (Execution)
- [ ] Create migration branch
- [ ] Migrate lazy-image
- [ ] Migrate loading-states
- [ ] Migrate theme-toggle
- [ ] Create PR with migrations

### Week 2 (Verification)
- [ ] Review and test migrations
- [ ] Merge migration PR
- [ ] Monitor for issues
- [ ] Begin evaluation phase

---

## Appendix: Usage Analysis Scripts

### Count Component Usage

```bash
#!/bin/bash
# count-component-usage.sh

COMPONENT=$1
APP_DIR="handoff/20250928/40_App/frontend-dashboard/src"

echo "Analyzing usage of: $COMPONENT"
echo ""

# Count imports
IMPORT_COUNT=$(grep -r "from.*$COMPONENT" $APP_DIR --include="*.tsx" --include="*.ts" | wc -l)
echo "Import count: $IMPORT_COUNT"

# List files using component
echo ""
echo "Files using $COMPONENT:"
grep -r "from.*$COMPONENT" $APP_DIR --include="*.tsx" --include="*.ts" -l

# Count JSX usage
echo ""
echo "JSX usage count:"
grep -r "<$COMPONENT" $APP_DIR --include="*.tsx" | wc -l
```

### Compare Component Features

```bash
#!/bin/bash
# compare-components.sh

LOCAL_COMPONENT=$1
SHARED_COMPONENT=$2

echo "Comparing: $LOCAL_COMPONENT vs $SHARED_COMPONENT"
echo ""

# Show file sizes
echo "File sizes:"
wc -l "handoff/20250928/40_App/frontend-dashboard/src/components/ui/$LOCAL_COMPONENT.tsx"
wc -l "packages/shared-ui/src/components/ui/$SHARED_COMPONENT.tsx"

echo ""
echo "Exported components:"
echo "Local:"
grep "export" "handoff/20250928/40_App/frontend-dashboard/src/components/ui/$LOCAL_COMPONENT.tsx" | head -10

echo ""
echo "Shared:"
grep "export" "packages/shared-ui/src/components/ui/$SHARED_COMPONENT.tsx" | head -10
```

---

**Summary**: Phase 1 focuses on migrating 3 confirmed utility components (lazy-image, loading-states, theme-toggle) and evaluating 5 overlapping components for future migration. Total effort: 10-15 hours over 2 weeks.
