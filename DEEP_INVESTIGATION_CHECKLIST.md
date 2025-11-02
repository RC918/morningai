# Deep Investigation Checklist
## MorningAI Design System - CTO Level Investigation Flow

**Version**: 1.0.0  
**Date**: 2025-11-02  
**Owner**: CTO (Chief Technology Officer)  
**Purpose**: Structured, repeatable investigation flow for design system audits

---

## Overview

This checklist provides a systematic approach to investigating design system issues, ensuring comprehensive coverage of all critical areas. Use this when:

- Conducting quarterly design system audits
- Investigating reported UI/UX inconsistencies
- Onboarding new team members to design system standards
- Preparing for major releases or refactoring
- Responding to accessibility compliance requirements

---

## Investigation Flow

### Phase 1: Inventory & Discovery (30 minutes)

#### 1.1 Project Structure
- [ ] Verify package manager (pnpm 9.15.1+)
- [ ] Confirm monorepo structure (pnpm workspaces)
- [ ] List all frontend applications
  - [ ] frontend-dashboard
  - [ ] owner-console
  - [ ] Other applications
- [ ] Identify shared UI packages
  - [ ] @morningai/shared-ui
  - [ ] Other shared packages
- [ ] Check build tools
  - [ ] Turbo configuration
  - [ ] Vite configuration
  - [ ] TypeScript version

**Output**: Document current project structure in investigation notes

#### 1.2 Design Token Files
- [ ] Locate all `tokens.json` files
  - [ ] `handoff/20250928/40_App/frontend-dashboard/public/tokens.json`
  - [ ] `handoff/20250928/40_App/owner-console/public/tokens.json`
  - [ ] `packages/shared-ui/src/tokens.json`
  - [ ] `docs/UX/tokens.json`
- [ ] Verify token structure
  - [ ] Color tokens (primary, accent, semantic, neutral)
  - [ ] Typography tokens (family, size, weight, lineHeight)
  - [ ] Spacing tokens
  - [ ] Radius tokens
  - [ ] Shadow tokens
  - [ ] Animation tokens
  - [ ] Breakpoint tokens
- [ ] Check for token consistency across files
- [ ] Identify any duplicate or conflicting tokens

**Output**: Token inventory with inconsistencies noted

#### 1.3 Design Token Implementation
- [ ] Locate design-tokens.ts/js files
- [ ] Review `applyDesignTokens()` function
- [ ] Check CSS variable generation
- [ ] Verify theme container class (`.theme-morning-ai`)
- [ ] Test token application in browser DevTools

**Output**: Implementation assessment with gaps identified

#### 1.4 Tailwind Configuration
- [ ] Review `tailwind.config.js` in each app
- [ ] Check CSS variable mapping
- [ ] Verify safelist patterns (if any)
- [ ] Review theme extensions
- [ ] Check plugin usage

**Output**: Tailwind configuration analysis

---

### Phase 2: Token Usage Analysis (45 minutes)

#### 2.1 Hardcoded Values Scan
- [ ] Run audit script: `./scripts/audit-design-system.sh`
- [ ] Review hardcoded hex colors
  - [ ] Document file paths and line numbers
  - [ ] Categorize by severity (critical/medium/low)
- [ ] Check for hardcoded spacing values
  - [ ] Search for `px`, `rem`, `em` values in JSX
  - [ ] Exclude legitimate cases (e.g., 1px borders)
- [ ] Check for hardcoded font sizes
- [ ] Check for hardcoded border radius values

**Output**: List of hardcoded values with replacement recommendations

#### 2.2 Token Scoping
- [ ] Verify `.theme-morning-ai` container in App.tsx
- [ ] Check if tokens are scoped or global
- [ ] Test token isolation (no global pollution)
- [ ] Review CSS specificity issues
- [ ] Check for token override patterns

**Output**: Scoping assessment with recommendations

#### 2.3 Dark Mode Support
- [ ] Check for dark mode tokens
- [ ] Review dark mode implementation
- [ ] Test dark mode toggle functionality
- [ ] Verify color contrast in dark mode
- [ ] Check for missing dark mode variants

**Output**: Dark mode readiness report

---

### Phase 3: Component Consistency (60 minutes)

#### 3.1 Component Inventory
- [ ] List all UI components
  - [ ] Shared UI components (`packages/shared-ui/src`)
  - [ ] App-specific components
- [ ] Categorize components
  - [ ] Atoms (Button, Input, Badge, etc.)
  - [ ] Molecules (Card, Form, etc.)
  - [ ] Organisms (Dashboard, Sidebar, etc.)
- [ ] Check for duplicate components
- [ ] Identify components without Storybook stories

**Output**: Component inventory with categorization

#### 3.2 Component Token Usage
- [ ] Review Button component
  - [ ] Uses color tokens
  - [ ] Uses spacing tokens
  - [ ] Uses typography tokens
  - [ ] Uses radius tokens
- [ ] Review Input component
  - [ ] Consistent styling
  - [ ] Token-based colors
  - [ ] Proper focus states
- [ ] Review Card component
- [ ] Review Modal/Dialog component
- [ ] Review Toast/Alert component

**Output**: Component-by-component token usage report

#### 3.3 Component Variants
- [ ] Document all component variants
  - [ ] Button: primary, secondary, outline, ghost, destructive
  - [ ] Alert: success, warning, error, info
  - [ ] Badge: default, secondary, outline, destructive
- [ ] Check variant consistency
- [ ] Verify variant naming conventions
- [ ] Test variant combinations

**Output**: Variant matrix with consistency issues

---

### Phase 4: Accessibility Compliance (60 minutes)

#### 4.1 WCAG 2.1 AA Requirements
- [ ] Color contrast ratios
  - [ ] Text on backgrounds (4.5:1 minimum)
  - [ ] Large text (3:1 minimum)
  - [ ] UI components (3:1 minimum)
  - [ ] Use WebAIM Contrast Checker
- [ ] Keyboard navigation
  - [ ] All interactive elements focusable
  - [ ] Logical tab order
  - [ ] Focus indicators visible
  - [ ] No keyboard traps
- [ ] Screen reader support
  - [ ] Semantic HTML
  - [ ] ARIA labels where needed
  - [ ] ARIA live regions for dynamic content
  - [ ] Alternative text for images

**Output**: WCAG compliance checklist with violations

#### 4.2 Skip Navigation
- [ ] Check for skip link in App.tsx
- [ ] Test skip link functionality
  - [ ] Tab to skip link (first focusable element)
  - [ ] Activate skip link
  - [ ] Verify focus moves to main content
- [ ] Verify skip link styling
  - [ ] Hidden by default
  - [ ] Visible on focus
  - [ ] Proper positioning and styling

**Output**: Skip navigation assessment

#### 4.3 ARIA Live Regions
- [ ] Identify dynamic content areas
  - [ ] Save status indicators
  - [ ] Error messages
  - [ ] Toast notifications
  - [ ] Form validation feedback
  - [ ] Loading states
- [ ] Check for `aria-live` attributes
  - [ ] `aria-live="polite"` for non-critical updates
  - [ ] `aria-live="assertive"` for critical alerts
- [ ] Check for `role="alert"` and `role="status"`
- [ ] Test with screen reader (NVDA, JAWS, or VoiceOver)

**Output**: ARIA live region coverage report

#### 4.4 Focus Management
- [ ] Modal dialogs
  - [ ] Focus trapped within modal
  - [ ] Focus returns to trigger on close
  - [ ] Escape key closes modal
- [ ] Dropdown menus
  - [ ] Arrow key navigation
  - [ ] Enter/Space to select
  - [ ] Escape to close
- [ ] Form validation
  - [ ] Focus moves to first error
  - [ ] Error messages associated with fields
  - [ ] `aria-invalid` and `aria-describedby` used

**Output**: Focus management assessment

#### 4.5 Motion & Animation
- [ ] Check for `prefers-reduced-motion` support
- [ ] Review animation durations
- [ ] Test with reduced motion enabled
- [ ] Ensure critical functionality works without animation

**Output**: Motion accessibility report

---

### Phase 5: Performance & Optimization (30 minutes)

#### 5.1 Bundle Size
- [ ] Run build: `pnpm build`
- [ ] Analyze bundle size
  - [ ] Check for large dependencies
  - [ ] Identify duplicate dependencies
  - [ ] Review code splitting
- [ ] Check for unused CSS
- [ ] Review Tailwind purge configuration

**Output**: Bundle size analysis with optimization opportunities

#### 5.2 Loading Performance
- [ ] Test initial page load
- [ ] Check for render-blocking resources
- [ ] Review lazy loading implementation
- [ ] Check for skeleton screens
- [ ] Test on slow network (3G)

**Output**: Loading performance metrics

#### 5.3 Runtime Performance
- [ ] Profile component rendering
- [ ] Check for unnecessary re-renders
- [ ] Review React DevTools Profiler
- [ ] Test animation performance (60fps)
- [ ] Check for memory leaks

**Output**: Runtime performance assessment

---

### Phase 6: Documentation Review (30 minutes)

#### 6.1 Design System Guidelines
- [ ] Review `DESIGN_SYSTEM_GUIDELINES.md`
  - [ ] Up to date
  - [ ] Complete
  - [ ] Examples accurate
- [ ] Check for missing sections
- [ ] Verify code examples work
- [ ] Review component usage guidelines

**Output**: Documentation gaps identified

#### 6.2 Storybook Documentation
- [ ] Count Storybook stories
- [ ] Check story coverage
  - [ ] All components documented
  - [ ] All variants shown
  - [ ] Interactive examples
- [ ] Review Storybook a11y addon
- [ ] Test Storybook build

**Output**: Storybook coverage report

#### 6.3 Component API Documentation
- [ ] Check TypeScript types
- [ ] Review prop documentation
- [ ] Verify default values
- [ ] Check for deprecated props

**Output**: API documentation assessment

---

### Phase 7: CI/CD Integration (20 minutes)

#### 7.1 Existing Workflows
- [ ] Review `.github/workflows/`
  - [ ] backend.yml
  - [ ] dependency-check.yml
  - [ ] Other workflows
- [ ] Check for design system checks
- [ ] Review PR requirements
- [ ] Check for automated testing

**Output**: CI/CD integration status

#### 7.2 Design System Audit Workflow
- [ ] Verify `design-system-audit.yml` exists
- [ ] Check workflow triggers
  - [ ] Pull requests to main
  - [ ] Push to main
- [ ] Review workflow steps
- [ ] Test workflow locally

**Output**: Audit workflow validation

---

### Phase 8: Dependency Management (15 minutes)

#### 8.1 Package Manager Policy
- [ ] Verify pnpm-only policy
- [ ] Check for forbidden lock files
  - [ ] No `package-lock.json`
  - [ ] No `yarn.lock`
- [ ] Verify `pnpm-lock.yaml` exists
- [ ] Check `packageManager` field in package.json

**Output**: Dependency management compliance

#### 8.2 Vercel Configuration
- [ ] Review `vercel.json`
- [ ] Check `installCommand` uses pnpm
- [ ] Verify `buildCommand`
- [ ] Check `outputDirectory`
- [ ] Review `ignoreCommand`

**Output**: Vercel configuration assessment

---

### Phase 9: Regression Risk Assessment (20 minutes)

#### 9.1 Impact Analysis
- [ ] Identify high-traffic pages
- [ ] List critical user flows
- [ ] Assess change impact
  - [ ] Visual changes
  - [ ] Functional changes
  - [ ] Performance impact
- [ ] Identify breaking changes

**Output**: Risk matrix with mitigation strategies

#### 9.2 Testing Strategy
- [ ] Unit tests
  - [ ] Component tests
  - [ ] Token utility tests
- [ ] Integration tests
  - [ ] User flow tests
- [ ] Visual regression tests
  - [ ] Playwright VRT
  - [ ] Storybook visual tests
- [ ] Accessibility tests
  - [ ] axe-core integration
  - [ ] Manual testing

**Output**: Testing plan with coverage gaps

---

### Phase 10: Sign-off & Next Steps (15 minutes)

#### 10.1 Executive Summary
- [ ] Summarize findings
  - [ ] Critical issues (P0)
  - [ ] High priority issues (P1)
  - [ ] Medium priority issues (P2)
- [ ] Estimate effort for fixes
- [ ] Prioritize remediation work
- [ ] Assign owners

**Output**: Executive summary for stakeholders

#### 10.2 Action Items
- [ ] Create GitHub issues for each finding
- [ ] Link to investigation report
- [ ] Set deadlines based on priority
- [ ] Schedule follow-up review
- [ ] Update design system roadmap

**Output**: Actionable task list with owners and deadlines

#### 10.3 CTO Sign-off
- [ ] Review all findings
- [ ] Approve remediation plan
- [ ] Authorize resource allocation
- [ ] Set quality gates for future PRs
- [ ] Document lessons learned

**Output**: CTO approval and strategic direction

---

## Investigation Report Template

Use this template to document your investigation:

```markdown
# Design System Investigation Report

**Date**: YYYY-MM-DD
**Investigator**: [Name]
**Scope**: [Full audit / Specific component / Accessibility / etc.]

## Executive Summary

[2-3 paragraphs summarizing key findings and recommendations]

## Findings

### Critical Issues (P0)
1. [Issue description]
   - **Impact**: [User impact, business impact]
   - **Recommendation**: [Specific fix]
   - **Effort**: [Hours/days]

### High Priority Issues (P1)
[Same format]

### Medium Priority Issues (P2)
[Same format]

## Metrics

- **Token Coverage**: X% (target: 95%+)
- **WCAG Compliance**: X/Y checks passed
- **Storybook Coverage**: X/Y components documented
- **Bundle Size**: X KB (target: < Y KB)

## Recommendations

1. [Prioritized recommendation]
2. [Prioritized recommendation]
3. [Prioritized recommendation]

## Next Steps

- [ ] Action item 1 (Owner: X, Deadline: Y)
- [ ] Action item 2 (Owner: X, Deadline: Y)

## Appendix

- Audit script output: `audit-design-system-report.md`
- Screenshots: [links]
- Test results: [links]
```

---

## Tools & Resources

### Audit Tools
- **Audit Script**: `./scripts/audit-design-system.sh`
- **Invariants Document**: `DESIGN_SYSTEM_INVARIANTS.md`
- **Guidelines**: `DESIGN_SYSTEM_GUIDELINES.md`

### Testing Tools
- **Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **axe DevTools**: Chrome/Firefox extension
- **Lighthouse**: Chrome DevTools
- **Screen Readers**: NVDA (Windows), VoiceOver (Mac), JAWS

### Development Tools
- **Storybook**: `pnpm storybook`
- **TypeScript**: `pnpm typecheck`
- **Linter**: `pnpm lint`
- **Tests**: `pnpm test`

---

## Frequency & Ownership

| Activity | Frequency | Owner | Duration |
|----------|-----------|-------|----------|
| Full Audit | Quarterly | CTO | 4-6 hours |
| Component Review | Per PR | Frontend Lead | 15-30 min |
| Accessibility Audit | Monthly | UX Lead | 2 hours |
| Performance Review | Monthly | Tech Lead | 1 hour |
| Documentation Update | Continuous | Team | Ongoing |

---

## Success Criteria

A successful investigation should result in:

1. **Comprehensive Report**: All phases completed with documented findings
2. **Actionable Items**: Specific, prioritized tasks with owners and deadlines
3. **Metrics Baseline**: Quantitative measures for tracking improvement
4. **Strategic Alignment**: Recommendations aligned with business goals
5. **Team Buy-in**: Stakeholder approval and resource commitment

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-02 | CTO | Initial checklist based on comprehensive audit |

---

**Note**: This checklist should be reviewed and updated quarterly to reflect evolving best practices and project needs.
