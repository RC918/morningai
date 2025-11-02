# Design System Invariants

**MorningAI - CTO Quality Standards**  
**Immutable Rules for System Integrity**

This document defines the invariants (unchanging rules) that MUST be maintained across the MorningAI design system and codebase to ensure consistency, quality, and maintainability. These rules are enforced through automated audits, CI/CD checks, and code review processes.

---

## Table of Contents

1. [Governance Invariants](#1-governance-invariants)
2. [Design Token Invariants](#2-design-token-invariants)
3. [Component Architecture Invariants](#3-component-architecture-invariants)
4. [Accessibility Invariants](#4-accessibility-invariants)
5. [Motion & Animation Invariants](#5-motion--animation-invariants)
6. [Internationalization Invariants](#6-internationalization-invariants)
7. [Performance Invariants](#7-performance-invariants)
8. [Documentation Invariants](#8-documentation-invariants)
9. [Testing Invariants](#9-testing-invariants)
10. [Security Invariants](#10-security-invariants)
11. [Enforcement Mechanisms](#11-enforcement-mechanisms)

---

## 1. Governance Invariants

### 1.1 Package Manager

**INVARIANT**: Only pnpm is allowed as the package manager in this monorepo.

**Rules**:
- ✅ **MUST**: Use pnpm >= 9.0.0 for all package operations
- ✅ **MUST**: Have single `pnpm-lock.yaml` at repository root
- ❌ **MUST NOT**: Commit `yarn.lock`, `package-lock.json`, or `npm-shrinkwrap.json`
- ❌ **MUST NOT**: Use `npm install` or `yarn install` commands
- ✅ **MUST**: Define `packageManager` field in root `package.json`

**Enforcement**:
- CI workflow: `.github/workflows/dependency-check.yml`
- Audit script: `./audit-design-system.sh`
- Pre-commit hook: Husky checks for forbidden lockfiles

**Rationale**: Ensures consistent dependency resolution, faster installs, and monorepo workspace support.

---

### 1.2 Node.js Version

**INVARIANT**: All development and production environments must use Node.js >= 20.0.0.

**Rules**:
- ✅ **MUST**: Use Node.js 20.x or higher
- ✅ **MUST**: Define `engines.node` in all `package.json` files
- ✅ **MUST**: Use `.nvmrc` or similar for version pinning

**Enforcement**:
- CI workflows check Node version
- Audit script validates Node version
- Docker images specify Node 20

**Rationale**: Ensures access to latest JavaScript features, performance improvements, and security patches.

---

### 1.3 Dependency Version Alignment

**INVARIANT**: Critical dependencies must have consistent versions across all workspace packages.

**Rules**:
- ✅ **MUST**: Use pnpm overrides in root `package.json` for:
  - `react` and `react-dom` (currently ^19.1.0)
  - `typescript` (currently 5.9.3)
  - `vite` (currently ^6.3.5)
  - `eslint` (currently ^9.25.0)
  - `tailwindcss` (currently ^4.1.7)
- ✅ **MUST**: Keep Radix UI packages aligned (all at compatible versions)
- ✅ **MUST**: Document version constraints in root `package.json`

**Enforcement**:
- Audit script checks version consistency
- Renovate bot for automated updates
- PR reviews verify version alignment

**Rationale**: Prevents version conflicts, ensures compatibility, simplifies debugging.

---

## 2. Design Token Invariants

### 2.1 Single Source of Truth

**INVARIANT**: All design tokens MUST be defined in `packages/shared-ui/src/tokens.json`.

**Rules**:
- ✅ **MUST**: Define all colors, typography, spacing, shadows, radii, animations in `tokens.json`
- ❌ **MUST NOT**: Hard-code design values in component files
- ✅ **MUST**: Use CSS variables or Tailwind utilities mapped to tokens
- ✅ **MUST**: Export tokens as TypeScript types via `tokens.d.ts`

**Enforcement**:
- Audit script scans for hard-coded hex/rgb values
- ESLint plugin (custom rule) warns on hard-coded values
- Code review checklist

**Rationale**: Ensures design consistency, enables theme switching, simplifies design updates.

---

### 2.2 Token Categories

**INVARIANT**: Design tokens must cover all required categories with complete definitions.

**Required Categories**:
1. **Colors**:
   - Primary (50-900 scale)
   - Accent (purple, orange scales)
   - Semantic (success, error, warning, info)
   - Neutral (50-900 scale)
   - Background (base, surface, overlay)

2. **Typography**:
   - Font families (primary, secondary, mono)
   - Font sizes (7 levels: caption to display)
   - Font weights (regular, medium, semibold, bold)
   - Line heights (tight, normal, relaxed)

3. **Spacing**:
   - 8-point grid system (xs to 4xl)

4. **Shadows**:
   - 5-level system (sm to 2xl)

5. **Border Radius**:
   - 6 levels (sm to full)

6. **Animation**:
   - Durations (instant, fast, normal, slow)
   - Easing functions (linear, easeIn, easeOut, easeInOut, spring)

7. **Breakpoints**:
   - Mobile, tablet, desktop

**Enforcement**:
- Audit script validates token completeness
- TypeScript types ensure all categories present
- Design review process

**Rationale**: Comprehensive token system enables consistent design implementation.

---

### 2.3 No Hard-coded Values

**INVARIANT**: Component files must not contain hard-coded design values.

**Rules**:
- ❌ **MUST NOT**: Use hex colors (e.g., `#FF6B35`) in TSX/CSS
- ❌ **MUST NOT**: Use rgb/rgba values (e.g., `rgb(255, 107, 53)`) in TSX/CSS
- ❌ **MUST NOT**: Use hard-coded spacing (e.g., `padding: 16px`) without token reference
- ❌ **MUST NOT**: Use hard-coded shadows without token reference
- ✅ **MUST**: Use CSS variables (e.g., `var(--color-primary)`)
- ✅ **MUST**: Use Tailwind utilities mapped to tokens (e.g., `bg-primary-500`)

**Exceptions**:
- Configuration files (`tailwind.config.ts`, `theme-apple.css`)
- `tokens.json` itself
- One-off animations with unique values (must be documented)

**Enforcement**:
- Audit script: `< 50` violations allowed (legacy code)
- ESLint warnings on violations
- PR review checklist

**Rationale**: Prevents design drift, enables theme switching, simplifies maintenance.

---

### 2.4 Tailwind v4 Token Mapping

**INVARIANT**: Tailwind CSS v4 utilities must be mapped to design tokens via CSS variables.

**Rules**:
- ✅ **MUST**: Define `@theme` block in `index.css` with CSS variables
- ✅ **MUST**: Map token values to CSS variables (e.g., `--color-primary: #FF8C42`)
- ✅ **MUST**: Use Tailwind utilities that reference these variables
- ❌ **MUST NOT**: Use default Tailwind color palette for brand/semantic colors

**Enforcement**:
- Audit script checks for `@theme` block
- Code review verifies token mapping
- Design system documentation

**Rationale**: Ensures Tailwind utilities respect design tokens, maintains consistency.

---

## 3. Component Architecture Invariants

### 3.1 Shared Component Library

**INVARIANT**: Components used in 2+ applications MUST be extracted to `@morningai/shared-ui`.

**Rules**:
- ✅ **MUST**: Extract components to `packages/shared-ui/src/components/ui/`
- ✅ **MUST**: Export all shared components from `packages/shared-ui/src/index.ts`
- ✅ **MUST**: Build shared-ui to `dist/` with ESM and CJS formats
- ✅ **MUST**: Provide TypeScript types (`.d.ts` files)
- ❌ **MUST NOT**: Duplicate components across applications

**Enforcement**:
- Audit script detects duplicate component names
- Code review checklist
- Adoption metrics tracked quarterly

**Rationale**: Reduces code duplication, ensures consistency, simplifies maintenance.

---

### 3.2 Component Structure

**INVARIANT**: All shared components must follow consistent structure and patterns.

**Rules**:
- ✅ **MUST**: Use Radix UI primitives for complex interactive components
- ✅ **MUST**: Define variants using `class-variance-authority`
- ✅ **MUST**: Use `forwardRef` for components that accept refs
- ✅ **MUST**: Export component props as TypeScript interfaces
- ✅ **MUST**: Use `cn()` utility from `tailwind-merge` for className merging
- ✅ **MUST**: Support dark mode via CSS variables

**Enforcement**:
- Code review checklist
- Component template/generator
- TypeScript strict mode

**Rationale**: Ensures components are composable, accessible, and maintainable.

---

### 3.3 Component Documentation

**INVARIANT**: Every shared component MUST have Storybook stories and usage documentation.

**Rules**:
- ✅ **MUST**: Create `.stories.tsx` file for each component
- ✅ **MUST**: Document all component variants and props
- ✅ **MUST**: Provide usage examples in stories
- ✅ **MUST**: Include accessibility notes in story documentation
- ✅ **MUST**: Add visual regression tests tagged with `@vrt`

**Enforcement**:
- PR checklist requires stories for new components
- Audit script tracks story coverage
- Quarterly review of documentation completeness

**Rationale**: Improves developer experience, ensures proper usage, enables visual testing.

---

## 4. Accessibility Invariants

### 4.1 WCAG AAA Compliance

**INVARIANT**: All UI components and color combinations MUST meet WCAG AAA standards (7:1 contrast ratio).

**Rules**:
- ✅ **MUST**: Ensure 7:1 contrast for normal text
- ✅ **MUST**: Ensure 4.5:1 contrast for large text (18pt+)
- ✅ **MUST**: Test color combinations with contrast checker
- ✅ **MUST**: Document contrast ratios in `tokens.json` comments
- ❌ **MUST NOT**: Use color as the only means of conveying information

**Enforcement**:
- Design review with contrast checker
- Automated axe tests in CI
- Manual accessibility audits quarterly

**Rationale**: Ensures usability for users with visual impairments, legal compliance.

---

### 4.2 Keyboard Navigation

**INVARIANT**: All interactive elements MUST be fully keyboard accessible.

**Rules**:
- ✅ **MUST**: Support Tab navigation for all interactive elements
- ✅ **MUST**: Provide visible focus indicators (2px outline, 2px offset)
- ✅ **MUST**: Support Enter/Space for button activation
- ✅ **MUST**: Support Escape for closing modals/dialogs
- ✅ **MUST**: Support Arrow keys for navigation in lists/menus
- ✅ **MUST**: Implement proper focus management (trap focus in modals)

**Enforcement**:
- eslint-plugin-jsx-a11y rules
- Manual keyboard testing in PR reviews
- E2E tests include keyboard navigation

**Rationale**: Ensures usability for keyboard-only users, improves overall UX.

---

### 4.3 ARIA Patterns

**INVARIANT**: Complex interactive components MUST implement proper ARIA patterns.

**Rules**:
- ✅ **MUST**: Use Radix UI primitives for dialogs, dropdowns, popovers, tooltips
- ✅ **MUST**: Provide `aria-label` or `aria-labelledby` for all interactive elements
- ✅ **MUST**: Use `role` attributes correctly (button, dialog, menu, etc.)
- ✅ **MUST**: Implement `aria-expanded`, `aria-haspopup` for expandable elements
- ✅ **MUST**: Use `aria-live` regions for dynamic content updates
- ❌ **MUST NOT**: Use `role="button"` on non-interactive elements without keyboard handlers

**Enforcement**:
- eslint-plugin-jsx-a11y rules
- axe automated tests
- Manual screen reader testing

**Rationale**: Ensures compatibility with assistive technologies.

---

### 4.4 Accessibility Testing

**INVARIANT**: All components MUST have automated accessibility tests.

**Rules**:
- ✅ **MUST**: Install `vitest-axe` or `jest-axe` in test environment
- ✅ **MUST**: Create `.a11y.test.tsx` files for critical components
- ✅ **MUST**: Run axe tests in CI pipeline
- ✅ **MUST**: Fix all axe violations before merging
- ✅ **MUST**: Document exceptions with justification

**Enforcement**:
- CI pipeline fails on axe violations
- PR checklist requires a11y tests for new components
- Quarterly manual audits

**Rationale**: Catches accessibility issues early, ensures consistent compliance.

---

## 5. Motion & Animation Invariants

### 5.1 Reduced Motion Support

**INVARIANT**: All animations MUST respect `prefers-reduced-motion` user preference.

**Rules**:
- ✅ **MUST**: Check `prefers-reduced-motion: reduce` media query
- ✅ **MUST**: Disable or minimize animations when preference is set
- ✅ **MUST**: Use CSS `@media (prefers-reduced-motion: reduce)` for CSS animations
- ✅ **MUST**: Check `window.matchMedia('(prefers-reduced-motion: reduce)')` for JS animations
- ✅ **MUST**: Reduce animation duration to `0.01ms` or disable entirely

**Enforcement**:
- Audit script checks for `prefers-reduced-motion` implementation
- Manual testing with reduced motion enabled
- Accessibility audits

**Rationale**: Respects user preferences, prevents motion sickness, improves accessibility.

---

### 5.2 Spring-based Animations

**INVARIANT**: Animations should use spring physics for natural, Apple-like motion.

**Rules**:
- ✅ **MUST**: Use Framer Motion for complex animations
- ✅ **MUST**: Use spring easing: `cubic-bezier(0.34, 1.56, 0.64, 1)`
- ✅ **MUST**: Define animation variants in shared utilities
- ✅ **MUST**: Use consistent animation durations from tokens
- ❌ **MUST NOT**: Use linear easing for UI animations

**Enforcement**:
- Code review checks animation implementation
- Design review ensures motion quality
- Animation utilities in shared-ui

**Rationale**: Creates polished, Apple-level user experience.

---

### 5.3 Animation Performance

**INVARIANT**: Animations must maintain 60fps performance.

**Rules**:
- ✅ **MUST**: Animate only `transform` and `opacity` properties
- ❌ **MUST NOT**: Animate `width`, `height`, `top`, `left` (causes layout thrashing)
- ✅ **MUST**: Use `will-change` sparingly and remove after animation
- ✅ **MUST**: Test animations on low-end devices
- ✅ **MUST**: Measure frame rate with Chrome DevTools Performance tab

**Enforcement**:
- Performance audits in CI (Lighthouse)
- Manual testing on target devices
- Code review checks animated properties

**Rationale**: Ensures smooth animations, prevents jank, improves perceived performance.

---

## 6. Internationalization Invariants

### 6.1 No Hard-coded Strings

**INVARIANT**: User-facing strings MUST NOT be hard-coded in component files.

**Rules**:
- ❌ **MUST NOT**: Use string literals for user-facing text in JSX
- ✅ **MUST**: Use `t()` function from `react-i18next` for all user-facing strings
- ✅ **MUST**: Define translation keys in locale files
- ✅ **MUST**: Provide fallback language (English)
- ✅ **MUST**: Use namespaces to organize translations

**Exceptions**:
- Developer-facing strings (console logs, error messages for debugging)
- Component prop names and technical identifiers

**Enforcement**:
- Audit script estimates i18n coverage
- Code review checklist
- ESLint plugin (custom rule) warns on string literals

**Rationale**: Enables internationalization, simplifies translation management.

---

### 6.2 Translation Coverage

**INVARIANT**: All user-facing text must have translation keys.

**Rules**:
- ✅ **MUST**: Achieve > 95% translation coverage
- ✅ **MUST**: Provide translations for all supported languages
- ✅ **MUST**: Use Tolgee or similar for translation management
- ✅ **MUST**: Test UI in all supported languages
- ✅ **MUST**: Handle pluralization and date/time formatting

**Enforcement**:
- Translation coverage reports
- Manual testing in each language
- Quarterly i18n audits

**Rationale**: Ensures complete internationalization, improves global UX.

---

## 7. Performance Invariants

### 7.1 Bundle Size Limits

**INVARIANT**: Application bundles must stay within defined size limits.

**Rules**:
- ✅ **MUST**: Keep main JS bundle < 500KB (gzipped)
- ✅ **MUST**: Keep main CSS bundle < 100KB (gzipped)
- ✅ **MUST**: Implement code splitting for routes
- ✅ **MUST**: Lazy load non-critical components
- ✅ **MUST**: Tree-shake unused code

**Enforcement**:
- Vite build reports bundle sizes
- CI fails if bundle exceeds limits
- Lighthouse CI tracks bundle size trends

**Rationale**: Improves load times, reduces bandwidth usage, enhances mobile experience.

---

### 7.2 Core Web Vitals

**INVARIANT**: Applications must meet Core Web Vitals thresholds.

**Targets**:
- ✅ **LCP** (Largest Contentful Paint): < 2.5s
- ✅ **CLS** (Cumulative Layout Shift): < 0.1
- ✅ **INP** (Interaction to Next Paint): < 200ms

**Rules**:
- ✅ **MUST**: Measure Web Vitals in production
- ✅ **MUST**: Optimize images (WebP, lazy loading)
- ✅ **MUST**: Minimize layout shifts (reserve space for dynamic content)
- ✅ **MUST**: Optimize JavaScript execution

**Enforcement**:
- Lighthouse CI in PR checks
- Real User Monitoring (RUM) in production
- Performance budgets in CI

**Rationale**: Ensures fast, responsive user experience, improves SEO.

---

### 7.3 Image Optimization

**INVARIANT**: All images must be optimized for web delivery.

**Rules**:
- ✅ **MUST**: Use WebP format with fallback
- ✅ **MUST**: Implement lazy loading for below-fold images
- ✅ **MUST**: Provide responsive images with `srcset`
- ✅ **MUST**: Compress images (< 200KB per image)
- ✅ **MUST**: Use CDN for image delivery

**Enforcement**:
- Build process optimizes images
- Lighthouse audits image optimization
- Manual review of large images

**Rationale**: Reduces bandwidth, improves load times, enhances mobile experience.

---

## 8. Documentation Invariants

### 8.1 Component Documentation

**INVARIANT**: Every shared component must have complete documentation.

**Rules**:
- ✅ **MUST**: Create Storybook story for each component
- ✅ **MUST**: Document all props with TypeScript types
- ✅ **MUST**: Provide usage examples
- ✅ **MUST**: Document accessibility features
- ✅ **MUST**: Include visual examples of all variants

**Enforcement**:
- PR checklist requires documentation
- Quarterly documentation audits
- Storybook build in CI

**Rationale**: Improves developer experience, ensures proper usage, reduces support burden.

---

### 8.2 Architecture Documentation

**INVARIANT**: System architecture must be documented and kept up-to-date.

**Required Documents**:
- ✅ `ARCHITECTURE.md`: System architecture overview
- ✅ `DESIGN_SYSTEM_GUIDELINES.md`: Design system rules and patterns
- ✅ `CODE_DUPLICATION_ANALYSIS.md`: Component duplication analysis
- ✅ `SHARED_COMPONENT_MIGRATION_PLAN.md`: Migration roadmap
- ✅ `DESIGN_SYSTEM_INVARIANTS.md`: This document

**Rules**:
- ✅ **MUST**: Update documentation with architectural changes
- ✅ **MUST**: Review documentation quarterly
- ✅ **MUST**: Keep documentation in version control
- ✅ **MUST**: Link related documents

**Enforcement**:
- PR checklist for architectural changes
- Quarterly documentation review
- Audit script checks for missing docs

**Rationale**: Ensures knowledge transfer, reduces onboarding time, maintains system understanding.

---

## 9. Testing Invariants

### 9.1 Test Coverage

**INVARIANT**: Shared components must maintain minimum test coverage.

**Rules**:
- ✅ **MUST**: Achieve > 60% code coverage for `@morningai/shared-ui`
- ✅ **MUST**: Write unit tests for all shared components
- ✅ **MUST**: Write integration tests for critical user flows
- ✅ **MUST**: Write E2E tests for happy paths
- ✅ **MUST**: Write accessibility tests for interactive components

**Enforcement**:
- CI fails if coverage drops below threshold
- Coverage reports in PR comments
- Quarterly coverage reviews

**Rationale**: Ensures code quality, prevents regressions, improves confidence in changes.

---

### 9.2 Test Quality

**INVARIANT**: Tests must be reliable, fast, and maintainable.

**Rules**:
- ✅ **MUST**: Tests must be deterministic (no flaky tests)
- ✅ **MUST**: Unit tests must run in < 10 seconds
- ✅ **MUST**: E2E tests must run in < 5 minutes
- ✅ **MUST**: Use Testing Library best practices
- ❌ **MUST NOT**: Test implementation details
- ✅ **MUST**: Test user-facing behavior

**Enforcement**:
- CI fails on flaky tests
- Test performance monitoring
- Code review checks test quality

**Rationale**: Ensures tests provide value, reduces maintenance burden, improves CI speed.

---

### 9.3 Visual Regression Testing

**INVARIANT**: Critical components must have visual regression tests.

**Rules**:
- ✅ **MUST**: Create Playwright tests tagged with `@vrt`
- ✅ **MUST**: Generate baseline snapshots for all variants
- ✅ **MUST**: Run VRT tests in CI on visual changes
- ✅ **MUST**: Review visual diffs before merging
- ✅ **MUST**: Update snapshots intentionally (not automatically)

**Enforcement**:
- CI runs VRT tests on component changes
- PR reviews include visual diff review
- Quarterly VRT coverage audits

**Rationale**: Catches unintended visual changes, ensures design consistency.

---

## 10. Security Invariants

### 10.1 No Committed Secrets

**INVARIANT**: Secrets and credentials MUST NOT be committed to version control.

**Rules**:
- ❌ **MUST NOT**: Commit `.env` files (except `.env.example`)
- ❌ **MUST NOT**: Commit API keys, tokens, passwords
- ✅ **MUST**: Use environment variables for secrets
- ✅ **MUST**: Add sensitive files to `.gitignore`
- ✅ **MUST**: Use secret management service (GitHub Secrets, Vault)

**Enforcement**:
- Pre-commit hooks scan for secrets
- CI scans for leaked secrets
- Regular security audits

**Rationale**: Prevents security breaches, protects sensitive data.

---

### 10.2 Dependency Security

**INVARIANT**: Dependencies must be kept secure and up-to-date.

**Rules**:
- ✅ **MUST**: Run `pnpm audit` regularly
- ✅ **MUST**: Fix high/critical vulnerabilities within 7 days
- ✅ **MUST**: Update dependencies quarterly
- ✅ **MUST**: Use Renovate or Dependabot for automated updates
- ✅ **MUST**: Review security advisories

**Enforcement**:
- CI runs `pnpm audit` on every PR
- Security dashboard tracks vulnerabilities
- Quarterly dependency updates

**Rationale**: Reduces security risks, ensures compliance, maintains system health.

---

## 11. Enforcement Mechanisms

### 11.1 Automated Enforcement

**Tools**:
1. **Audit Script**: `./audit-design-system.sh`
   - Runs on every PR
   - Checks all invariants
   - Fails PR on critical violations

2. **CI/CD Workflows**:
   - `.github/workflows/dependency-check.yml`: Package governance
   - `.github/workflows/backend.yml`: Backend tests and coverage
   - Lighthouse CI: Performance budgets
   - ESLint: Code quality and accessibility

3. **Pre-commit Hooks**:
   - Husky + lint-staged
   - Runs ESLint on staged files
   - Checks for secrets

### 11.2 Manual Enforcement

**Processes**:
1. **Code Review Checklist**:
   - Verify invariants compliance
   - Check documentation
   - Review test coverage

2. **Quarterly Audits**:
   - Design system audit
   - Accessibility audit
   - Performance audit
   - Security audit

3. **Architecture Review**:
   - Review major changes
   - Ensure alignment with invariants
   - Update documentation

### 11.3 Violation Handling

**Process**:
1. **Detection**: Automated tools or manual review identifies violation
2. **Triage**: Determine severity (P0, P1, P2)
3. **Remediation**: Create ticket, assign owner, set deadline
4. **Verification**: Re-run audit after fix
5. **Prevention**: Update enforcement mechanisms to prevent recurrence

**Severity Levels**:
- **P0 (Critical)**: Blocks PR, must fix immediately
- **P1 (High)**: Must fix within 7 days
- **P2 (Medium)**: Must fix within 30 days

---

## Appendix: Quick Reference

### Checklist for New Components

- [ ] Component in `packages/shared-ui/src/components/ui/`
- [ ] Uses design tokens (no hard-coded values)
- [ ] Uses Radix UI primitives (if interactive)
- [ ] Implements ARIA patterns
- [ ] Supports keyboard navigation
- [ ] Respects `prefers-reduced-motion`
- [ ] Has Storybook story
- [ ] Has unit tests
- [ ] Has accessibility tests
- [ ] Has visual regression tests
- [ ] Documented in README
- [ ] Exported from index.ts

### Checklist for PRs

- [ ] Passes `./audit-design-system.sh`
- [ ] Passes all CI checks
- [ ] No hard-coded design values
- [ ] No accessibility violations
- [ ] Test coverage maintained
- [ ] Documentation updated
- [ ] No secrets committed
- [ ] No forbidden lockfiles

---

**Last Updated**: 2025-11-02  
**Next Review**: 2026-02-02 (Quarterly)  
**Owner**: CTO / Engineering Leadership
