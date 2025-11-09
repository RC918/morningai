# Week 1 Calibration Data Collection Tracker

**Period**: November 2025  
**Purpose**: Collect calibration data for AI Perceptual QA threshold tuning  
**Target**: 8-10 bad case PRs with isolated UX issues

---

## 📊 Progress Summary

- **Total PRs Created**: 0 / 10
- **PRs with Data Collected**: 0 / 10
- **Average Harmony Score**: TBD
- **Pass/Fail Ratio**: TBD

---

## 📝 Bad Case PR Tracking

| PR # | Type | Page/Component | Labels | Harmony Score | Delight Score | Decision | Deploy URL | Status | Notes |
|------|------|----------------|--------|---------------|---------------|----------|------------|--------|-------|
| TBD | WCAG Contrast | Dashboard | ai-calibration-bad, ux-wcag-contrast | TBD | TBD | TBD | TBD | Pending | Secondary text color |
| TBD | Spacing | Dashboard Cards | ai-calibration-bad, ux-spacing | TBD | TBD | TBD | TBD | Pending | Card gap 17px |
| TBD | Typography | Settings/Form | ai-calibration-bad, ux-typography | TBD | TBD | TBD | TBD | Pending | H2 same size as body |
| TBD | Alignment | Login Form | ai-calibration-bad, ux-alignment | TBD | TBD | TBD | TBD | Pending | Form field offset |
| TBD | Focus Visible | Login Form | ai-calibration-bad, ux-focus-visible, ux-keyboard-nav | TBD | TBD | TBD | TBD | Pending | Removed focus outline |
| TBD | Touch Target | Mobile Nav | ai-calibration-bad, ux-touch-target | TBD | TBD | TBD | TBD | Pending | Icon button 32x32px |
| TBD | Content Overflow | Dashboard Cards | ai-calibration-bad, ux-content-overflow | TBD | TBD | TBD | TBD | Pending | Fixed width no ellipsis |
| TBD | Motion A11y | Dashboard/Modal | ai-calibration-bad, ux-motion-a11y | TBD | TBD | TBD | TBD | Pending | Removed prefers-reduced-motion |
| TBD | Dismissable | Toast | ai-calibration-bad, ux-dismissable, ux-keyboard-nav | TBD | TBD | TBD | TBD | Pending | No close button |
| TBD | Visual Hierarchy | Login/Register | ai-calibration-bad, ux-alignment | TBD | TBD | TBD | TBD | Pending | CTA less prominent |

---

## 🎯 Success Criteria

- [x] All 10 GitHub labels created
- [ ] 8-10 bad case PRs created
- [ ] Each PR triggers UX Pipeline successfully
- [ ] Calibration data collected for each PR
- [ ] At least 5 different pages/components covered
- [ ] At least 8 different UX issue types covered
- [ ] Most Harmony Scores < 70
- [ ] Most Decisions = "fail"

---

## 📈 Data Analysis (Week 2)

### Harmony Score Distribution
- **< 50**: 0 PRs
- **50-69**: 0 PRs
- **70-79**: 0 PRs
- **80-89**: 0 PRs
- **90-100**: 0 PRs

### Decision Distribution
- **Pass**: 0 PRs
- **Fail**: 0 PRs

### False Negatives (Score > 70 despite bad UX)
- TBD

### False Positives (Score < 70 despite good UX)
- N/A (no good case PRs in Week 1)

---

## 🔍 Observations & Insights

### What AI Detected Well
- TBD

### What AI Missed
- TBD

### Threshold Recommendations for Week 2
- **Current Harmony Threshold**: 70
- **Recommended Adjustment**: TBD based on data

---

## 📅 Timeline

- **Day 1-2** (Nov 6-7): Labels created ✅ + First 3 PRs
- **Day 3-4** (Nov 8-9): Middle 3-4 PRs
- **Day 5** (Nov 10): Last 2-3 PRs
- **Day 6-7** (Nov 11-12): Data collection & analysis

---

## ⚠️ Important Notes

1. **DO NOT MERGE** these PRs - they are for calibration only
2. Each PR should contain **only one** UX issue for clear attribution
3. Download `calibration-csv-[app]` artifact from each PR's Actions
4. Record Harmony Score and Decision for each PR
5. Close PRs after data collection with note "Calibration completed"

---

## 🆘 Issues Encountered

### CI/Pipeline Issues
- None yet

### Unexpected Results
- None yet

### Blockers
- None yet

---

**Last Updated**: 2025-11-06  
**Updated By**: Devin AI  
**Status**: In Progress - Labels Created ✅
