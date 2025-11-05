# UX Ops Pipeline Gating Timeline

## Overview

This document outlines the timeline for transitioning UX quality checks from **informational** (continue-on-error) to **gating** (blocking PR merges) status.

**Current Status:** Week 1 (November 5, 2025)  
**Target:** Full gating by Week 2 (November 12, 2025)

---

## Phase 1: Informational Mode (Week 1 - Current)

**Status:** ✅ ACTIVE

All UX checks run but do NOT block PR merges (`continue-on-error: true`):

### Active Checks
1. **Design Tokens Drift Check** - ⚠️ **ALREADY GATING** (critical)
   - Status: BLOCKING
   - Rationale: Prevents visual inconsistency across apps
   
2. **Visual Regression Testing (VRT)**
   - Status: Informational
   - Runs: Playwright VRT tests
   - Artifacts: Screenshots uploaded for manual review
   
3. **Motion Performance Testing**
   - Status: Informational  
   - Metrics: FPS, frame drops, P95 latency
   - Thresholds: 60 FPS, <1% drops, <16.67ms P95
   
4. **Accessibility Audit**
   - Status: Informational
   - Tools: ESLint jsx-a11y + axe-core runtime tests
   - Checks: WCAG 2.1 AA compliance

### Goals for Week 1
- ✅ Establish baseline metrics for all checks
- ✅ Fix critical bugs (motion test infinite loop)
- ✅ Add preview server startup in CI
- ✅ Integrate axe-core automated testing
- ⏳ Monitor false positive rates
- ⏳ Collect team feedback on check reliability

---

## Phase 2: Selective Gating (Week 2 - Target: Nov 12)

**Status:** 🎯 PLANNED

Transition checks to gating based on stability and team readiness.

### Gating Criteria

A check becomes gating when:
1. **False positive rate < 5%** (measured over 20+ PR runs)
2. **Clear remediation paths** documented for all failure modes
3. **Team consensus** on thresholds and exceptions
4. **Escape hatches** available (e.g., `[skip-ux-checks]` in commit message)

### Proposed Gating Schedule

#### Week 2 Day 1-2 (Nov 12-13): Motion Performance
- **Change:** Remove `continue-on-error: true` from motion tests
- **Rationale:** 
  - Fixed infinite loop bug
  - Preview servers now start correctly in CI
  - Clear thresholds (60 FPS, <1% drops)
- **Escape Hatch:** `[skip-motion]` in PR title
- **Rollback Plan:** Re-enable `continue-on-error` if >10% false positives

#### Week 2 Day 3-4 (Nov 14-15): Accessibility (Critical/Serious only)
- **Change:** Fail PR if axe-core finds **critical** or **serious** violations
- **Rationale:**
  - WCAG 2.1 AA is legal requirement
  - Critical/serious violations are objective (not subjective)
- **Escape Hatch:** `[skip-a11y]` with justification in PR description
- **Rollback Plan:** Downgrade to moderate+ if team velocity drops >20%

#### Week 2 Day 5 (Nov 15): Visual Regression (High-confidence only)
- **Change:** Fail PR if VRT mismatch rate > 1% AND manual review confirms regression
- **Rationale:**
  - Requires manual review step (not fully automated)
  - High mismatch rate indicates likely real issue
- **Escape Hatch:** Manual override by reviewer
- **Rollback Plan:** Increase threshold to 5% if too many false positives

---

## Phase 3: Full Gating (Week 3+)

**Status:** 📅 FUTURE

All checks become fully gating with refined thresholds.

### Week 3 Goals
- Remove all escape hatches except for emergency deploys
- Lower VRT mismatch threshold to 0.5%
- Add moderate a11y violations to gating criteria
- Introduce Delight Index checks (if AI Perceptual QA is ready)

### Week 4+ Goals
- Integrate UX metrics into team KPIs
- Add pre-commit hooks for local UX checks
- Expand motion tests to cover more user flows
- Add performance budgets (LCP, INP, CLS)

---

## Escape Hatches & Overrides

### Commit Message Flags

Use these in PR title or commit message to skip specific checks:

- `[skip-ux-checks]` - Skip ALL UX checks (emergency only)
- `[skip-motion]` - Skip motion performance tests
- `[skip-a11y]` - Skip accessibility tests (requires justification)
- `[skip-vrt]` - Skip visual regression tests

**Example:**
```
feat: add new dashboard widget [skip-vrt]

VRT skipped because this is a new component with no baseline screenshots yet.
Will add VRT baseline in follow-up PR.
```

---

**Last Updated:** November 5, 2025  
**Owner:** UI/UX Strategy Director (Devin)  
**Next Review:** November 12, 2025
