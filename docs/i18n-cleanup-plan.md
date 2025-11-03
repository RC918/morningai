# i18n Violation Cleanup Plan (30/60/90 Days)

## Executive Summary

**Current Status** (2025-11-03):
- **frontend-dashboard**: 0 violations ✅
- **owner-console**: 97 violations
- **Total**: 97 violations

**Goal**: Reduce to 0 violations within 90 days

**Strategy**: Violation baseline mechanism (Option A) - prevents new violations while allowing gradual cleanup

## Baseline Information

- **Baseline Commit**: `11c65e6a63fe9feb20991d27307cab792c1c0148`
- **Baseline Date**: 2025-11-03T13:06:34Z
- **Baseline File**: `scripts/i18n-baseline.json`

## Top Offending Files (owner-console)

| File | Violations | Priority |
|------|-----------|----------|
| `src/components/MetricsDashboard.tsx` | 23 | P0 - High traffic |
| `src/components/2fa/TwoFAStatusCard.jsx` | 15 | P1 - User-facing |
| `src/components/2fa/TwoFASetupWizard.jsx` | 11 | P1 - User-facing |
| `src/components/2fa/BackupCodesList.jsx` | 8 | P1 - User-facing |
| `src/components/2fa/DisableTwoFAModal.jsx` | 8 | P1 - User-facing |
| `src/components/2fa/QRCodeDisplay.jsx` | 7 | P1 - User-facing |
| `src/components/2fa/RegenerateBackupCodesModal.jsx` | 6 | P2 - Modal |
| `src/components/PWAInstallPrompt.tsx` | 6 | P2 - Optional feature |

## 30-Day Plan (Target: 50% reduction → 48 violations)

**Goal**: Reduce from 97 to 48 violations (49 violations fixed)

**Week 1-2** (Target: 25 violations fixed):
- [ ] Fix `MetricsDashboard.tsx` (23 violations) - P0 priority
  - Extract all hardcoded strings to translation keys
  - Add keys to `en-US.json` and `zh-TW.json`
  - Test dashboard rendering with both locales
- [ ] Fix `PWAInstallPrompt.tsx` (6 violations) - Low risk, quick win
  - Simple component with minimal strings

**Week 3-4** (Target: 24 violations fixed):
- [ ] Fix 2FA components (total 55 violations, target 24):
  - `TwoFAStatusCard.jsx` (15 violations)
  - `TwoFASetupWizard.jsx` (11 violations) - partial
  
**Deliverables**:
- Updated `scripts/i18n-baseline.json` with new count: 48
- PR with all fixes
- Verification that all fixed components render correctly in both locales

**Owner**: Frontend Team Lead
**Review Cadence**: Weekly standup progress check

## 60-Day Plan (Target: 80% reduction → 19 violations)

**Goal**: Reduce from 48 to 19 violations (29 violations fixed)

**Week 5-6** (Target: 15 violations fixed):
- [ ] Complete remaining 2FA components:
  - Finish `TwoFASetupWizard.jsx` (remaining violations)
  - `BackupCodesList.jsx` (8 violations)
  - `DisableTwoFAModal.jsx` (8 violations) - partial

**Week 7-8** (Target: 14 violations fixed):
- [ ] Fix remaining 2FA and misc components:
  - Complete `DisableTwoFAModal.jsx`
  - `QRCodeDisplay.jsx` (7 violations)
  - `RegenerateBackupCodesModal.jsx` (6 violations)
  - Other small components

**Deliverables**:
- Updated `scripts/i18n-baseline.json` with new count: 19
- Complete 2FA flow tested in both locales
- PR with all fixes

**Owner**: Frontend Team
**Review Cadence**: Bi-weekly progress review

## 90-Day Plan (Target: 100% → 0 violations)

**Goal**: Reduce from 19 to 0 violations (19 violations fixed)

**Week 9-10** (Target: 10 violations fixed):
- [ ] Fix remaining components in order of user visibility
- [ ] Add comprehensive i18n tests to prevent regressions

**Week 11-12** (Target: 9 violations fixed):
- [ ] Fix final remaining violations
- [ ] Update `scripts/i18n-baseline.json` to 0 violations
- [ ] Remove any temporary ESLint overrides
- [ ] Document i18n best practices in team wiki

**Final Deliverables**:
- ✅ 0 i18n violations across all apps
- ✅ Comprehensive translation coverage (en-US, zh-TW)
- ✅ i18n testing suite
- ✅ Team training on i18n best practices
- ✅ Updated baseline: `{"frontend-dashboard": 0, "owner-console": 0}`

**Owner**: Frontend Team Lead + CTO Review
**Final Review**: End of Week 12

## Enforcement Mechanisms

### Pre-commit Hook
- Runs `eslint --fix --quiet` on staged files
- Blocks commits with i18n violations (errors)
- Configured in `.husky/pre-commit`

### CI Baseline Check
- Runs on every PR
- Fails if violation count exceeds baseline
- Job: `i18n-baseline-check` in `.github/workflows/frontend.yml`
- Script: `scripts/check-i18n-baseline.js`

### Baseline Updates
When violations are reduced:
1. Run `node scripts/check-i18n-baseline.js` to verify improvement
2. Update `scripts/i18n-baseline.json` with new counts
3. Commit baseline update with PR
4. Celebrate the progress! 🎉

## Progress Tracking

### Metrics Dashboard
Track progress in weekly standups:
- Current violation count vs baseline
- Violations fixed this week
- % progress toward 90-day goal
- Top remaining offending files

### Success Criteria
- [ ] 30-day: ≤ 48 violations (50% reduction)
- [ ] 60-day: ≤ 19 violations (80% reduction)
- [ ] 90-day: 0 violations (100% complete)
- [ ] All user-facing strings translated
- [ ] Both locales (en-US, zh-TW) fully functional
- [ ] No new violations introduced (enforced by CI)

## Risk Mitigation

### Risk: Breaking existing functionality
**Mitigation**: 
- Test each component after i18n fixes
- Use Storybook to verify UI rendering
- Run E2E tests for critical flows

### Risk: Missing translation keys
**Mitigation**:
- Use fallback to English if key missing
- Add comprehensive translation coverage
- Review translations with native speakers

### Risk: Team velocity impact
**Mitigation**:
- Spread work across 90 days
- Prioritize high-traffic components first
- Pair junior devs with senior for i18n training

## Resources

- **i18n Documentation**: `CONTRIBUTING.md` - i18n 國際化規範
- **Baseline Script**: `scripts/check-i18n-baseline.js`
- **Baseline Data**: `scripts/i18n-baseline.json`
- **Translation Files**: 
  - `handoff/20250928/40_App/owner-console/src/i18n/locales/en-US.json`
  - `handoff/20250928/40_App/owner-console/src/i18n/locales/zh-TW.json`

## Contact

**Questions or Issues?**
- Frontend Team Lead: Review in weekly standup
- CTO: Final review and approval at 90-day milestone
- Slack: #frontend-i18n channel

---

**Last Updated**: 2025-11-03  
**Next Review**: 2025-11-10 (Week 1 checkpoint)
