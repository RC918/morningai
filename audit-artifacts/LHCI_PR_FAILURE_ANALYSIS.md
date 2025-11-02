# LHCI-PR Failure Analysis

**Date**: 2025-11-02  
**PR**: #1041 (devin/1762085648-fix-design-system-violations)  
**Job ID**: 48954263948

## Executive Summary

The lhci-pr CI check failed with 7 failing assertions and 4 warnings across all 3 tested URLs (/, /login, /pricing). Analysis reveals two distinct categories of failures:

1. **Environment-induced failures**: CORS errors causing console errors (not related to PR changes)
2. **Genuine code issues**: Accessibility and performance problems requiring code fixes

**Verdict**: The failures are **NOT caused by this PR's changes** (audit script + React peerDependencies). However, they reveal pre-existing issues that should be addressed.

## Changes in This PR

- Modified `audit-design-system.sh` (bash script only)
- Modified `packages/shared-ui/package.json` (React peerDependencies: `^18.0.0 || ^19.0.0` → `^19.1.0`)

**Impact on LHCI**: None. These changes do not affect frontend code, bundle size, or page rendering.

## Detailed Failure Analysis

### URLs Tested
- `http://localhost:4173/` (homepage)
- `http://localhost:4173/login`
- `http://localhost:4173/pricing`

### Failing Assertions (7 total)

#### 1. **errors-in-console** ✗ CRITICAL
- **Score**: 0 (expected ≥0.9)
- **All values**: 0, 0, 0 (consistent across all runs)
- **Root Cause**: CORS errors from calling production backend

**Evidence from logs**:
```
[Browser error] Access to fetch at 'https://morningai-backend-v2.onrender.com/api/user/preferences' 
from origin 'http://localhost:4173' has been blocked by CORS policy: Response to preflight request 
doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the 
requested resource.

[Browser error] Access to fetch at 'https://morningai-backend-v2.onrender.com/api/auth/login' 
from origin 'http://localhost:4173' has been blocked by CORS policy
```

**Impact**: This single issue cascades to affect other metrics and creates noise in the audit.

#### 2. **button-name** ✗ ACCESSIBILITY
- **Score**: 0 (expected ≥0.9)
- **All values**: 0, 0, 0
- **Issue**: "Buttons do not have an accessible name"
- **Reference**: https://dequeuniversity.com/rules/axe/4.10/button-name

**Likely Causes**:
- Icon-only buttons without `aria-label` or `aria-labelledby`
- Common locations: header navigation, dark mode toggle, language switcher, mobile menu

#### 3. **heading-order** ✗ ACCESSIBILITY
- **Score**: 0 (expected ≥0.9)
- **All values**: 0, 0, 0
- **Issue**: "Heading elements are not in a sequentially-descending order"
- **Reference**: https://dequeuniversity.com/rules/axe/4.10/heading-order

**Likely Causes**:
- Missing h1 or multiple h1 elements
- Skipping heading levels (e.g., h1 → h3 without h2)
- Common in page templates/layouts

#### 4. **image-delivery-insight** ✗ PERFORMANCE
- **Score**: 0 (expected ≥0.9)
- **All values**: 0, 0, 0
- **Issue**: "Improve image delivery"
- **Reference**: https://developer.chrome.com/docs/lighthouse/performance/uses-optimized-images/

#### 5. **network-dependency-tree-insight** ✗ PERFORMANCE
- **Score**: 0 (expected ≥0.9)
- **All values**: 0, 0, 0
- **Issue**: "Network dependency tree"
- **Reference**: https://developer.chrome.com/docs/lighthouse/performance/critical-request-chains

#### 6. **unused-javascript** ✗ PERFORMANCE
- **Found**: 2 items (expected ≤0)
- **All values**: 2, 2, 2
- **Issue**: "Reduce unused JavaScript"
- **Reference**: https://developer.chrome.com/docs/lighthouse/performance/unused-javascript/

#### 7. **uses-responsive-images** ✗ PERFORMANCE
- **Found**: 1 item (expected ≤0)
- **All values**: 1, 1, 1
- **Issue**: "Properly size images"
- **Reference**: https://developer.chrome.com/docs/lighthouse/performance/uses-responsive-images/

### Warnings (4 total)

1. **legacy-javascript** ⚠️ - 1 item (expected ≤0)
2. **modern-image-formats** ⚠️ - 1 item (expected ≤0)
3. **render-blocking-insight** ⚠️ - 1 item (expected ≤0)
4. **render-blocking-resources** ⚠️ - 1 item (expected ≤0)

## Remediation Plan

### Priority 0: CI Environment Fix (Immediate)

**Problem**: CORS errors from calling production backend during LHCI tests

**Solutions** (choose one):
1. **Mock Backend** (Recommended):
   - Add a tiny mock server in CI that serves `/api/user/preferences` and `/api/auth/login` with 200 responses
   - Set `VITE_API_BASE_URL=http://127.0.0.1:5555` during LHCI runs
   - This eliminates console errors without changing thresholds

2. **Feature Flag**:
   - If the app already supports a CI/E2E mode, enable it to disable remote API calls
   - Check for existing `import.meta.env.VITE_*` flags

3. **Disable Prefetch**:
   - If the app has a flag to disable initial data fetching, use it during LHCI

**Estimated Time**: 2-3 hours

### Priority 1: Accessibility Fixes (High Impact)

#### Fix 1: Button Names (2-3 hours)
**Action**:
- Search for icon-only buttons: `grep -r "<button" --include="*.tsx" | grep -v "aria-label" | grep -v "children"`
- Add `aria-label` to all icon-only buttons
- Common locations:
  - Header navigation toggles
  - Dark mode toggle
  - Language switcher
  - Mobile menu button

**Example Fix**:
```tsx
// Before
<button onClick={toggleDarkMode}>
  <MoonIcon />
</button>

// After
<button onClick={toggleDarkMode} aria-label="Toggle dark mode">
  <MoonIcon />
</button>
```

#### Fix 2: Heading Order (1-2 hours)
**Action**:
- Audit page templates for heading hierarchy
- Ensure each page has exactly one h1
- Ensure logical progression (h1 → h2 → h3, no skipping)
- Check: HomePage.tsx, LoginPage.tsx, PricingPage.tsx

**Example Fix**:
```tsx
// Before
<div>
  <h3>Welcome</h3>  {/* Wrong: should be h1 */}
  <h2>Features</h2>
</div>

// After
<div>
  <h1>Welcome</h1>
  <h2>Features</h2>
</div>
```

### Priority 2: Performance Fixes (Medium Impact)

#### Fix 3: Responsive Images (1-2 hours)
**Action**:
- Identify large images on /, /login, /pricing
- Add `width`, `height`, `sizes`, and `srcset` attributes
- Consider converting to WebP/AVIF formats

#### Fix 4: Unused JavaScript (2-3 hours)
**Action**:
- Identify heavy libraries loaded on every page
- Implement lazy loading for route-specific code
- Use dynamic imports for non-critical features

**Example**:
```tsx
// Before
import HeavyChart from './HeavyChart';

// After
const HeavyChart = lazy(() => import('./HeavyChart'));
```

### Priority 3: Image Optimization (Low Impact)

- Convert images to next-gen formats (WebP/AVIF)
- Implement lazy loading for below-the-fold images
- Add proper caching headers

## Immediate Next Steps

1. **Re-run lhci-pr once** (per CTO merge conditions)
   - Command: Re-trigger the lhci-pr job in GitHub Actions
   - Purpose: Rule out transient failures

2. **If still failing**:
   - Create ticket with this analysis
   - Link to logs: `/audit-artifacts/LHCI_PR_FAILURE_ANALYSIS.md`
   - Proceed with P0 CI environment fix in parallel with P1 accessibility fixes

3. **Do NOT**:
   - Lower LHCI thresholds
   - Disable failing audits
   - Change CORS on production backend for CI

## Conclusion

The lhci-pr failure is **NOT caused by this PR's changes**. The failures reveal:
- 1 environment issue (CORS) that needs CI configuration
- 6 genuine code issues (accessibility + performance) that need code fixes

**Recommendation**: Merge this PR after re-running lhci-pr once, then address the genuine issues in follow-up PRs as outlined in the remediation plan above.

## References

- LHCI logs: `logs_48954263948.zip`
- Assertion failures: `lhci-pr/16_Assert Lighthouse CI budgets.txt`
- Console errors: `0_lhci-pr.txt` (lines with CORS errors)
- CTO merge conditions: See PR #1041 comments
