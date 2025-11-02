# Deep Investigation Checklist

**MorningAI Design System & Architecture Audit**  
**CTO Quality Assurance Framework**

This checklist provides a systematic investigation flow for auditing the MorningAI design system, ensuring comprehensive coverage of all critical areas for a top-tier SaaS platform.

---

## Table of Contents

1. [Baseline Environment Setup](#1-baseline-environment-setup)
2. [Package Governance & Dependencies](#2-package-governance--dependencies)
3. [Design System Integrity](#3-design-system-integrity)
4. [Component Architecture & Adoption](#4-component-architecture--adoption)
5. [Accessibility Compliance](#5-accessibility-compliance)
6. [Performance & Quality](#6-performance--quality)
7. [Internationalization (i18n)](#7-internationalization-i18n)
8. [Documentation & Knowledge Management](#8-documentation--knowledge-management)
9. [CI/CD & Automation](#9-cicd--automation)
10. [Security & Compliance](#10-security--compliance)
11. [Remediation Planning](#11-remediation-planning)

---

## 1. Baseline Environment Setup

### 1.1 Prerequisites Verification

- [ ] **Node.js Version**: Verify Node.js >= 20.0.0
  ```bash
  node --version
  ```
  - Expected: v20.x.x or higher
  - Action if failed: Update Node.js via nvm or official installer

- [ ] **pnpm Version**: Verify pnpm >= 9.0.0
  ```bash
  pnpm --version
  ```
  - Expected: 9.x.x or higher
  - Action if failed: Update pnpm via `npm install -g pnpm@latest`

- [ ] **Git Status**: Ensure clean working directory
  ```bash
  git status
  ```
  - Expected: No uncommitted changes for baseline audit
  - Action if failed: Stash or commit changes

### 1.2 Workspace Bootstrap

- [ ] **Install Dependencies**: Bootstrap entire monorepo
  ```bash
  pnpm install
  ```
  - Expected: All packages installed without errors
  - Action if failed: Check for lockfile conflicts, clear node_modules

- [ ] **Build Shared UI**: Ensure shared-ui package builds successfully
  ```bash
  pnpm --filter @morningai/shared-ui build
  ```
  - Expected: Build completes, dist/ directory created
  - Action if failed: Check TypeScript errors, missing dependencies

- [ ] **Type Check All**: Verify TypeScript across workspace
  ```bash
  pnpm typecheck
  ```
  - Expected: No type errors
  - Action if failed: Document errors, create remediation tickets

---

## 2. Package Governance & Dependencies

### 2.1 Lockfile Integrity

- [ ] **Forbidden Lockfiles**: Scan for yarn.lock, package-lock.json, npm-shrinkwrap.json
  ```bash
  find . -name "yarn.lock" -o -name "package-lock.json" -o -name "npm-shrinkwrap.json"
  ```
  - Expected: No results
  - Action if failed: Delete forbidden lockfiles, regenerate pnpm-lock.yaml

- [ ] **pnpm-lock.yaml**: Verify single lockfile at root
  ```bash
  ls -la pnpm-lock.yaml
  ```
  - Expected: File exists at root
  - Action if failed: Run `pnpm install` to generate

### 2.2 Package Configuration

- [ ] **packageManager Field**: Check root package.json
  ```bash
  grep '"packageManager"' package.json
  ```
  - Expected: `"packageManager": "pnpm@9.15.1"` or similar
  - Action if failed: Add field to package.json

- [ ] **Engines Field**: Verify all workspace packages have engines
  ```bash
  for pkg in packages/*/package.json handoff/20250928/40_App/*/package.json; do
    if [ -f "$pkg" ]; then
      if ! grep -q '"engines"' "$pkg"; then
        echo "Missing engines: $pkg"
      fi
    fi
  done
  ```
  - Expected: All packages have engines field
  - Action if failed: Add engines to each package.json

### 2.3 Version Alignment

- [ ] **React Versions**: Check consistency across packages
  ```bash
  grep -h '"react":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json | sort -u
  ```
  - Expected: Single version (^19.1.0)
  - Action if failed: Update pnpm overrides in root package.json

- [ ] **React-DOM Versions**: Check consistency
  ```bash
  grep -h '"react-dom":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json | sort -u
  ```
  - Expected: Matches React version
  - Action if failed: Update pnpm overrides

- [ ] **TypeScript Versions**: Check consistency
  ```bash
  grep -h '"typescript":' package.json packages/*/package.json handoff/20250928/40_App/*/package.json | sort -u
  ```
  - Expected: Single version (5.9.3)
  - Action if failed: Update pnpm overrides

- [ ] **Radix UI Versions**: Verify React 19 compatibility
  ```bash
  grep -h '@radix-ui' handoff/20250928/40_App/frontend-dashboard/package.json | head -5
  ```
  - Expected: Latest versions compatible with React 19
  - Action if failed: Update via pnpm overrides if needed

---

## 3. Design System Integrity

### 3.1 Design Tokens

- [ ] **tokens.json Exists**: Verify design tokens file
  ```bash
  ls -la packages/shared-ui/src/tokens.json
  ```
  - Expected: File exists with complete token definitions
  - Action if failed: Create tokens.json from design system spec

- [ ] **Token Completeness**: Verify all token categories
  - [ ] Colors (primary, accent, semantic, neutral, background)
  - [ ] Typography (font families, sizes, weights, line heights)
  - [ ] Spacing (8-point grid system)
  - [ ] Shadows (5-level system)
  - [ ] Border radius (6 levels)
  - [ ] Animation (durations, easing functions)
  - [ ] Breakpoints (mobile, tablet, desktop)
  - Action if failed: Add missing token categories

- [ ] **Tailwind v4 Token Mapping**: Check CSS variables in index.css
  ```bash
  grep -A 20 "@theme" handoff/20250928/40_App/frontend-dashboard/src/index.css
  ```
  - Expected: @theme block with CSS variables mapped to tokens
  - Action if failed: Create CSS variable bridge from tokens.json

- [ ] **Theme CSS Variables**: Verify theme-apple.css
  ```bash
  ls -la handoff/20250928/40_App/frontend-dashboard/src/styles/theme-apple.css
  ```
  - Expected: Comprehensive CSS variables for theming
  - Action if failed: Document gaps, create migration plan

### 3.2 Token Enforcement

- [ ] **Run Audit Script**: Execute design system audit
  ```bash
  ./audit-design-system.sh --verbose
  ```
  - Expected: Pass or warnings only, no failures
  - Action if failed: Address each failure per audit report

- [ ] **Hard-coded Colors**: Search for hex/rgb values in components
  ```bash
  grep -r "#[0-9A-Fa-f]\{6\}" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
  ```
  - Expected: < 50 instances (excluding config files)
  - Action if failed: Create refactoring tickets to use tokens

- [ ] **Inline Styles**: Search for style={{ usage
  ```bash
  grep -r "style={{" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | wc -l
  ```
  - Expected: < 50 instances
  - Action if failed: Refactor to use utility classes or styled components

---

## 4. Component Architecture & Adoption

### 4.1 Shared Component Library

- [ ] **Component Count**: Verify 47 shared components
  ```bash
  find packages/shared-ui/src/components/ui -name "*.tsx" | wc -l
  ```
  - Expected: 47 components
  - Action if failed: Audit component list, add missing components

- [ ] **Component Exports**: Check index.ts exports all components
  ```bash
  cat packages/shared-ui/src/components/ui/index.ts
  ```
  - Expected: All 47 components exported
  - Action if failed: Update index.ts with missing exports

- [ ] **Build Output**: Verify dist/ directory structure
  ```bash
  ls -la packages/shared-ui/dist/
  ```
  - Expected: index.js, index.mjs, index.d.ts
  - Action if failed: Fix build configuration in package.json

### 4.2 Component Duplication Analysis

- [ ] **Frontend-Dashboard Local Components**: Count local UI components
  ```bash
  find handoff/20250928/40_App/frontend-dashboard/src/components/ui -name "*.tsx" | wc -l
  ```
  - Expected: Document count (currently 55)
  - Action: Create migration plan for duplicates

- [ ] **Owner-Console Local Components**: Count local UI components
  ```bash
  find handoff/20250928/40_App/owner-console/src/components/ui -name "*.tsx" | wc -l
  ```
  - Expected: 0 (fully migrated) or document count
  - Action: Create migration plan if > 0

- [ ] **Duplicate Component Names**: Identify overlapping names
  ```bash
  comm -12 \
    <(find packages/shared-ui/src/components/ui -name "*.tsx" -exec basename {} \; | sort) \
    <(find handoff/20250928/40_App/frontend-dashboard/src/components/ui -name "*.tsx" -exec basename {} \; | sort)
  ```
  - Expected: List of duplicates (if any)
  - Action: For each duplicate, decide: migrate, rename, or keep separate

### 4.3 Adoption Metrics

- [ ] **Shared-UI Import Count (Dashboard)**: Measure adoption
  ```bash
  grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" | wc -l
  ```
  - Expected: > 100 imports
  - Action: Calculate adoption ratio, create migration roadmap

- [ ] **Shared-UI Import Count (Console)**: Measure adoption
  ```bash
  grep -r "from '@morningai/shared-ui'" handoff/20250928/40_App/owner-console/src --include="*.tsx" --include="*.ts" | wc -l
  ```
  - Expected: > 50 imports
  - Action: Calculate adoption ratio, create migration roadmap

- [ ] **Adoption Ratio**: Calculate percentage of shared vs local
  - Formula: `(shared_imports / (shared_imports + local_components)) * 100`
  - Expected: > 50%
  - Action: Set target (e.g., 80%), create migration plan

---

## 5. Accessibility Compliance

### 5.1 Tooling & Configuration

- [ ] **eslint-plugin-jsx-a11y**: Verify installation
  ```bash
  grep "eslint-plugin-jsx-a11y" handoff/20250928/40_App/frontend-dashboard/package.json
  ```
  - Expected: Installed in both apps
  - Action if failed: Install plugin, configure ESLint rules

- [ ] **ESLint A11y Rules**: Check .eslintrc or eslint.config.js
  ```bash
  find handoff/20250928/40_App/frontend-dashboard -name "eslint.config.*" -o -name ".eslintrc.*"
  ```
  - Expected: jsx-a11y rules enabled
  - Action if failed: Add recommended jsx-a11y rules

- [ ] **Axe Testing Tools**: Verify installation
  ```bash
  grep -E "vitest-axe|jest-axe|@axe-core" handoff/20250928/40_App/frontend-dashboard/package.json
  ```
  - Expected: At least one axe tool installed
  - Action if failed: Install vitest-axe or jest-axe

### 5.2 A11y Testing Coverage

- [ ] **A11y Test Files**: Count dedicated a11y tests
  ```bash
  find handoff/20250928/40_App/frontend-dashboard/src -name "*.a11y.test.*" | wc -l
  ```
  - Expected: > 5 test files
  - Action: Create a11y tests for critical components

- [ ] **Run A11y Tests**: Execute accessibility tests
  ```bash
  pnpm --filter frontend-dashboard test -- --grep "a11y|accessibility"
  ```
  - Expected: All tests pass
  - Action if failed: Fix violations, document exceptions

- [ ] **Image Alt Attributes**: Check for missing alt
  ```bash
  grep -r "<img" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | grep -v "alt=" | wc -l
  ```
  - Expected: 0 instances
  - Action if failed: Add alt attributes to all images

- [ ] **ARIA Patterns**: Verify Radix UI usage for complex components
  - [ ] Dialogs use Radix Dialog
  - [ ] Dropdowns use Radix DropdownMenu
  - [ ] Popovers use Radix Popover
  - [ ] Tooltips use Radix Tooltip
  - Action: Ensure all interactive overlays use Radix primitives

### 5.3 Color Contrast

- [ ] **WCAG AAA Compliance**: Verify contrast ratios in tokens.json
  - [ ] Primary colors: 7:1 contrast
  - [ ] Semantic colors: 7:1 contrast
  - [ ] Text colors: 7:1 contrast on backgrounds
  - Action: Use contrast checker tool, adjust colors if needed

---

## 6. Performance & Quality

### 6.1 Testing Infrastructure

- [ ] **Unit Tests**: Run unit tests
  ```bash
  pnpm test
  ```
  - Expected: All tests pass
  - Action if failed: Fix failing tests, document flaky tests

- [ ] **Coverage Report**: Generate coverage
  ```bash
  pnpm --filter frontend-dashboard test:coverage
  ```
  - Expected: > 60% coverage for shared-ui
  - Action: Set coverage thresholds, add tests for uncovered code

- [ ] **E2E Tests**: Run end-to-end tests
  ```bash
  pnpm --filter frontend-dashboard test:e2e
  ```
  - Expected: Critical paths pass
  - Action if failed: Fix broken tests, update selectors

- [ ] **Smoke Tests**: Run smoke tests
  ```bash
  pnpm --filter frontend-dashboard test:smoke
  ```
  - Expected: All smoke tests pass
  - Action if failed: Fix critical issues immediately

### 6.2 Performance Budgets

- [ ] **Lighthouse CI**: Check configuration
  ```bash
  cat lighthouserc.json
  ```
  - Expected: Performance budgets defined
  - Action: Set budgets for LCP, CLS, INP, bundle size

- [ ] **Bundle Size**: Analyze build output
  ```bash
  pnpm --filter frontend-dashboard build
  ls -lh handoff/20250928/40_App/frontend-dashboard/dist/assets/
  ```
  - Expected: JS < 500KB, CSS < 100KB (gzipped)
  - Action: Implement code splitting, lazy loading if needed

- [ ] **Web Vitals**: Check for web-vitals integration
  ```bash
  grep "web-vitals" handoff/20250928/40_App/frontend-dashboard/package.json
  ```
  - Expected: Installed and integrated
  - Action: Add Web Vitals reporting to analytics

---

## 7. Internationalization (i18n)

### 7.1 i18n Infrastructure

- [ ] **i18n Library**: Verify installation
  ```bash
  grep -E "react-i18next|i18next" handoff/20250928/40_App/frontend-dashboard/package.json
  ```
  - Expected: react-i18next and i18next installed
  - Action if failed: Install i18n libraries

- [ ] **i18n Configuration**: Check i18n setup
  ```bash
  find handoff/20250928/40_App/frontend-dashboard/src -name "i18n.*" -o -name "i18next.*"
  ```
  - Expected: Configuration file exists
  - Action: Review configuration, ensure proper setup

- [ ] **Translation Files**: Verify translation resources
  ```bash
  find handoff/20250928/40_App/frontend-dashboard -name "locales" -o -name "translations"
  ```
  - Expected: Translation files for supported languages
  - Action: Create translation structure if missing

### 7.2 i18n Coverage

- [ ] **i18n Usage Count**: Measure adoption
  ```bash
  grep -rE "useTranslation|t\(" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" --include="*.ts" | wc -l
  ```
  - Expected: > 1000 instances (currently 2781)
  - Action: Document coverage, identify untranslated strings

- [ ] **String Literals**: Identify hard-coded strings
  ```bash
  grep -r ">[A-Z][a-z]" handoff/20250928/40_App/frontend-dashboard/src --include="*.tsx" | head -20
  ```
  - Expected: Minimal user-facing literals
  - Action: Create tickets to wrap literals in t()

---

## 8. Documentation & Knowledge Management

### 8.1 Design System Documentation

- [ ] **DESIGN_SYSTEM_GUIDELINES.md**: Verify existence and completeness
  ```bash
  ls -la DESIGN_SYSTEM_GUIDELINES.md
  ```
  - Expected: Comprehensive guidelines document
  - Action: Review and update with latest standards

- [ ] **CODE_DUPLICATION_ANALYSIS.md**: Verify existence
  ```bash
  ls -la CODE_DUPLICATION_ANALYSIS.md
  ```
  - Expected: Analysis of component duplication
  - Action: Update with current metrics

- [ ] **SHARED_COMPONENT_MIGRATION_PLAN.md**: Verify existence
  ```bash
  ls -la SHARED_COMPONENT_MIGRATION_PLAN.md
  ```
  - Expected: Migration roadmap and timeline
  - Action: Update with progress, adjust timeline

- [ ] **UI/UX Documentation**: Check docs directory
  ```bash
  ls -la docs/UI_UX_*.md docs/UX/
  ```
  - Expected: UI_UX_QUICKSTART.md, UI_UX_CHEATSHEET.md, APPLE_LEVEL_UI_UX_OPTIMIZATION_REPORT.md
  - Action: Verify all referenced docs exist

### 8.2 Storybook Documentation

- [ ] **Storybook Configuration**: Verify .storybook directory
  ```bash
  ls -la handoff/20250928/40_App/frontend-dashboard/.storybook/
  ```
  - Expected: Complete Storybook configuration
  - Action: Review configuration, ensure addons installed

- [ ] **Story Files Count**: Count story files
  ```bash
  find handoff/20250928/40_App/frontend-dashboard/src -name "*.stories.*" | wc -l
  ```
  - Expected: > 20 story files
  - Action: Create stories for all shared components

- [ ] **Story Coverage**: Calculate coverage
  - Formula: `(story_files / total_components) * 100`
  - Expected: > 80% for shared components
  - Action: Create stories for uncovered components

- [ ] **Build Storybook**: Test Storybook build
  ```bash
  pnpm --filter frontend-dashboard build-storybook
  ```
  - Expected: Builds successfully
  - Action if failed: Fix build errors, update dependencies

### 8.3 Visual Regression Testing

- [ ] **VRT Configuration**: Check Playwright VRT setup
  ```bash
  grep -r "@vrt" handoff/20250928/40_App/frontend-dashboard --include="*.spec.*" --include="*.test.*"
  ```
  - Expected: VRT tests tagged with @vrt
  - Action: Create VRT tests for critical components

- [ ] **VRT Baseline**: Verify baseline snapshots exist
  ```bash
  find handoff/20250928/40_App/frontend-dashboard -name "__snapshots__" -type d
  ```
  - Expected: Snapshot directories exist
  - Action: Generate baseline snapshots if missing

---

## 9. CI/CD & Automation

### 9.1 GitHub Actions Workflows

- [ ] **Dependency Check Workflow**: Verify enforcement
  ```bash
  cat .github/workflows/dependency-check.yml
  ```
  - Expected: Enforces pnpm-only, checks for forbidden lockfiles
  - Action: Ensure workflow runs on all PRs

- [ ] **Backend CI**: Verify test and coverage
  ```bash
  cat .github/workflows/backend.yml
  ```
  - Expected: Runs pytest with coverage
  - Action: Review coverage thresholds

- [ ] **Frontend CI**: Check for lint, test, typecheck
  ```bash
  ls -la .github/workflows/ | grep -E "frontend|lint|test"
  ```
  - Expected: Workflows for frontend quality checks
  - Action: Add if missing

- [ ] **Audit Script Integration**: Add audit to CI
  ```bash
  grep -r "audit-design-system" .github/workflows/
  ```
  - Expected: Audit script runs on PRs
  - Action: Create workflow to run audit script

### 9.2 Pre-commit Hooks

- [ ] **Husky Configuration**: Verify husky setup
  ```bash
  ls -la .husky/
  ```
  - Expected: Pre-commit hooks configured
  - Action: Set up husky if missing

- [ ] **Lint-staged**: Check configuration
  ```bash
  grep "lint-staged" package.json
  ```
  - Expected: Configured to run ESLint on staged files
  - Action: Add lint-staged if missing

---

## 10. Security & Compliance

### 10.1 Secret Management

- [ ] **No Committed Secrets**: Scan for secrets
  ```bash
  grep -r "API_KEY\|SECRET\|PASSWORD" . --include="*.env" --include="*.json" --include="*.ts" --include="*.tsx" | grep -v "example" | grep -v "node_modules"
  ```
  - Expected: No secrets in code
  - Action: Remove secrets, add to .gitignore, use env vars

- [ ] **.env Files**: Check .gitignore
  ```bash
  grep "\.env" .gitignore
  ```
  - Expected: .env files ignored
  - Action: Add to .gitignore if missing

- [ ] **Sentry Integration**: Verify error tracking
  ```bash
  grep "@sentry" handoff/20250928/40_App/frontend-dashboard/package.json
  ```
  - Expected: Sentry installed and configured
  - Action: Review Sentry DSN configuration

### 10.2 Dependency Security

- [ ] **Audit Dependencies**: Run security audit
  ```bash
  pnpm audit
  ```
  - Expected: No high/critical vulnerabilities
  - Action: Update vulnerable dependencies

- [ ] **Outdated Packages**: Check for updates
  ```bash
  pnpm outdated
  ```
  - Expected: Document outdated packages
  - Action: Create update plan for major versions

---

## 11. Remediation Planning

### 11.1 Issue Prioritization

- [ ] **Critical Issues (P0)**: List all failures from audit
  - Timeline: 2 weeks
  - Action: Create GitHub issues with P0-critical label

- [ ] **High Priority (P1)**: List all warnings from audit
  - Timeline: 30 days
  - Action: Create GitHub issues with P1-high label

- [ ] **Medium Priority (P2)**: List improvement opportunities
  - Timeline: 90 days
  - Action: Create GitHub issues with P2-medium label

### 11.2 Migration Roadmap

- [ ] **Component Migration**: Create phased plan
  - Phase 1: Migrate high-usage components (2 weeks)
  - Phase 2: Migrate medium-usage components (4 weeks)
  - Phase 3: Migrate low-usage components (4 weeks)
  - Action: Assign owners, set milestones

- [ ] **Token Enforcement**: Create refactoring plan
  - Phase 1: Audit and document violations (1 week)
  - Phase 2: Refactor critical paths (2 weeks)
  - Phase 3: Refactor remaining code (4 weeks)
  - Action: Create tickets, assign to team

### 11.3 Documentation Updates

- [ ] **Update DESIGN_SYSTEM_INVARIANTS.md**: Document rules
  - Action: Create/update invariants document

- [ ] **Update Architecture Docs**: Reflect current state
  - Action: Update ARCHITECTURE.md with findings

- [ ] **Create Runbooks**: Document common issues
  - Action: Create troubleshooting guides

---

## Completion Checklist

- [ ] All sections completed
- [ ] Audit report generated
- [ ] Issues created in GitHub
- [ ] Remediation plan documented
- [ ] Team notified of findings
- [ ] Follow-up audit scheduled (quarterly)

---

## Notes

Use this space to document findings, observations, and action items during the investigation:

```
[Date] [Investigator] [Finding]
Example:
2025-11-02 CTO Found 55 local components in frontend-dashboard that could be migrated to shared-ui
```

---

**Last Updated**: 2025-11-02  
**Next Review**: 2026-02-02 (Quarterly)
