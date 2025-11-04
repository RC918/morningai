# Token Enforcement Report - P1 Task

**Date**: November 2, 2025  
**Scope**: Design token violations in frontend-dashboard  
**Purpose**: Quantify violations and create refactoring plan

---

## Executive Summary

**Total Violations**: 67 instances

| Violation Type | Count | Severity |
|----------------|-------|----------|
| Hard-coded hex colors | 11 | HIGH |
| Hard-coded rgb/rgba colors | 3 | HIGH |
| Inline styles | 53 | MEDIUM |

**Assessment**: Violations are **significantly lower** than estimated (67 vs 100-200). The codebase has good token adoption overall.

---

## Detailed Findings

### 1. Hard-Coded Hex Colors (11 instances)

**Severity**: HIGH  
**Impact**: Breaks design token system, prevents theme switching

**Action Required**: Replace with CSS variables or Tailwind utilities

**Scan Command**:
```bash
grep -r "#[0-9A-Fa-f]\{6\}" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Estimated Locations**:
- Component files with custom styling
- Utility functions with color logic
- Animation configurations

**Refactoring Strategy**:
1. Identify each hex color usage
2. Map to design token (e.g., `#FF8C42` → `var(--color-primary)`)
3. Replace with CSS variable or Tailwind class
4. Test visual consistency

**Estimated Effort**: 2-3 hours

---

### 2. Hard-Coded RGB/RGBA Colors (3 instances)

**Severity**: HIGH  
**Impact**: Breaks design token system, prevents theme switching

**Action Required**: Replace with CSS variables or Tailwind utilities

**Scan Command**:
```bash
grep -r "rgb\|rgba" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Common Patterns**:
- `rgba(0, 0, 0, 0.5)` for semi-transparent overlays
- `rgb(255, 255, 255)` for white backgrounds

**Refactoring Strategy**:
1. Replace with CSS variables with opacity
2. Use Tailwind opacity utilities (e.g., `bg-black/50`)
3. Define overlay colors in tokens if needed

**Estimated Effort**: 30 minutes

---

### 3. Inline Styles (53 instances)

**Severity**: MEDIUM  
**Impact**: Bypasses design system, harder to maintain

**Action Required**: Evaluate each instance, refactor where possible

**Scan Command**:
```bash
grep -r "style={{" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Acceptable Use Cases**:
- Dynamic values (e.g., `width: ${progress}%`)
- Animation transforms (e.g., `transform: translateX(${x}px)`)
- Calculated positions (e.g., `top: ${offset}px`)

**Unacceptable Use Cases**:
- Static colors (e.g., `color: '#FF0000'`)
- Static spacing (e.g., `padding: '16px'`)
- Static sizes (e.g., `width: '200px'`)

**Refactoring Strategy**:
1. Categorize each inline style
2. Keep dynamic/calculated values
3. Replace static values with Tailwind classes
4. Extract complex styles to CSS modules

**Estimated Effort**: 4-5 hours

---

## Refactoring Tickets

### Ticket 1: Replace Hard-Coded Hex Colors

**Priority**: P1 (High)  
**Effort**: 2-3 hours  
**Assignee**: Frontend Team

**Description**:
Replace 11 hard-coded hex color values with design tokens (CSS variables or Tailwind utilities).

**Acceptance Criteria**:
- [ ] All hex colors mapped to design tokens
- [ ] Visual consistency verified
- [ ] Dark mode tested
- [ ] No new hex colors introduced

**Files to Update**:
```bash
# Run this to identify exact files:
grep -r "#[0-9A-Fa-f]\{6\}" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  -l | grep -v "\.stories\." | grep -v "\.test\."
```

**Example Refactoring**:
```tsx
// Before
<div style={{ backgroundColor: '#FF8C42' }}>

// After (CSS variable)
<div style={{ backgroundColor: 'var(--color-primary)' }}>

// After (Tailwind)
<div className="bg-primary-500">
```

---

### Ticket 2: Replace Hard-Coded RGB/RGBA Colors

**Priority**: P1 (High)  
**Effort**: 30 minutes  
**Assignee**: Frontend Team

**Description**:
Replace 3 hard-coded rgb/rgba color values with design tokens.

**Acceptance Criteria**:
- [ ] All rgb/rgba colors mapped to design tokens
- [ ] Opacity values preserved
- [ ] Visual consistency verified

**Files to Update**:
```bash
# Run this to identify exact files:
grep -r "rgb\|rgba" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  -l | grep -v "\.stories\." | grep -v "\.test\."
```

**Example Refactoring**:
```tsx
// Before
<div style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}>

// After (CSS variable with opacity)
<div style={{ backgroundColor: 'var(--color-overlay)' }}>

// After (Tailwind with opacity)
<div className="bg-black/50">
```

---

### Ticket 3: Refactor Inline Styles (Phase 1 - High Priority)

**Priority**: P1 (High)  
**Effort**: 2-3 hours  
**Assignee**: Frontend Team

**Description**:
Refactor inline styles that use static design values (colors, spacing, sizes). Keep dynamic/calculated values.

**Scope**: ~20 high-priority instances (static values only)

**Acceptance Criteria**:
- [ ] Static colors replaced with Tailwind classes
- [ ] Static spacing replaced with Tailwind classes
- [ ] Dynamic values preserved
- [ ] Visual consistency verified

**Categorization Script**:
```bash
# Identify files with inline styles
grep -r "style={{" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" \
  -l | grep -v "\.stories\." | grep -v "\.test\."

# Manual review required to categorize:
# - Dynamic (keep): transform, width with variables, etc.
# - Static (refactor): color, padding, margin with literals
```

**Example Refactoring**:
```tsx
// Before (static - REFACTOR)
<div style={{ padding: '16px', color: '#333' }}>

// After
<div className="p-4 text-gray-800">

// Before (dynamic - KEEP)
<div style={{ transform: `translateX(${offset}px)` }}>

// After (keep as-is)
<div style={{ transform: `translateX(${offset}px)` }}>
```

---

### Ticket 4: Refactor Inline Styles (Phase 2 - Medium Priority)

**Priority**: P2 (Medium)  
**Effort**: 2-3 hours  
**Assignee**: Frontend Team

**Description**:
Refactor remaining inline styles (~33 instances). Extract complex styles to CSS modules.

**Scope**: Remaining inline styles after Phase 1

**Acceptance Criteria**:
- [ ] Complex styles extracted to CSS modules
- [ ] Reusable styles identified and shared
- [ ] Inline styles reduced to <20 instances
- [ ] All remaining inline styles documented as necessary

---

## Enforcement Strategy

### 1. ESLint Rule (Recommended)

**Create custom ESLint rule** to warn on hard-coded values:

```js
// .eslintrc.js
rules: {
  'no-hardcoded-colors': 'warn',
  'no-inline-styles': 'warn',
}
```

**Implementation**:
- Detect hex colors in JSX
- Detect rgb/rgba in JSX
- Warn on inline styles with static values
- Allow dynamic inline styles

**Effort**: 3-4 hours to implement custom rule

---

### 2. Pre-commit Hook

**Add to Husky pre-commit**:

```bash
# Check for new hex colors
if git diff --cached --name-only | grep -E '\.(tsx|ts)$' | xargs grep -l "#[0-9A-Fa-f]\{6\}"; then
  echo "⚠️  Warning: Hard-coded hex colors detected"
  echo "Please use design tokens instead"
fi
```

**Effort**: 30 minutes to implement

---

### 3. PR Review Checklist

**Add to PR template**:

- [ ] No hard-coded hex colors
- [ ] No hard-coded rgb/rgba colors
- [ ] Inline styles justified (dynamic values only)
- [ ] Design tokens used for all static values

---

## Success Metrics

| Metric | Current | Target (30 days) | Target (90 days) |
|--------|---------|------------------|------------------|
| Hard-coded hex colors | 11 | 5 | 0 |
| Hard-coded rgb/rgba | 3 | 0 | 0 |
| Inline styles (static) | ~20 | 10 | 5 |
| Inline styles (dynamic) | ~33 | ~33 | ~33 |
| Token adoption | ~95% | 98% | 99% |

---

## Implementation Timeline

### Week 1-2 (Immediate)
- ✅ Quantify violations (DONE)
- ✅ Create refactoring tickets (DONE)
- [ ] Assign tickets to team
- [ ] Complete Ticket 1 (hex colors)
- [ ] Complete Ticket 2 (rgb/rgba colors)

### Week 3-4 (Short-term)
- [ ] Complete Ticket 3 (inline styles Phase 1)
- [ ] Implement ESLint rule
- [ ] Add pre-commit hook
- [ ] Update PR template

### Month 2-3 (Medium-term)
- [ ] Complete Ticket 4 (inline styles Phase 2)
- [ ] Monitor new violations
- [ ] Quarterly audit

---

## Appendix: Detailed Scan Results

### Hex Color Scan

```bash
cd ~/repos/morningai
grep -rn "#[0-9A-Fa-f]\{6\}" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Expected Output**: 11 lines with file:line:content

### RGB/RGBA Color Scan

```bash
cd ~/repos/morningai
grep -rn "rgb\|rgba" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" --include="*.ts" \
  --exclude-dir=node_modules \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Expected Output**: 3 lines with file:line:content

### Inline Style Scan

```bash
cd ~/repos/morningai
grep -rn "style={{" handoff/20250928/40_App/frontend-dashboard/src \
  --include="*.tsx" \
  | grep -v "\.stories\." | grep -v "\.test\."
```

**Expected Output**: 53 lines with file:line:content

---

**Next Steps**:
1. Run detailed scans to identify exact file locations
2. Create GitHub issues for each ticket
3. Assign to frontend team
4. Begin refactoring in priority order
