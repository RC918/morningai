# Design System Invariants
## MorningAI - Non-Negotiable Rules & Allowed Variants

**Version**: 1.0.0  
**Date**: 2025-11-02  
**Owner**: CTO (Chief Technology Officer)  
**Status**: Active  
**Review Cycle**: Quarterly

---

## Purpose

This document defines the **invariants** (non-negotiable rules) and **allowed variants** for the MorningAI design system. These rules ensure consistency, maintainability, and quality across all frontend applications.

**Invariants** are rules that MUST be followed without exception. Violations will block PR merges.

**Allowed Variants** are approved deviations for specific use cases, documented here to prevent confusion.

---

## 1. Token System Invariants

### 1.1 Token-Only Colors (CRITICAL)

**Rule**: All color values MUST come from design tokens. No hardcoded hex, RGB, or HSL values in application code.

**Rationale**: Ensures consistent theming, enables dark mode, and simplifies brand updates.

**Enforcement**:
- ✅ Allowed: `bg-primary-500`, `text-semantic-success-600`, `var(--color-primary-500)`
- ❌ Forbidden: `#007AFF`, `rgb(0, 122, 255)`, `hsl(211, 100%, 50%)`

**Exceptions**:
- `tokens.json` files (source of truth)
- `tailwind.config.js` (token mapping only)
- Test files (`*.test.tsx`, `*.stories.tsx`) for mocking
- Third-party library overrides (must be documented in code comments)

**Verification**: `./scripts/audit-design-system.sh` checks for hardcoded colors

---

### 1.2 Token-Only Spacing (HIGH)

**Rule**: All spacing values MUST use design tokens or Tailwind spacing scale.

**Rationale**: Maintains consistent rhythm and visual hierarchy.

**Enforcement**:
- ✅ Allowed: `p-4`, `gap-md`, `var(--spacing-lg)`, `space-y-2`
- ❌ Forbidden: `padding: 16px`, `margin: 1.5rem`, `gap: 24px`

**Exceptions**:
- 1px borders (e.g., `border-[1px]`) - too granular for tokens
- SVG viewBox dimensions
- Calculated values for animations (must be documented)

---

### 1.3 Token-Only Typography (HIGH)

**Rule**: All font sizes, weights, and line heights MUST use design tokens.

**Rationale**: Ensures readable, accessible, and consistent typography.

**Enforcement**:
- ✅ Allowed: `text-base`, `font-semibold`, `leading-normal`, `var(--font-size-body)`
- ❌ Forbidden: `font-size: 16px`, `font-weight: 600`, `line-height: 1.5`

**Exceptions**:
- Icon sizes (may use pixel values for precision)
- Third-party rich text editors (must be scoped)

---

### 1.4 Scoped Token Application (CRITICAL)

**Rule**: Design tokens MUST be applied within a `.theme-morning-ai` container, not globally to `:root`.

**Rationale**: Prevents token pollution in embedded contexts (iframes, browser extensions, etc.).

**Enforcement**:
- ✅ Required: Root element has `className="theme-morning-ai"`
- ✅ Required: `applyDesignTokens('.theme-morning-ai')` called in App.tsx
- ❌ Forbidden: Applying tokens to `document.documentElement` without scoping

**Verification**: Audit script checks for `.theme-morning-ai` usage

---

## 2. Accessibility Invariants (WCAG 2.1 AA)

### 2.1 Color Contrast (CRITICAL)

**Rule**: All text and UI components MUST meet WCAG 2.1 AA contrast ratios.

**Requirements**:
- Normal text: 4.5:1 minimum
- Large text (18pt+ or 14pt+ bold): 3:1 minimum
- UI components (buttons, inputs, icons): 3:1 minimum

**Enforcement**:
- Use WebAIM Contrast Checker during design
- Test with Lighthouse accessibility audit
- Review with axe DevTools

**No Exceptions**: Contrast is a legal requirement for accessibility compliance.

---

### 2.2 Keyboard Navigation (CRITICAL)

**Rule**: All interactive elements MUST be keyboard accessible.

**Requirements**:
- All buttons, links, inputs focusable via Tab
- Logical tab order (matches visual order)
- Visible focus indicators (`:focus-visible` styling)
- No keyboard traps (user can always escape)
- Modal dialogs trap focus within modal
- Escape key closes modals and dropdowns

**Enforcement**:
- Manual keyboard testing required for all PRs
- Automated tests with `@testing-library/user-event`

**No Exceptions**: Keyboard accessibility is non-negotiable.

---

### 2.3 Skip Navigation (CRITICAL)

**Rule**: All applications MUST provide a skip navigation link as the first focusable element.

**Requirements**:
- Link text: "Skip to main content" (or translated equivalent)
- Link target: `#main-content` (main content area)
- Visually hidden by default, visible on focus
- Positioned at top-left when focused

**Implementation**:
```tsx
<a href="#main-content" className="skip-link">
  Skip to main content
</a>

<main id="main-content" role="main">
  {/* Main content */}
</main>
```

**Verification**: Audit script checks for skip link presence

---

### 2.4 ARIA Live Regions (HIGH)

**Rule**: Dynamic content updates MUST be announced to screen readers via ARIA live regions.

**Requirements**:
- Save status indicators: `role="status"` or `aria-live="polite"`
- Error messages: `role="alert"` or `aria-live="assertive"`
- Toast notifications: `role="status"` with `aria-live="polite"`
- Form validation: `aria-invalid` + `aria-describedby` linking to error message

**Enforcement**:
- Minimum 5 live region implementations per app
- Test with screen reader (NVDA, JAWS, or VoiceOver)

**Allowed Variants**:
- `aria-live="polite"` for non-critical updates
- `aria-live="assertive"` for critical alerts
- `aria-atomic="true"` for complete message replacement

---

### 2.5 Semantic HTML (HIGH)

**Rule**: Use semantic HTML elements over generic divs/spans where appropriate.

**Requirements**:
- `<button>` for clickable actions (not `<div onClick>`)
- `<a>` for navigation (not `<button>` with routing)
- `<nav>`, `<main>`, `<header>`, `<footer>` for page structure
- `<h1>`-`<h6>` for headings (proper hierarchy)
- `<form>` for form submissions
- `<label>` for form inputs

**Rationale**: Improves accessibility, SEO, and code maintainability.

---

### 2.6 Motion Accessibility (MEDIUM)

**Rule**: Respect user's motion preferences via `prefers-reduced-motion`.

**Requirements**:
- Check `prefers-reduced-motion: reduce` media query
- Disable or reduce animations when enabled
- Ensure functionality works without animations

**Implementation**:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 3. Component Invariants

### 3.1 Radix UI Primitives (HIGH)

**Rule**: Use Radix UI primitives for complex interactive components.

**Rationale**: Radix provides accessible, unstyled primitives that meet WCAG standards.

**Required Components**:
- Dialog/Modal: `@radix-ui/react-dialog`
- Dropdown: `@radix-ui/react-dropdown-menu`
- Tooltip: `@radix-ui/react-tooltip`
- Popover: `@radix-ui/react-popover`
- Select: `@radix-ui/react-select`
- Tabs: `@radix-ui/react-tabs`
- Accordion: `@radix-ui/react-accordion`

**Enforcement**: Do not build custom implementations of these patterns.

**Allowed Variants**: Styling customization via Tailwind classes.

---

### 3.2 Component Naming Convention (MEDIUM)

**Rule**: Components MUST follow PascalCase naming convention.

**Examples**:
- ✅ `Button.tsx`, `SaveStatusIndicator.tsx`, `DashboardWidget.tsx`
- ❌ `button.tsx`, `save-status-indicator.tsx`, `dashboard_widget.tsx`

**Rationale**: Consistent with React conventions and improves code readability.

---

### 3.3 Component File Structure (MEDIUM)

**Rule**: Components MUST follow this structure:

```
ComponentName/
├── ComponentName.tsx          # Main component
├── ComponentName.test.tsx     # Unit tests
├── ComponentName.stories.tsx  # Storybook stories
├── index.ts                   # Re-export
└── types.ts                   # TypeScript types (if complex)
```

**Exceptions**: Simple components may be single-file.

---

### 3.4 Shared UI Package (HIGH)

**Rule**: Reusable components MUST be published to `@morningai/shared-ui` package.

**Criteria for Shared Components**:
- Used in 2+ applications
- Stable API (no frequent breaking changes)
- Fully tested and documented
- Storybook story included

**Process**:
1. Develop in app-specific directory
2. Stabilize and test
3. Move to `packages/shared-ui/src`
4. Update exports in `packages/shared-ui/src/index.ts`
5. Publish new version

---

## 4. Dependency Management Invariants

### 4.1 pnpm Only (CRITICAL)

**Rule**: ONLY pnpm is allowed as the package manager. No npm or yarn.

**Rationale**: Monorepo consistency, disk space efficiency, and deterministic installs.

**Enforcement**:
- ✅ Required: `pnpm-lock.yaml`
- ❌ Forbidden: `package-lock.json`, `yarn.lock`
- CI workflow checks for forbidden lock files

**Verification**: `dependency-check.yml` workflow enforces this policy.

---

### 4.2 Package Manager Version (HIGH)

**Rule**: Use pnpm 9.0.0 or higher.

**Enforcement**:
- `package.json`: `"packageManager": "pnpm@9.15.1"`
- `engines`: `"pnpm": ">=9.0.0"`

---

### 4.3 Node Version (HIGH)

**Rule**: Use Node.js 20.0.0 or higher.

**Rationale**: Modern JavaScript features, security updates, and performance improvements.

**Enforcement**:
- `package.json`: `"engines": { "node": ">=20.0.0" }`
- `.nvmrc`: `20` (if using nvm)

---

## 5. Build & Deployment Invariants

### 5.1 Vercel Configuration (HIGH)

**Rule**: Vercel deployments MUST use pnpm for installation.

**Required Configuration** (`vercel.json`):
```json
{
  "installCommand": "pnpm install --prod=false",
  "buildCommand": "pnpm --filter @morningai/shared-ui build && pnpm --filter frontend-dashboard build"
}
```

**Forbidden**:
- ❌ `"installCommand": "npm install"`
- ❌ `"installCommand": "yarn install"`
- ❌ `"rootDirectory"` (breaks monorepo)

**Verification**: Audit script checks Vercel config.

---

### 5.2 TypeScript Strict Mode (MEDIUM)

**Rule**: All TypeScript code MUST compile without errors in strict mode.

**Configuration** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

**Enforcement**: `pnpm typecheck` must pass in CI.

---

### 5.3 Linting (MEDIUM)

**Rule**: All code MUST pass ESLint checks.

**Required Plugins**:
- `eslint-plugin-react`
- `eslint-plugin-react-hooks`
- `eslint-plugin-jsx-a11y` (accessibility linting)

**Enforcement**: `pnpm lint` must pass in CI.

---

## 6. Testing Invariants

### 6.1 Component Testing (HIGH)

**Rule**: All shared UI components MUST have unit tests.

**Requirements**:
- Test rendering
- Test user interactions
- Test accessibility (with `jest-axe` or `vitest-axe`)
- Test edge cases

**Coverage Target**: 80%+ for shared components.

---

### 6.2 Visual Regression Testing (MEDIUM)

**Rule**: Critical user flows MUST have visual regression tests.

**Implementation**: Playwright with `@vrt` tag.

**Coverage**:
- Login flow
- Dashboard customization
- Settings pages
- Checkout flow (when implemented)

---

## 7. Documentation Invariants

### 7.1 Storybook Stories (HIGH)

**Rule**: All shared UI components MUST have Storybook stories.

**Requirements**:
- Default story (basic usage)
- Variant stories (all supported variants)
- Interactive story (with controls)
- Accessibility story (with a11y addon)

**Enforcement**: Storybook build must succeed in CI.

---

### 7.2 Component Props Documentation (MEDIUM)

**Rule**: All component props MUST be documented with TypeScript types and JSDoc comments.

**Example**:
```tsx
interface ButtonProps {
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
  
  /** Button size */
  size?: 'sm' | 'md' | 'lg'
  
  /** Disabled state */
  disabled?: boolean
  
  /** Click handler */
  onClick?: () => void
}
```

---

## 8. Git & CI/CD Invariants

### 8.1 Branch Protection (CRITICAL)

**Rule**: `main` branch MUST be protected with required checks.

**Required Checks**:
- ✅ All CI workflows pass
- ✅ Design system audit passes
- ✅ At least 1 approval from code owner
- ✅ No merge conflicts

**Enforcement**: GitHub branch protection rules.

---

### 8.2 Commit Messages (LOW)

**Rule**: Commit messages SHOULD follow Conventional Commits format.

**Format**: `<type>(<scope>): <description>`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
- `feat(dashboard): add undo/redo functionality`
- `fix(button): correct focus indicator color contrast`
- `docs(design-system): update token usage guidelines`

---

### 8.3 No Force Push (CRITICAL)

**Rule**: Force pushing to shared branches is FORBIDDEN.

**Rationale**: Prevents loss of work and maintains git history integrity.

**Enforcement**: GitHub branch protection prevents force push to `main`.

---

## 9. Allowed Variants

These are approved deviations from standard patterns for specific use cases.

### 9.1 Brand Color Palettes

**Variant**: Different brand color palettes for white-label deployments.

**Approval**: Requires CTO sign-off.

**Implementation**: Separate `tokens.json` files per brand, loaded dynamically.

---

### 9.2 Dark Mode & High Contrast Themes

**Variant**: Additional theme variants beyond default light theme.

**Approval**: Automatic (encouraged).

**Implementation**: Additional token sets in `tokens.json`:
```json
{
  "color": {
    "primary": { /* light mode */ },
    "primary-dark": { /* dark mode */ },
    "primary-hc": { /* high contrast */ }
  }
}
```

---

### 9.3 Experimental Components

**Variant**: Experimental components behind feature flags.

**Approval**: Requires Tech Lead approval.

**Requirements**:
- Must be behind feature flag
- Must not affect production users
- Must have clear migration path
- Must be documented as experimental

**Implementation**:
```tsx
import { useFeatureFlag } from '@/lib/feature-flags'

function MyComponent() {
  const isExperimentalEnabled = useFeatureFlag('experimental-feature')
  
  if (isExperimentalEnabled) {
    return <ExperimentalComponent />
  }
  
  return <StableComponent />
}
```

---

### 9.4 Third-Party Component Overrides

**Variant**: Styling overrides for third-party components (e.g., rich text editors, charts).

**Approval**: Automatic (document in code).

**Requirements**:
- Must be scoped to component
- Must be documented with comment explaining why
- Must use tokens where possible

**Example**:
```tsx
// Override Recharts default colors to match our design system
<LineChart>
  <Line stroke="var(--color-primary-500)" />
</LineChart>
```

---

## 10. Enforcement & Compliance

### 10.1 Automated Enforcement

**CI Checks** (must pass for PR merge):
- ✅ `./scripts/audit-design-system.sh` (design system audit)
- ✅ `pnpm lint` (code quality)
- ✅ `pnpm typecheck` (type safety)
- ✅ `pnpm test` (unit tests)
- ✅ Dependency check (pnpm-only policy)

---

### 10.2 Manual Review

**Code Review Checklist**:
- [ ] No hardcoded colors, spacing, or typography
- [ ] Accessibility requirements met
- [ ] Keyboard navigation tested
- [ ] Screen reader tested (for complex components)
- [ ] Storybook story included (for shared components)
- [ ] Tests included and passing
- [ ] Documentation updated

---

### 10.3 Violation Handling

**Severity Levels**:

**CRITICAL** (blocks merge):
- Hardcoded colors in application code
- Missing skip navigation
- WCAG contrast violations
- Forbidden lock files (npm/yarn)
- Force push to main

**HIGH** (requires fix before merge):
- Missing ARIA live regions
- Keyboard navigation issues
- Missing Storybook stories for shared components
- TypeScript errors

**MEDIUM** (fix in follow-up PR):
- Incomplete documentation
- Missing tests for non-critical components
- Non-conventional commit messages

**LOW** (optional):
- Code style inconsistencies (auto-fixed by linter)
- Minor documentation improvements

---

## 11. Review & Updates

### 11.1 Review Cycle

**Frequency**: Quarterly (every 3 months)

**Participants**:
- CTO (owner)
- Tech Lead
- Frontend Lead
- UX Lead

**Agenda**:
1. Review current invariants
2. Discuss proposed changes
3. Review violation patterns
4. Update enforcement mechanisms
5. Communicate changes to team

---

### 11.2 Change Process

**Proposing Changes**:
1. Create RFC (Request for Comments) issue
2. Document rationale and impact
3. Gather feedback from team
4. Present to CTO for approval
5. Update this document
6. Communicate to team
7. Update audit scripts and CI

**Approval Authority**: CTO (final decision)

---

## 12. Exceptions & Waivers

### 12.1 Exception Request Process

In rare cases, exceptions to invariants may be granted.

**Process**:
1. Document specific invariant and reason for exception
2. Propose alternative approach
3. Assess risk and impact
4. Submit to CTO for approval
5. Document exception in code and this document

**Approval**: Requires CTO sign-off.

---

### 12.2 Temporary Waivers

For urgent hotfixes, temporary waivers may be granted.

**Requirements**:
- Must be truly urgent (production outage, security vulnerability)
- Must have follow-up issue to fix properly
- Must be documented in PR description
- Must be approved by Tech Lead or CTO

**Duration**: Maximum 1 week before proper fix required.

---

## Appendix A: Quick Reference

### Critical Invariants (Must Follow)
1. ✅ Token-only colors (no hardcoded hex)
2. ✅ Scoped token application (`.theme-morning-ai`)
3. ✅ WCAG 2.1 AA contrast ratios
4. ✅ Keyboard navigation for all interactive elements
5. ✅ Skip navigation link
6. ✅ pnpm-only package manager
7. ✅ No force push to main

### High Priority Invariants
1. ✅ Token-only spacing and typography
2. ✅ ARIA live regions for dynamic content
3. ✅ Radix UI primitives for complex components
4. ✅ Shared UI package for reusable components
5. ✅ Vercel uses pnpm
6. ✅ Component unit tests

### Recommended Practices
1. ✅ Storybook stories for all components
2. ✅ TypeScript strict mode
3. ✅ Semantic HTML
4. ✅ Motion accessibility
5. ✅ Conventional commit messages

---

## Appendix B: Resources

- **Design System Guidelines**: `DESIGN_SYSTEM_GUIDELINES.md`
- **Investigation Checklist**: `DEEP_INVESTIGATION_CHECKLIST.md`
- **Audit Script**: `./scripts/audit-design-system.sh`
- **Enhancement Roadmap**: `docs/UX/DESIGN_SYSTEM_ENHANCEMENT_ROADMAP.md`

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-02 | CTO | Initial invariants document based on comprehensive audit |

---

**Maintained by**: CTO (Chief Technology Officer)  
**Last Review**: 2025-11-02  
**Next Review**: 2026-02-02 (Quarterly)

---

**Note**: This document represents the technical standards and governance for the MorningAI design system. All team members are expected to understand and follow these invariants. Questions or concerns should be directed to the CTO or Tech Lead.
