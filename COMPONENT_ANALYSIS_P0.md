# Component Analysis Report - P0 Task

**Date**: November 2, 2025  
**Scope**: Frontend-dashboard local components vs @morningai/shared-ui  
**Purpose**: Identify duplicates vs app-specific components for migration planning

---

## Executive Summary

**Total Local Components**: 16 (excluding tests and stories)  
**Shared-UI Imports**: 101 instances across codebase  
**Migration Status**: ~40% adoption (estimated)

**Key Finding**: All 16 local components are **Apple-specific UI patterns** that extend beyond standard shared-ui components. These are intentionally app-specific and represent the "Apple-level UX" design system layer.

---

## Component Inventory

### 1. Apple-Specific Interactive Components (13 components)

These components implement iOS/macOS-style interactions and are **app-specific** (not duplicates):

| Component | Purpose | Migration Recommendation |
|-----------|---------|--------------------------|
| `apple-button.tsx` | iOS-style button with haptic feedback | ⚠️ **Evaluate** - May overlap with shared-ui Button |
| `apple-input.tsx` | iOS-style input with validation states | ⚠️ **Evaluate** - May overlap with shared-ui Input |
| `apple-modal.tsx` | iOS-style modal with spring animations | ⚠️ **Evaluate** - May overlap with shared-ui Dialog |
| `apple-sheet.tsx` | iOS bottom sheet with swipe gestures | ⚠️ **Evaluate** - May overlap with shared-ui Sheet |
| `apple-action-sheet.tsx` | iOS action sheet (bottom menu) | ✅ **Keep Local** - iOS-specific pattern |
| `apple-tab-bar.tsx` | iOS tab bar navigation | ✅ **Keep Local** - iOS-specific pattern |
| `apple-segmented-control.tsx` | iOS segmented control | ✅ **Keep Local** - iOS-specific pattern |
| `apple-picker.tsx` | iOS wheel picker | ✅ **Keep Local** - iOS-specific pattern |
| `apple-toast.tsx` | iOS-style toast notifications | ⚠️ **Evaluate** - May overlap with shared-ui Sonner |
| `apple-spotlight.tsx` | macOS Spotlight search | ✅ **Keep Local** - macOS-specific pattern |
| `apple-control-center.tsx` | iOS Control Center | ✅ **Keep Local** - iOS-specific pattern |
| `apple-live-activity.tsx` | iOS Live Activity widget | ✅ **Keep Local** - iOS-specific pattern |
| `apple-accessibility-settings.tsx` | iOS accessibility panel | ✅ **Keep Local** - iOS-specific pattern |

### 2. Utility Components (3 components)

| Component | Purpose | Migration Recommendation |
|-----------|---------|--------------------------|
| `lazy-image.tsx` | Lazy loading image component | ⚠️ **Consider Migration** - Generic utility |
| `loading-states.tsx` | Loading spinner variants | ⚠️ **Consider Migration** - Generic utility |
| `theme-toggle.tsx` | Dark mode toggle | ⚠️ **Consider Migration** - Generic utility |

---

## Detailed Analysis

### High-Priority Evaluation (5 components)

These components may have overlap with shared-ui and should be evaluated for consolidation:

#### 1. apple-button.tsx vs shared-ui/button.tsx

**Overlap Assessment**: HIGH

**apple-button.tsx features**:
- Uses `class-variance-authority` for variants
- Framer Motion animations
- Haptic feedback integration
- iOS-specific styling

**shared-ui/button.tsx features**:
- Uses `class-variance-authority` for variants
- Radix UI Slot for composition
- Standard button variants

**Recommendation**: 
- **Option A**: Migrate to shared-ui Button with iOS variant
- **Option B**: Keep apple-button as iOS-specific wrapper around shared-ui Button
- **Decision**: Evaluate usage patterns (need usage analysis)

#### 2. apple-input.tsx vs shared-ui/input.tsx

**Overlap Assessment**: HIGH

**apple-input.tsx features**:
- Validation states (error, success)
- Password visibility toggle
- Animated error messages
- iOS-specific styling

**shared-ui/input.tsx features**:
- Standard input component
- Radix UI integration

**Recommendation**:
- **Option A**: Extend shared-ui Input with validation variant
- **Option B**: Keep apple-input as enhanced wrapper
- **Decision**: Evaluate if validation logic should be in shared-ui

#### 3. apple-modal.tsx vs shared-ui/dialog.tsx

**Overlap Assessment**: MEDIUM

**apple-modal.tsx features**:
- iOS-style modal presentation
- Spring animations
- Backdrop blur
- Swipe-to-dismiss

**shared-ui/dialog.tsx features**:
- Radix UI Dialog primitive
- Standard modal patterns
- Accessibility built-in

**Recommendation**:
- **Keep apple-modal** - iOS-specific interaction patterns
- Use shared-ui Dialog for standard modals
- Document when to use each

#### 4. apple-sheet.tsx vs shared-ui/sheet.tsx

**Overlap Assessment**: HIGH

**apple-sheet.tsx features**:
- Bottom sheet with swipe gestures
- Spring physics
- Drag indicators
- iOS-specific styling

**shared-ui/sheet.tsx features**:
- Radix UI Dialog-based sheet
- Side/bottom positioning
- Standard sheet patterns

**Recommendation**:
- **Evaluate consolidation** - Both implement bottom sheets
- Consider: Can shared-ui Sheet support iOS gestures?
- If not, keep apple-sheet for iOS-specific behavior

#### 5. apple-toast.tsx vs shared-ui/sonner.tsx

**Overlap Assessment**: MEDIUM

**apple-toast.tsx features**:
- iOS-style toast notifications
- Custom positioning
- Spring animations
- Haptic feedback

**shared-ui/sonner.tsx features**:
- Sonner library integration
- Standard toast patterns
- Multiple variants

**Recommendation**:
- **Keep apple-toast** - iOS-specific toast style
- Use shared-ui Sonner for standard notifications
- Document when to use each

---

## Migration Candidates

### Immediate Migration (P1 - 30 days)

**3 Utility Components** - Generic, no iOS-specific behavior:

1. **lazy-image.tsx** → shared-ui
   - Generic lazy loading
   - No app-specific logic
   - Reusable across all apps
   - **Effort**: Low (1-2 hours)

2. **loading-states.tsx** → shared-ui
   - Generic spinner component
   - Standard loading patterns
   - Reusable across all apps
   - **Effort**: Low (1-2 hours)

3. **theme-toggle.tsx** → shared-ui
   - Generic dark mode toggle
   - Standard theme switching
   - Reusable across all apps
   - **Effort**: Low (2-3 hours)

**Total Effort**: 5-7 hours  
**Impact**: Reduces local components from 16 to 13

### Evaluation Required (P1 - 30 days)

**5 Components** - Potential overlap with shared-ui:

1. **apple-button.tsx** - Evaluate vs shared-ui Button
2. **apple-input.tsx** - Evaluate vs shared-ui Input
3. **apple-modal.tsx** - Evaluate vs shared-ui Dialog
4. **apple-sheet.tsx** - Evaluate vs shared-ui Sheet
5. **apple-toast.tsx** - Evaluate vs shared-ui Sonner

**Action Required**:
- Usage analysis (grep for imports)
- Feature comparison
- Decision: Consolidate or keep separate
- Document usage guidelines

### Keep Local (Confirmed)

**8 Components** - iOS/macOS-specific patterns:

1. apple-action-sheet.tsx
2. apple-tab-bar.tsx
3. apple-segmented-control.tsx
4. apple-picker.tsx
5. apple-spotlight.tsx
6. apple-control-center.tsx
7. apple-live-activity.tsx
8. apple-accessibility-settings.tsx

**Rationale**: These implement platform-specific interaction patterns that are intentionally app-specific and part of the "Apple-level UX" design system.

---

## Usage Analysis

### Shared-UI Adoption Metrics

**Current State**:
- Shared-UI imports: 101 instances
- Local component files: 16
- Test files: 13
- Story files: 20

**Adoption Estimate**: ~40-50%

**Most Used Shared-UI Components** (estimated):
- Button, Input, Card, Dialog, Sheet
- Form components (Label, Checkbox, Select)
- Navigation (Tabs, Breadcrumb)

### Local Component Usage

**Need to analyze**:
```bash
# Count imports of each local component
grep -r "from.*apple-button" --include="*.tsx" --include="*.ts"
grep -r "from.*apple-input" --include="*.tsx" --include="*.ts"
# ... etc for all components
```

**High-usage components** should be prioritized for evaluation.

---

## Recommendations

### Immediate Actions (P0 - 2 weeks)

1. ✅ **Complete this analysis** - DONE
2. **Run usage analysis** - Count imports of each local component
3. **Document component guidelines** - When to use apple-* vs shared-ui

### Short-Term Actions (P1 - 30 days)

1. **Migrate 3 utility components** to shared-ui:
   - lazy-image → @morningai/shared-ui/lazy-image
   - loading-states → @morningai/shared-ui/spinner
   - theme-toggle → @morningai/shared-ui/theme-toggle

2. **Evaluate 5 overlapping components**:
   - Compare features with shared-ui equivalents
   - Decide: consolidate or keep separate
   - Document decision rationale

3. **Create component usage guidelines**:
   - When to use apple-* components
   - When to use shared-ui components
   - Migration path for future components

### Long-Term Actions (P2 - 90 days)

1. **Standardize iOS patterns** in shared-ui:
   - Add iOS variant to Button, Input, etc.
   - Support haptic feedback in shared-ui
   - Support spring animations in shared-ui

2. **Reduce duplication**:
   - Target: <10 local components
   - All generic utilities in shared-ui
   - Only platform-specific patterns remain local

---

## Success Metrics

| Metric | Current | Target (30 days) | Target (90 days) |
|--------|---------|------------------|------------------|
| Local components | 16 | 13 | <10 |
| Shared-UI adoption | ~45% | 60% | 75% |
| Duplicate components | 5 (estimated) | 2 | 0 |
| Component guidelines | ❌ None | ✅ Documented | ✅ Enforced |

---

## Appendix: Component File Structure

**Local Components** (16):
```
frontend-dashboard/src/components/ui/
├── apple-accessibility-settings.tsx
├── apple-action-sheet.tsx
├── apple-button.tsx
├── apple-control-center.tsx
├── apple-input.tsx
├── apple-live-activity.tsx
├── apple-modal.tsx
├── apple-picker.tsx
├── apple-segmented-control.tsx
├── apple-sheet.tsx
├── apple-spotlight.tsx
├── apple-tab-bar.tsx
├── apple-toast.tsx
├── lazy-image.tsx
├── loading-states.tsx
└── theme-toggle.tsx
```

**Test Files** (13):
```
├── apple-action-sheet.test.tsx
├── apple-button.test.tsx
├── apple-control-center.test.tsx
├── apple-input.test.tsx
├── apple-live-activity.test.tsx
├── apple-modal.test.tsx
├── apple-picker.test.tsx
├── apple-segmented-control.test.tsx
├── apple-sheet.test.tsx
├── apple-spotlight.test.tsx
├── apple-tab-bar.test.tsx
├── apple-toast.test.tsx
└── typography-system.test.tsx
```

**Story Files** (20):
```
├── apple-action-sheet.stories.tsx
├── apple-button.stories.tsx
├── apple-control-center.stories.tsx
├── apple-input.stories.tsx
├── apple-live-activity.stories.tsx
├── apple-modal.stories.tsx
├── apple-picker.stories.tsx
├── apple-segmented-control.stories.tsx
├── apple-sheet.stories.tsx
├── apple-spotlight.stories.tsx
├── apple-tab-bar.stories.tsx
├── apple-toast.stories.tsx
├── color-system.stories.tsx
├── lazy-image.stories.tsx
├── material-system.stories.tsx
├── micro-interactions.stories.tsx
├── shadow-system.stories.tsx
├── spacing-system.stories.tsx
├── spring-animation.stories.tsx
├── theme-toggle.stories.tsx
└── typography-system.stories.tsx
```

**Accessibility Test Files** (5):
```
├── apple-action-sheet.a11y.test.tsx
├── apple-control-center.a11y.test.tsx
├── apple-live-activity.a11y.test.tsx
├── apple-picker.a11y.test.tsx
└── apple-spotlight.a11y.test.tsx
```

---

**Next Steps**: 
1. Run usage analysis script
2. Prioritize migration based on usage frequency
3. Create component usage guidelines document
4. Begin P1 migration of 3 utility components
