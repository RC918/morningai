# Shared Component Library Migration Plan

**Status**: Ready for Implementation  
**Related**: PR #775, CODE_DUPLICATION_ANALYSIS.md  
**Estimated Time**: 10 days  
**Code Reduction**: 33% (55 duplicate components)

## Overview

This document outlines the step-by-step plan to create `@morningai/shared-ui` package and migrate duplicate components from frontend-dashboard and owner-console.

## Phase 1: Foundation Setup ✅

### 1.1 Package Structure Created
```
packages/shared-ui/
├── package.json          ✅ Created
├── tsconfig.json         ✅ Created
├── src/
│   ├── utils.ts          ✅ Created
│   ├── components/
│   │   ├── ui/           ✅ Created
│   │   ├── feedback/     ✅ Created
│   │   ├── i18n/         ✅ Created
│   │   └── error/        ✅ Created
│   └── index.ts          ⏳ Pending
└── README.md             ⏳ Pending
```

### 1.2 Dependencies Configured
- ✅ Radix UI components
- ✅ class-variance-authority
- ✅ clsx, tailwind-merge
- ✅ TypeScript, tsup

## Phase 2: Component Extraction (Priority Order)

### Batch 1: Core UI Components (Day 1-2)
**Priority**: HIGH - Most frequently used

1. **button.jsx** - Primary interaction component
2. **input.jsx** - Form input
3. **label.jsx** - Form labels
4. **card.jsx** - Content containers
5. **dialog.jsx** - Modal dialogs

**Migration Steps**:
```bash
# For each component:
1. Copy from frontend-dashboard/src/components/ui/[component].jsx
2. Convert to TypeScript (.tsx)
3. Add proper type definitions
4. Export from packages/shared-ui/src/components/ui/index.ts
5. Test build: pnpm --filter @morningai/shared-ui build
```

### Batch 2: Form Components (Day 3)
**Priority**: HIGH - Form functionality

6. **select.jsx** - Dropdown selection
7. **textarea.jsx** - Multi-line input
8. **checkbox.jsx** - Boolean input
9. **switch.jsx** - Toggle switch
10. **slider.jsx** - Range input

### Batch 3: Layout Components (Day 4)
**Priority**: MEDIUM - Layout structure

11. **separator.jsx** - Visual divider
12. **aspect-ratio.jsx** - Image/video containers
13. **tabs.jsx** - Tab navigation
14. **accordion.jsx** - Collapsible sections
15. **table.jsx** - Data tables

### Batch 4: Overlay Components (Day 5)
**Priority**: MEDIUM - User interactions

16. **drawer.jsx** - Side panel
17. **sheet.jsx** - Bottom sheet
18. **dropdown-menu.jsx** - Context menus
19. **popover.jsx** - Floating content
20. **tooltip.jsx** - Hover hints

### Batch 5: Feedback Components (Day 6)
**Priority**: MEDIUM - User feedback

21. **alert.jsx** - Alert messages
22. **toast.jsx** - Notifications
23. **progress.jsx** - Progress indicators
24. **skeleton.jsx** - Loading placeholders
25. **badge.jsx** - Status indicators
26. **avatar.jsx** - User avatars

### Batch 6: Infrastructure Components (Day 7)
**Priority**: HIGH - Critical functionality

27. **ErrorBoundary.jsx** - Error handling
28. **PageLoader.jsx** - Page loading state
29. **OfflineIndicator.jsx** - Network status
30. **SkipToContent.jsx** - Accessibility
31. **LanguageSwitcher.jsx** - i18n

### Batch 7: i18n Configuration (Day 7)
32. **tolgee.js** - i18n setup

## Phase 3: Application Migration

### 3.1 Update Root package.json
```json
{
  "workspaces": [
    "packages/*",
    "handoff/20250928/40_App/frontend-dashboard",
    "handoff/20250928/40_App/owner-console"
  ]
}
```

### 3.2 Migrate frontend-dashboard (Day 8-9)

**Step 1**: Install shared-ui
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm add @morningai/shared-ui@workspace:*
```

**Step 2**: Update imports (automated script)
```bash
# Replace:
import { Button } from "@/components/ui/button"
# With:
import { Button } from "@morningai/shared-ui"
```

**Step 3**: Remove duplicate files
```bash
# After verifying all imports work:
rm -rf src/components/ui/button.jsx
rm -rf src/components/ui/input.jsx
# ... (all migrated components)
```

**Step 4**: Test
```bash
pnpm run build
pnpm run test
pnpm run lint
```

### 3.3 Migrate owner-console (Day 10)

Repeat steps 3.2 for owner-console.

## Automation Scripts

### Script 1: Extract Component
```bash
#!/bin/bash
# extract-component.sh
COMPONENT=$1
SRC="handoff/20250928/40_App/frontend-dashboard/src/components/ui/${COMPONENT}.jsx"
DEST="packages/shared-ui/src/components/ui/${COMPONENT}.tsx"

if [ -f "$SRC" ]; then
  cp "$SRC" "$DEST"
  echo "Extracted: $COMPONENT"
else
  echo "Not found: $SRC"
fi
```

### Script 2: Update Imports
```bash
#!/bin/bash
# update-imports.sh
APP_DIR=$1

find "$APP_DIR/src" -type f \( -name "*.jsx" -o -name "*.tsx" -o -name "*.js" -o -name "*.ts" \) -exec sed -i \
  's|from "@/components/ui/\(.*\)"|from "@morningai/shared-ui"|g' {} +

echo "Updated imports in $APP_DIR"
```

### Script 3: Verify Migration
```bash
#!/bin/bash
# verify-migration.sh
APP_DIR=$1

echo "Checking for remaining local UI imports..."
grep -r "from \"@/components/ui/" "$APP_DIR/src" || echo "✅ All imports migrated"

echo "Checking for orphaned component files..."
find "$APP_DIR/src/components/ui" -name "*.jsx" -o -name "*.tsx" | wc -l
```

## Testing Strategy

### Unit Tests
- Test each shared component in isolation
- Verify props interface
- Test accessibility (a11y)

### Integration Tests
- Test in frontend-dashboard context
- Test in owner-console context
- Verify styling consistency

### Visual Regression Tests
- Screenshot comparison before/after
- Verify no visual changes

## Rollback Plan

If issues arise:

1. **Keep original files** until migration verified
2. **Git branches**: Create migration branch per app
3. **Version pinning**: Pin shared-ui version during testing
4. **Gradual rollout**: Migrate one component batch at a time

## Success Metrics

### Code Metrics
- ✅ 33% code reduction (55 components eliminated)
- ✅ 150-200KB bundle size reduction
- ✅ Single source of truth for UI components

### Quality Metrics
- ✅ All tests passing
- ✅ No visual regressions
- ✅ Build time unchanged or improved
- ✅ Type safety maintained

### Developer Experience
- ✅ Faster component reuse
- ✅ Consistent UI across apps
- ✅ Easier maintenance

## Timeline Summary

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Extract Batch 1-2 (Core + Forms) | 10 components in shared-ui |
| 3-4 | Extract Batch 3-4 (Layout + Overlay) | 10 more components |
| 5-6 | Extract Batch 5-6 (Feedback + Infrastructure) | 12 more components |
| 7 | Extract i18n, build pipeline | Complete shared-ui package |
| 8-9 | Migrate frontend-dashboard | App using shared components |
| 10 | Migrate owner-console | Both apps migrated |

**Total**: 10 days, 32 components migrated, 33% code reduction

## Next Actions

### Immediate (Today)
1. ✅ Create package structure
2. ✅ Write migration plan
3. ⏳ Extract Batch 1 components (button, input, label, card, dialog)
4. ⏳ Set up build pipeline
5. ⏳ Test shared-ui package builds

### This Week
1. Complete component extraction (all 32 components)
2. Set up automated testing
3. Create component documentation
4. Begin frontend-dashboard migration

### Next Week
1. Complete frontend-dashboard migration
2. Migrate owner-console
3. Remove duplicate files
4. Update PR #775

## Risk Mitigation

### Technical Risks
- **Risk**: TypeScript conversion errors
  - **Mitigation**: Gradual conversion, thorough testing
  
- **Risk**: Import path issues
  - **Mitigation**: Automated script, comprehensive search

- **Risk**: Styling inconsistencies
  - **Mitigation**: Visual regression tests

### Process Risks
- **Risk**: Breaking changes during migration
  - **Mitigation**: Keep original files, gradual rollout
  
- **Risk**: CI/CD pipeline failures
  - **Mitigation**: Test each batch before proceeding

## Documentation

### Component Documentation Template
```typescript
/**
 * Button Component
 * 
 * A reusable button component with multiple variants.
 * 
 * @example
 * ```tsx
 * import { Button } from "@morningai/shared-ui"
 * 
 * <Button variant="primary" size="lg">
 *   Click me
 * </Button>
 * ```
 * 
 * @see https://ui.shadcn.com/docs/components/button
 */
```

### Migration Guide
Create `packages/shared-ui/MIGRATION.md` with:
- Import path changes
- Breaking changes (if any)
- Component API reference
- Troubleshooting guide

## Conclusion

This migration plan provides a structured approach to eliminating 33% of duplicate code while maintaining quality and minimizing risk. The gradual, batch-based approach allows for testing and validation at each step.

**Status**: Ready to proceed with Phase 2 (Component Extraction)

---

**Related Documents:**
- CODE_DUPLICATION_ANALYSIS.md
- PR #775: P2: Unify Dependency Versions
- packages/shared-ui/README.md (to be created)
