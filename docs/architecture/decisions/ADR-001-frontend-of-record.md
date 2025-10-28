# ADR-001: Frontend-of-Record Decision

**Status**: Proposed  
**Date**: 2025-10-28  
**Decision Maker**: CTO  
**Stakeholders**: Engineering Team, Product, DevOps

---

## Context

The MorningAI repository contains two frontend applications with similar structure but unclear production designation:

1. **`handoff/20250928/40_App/frontend-dashboard/`**
   - Referenced in `vercel.json:4-6` as build target
   - Full production dependencies (React 19, Supabase, Sentry, i18n)
   - Contains Storybook configuration
   - Has comprehensive testing (Vitest, Playwright)

2. **`frontend-dashboard-deploy/`**
   - Similar package.json structure
   - Focused on Storybook and Lighthouse CI (package.json:11-19)
   - Uses pnpm@10.4.1 (vs 9.15.1 in root)
   - Contains LHCI scripts and visual regression testing

**Evidence**:
- `vercel.json` buildCommand: `pnpm --filter frontend-dashboard build`
- `vercel.json` outputDirectory: `handoff/20250928/40_App/frontend-dashboard/dist`
- Both directories have similar component structures
- No clear documentation distinguishing their purposes

**Problem**:
- Deployment confusion: Which frontend should be deployed to production?
- Maintenance overhead: Two similar codebases require duplicate effort
- Risk: Wrong build target could be deployed
- Team clarity: New developers don't know which to modify

---

## Decision

**We designate `handoff/20250928/40_App/frontend-dashboard/` as the production frontend-of-record.**

**`frontend-dashboard-deploy/` is designated for Storybook development and Lighthouse CI only.**

---

## Rationale

### Evidence Supporting This Decision:

1. **Vercel Configuration** (`vercel.json:4-6`):
   ```json
   "buildCommand": "pnpm --filter frontend-dashboard build",
   "outputDirectory": "handoff/20250928/40_App/frontend-dashboard/dist"
   ```
   - Vercel explicitly targets `frontend-dashboard` for production builds
   - This is the current production deployment configuration

2. **Dependency Completeness**:
   - `frontend-dashboard` has full production stack:
     - Supabase 2.76.1 (authentication/database)
     - Sentry 10.17.0 (error tracking)
     - i18next 25.6.0 + Tolgee 6.2.7 (internationalization)
     - Recharts 2.15.3 (data visualization)
   - `frontend-dashboard-deploy` lacks Supabase and some production dependencies

3. **Package Scripts Analysis**:
   - `frontend-dashboard-deploy/package.json:11-19`:
     ```json
     "lhci": "lhci autorun --rc=../lighthouserc.json",
     "storybook": "storybook dev -p 6006",
     "build-storybook": "storybook build"
     ```
   - Scripts are focused on Storybook and LHCI, not production deployment

4. **Directory Naming Convention**:
   - `handoff/20250928/40_App/` follows the phase-based handoff structure
   - `frontend-dashboard-deploy/` at root level suggests tooling/CI purpose

### Alternative Considered:

**Option B: Use `frontend-dashboard-deploy` as production**
- Rejected because:
  - Vercel config would need to be changed
  - Missing critical production dependencies (Supabase)
  - Name suggests deployment tooling, not application code
  - Would require significant refactoring

---

## Consequences

### Positive:

1. **Clarity**: Single source of truth for production frontend code
2. **Reduced Risk**: CI checks will verify correct build target
3. **Maintenance**: Focus development effort on one codebase
4. **Onboarding**: New developers have clear guidance

### Negative:

1. **Storybook Duplication**: Both directories have Storybook configs
   - Mitigation: Document that `frontend-dashboard-deploy` is for Storybook development only
   
2. **pnpm Version Mismatch**: `frontend-dashboard-deploy` uses pnpm@10.4.1
   - Mitigation: Separate RFC to standardize pnpm version (see ADR-004 proposal)

### Action Items:

1. **Documentation** (Week 1):
   - Add `frontend-dashboard-deploy/README.md`:
     ```markdown
     # Frontend Dashboard Deploy
     
     **Purpose**: Storybook development and Lighthouse CI only.
     **Production Build**: Uses `handoff/20250928/40_App/frontend-dashboard/`
     
     This directory is for:
     - Storybook component development
     - Lighthouse CI performance testing
     - Visual regression testing
     
     DO NOT use this for production code changes.
     ```

2. **CI Verification** (Week 1):
   - Create `.github/workflows/verify-frontend-target.yml`:
     ```yaml
     name: Verify Frontend Build Target
     on: [push, pull_request]
     jobs:
       verify:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - name: Verify vercel.json points to production frontend
             run: |
               if ! grep -q "handoff/20250928/40_App/frontend-dashboard" vercel.json; then
                 echo "❌ ERROR: vercel.json does not point to production frontend"
                 exit 1
               fi
               echo "✅ Vercel config correctly points to production frontend"
     ```

3. **Team Communication** (Week 1):
   - Announce decision in team sync
   - Update CONTRIBUTING.md with frontend guidelines
   - Add to Architecture README (when created)

4. **Future Consolidation** (Month 2-3):
   - Consider moving Storybook config to production frontend
   - Evaluate if `frontend-dashboard-deploy` can be removed entirely
   - Standardize pnpm version across monorepo

---

## Compliance

This decision aligns with:
- **CTO Responsibility 1**: Technical Strategy & Architecture (clarity on tech stack)
- **CTO Responsibility 2**: Engineering Management (clear development standards)
- **Risk Mitigation**: Addresses ARCH-001 in Risk Register (HIGH priority)

---

## References

- `vercel.json:4-6` - Production build configuration
- `handoff/20250928/40_App/frontend-dashboard/package.json` - Production dependencies
- `frontend-dashboard-deploy/package.json:11-19` - Storybook/LHCI scripts
- CTO Technical Assessment Report (2025-10-28) - Section on Frontend Ambiguity

---

## Approval

- [ ] CTO Review
- [ ] Engineering Lead Review
- [ ] CEO Approval
- [ ] Documented in team wiki

**Target Approval Date**: 2025-10-30  
**Implementation Start**: Upon approval  
**Review Date**: 2025-11-30 (reassess if issues arise)
