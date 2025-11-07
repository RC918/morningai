# UX Ops Pipeline Documentation

## Overview

The UX Ops Pipeline is a comprehensive CI/CD integration that enforces design system consistency, accessibility standards, internationalization coverage, and performance benchmarks across all frontend applications.

This pipeline implements a multi-phase approach with **Warning Mode** for data collection before enabling blocking enforcement.

## Architecture

### Pipeline Phases

1. **Phase 1**: Design Tokens Drift Check (BLOCKING)
2. **Phase 2**: AI Perceptual QA (WARNING MODE)
3. **Phase 3**: Objective UX Metrics (WARNING MODE) ← Current Phase

### Workflow Jobs

```yaml
jobs:
  smoke-tests          # Fast validation (BLOCKING)
  tokens-drift-check   # Design tokens consistency (BLOCKING)
  visual-regression-test  # VRT baseline comparison (WARNING)
  motion-performance-test # Animation performance (WARNING)
  accessibility-audit  # A11y violations (WARNING)
  i18n-coverage       # Translation coverage (WARNING)
  ai-perceptual-qa    # AI-powered UX analysis (WARNING)
  ux-quality-gate     # Final summary and decision
```

## Phase 3: Objective UX Metrics (Current)

**Status**: Warning Mode (Non-blocking)  
**Timeline**: 2025-11-07 to 2025-11-21 (2 weeks)  
**Decision Date**: 2025-11-21

### Implemented Checks

#### 1. i18n Coverage Check

**Purpose**: Ensure translation completeness across all supported locales.

**Implementation**:
- Script: `scripts/test-i18n.cjs`
- Primary locale: `en-US` (source of truth)
- Secondary locales: `zh-TW`
- Target coverage: ≥95%

**Directory Structure**:
- **frontend-dashboard**: `src/i18n/locales/`
- **owner-console**: `src/locales/`

**How to run locally**:
```bash
# Frontend Dashboard
cd handoff/20250928/40_App/frontend-dashboard
pnpm run test:i18n

# Owner Console
cd handoff/20250928/40_App/owner-console
pnpm run test:i18n
```

**Output**:
```json
{
  "timestamp": "2025-11-07T08:00:00.000Z",
  "passed": true,
  "results": {
    "primary": {
      "locale": "en-US",
      "totalKeys": 828
    },
    "secondary": [
      {
        "locale": "zh-TW",
        "totalKeys": 828,
        "coverage": 100,
        "missing": 0,
        "extra": 0,
        "passed": true
      }
    ]
  }
}
```

**Current Limitations**:
- Does not support ICU/pluralization format validation
- No dynamic key ignore list
- No per-namespace statistics
- Planned improvements in Week 4+

#### 2. Motion Performance Testing

**Purpose**: Ensure smooth animations and transitions.

**Metrics**:
- **P95 Frame Time**: ≤16.67ms (60 FPS)
- **Dropped Frames**: ≤1%

**Implementation**:
- Script: `scripts/test-motion.cjs`
- Uses Playwright with Chrome DevTools Protocol
- Measures frame timing during interactions

**How to run locally**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run build
pnpm run preview --port 4173 &
pnpm run test:motion
```

#### 3. Accessibility Audit

**Purpose**: Detect WCAG violations and ensure inclusive design.

**Metrics**:
- **Critical violations**: 0
- **Serious violations**: ≤2

**Implementation**:
- Script: `scripts/test-a11y.cjs`
- Uses axe-core for runtime testing
- ESLint jsx-a11y for static analysis

**How to run locally**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run build
pnpm run preview --port 4173 &
pnpm run test:a11y
```

#### 4. Visual Regression Testing (VRT)

**Purpose**: Detect unintended visual changes.

**Metrics**:
- **Mismatch threshold**: ≤0.1%
- **Flake rate**: <3%

**Implementation**:
- Uses Playwright's screenshot comparison
- Baseline stored in repository
- Pixel-by-pixel comparison

**How to run locally**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm run test:vrt
```

## Warning Mode Strategy

### Why Warning Mode?

All Phase 3 checks run in **non-blocking mode** during the initial 2-week period to:

1. **Collect baseline data** from real PRs
2. **Identify false positives** and adjust thresholds
3. **Validate check reliability** before enforcement
4. **Avoid blocking legitimate PRs** during calibration

### Warning Mode Implementation

All checks use `continue-on-error: true` in the workflow:

```yaml
- name: Run i18n coverage tests
  run: pnpm run test:i18n
  continue-on-error: true  # Non-blocking
```

### Exit Strategy

**Tracking Issue**: [Phase 3 Warning Mode Exit Strategy - Decision: 2025-11-21](https://github.com/RC918/morningai/issues/1172)

**Decision Timeline**:
- **Start**: 2025-11-07
- **Mid-point Review**: 2025-11-14 (1 week data)
- **Decision Meeting**: 2025-11-21
- **Implementation**: 2025-11-22+

**Success Criteria for Blocking Mode**:
- i18n coverage: ≥98% (based on 20+ PR data)
- A11y: Critical=0, Serious≤2
- Motion: P95<16.67ms, Dropped<1%
- VRT: Flake rate <3%

**Decision Options**:
- **Option A**: Enable blocking mode (all criteria met)
- **Option B**: Adjust thresholds and enable (data-driven adjustment)
- **Option C**: Extend observation period (insufficient data)
- **Option D**: Keep warning mode (checks unreliable)

## Thresholds and Baselines

### Current Baselines (as of 2025-11-07)

| Metric | frontend-dashboard | owner-console | Target |
|--------|-------------------|---------------|--------|
| i18n Coverage | 100% (828 keys) | 100% (266 keys) | ≥95% |
| A11y Critical | TBD | TBD | 0 |
| A11y Serious | TBD | TBD | ≤2 |
| Motion P95 | TBD | TBD | ≤16.67ms |
| Motion Dropped | TBD | TBD | ≤1% |
| VRT Mismatch | TBD | TBD | ≤0.1% |

### Threshold Adjustment Process

1. Collect data from 20+ PRs
2. Calculate P50, P95, P99 distributions
3. Identify outliers and false positives
4. Adjust thresholds to balance:
   - **Strictness**: Catch real issues
   - **Practicality**: Avoid blocking valid PRs
   - **Reliability**: <5% false positive rate

## Integration with AI Perceptual QA

Phase 3 complements the existing AI Perceptual QA (Phase 2):

### AI Perceptual QA (Phase 2)
- **Visual Harmony**: ≥76/100
- **Delight Index**: ≥90/100
- **Status**: Warning Mode
- **Scope**: Subjective design quality

### Objective UX Metrics (Phase 3)
- **i18n, A11y, Motion, VRT**
- **Status**: Warning Mode
- **Scope**: Objective technical quality

### Combined UX Quality Gate

The `ux-quality-gate` job aggregates all metrics:

```
📋 Phase 3 Warning Mode Summary (Week 3):
All UX checks are currently in WARNING MODE (non-blocking)

Objective Metrics (Informational):
  - Motion Performance: success
  - VRT: success
  - A11y: success
  - i18n: success

ℹ️  These checks collect data for 1-2 weeks before enabling blocking
ℹ️  Review artifacts for detailed metrics and recommendations
```

## Monitoring and Data Collection

### Week 3 Data Collection (2025-11-07 to 2025-11-21)

**Required Data**:
- At least 20 PRs with complete metrics
- All false positive/negative cases documented
- Threshold distribution analysis

**Monitoring Checklist**:
- [ ] i18n coverage distribution
- [ ] Missing key patterns (dynamic keys, ICU format)
- [ ] A11y violation types and frequency
- [ ] Motion performance across different pages
- [ ] VRT baseline stability and flake rate

### Accessing Results

**CI Artifacts**:
- `i18n-results-{app}`: i18n coverage reports
- `a11y-results-{app}`: Accessibility violation details
- `motion-results-{app}`: Frame timing data
- `vrt-results-{app}`: Visual diff screenshots

**Local Results**:
```bash
# i18n
cat handoff/20250928/40_App/frontend-dashboard/i18n-test-results/i18n-test-report.json

# A11y
cat handoff/20250928/40_App/frontend-dashboard/a11y-test-results/a11y-report.json

# Motion
cat handoff/20250928/40_App/frontend-dashboard/motion-test-results/motion.json
```

## Troubleshooting

### i18n Coverage Failures

**Issue**: Coverage below 95%

**Solutions**:
1. Check for missing translations in `src/i18n/locales/zh-TW.json`
2. Verify key structure matches `en-US.json`
3. Review dynamic keys (may need ignore list)

**Issue**: Extra keys in secondary locale

**Solutions**:
1. Remove unused keys from `zh-TW.json`
2. Add missing keys to `en-US.json` if needed

### A11y Violations

**Issue**: Critical violations detected

**Solutions**:
1. Review `a11y-report.json` for specific violations
2. Fix WCAG issues (missing alt text, ARIA labels, etc.)
3. Run `pnpm run lint` to catch jsx-a11y issues early

### Motion Performance Issues

**Issue**: P95 > 16.67ms

**Solutions**:
1. Profile animations with Chrome DevTools
2. Reduce animation complexity
3. Use CSS transforms instead of layout properties
4. Consider hardware acceleration

### VRT Flakiness

**Issue**: High false positive rate

**Solutions**:
1. Update baseline: `pnpm run test:vrt -- --update-snapshots`
2. Increase threshold temporarily
3. Investigate dynamic content (timestamps, random data)

## Future Improvements

### Week 4+ Enhancements

**i18n Script**:
- [ ] ICU/pluralization format support
- [ ] Dynamic key ignore list
- [ ] Per-namespace statistics
- [ ] Translation quality checks (empty strings, duplicates)

**UX Quality Gate**:
- [ ] Add specific metric values to summary
- [ ] Link to artifacts directly
- [ ] Trend analysis (compare with previous PRs)

**Documentation**:
- [ ] Add runbook for common failures
- [ ] Create video tutorials for local testing
- [ ] Document threshold adjustment methodology

### Long-term Goals

**Directory Structure Unification**:
- Consider standardizing locale paths across apps
- Current: `frontend-dashboard` uses `src/i18n/locales/`, `owner-console` uses `src/locales/`
- Target: Unified structure for consistency

**Advanced Metrics**:
- Web Vitals integration (LCP, FID, CLS)
- Bundle size tracking
- Lighthouse CI scores

## Related Documentation

- [AI Perceptual QA](./AI_PERCEPTUAL_QA.md) - Phase 2 implementation
- [Design System](../packages/shared-ui/README.md) - Tokens and components
- [Week 2 Calibration Report](../WEEK2_CALIBRATION_REPORT.md) - AI QA baseline

## References

- **PR #1171**: Phase 3 UX Pipeline Warning Mode
- **PR #1170**: Week 2/3 AI QA Threshold Adjustment
- **PR #1168**: Week 2 Calibration Report
- **Issue #1172**: Phase 3 Warning Mode Exit Strategy

---

**Last Updated**: 2025-11-07  
**Status**: Phase 3 Warning Mode Active  
**Next Review**: 2025-11-14 (Mid-point)  
**Decision Date**: 2025-11-21
