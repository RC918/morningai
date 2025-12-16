# AI Perceptual QA Calibration Report v1

**Date:** TBD (After collecting 20-30 PRs)  
**Status:** Template - Awaiting Data Collection  
**Calibration Period:** Week 1-2 of Phase 2 v2

---

## Executive Summary

[To be filled after data collection]

- **Dataset Size:** X PRs (Y good, Z bad)
- **Current Thresholds:** Harmony ≥70, Delight ≥75
- **Recommended Thresholds:** TBD
- **False Block Rate:** TBD% (target: ≤5-10%)
- **Detection Rate:** TBD% (target: ≥80%)

---

## 1. Dataset Overview

### 1.1 Data Collection Summary

| Metric | Count |
|--------|-------|
| Total PRs Analyzed | TBD |
| Good UX PRs (ai-calibration-good) | TBD |
| Bad UX PRs (ai-calibration-bad) | TBD |
| Total Pages Scored | TBD |
| Prompt Version | v0.1 |
| Model | gpt-4o-mini |

### 1.2 PR Distribution

[Insert table or chart showing PR distribution by label, app, and outcome]

---

## 2. Score Distribution Analysis

### 2.1 Visual Harmony Scores

| Percentile | Score |
|------------|-------|
| P10 | TBD |
| P25 | TBD |
| P50 (Median) | TBD |
| P75 | TBD |
| P90 | TBD |
| Mean | TBD |
| Std Dev | TBD |

**Observations:**
- [Describe score distribution patterns]
- [Note any outliers or unexpected results]

### 2.2 Delight Index Scores

| Percentile | Score |
|------------|-------|
| P10 | TBD |
| P25 | TBD |
| P50 (Median) | TBD |
| P75 | TBD |
| P90 | TBD |
| Mean | TBD |
| Std Dev | TBD |

**Observations:**
- [Describe delight score patterns]
- [Compare with harmony scores]

---

## 3. Threshold Performance Analysis

### 3.1 Current Thresholds (Harmony ≥70, Delight ≥75)

**Confusion Matrix:**

|  | Predicted Pass | Predicted Fail |
|---|----------------|----------------|
| **Actual Good** | TP: TBD | FP: TBD |
| **Actual Bad** | FN: TBD | TN: TBD |

**Metrics:**
- **False Block Rate:** TBD% (FP / (TP + FP))
- **Detection Rate:** TBD% (TN / (TN + FN))
- **Precision:** TBD%
- **Recall:** TBD%

### 3.2 Threshold Optimization

[Insert ROC curve or threshold sweep analysis]

**Recommended Thresholds:**
- **Harmony Minimum:** TBD (current: 70)
- **Harmony Critical:** TBD (new, absolute minimum)
- **Delight Minimum:** TBD (current: 75)
- **Delight Critical:** TBD (new, absolute minimum)

**Rationale:**
- [Explain why these thresholds were chosen]
- [Show trade-offs between false positives and false negatives]

---

## 4. Dimension-Level Analysis

### 4.1 Harmony Dimensions

| Dimension | Mean | Std Dev | Most Variable | Notes |
|-----------|------|---------|---------------|-------|
| Color | TBD | TBD | TBD | [Observations] |
| Spacing | TBD | TBD | TBD | [Observations] |
| Typography | TBD | TBD | TBD | [Observations] |
| Alignment | TBD | TBD | TBD | [Observations] |
| Contrast | TBD | TBD | TBD | [Observations] |

**Insights:**
- [Which dimensions are most predictive of overall quality?]
- [Which dimensions have highest variance?]
- [Should dimension weights be adjusted?]

---

## 5. False Positive Analysis

### 5.1 Good PRs That Failed AI QA

[List PRs labeled "ai-calibration-good" that scored below threshold]

| PR # | Harmony | Delight | Why It Failed | Root Cause |
|------|---------|---------|---------------|------------|
| TBD | TBD | TBD | [Description] | [AI misunderstanding / Edge case / Actual issue] |

**Patterns:**
- [Common reasons for false positives]
- [Prompt improvements needed]

### 5.2 Mitigation Strategies

- [Prompt refinements for v0.2]
- [Additional context needed]
- [Edge cases to handle]

---

## 6. False Negative Analysis

### 6.1 Bad PRs That Passed AI QA

[List PRs labeled "ai-calibration-bad" that scored above threshold]

| PR # | Harmony | Delight | Issue Type | Why It Passed |
|------|---------|---------|------------|---------------|
| TBD | TBD | TBD | [e.g., Low contrast] | [AI didn't detect / Threshold too lenient] |

**Patterns:**
- [Common reasons for false negatives]
- [Threshold adjustments needed]

### 6.2 Mitigation Strategies

- [Lower thresholds for critical issues]
- [Add dimension-specific minimums]
- [Improve prompt specificity]

---

## 7. Prompt Version Comparison (v0.1 vs v0.2)

[If v0.2 A/B testing was conducted]

| Metric | v0.1 | v0.2 | Change |
|--------|------|------|--------|
| False Block Rate | TBD% | TBD% | TBD% |
| Detection Rate | TBD% | TBD% | TBD% |
| Findings Specificity | TBD | TBD | TBD |
| Avg Tokens Used | TBD | TBD | TBD |

**Recommendation:**
- [Which prompt version to use going forward]
- [Key improvements in v0.2]

---

## 8. Blocking Rules Recommendation

### 8.1 Proposed Blocking Logic

```javascript
// Phase 2 v2 Blocking Rules
const shouldBlock = (report) => {
  // Skip if bypass label present
  if (report.labels.includes('ai-qa-bypass')) {
    return false;
  }

  // Critical threshold (absolute minimum)
  if (report.harmony.overall < HARMONY_CRITICAL) {
    return true;
  }

  // Standard threshold with confidence check
  if (report.harmony.overall < HARMONY_MIN && report.confidence > 0.8) {
    return true;
  }

  // Delight threshold
  if (report.delight.index < DELIGHT_MIN) {
    return true;
  }

  return false;
};
```

### 8.2 Environment Variables

```bash
# Recommended settings for Phase 2 v2
UX_AI_BLOCKING_ENABLE=false  # Start with opt-in only
UX_HARMONY_MIN=TBD           # Tuned threshold
UX_HARMONY_CRITICAL=TBD      # Absolute minimum
UX_DELIGHT_MIN=TBD           # Tuned threshold
UX_DELIGHT_CRITICAL=TBD      # Absolute minimum
```

### 8.3 Rollout Plan

**Week 3: Opt-in Testing**
- Set `UX_AI_BLOCKING_ENABLE=true` only for PRs with `ai-qa-blocking-optin` label
- Monitor false block rate in production
- Collect team feedback

**Week 4: Full Rollout (If Week 3 Successful)**
- Remove opt-in requirement
- All PRs subject to AI QA blocking
- Keep `ai-qa-bypass` label for emergencies

---

## 9. Findings Quality Analysis

### 9.1 Findings Usefulness

[Analyze the quality and specificity of AI-generated findings]

**Sample Findings:**
- [Good example: Specific, actionable]
- [Bad example: Vague, not actionable]

**Improvements Needed:**
- [How to make findings more specific]
- [Additional context to provide]

---

## 10. Recommendations

### 10.1 Immediate Actions

1. **Update Thresholds:**
   - Harmony: TBD → TBD
   - Delight: TBD → TBD

2. **Deploy Prompt v0.2:**
   - [Key changes]
   - [Expected improvements]

3. **Enable Opt-in Blocking:**
   - Start with design team PRs
   - Monitor for 1 week

### 10.2 Future Improvements

1. **Dimension-Specific Thresholds:**
   - Critical dimensions (e.g., contrast) should have higher minimums
   - Less critical dimensions can be more lenient

2. **Page-Type Specific Thresholds:**
   - Landing pages: Higher standards
   - Admin pages: More lenient

3. **Confidence Scoring:**
   - Add confidence metric to AI output
   - Only block on high-confidence failures

4. **Continuous Calibration:**
   - Re-calibrate quarterly
   - Track threshold drift over time

---

## 11. Risks and Mitigation

### 11.1 Identified Risks

1. **False Blocks Slow Development:**
   - Mitigation: Keep `ai-qa-bypass` label, monitor usage
   - Mitigation: Tune thresholds conservatively

2. **Team Loses Trust in AI QA:**
   - Mitigation: Transparent calibration process
   - Mitigation: Quick response to false positives

3. **Threshold Drift Over Time:**
   - Mitigation: Quarterly re-calibration
   - Mitigation: Track metrics in dashboard

### 11.2 Rollback Plan

If false block rate exceeds 15% in Week 3:
1. Immediately disable blocking mode
2. Re-analyze calibration data
3. Adjust thresholds more conservatively
4. Re-test with smaller opt-in group

---

## 12. Appendix

### 12.1 Calibration Data Files

- `calibration.csv`: Raw calibration data
- `CALIBRATION_TRACKER.md`: PR-level tracking
- `prompts/ux_vision_v0.1.json`: Prompt used for calibration

### 12.2 Analysis Scripts

[Link to any Python/R scripts used for analysis]

### 12.3 Team Feedback

[Collect feedback from designers and developers during opt-in period]

---

**Report Generated:** TBD  
**Next Review:** TBD (After Week 3 opt-in testing)
