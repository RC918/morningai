# AppleButton Migration Plan

## Overview
This document outlines the migration strategy from the standard `Button` component to the new `AppleButton` component with Apple-level design system integration.

## Migration Status

### ✅ Completed
- **TenantSettings.jsx**: Migrated retry button to AppleButton with destructive variant
- **SystemSettings.jsx**: Migrated all buttons (6 instances) to AppleButton
  - Avatar upload button (outline variant, sm size)
  - Save changes buttons (3 instances, default variant)
  - 2FA enable button (outline variant, sm size, disabled)
  - Cancel button (outline variant)
  - Update password button (default variant)

### 🔄 In Progress
- Unit tests (80% coverage target)
- Storybook documentation

### 📋 Pending Migration

#### High Priority Components
1. **Dashboard.jsx**
   - Primary action buttons
   - Secondary action buttons
   - Estimated: 5-8 buttons

2. **StrategyManagement.jsx**
   - Create/Edit strategy buttons
   - Delete/Archive buttons
   - Estimated: 4-6 buttons

3. **CostAnalysis.jsx**
   - Export buttons
   - Filter action buttons
   - Estimated: 3-5 buttons

#### Medium Priority Components
4. **Sidebar.jsx**
   - Navigation action buttons
   - Estimated: 2-3 buttons

5. **GlobalSearch.jsx**
   - Search action buttons
   - Estimated: 1-2 buttons

6. **Phase3WelcomeModal.jsx**
   - Modal action buttons
   - Estimated: 2-3 buttons

#### Low Priority Components
7. **EmptyStateLibrary.jsx**
   - Call-to-action buttons
   - Estimated: 1-2 buttons per state

8. **NPSQuestionnaire.jsx**
   - Submit/Skip buttons
   - Estimated: 2-3 buttons

## Migration Guidelines

### 1. Import Statement
```jsx
// Old
import { Button } from '@/components/ui/button'

// New
import { AppleButton } from '@/components/ui/apple-button'
```

### 2. Variant Mapping
| Old Button Variant | AppleButton Variant | Use Case |
|-------------------|---------------------|----------|
| `default` | `primary` | Primary actions |
| `secondary` | `secondary` | Secondary actions |
| `destructive` | `destructive` | Delete/Remove actions |
| `outline` | `outline` | Tertiary actions |
| `ghost` | `ghost` | Minimal emphasis |
| `link` | `link` | Text-only actions |
| N/A | `filled` | iOS-style filled buttons |
| N/A | `tinted` | iOS-style tinted buttons |

### 3. Size Mapping
| Old Button Size | AppleButton Size | Use Case |
|----------------|------------------|----------|
| `sm` | `sm` | Compact spaces |
| `default` | `default` | Standard buttons |
| `lg` | `lg` | Prominent actions |
| `icon` | `icon` | Icon-only buttons |
| N/A | `icon-sm` | Small icon buttons |
| N/A | `icon-lg` | Large icon buttons |

### 4. Haptic Feedback
AppleButton includes haptic feedback levels:
- `none`: No haptic feedback
- `light`: Subtle feedback (default for secondary actions)
- `medium`: Standard feedback (default)
- `heavy`: Strong feedback (for important actions)

Example:
```jsx
<AppleButton 
  variant="destructive" 
  haptic="heavy"
  onClick={handleDelete}
>
  Delete
</AppleButton>
```

### 5. Migration Checklist
For each component:
- [ ] Update import statement
- [ ] Replace `Button` with `AppleButton`
- [ ] Map variants appropriately
- [ ] Map sizes appropriately
- [ ] Add haptic feedback level (optional)
- [ ] Test functionality
- [ ] Test visual appearance
- [ ] Test accessibility (keyboard navigation)
- [ ] Update component tests if applicable

## Testing Strategy

### Visual Testing
1. Test all variants in Storybook
2. Verify spring animations work correctly
3. Check hover/active states
4. Verify disabled states

### Functional Testing
1. Click handlers work correctly
2. Haptic feedback triggers appropriately
3. Keyboard navigation (Enter/Space)
4. Focus management

### Accessibility Testing
1. Screen reader compatibility
2. Keyboard navigation
3. Focus indicators
4. ARIA attributes

## Rollback Plan
If issues arise during migration:
1. Keep old Button component available
2. Revert specific components if needed
3. Document any compatibility issues
4. Create bug reports for AppleButton issues

## Timeline

### Week 1 (Current)
- ✅ Complete high-priority pages (TenantSettings, SystemSettings)
- ✅ Create migration documentation
- 🔄 Complete unit tests (80% coverage)
- 🔄 Optimize Storybook loading

### Week 2
- Migrate Dashboard.jsx
- Migrate StrategyManagement.jsx
- Migrate CostAnalysis.jsx

### Week 3
- Migrate remaining medium-priority components
- Migrate low-priority components
- Complete visual regression testing

### Week 4
- Final testing and bug fixes
- Documentation updates
- Deprecate old Button usage (optional)

## Benefits of Migration

### User Experience
- Smooth spring animations (iOS-style)
- Haptic feedback for better interaction
- Consistent Apple-level design language
- Better visual hierarchy

### Developer Experience
- Consistent API across all buttons
- Built-in haptic feedback
- Better TypeScript support
- Comprehensive Storybook documentation

### Performance
- Optimized animations with spring physics
- Efficient re-renders
- Smaller bundle size (shared animation utilities)

## Notes
- Old Button component remains available during migration
- No breaking changes to existing functionality
- Migration can be done incrementally
- Each component can be tested independently

## Support
For questions or issues during migration:
1. Check Storybook documentation
2. Review APPLE_BUTTON_SYSTEM.md
3. Check unit tests for usage examples
4. Contact UX team for design guidance
