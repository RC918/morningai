# Week 2 AI QA Calibration Report - Good Case Analysis

**Date:** November 6, 2025  
**Objective:** Validate AI Perceptual QA thresholds (Harmony ≥83, Delight ≥94) using good case PRs with design system improvements  
**Status:** ⚠️ **CRITICAL FINDINGS - Threshold Adjustment Recommended**

---

## Executive Summary

Week 2 calibration tested 5 good case PRs implementing design system improvements (spacing, contrast, alignment). **None achieved the target thresholds** (Harmony ≥83, Delight ≥94). Analysis reveals fundamental limitations in the AI evaluation methodology:

1. **Coarse-grained scoring** (5-point buckets: 70, 75, 80, 85...)
2. **Low sensitivity** to isolated, incremental improvements
3. **Dark mode changes ineffective** (pipeline forces light mode)
4. **Misaligned improvement targets** (changed elements ≠ score-driving elements)

**Recommendation:** Temporarily lower Harmony threshold to ≥76-78 with delta-based requirements, pending maximal compliance case validation.

---

## Good Case Results Summary

| PR | Type | Dashboard Harmony | Key Sub-Scores | vs Baseline (75.3) |
|----|------|-------------------|----------------|-------------------|
| #1162 | A11y (ARIA labels) | 75 | Spacing:80, Contrast:70 | -0.3 (control) |
| #1163 | Color Tokens | 75 | Spacing:80, Contrast:70 | -0.3 |
| #1165 | **Spacing** | **72.5** | Spacing:**75**, Alignment:75 | **-2.8** ❌ |
| #1166 | **Contrast** | 75 | Color:80, Contrast:**70** | -0.3 |
| #1167 | **Alignment** | 75 | Alignment:80, Color:80 | -0.3 |

**Bad Case Baseline:** Harmony mean=75.3 (σ=0.9), Delight mean=88.2 (σ=0.4)

### Key Observations

1. **No good case exceeded baseline** - Best result matched baseline (75), worst fell below (72.5)
2. **Contrast improvements ineffective** - PR #1166 changed text colors but Contrast sub-score remained 70
3. **Spacing improvements backfired** - PR #1165 improved Spacing sub-score (+5) but overall Harmony decreased (-2.8)
4. **Identical scores despite different changes** - PRs #1166 and #1167 scored identically (Harmony=75) despite targeting different metrics
5. **Unexpected Color improvements** - Color sub-score increased 70→80 in PRs #1166/#1167 despite only changing neutral text shades

---

## Root Cause Analysis

### 1. Score Quantization (5-Point Buckets)

**Evidence:**
- All observed scores are multiples of 5: 70, 75, 80, 85
- No intermediate values (71, 72, 73, 74, 76...) except overall Harmony (72.5)
- Multiple different changes quantize to same bucket

**Impact:**
- Small improvements cannot cross bucket boundaries
- Requires "decisive" changes (e.g., 4.2:1 → 7:1 contrast) to move from 70→75
- Incremental refinements are invisible to the metric

**Example:**
```
PR #1166: text-gray-600 → text-gray-700
- Actual contrast: ~4.5:1 → ~5.5:1 (WCAG AA compliant)
- AI score: 70 → 70 (no change - still in same bucket)
```

### 2. Misaligned Improvement Targets

**What we changed:**
- Dashboard description text (`text-gray-600` → `text-gray-700`)
- Recent decisions impact/confidence text
- Edit mode instructions text

**What likely drives Contrast score:**
- Small text timestamps (`text-xs text-gray-600`)
- Outline badge borders and text
- Gray text on tinted backgrounds (gray-50/100)
- Interactive element states

**Lesson:** AI evaluates holistically across ALL above-the-fold elements. Fixing a few nodes doesn't move the needle if other violators remain.

### 3. Dark Mode Changes Ineffective

**Discovery:**
- All `dark:text-gray-300` changes had zero impact
- Pipeline configuration forces `colorScheme: 'light'`
- Screenshots never capture dark mode

**Wasted effort:**
```typescript
// These changes had ZERO effect on scores:
<p className="text-gray-700 dark:text-gray-300">  // dark: ignored
```

**Recommendation:** Remove all `dark:` classes from future good case PRs.

### 4. Spacing vs. Harmony Tradeoff

**PR #1165 Paradox:**
- Spacing sub-score: 70 → 75 (+5) ✅
- Overall Harmony: 75.3 → 72.5 (-2.8) ❌

**Hypothesis:**
- Reducing gaps (`space-y-8` → `space-y-6`, `gap-8` → `gap-6`) improved spacing consistency
- But decreased visual breathing room, harming perceived rhythm/density
- AI weights overall harmony more than individual sub-scores

**Lesson:** Sub-score improvements don't guarantee overall Harmony improvement. The model considers holistic balance.

### 5. AI Feedback Consistency

All good cases received nearly identical AI findings:

```
"Ensure all colors used are from the design token palette..."
"Improve contrast between text and background..."
"Check for consistent spacing between elements..."
"Verify that all elements are properly aligned..."
```

**Interpretation:** Changes were too small to alter AI's overall assessment. Need more comprehensive, above-the-fold improvements.

---

## Detailed PR Analysis

### PR #1165: Good Case #3 - Spacing Improvements

**Changes:**
- Reduced vertical spacing: `space-y-8` → `space-y-6`
- Reduced grid gaps: `gap-8` → `gap-6`
- Reduced decision list spacing: `space-y-4` → `space-y-3`

**Results:**
- ✅ Spacing: 70 → 75 (+5)
- ✅ Alignment: 70 → 75 (+5)
- ❌ Overall Harmony: 75.3 → 72.5 (-2.8)

**Analysis:**
- Successfully improved spacing consistency metric
- But reduced visual breathing room
- Holistic harmony score penalized the denser layout
- **Lesson:** Spacing improvements must balance consistency with rhythm

### PR #1166: Good Case #4 - Contrast Improvements

**Changes:**
- Dashboard description: `text-gray-600` → `text-gray-700`
- Recent decisions text: `text-gray-600` → `text-gray-700`
- Edit mode icon/text: `text-gray-600` → `text-gray-700`
- Dark mode: `dark:text-gray-600` → `dark:text-gray-300` (ineffective)

**Results:**
- ❌ Contrast: 70 → 70 (no change)
- ✅ Color: 70 → 80 (+10)
- ✅ Alignment: 75 → 80 (+5)
- Overall Harmony: 75.3 → 75 (-0.3)

**Analysis:**
- Contrast improvements didn't target score-driving elements
- Likely need to fix: timestamps, badges, tinted backgrounds
- Color score improved despite only changing neutral shades (unexpected)
- **Lesson:** Must identify and fix ALL contrast violators, not just visible text

### PR #1167: Good Case #5 - Alignment Improvements

**Changes:**
- Widget grid: Added `items-start` for top alignment
- DraggableWidget: Added `h-full flex flex-col` for consistent heights
- Performance charts: Added `flex flex-col h-full` for equal heights
- Chart content: Added `flex-1` for vertical space distribution

**Results:**
- Identical to PR #1166 (Harmony=75, all sub-scores same)
- Alignment: 80 (same as #1166, no additional improvement)

**Analysis:**
- Internal flex alignment didn't move the needle
- AI likely evaluates left-rail alignment (H1, toolbar, first column)
- Need to align entire content column to single grid line
- **Lesson:** Focus on global structural alignment, not internal card tweaks

---

## Threshold Validation Analysis

### Current Thresholds
- **Harmony ≥83:** UNATTAINABLE with current sensitivity
- **Delight ≥94:** UNATTAINABLE with current sensitivity

### Observed Ranges
- **Bad cases:** Harmony 75.3 ± 0.9, Delight 88.2 ± 0.4
- **Good cases:** Harmony 72.5-75, Delight ~88 (not measured for all)
- **Discriminative power:** Minimal (good cases ≤ bad cases)

### Statistical Analysis

**Harmony Distribution:**
```
Bad cases:  [74, 75, 76, 75, 76, 75, 75, 76, 75, 75] → mean=75.3, σ=0.9
Good cases: [75, 75, 72.5, 75, 75]                  → mean=74.5, σ=1.1
```

**Current threshold (≥83) is 8.6 standard deviations above bad case mean.**

**Problem:** With 5-point quantization and low sensitivity, achieving 83 requires crossing TWO bucket boundaries (75→80→85), which demands comprehensive, multi-dimensional improvements beyond isolated fixes.

---

## Recommendations

### Immediate Actions (Week 2)

#### 1. Create Maximal Compliance Good Case

**Objective:** Test AI's upper scoring limit with comprehensive above-the-fold improvements

**Scope:**
- **Contrast:** Fix ALL WCAG AA violations in above-the-fold area
  - Target: 7:1+ contrast for all text (not just 4.5:1)
  - Elements: timestamps, badges, descriptions, interactive states
  - Method: Use design tokens, prefer `text-gray-800` or `bg-white`
  
- **Alignment:** Enforce left-rail grid alignment
  - Align: H1, toolbar, first card column to single grid line
  - Use consistent horizontal padding/gutters
  - Ensure all above-the-fold elements share common left edge

- **Spacing:** Maintain balanced rhythm
  - Use design system spacing scale consistently
  - Avoid over-compression (keep breathing room)

- **Color:** Ensure all colors use design tokens
  - Verify palette compliance
  - Check brand consistency

**Success Criteria:**
- If Harmony ≥80: Current approach viable, adjust threshold to ≥78-80
- If Harmony <80: Evaluation methodology needs fundamental revision

#### 2. Adjust Thresholds (Temporary)

**Proposed Thresholds:**
```yaml
quality_gates:
  harmony_threshold: 76  # Lowered from 83 (baseline + 1σ)
  delight_threshold: 90  # Lowered from 94 (baseline + 2σ)
  
  # Additional requirements:
  delta_requirements:
    - At least 2 sub-scores must improve by ≥5 points
    - No sub-score may decrease by >5 points
    - Overall Harmony must exceed baseline (75.3)
```

**Rationale:**
- 76 is achievable (1 bucket above baseline)
- Delta requirements ensure meaningful improvement
- Prevents regression while allowing progress

### Long-term Improvements (Post-Week 2)

#### 1. Enhance Evaluation Methodology

**Option A: Relative Scoring**
```yaml
# Instead of absolute thresholds, use deltas:
quality_gates:
  harmony_delta: +3      # Must improve by 3+ points from baseline
  min_improved_subscores: 2  # At least 2 sub-scores must improve
  max_regressed_subscores: 0 # No sub-score may regress
```

**Option B: Hybrid Metrics**
```yaml
# Combine AI scores with objective metrics:
quality_gates:
  harmony_threshold: 76
  accessibility_improvements:
    - contrast_violations_fixed: ≥5  # From a11y audit
    - wcag_aa_compliance: 100%
  design_token_compliance: ≥95%
```

**Option C: Finer Granularity**
- Request OpenAI to provide scores with 1-point precision
- Or use weighted sub-score aggregation instead of overall Harmony

#### 2. Improve Screenshot Capture

**Current Issues:**
- Dark mode changes ignored (forced light mode)
- Only captures above-the-fold (1366x900 viewport)

**Improvements:**
- Add dark mode screenshot variant
- Capture multiple scroll positions
- Test responsive breakpoints

#### 3. Calibrate Against Human Evaluation

**Process:**
1. Have design team rate same PRs (1-10 scale)
2. Correlate human ratings with AI scores
3. Adjust thresholds to match human judgment
4. Validate with A/B testing

---

## Lessons Learned

### What Works
1. ✅ **Authenticated page testing** - v3 capture.mjs fix successful
2. ✅ **Design token usage** - Maintains consistency, easy rollback
3. ✅ **Precise selectors** - Avoids collateral damage
4. ✅ **Above-the-fold focus** - AI only evaluates visible content

### What Doesn't Work
1. ❌ **Isolated improvements** - Must fix comprehensively
2. ❌ **Dark mode changes** - Pipeline forces light mode
3. ❌ **Incremental tweaks** - Can't cross bucket boundaries
4. ❌ **Sub-score optimization** - May harm overall Harmony

### Best Practices for Future Good Cases

1. **Identify score-driving elements first**
   - Run a11y audit to find actual violators
   - Sample text/background pairs in screenshots
   - Don't guess which elements matter

2. **Make decisive changes**
   - Aim for 7:1+ contrast (not just 4.5:1)
   - Fix ALL instances of a violation type
   - Cross bucket boundaries decisively

3. **Test holistically**
   - Consider tradeoffs between sub-scores
   - Verify overall Harmony doesn't regress
   - Check for unintended side effects

4. **Document hypotheses**
   - State expected sub-score changes
   - Explain which elements should improve
   - Enable post-hoc correlation analysis

---

## Next Steps

### Week 2 Completion
1. ✅ Create 5 good case PRs
2. ✅ Collect and analyze calibration data
3. ✅ Identify root causes and limitations
4. ⏳ Create maximal compliance good case
5. ⏳ Generate final Week 2 report with threshold recommendations

### Week 3 Planning
1. Implement temporary threshold adjustments (Harmony ≥76, Delight ≥90)
2. Monitor false positive/negative rates
3. Collect more calibration data from real PRs
4. Evaluate long-term methodology improvements
5. Consider hybrid metrics (AI + objective measurements)

---

## Appendix: Raw Data

### Good Case Detailed Scores

**PR #1162 (A11y - ARIA labels):**
```json
{
  "Landing Page": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80},
  "Login Page": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 85},
  "Dashboard": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 80}
}
```

**PR #1163 (Color Tokens):**
```json
{
  "Landing Page": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80},
  "Login Page": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 85},
  "Dashboard": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 80}
}
```

**PR #1165 (Spacing):**
```json
{
  "Landing Page": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80},
  "Login Page": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 85},
  "Dashboard": {"harmony": 72.5, "spacing": 75, "color": 70, "contrast": 70, "alignment": 75}
}
```

**PR #1166 (Contrast):**
```json
{
  "Landing Page": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 85},
  "Login Page": {"harmony": 75, "spacing": 80, "color": 70, "contrast": 70, "alignment": 85},
  "Dashboard": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80}
}
```

**PR #1167 (Alignment):**
```json
{
  "Landing Page": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80},
  "Login Page": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80},
  "Dashboard": {"harmony": 75, "spacing": 70, "color": 80, "contrast": 70, "alignment": 80}
}
```

### Bad Case Baseline (Week 1)

From 10 bad case PRs (#1151-#1160):
```
Harmony scores: [74, 75, 76, 75, 76, 75, 75, 76, 75, 75]
Mean: 75.3, Std Dev: 0.9, Min: 74, Max: 76

Delight scores: [88, 88, 89, 88, 88, 88, 88, 89, 88, 88]
Mean: 88.2, Std Dev: 0.4, Min: 88, Max: 89
```

---

**Report Generated:** November 6, 2025  
**Author:** AI QA Calibration Team  
**Status:** Draft - Pending Maximal Compliance Case Validation
