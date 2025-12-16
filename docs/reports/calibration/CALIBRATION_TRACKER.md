# AI Perceptual QA Calibration Tracker

**Purpose:** Track all PRs used for calibrating AI Perceptual QA thresholds and prompt versions.

**Goal:** Collect 20-30 PRs with diverse UX quality to tune thresholds and minimize false positives/negatives.

## Calibration Dataset

| Date | PR # | PR Link | Commit SHA | Labels | Prompt Ver | Model | Pages | Harmony Avg | Delight | Pass/Fail | Notes |
|------|------|---------|------------|--------|------------|-------|-------|-------------|---------|-----------|-------|
| 2025-11-05 | 1145 | [#1145](https://github.com/RC918/morningai/pull/1145) | 8ee05ce5 | ai-calibration-good | v0.1 | gpt-4o-mini | 2 | TBD | TBD | TBD | Supabase safe client fix |
| | | | | | | | | | | | |

## Label Definitions

- **ai-calibration-good**: PR with good UX quality (expected to pass AI QA)
- **ai-calibration-bad**: PR with known UX issues (expected to fail AI QA)
- **ai-qa-bypass**: Emergency bypass for AI QA checks
- **ai-qa-blocking-optin**: Opt-in to Phase 2 v2 blocking AI QA (early testing)

## Data Collection Strategy

### Week 1: Baseline + Bad Cases (Target: 20-30 PRs)

**Good UX PRs (15-20):**
- Recent merged PRs with design system compliance
- New features with proper spacing/typography
- Bug fixes that improve visual quality

**Bad UX PRs (8-10):**
Intentionally create PRs with isolated UX issues:
1. Low contrast text (#9aa on white background)
2. Overlapping elements (negative margins)
3. Missing alt text on images
4. Excessive animation duration (>500ms)
5. Wrong brand color tokens
6. Mobile layout breakage
7. Unclear form error states
8. Misaligned grid elements

### Week 2: Analysis + Threshold Tuning

**Metrics to Calculate:**
- False Block Rate: % of "good" PRs that fail AI QA (target: ≤5-10%)
- Detection Rate: % of "bad" PRs that AI QA catches (target: ≥80%)
- Score Distribution: P10, P25, P50, P75, P90 for harmony and delight
- Optimal Thresholds: Balance between false positives and false negatives

## Prompt Versions

### v0.1 (Current)
- **File:** `prompts/ux_vision_v0.1.json`
- **Focus:** Design system token adherence, WCAG contrast, spacing consistency
- **Weights:** Color 25%, Spacing 20%, Typography 20%, Alignment 20%, Contrast 15%
- **Status:** Baseline for calibration

### v0.2 (Planned)
- **Changes:** TBD based on v0.1 calibration results
- **A/B Testing:** Run both versions on 5-10 PRs to compare
- **Goal:** More specific findings, fewer false positives

## Usage

### Adding a PR to Calibration Dataset

1. **Label the PR** with appropriate calibration label
2. **Run AI QA** (automatically runs in CI if `UX_AI_ENABLE=true`)
3. **Download calibration.csv** from GitHub Actions artifacts
4. **Update this tracker** with PR details and results
5. **Add notes** about any interesting findings or edge cases

### Analyzing Calibration Data

```bash
# Aggregate all calibration CSVs
cat calibration-*.csv > all-calibration-data.csv

# Calculate statistics (use spreadsheet or Python/R)
# - Mean, median, std dev for harmony and delight
# - Pass/fail rates by label
# - ROC curve for threshold optimization
```

## Next Steps

- [ ] Collect 15-20 "good" PRs (label: ai-calibration-good)
- [ ] Create 8-10 "bad" PRs with isolated UX issues (label: ai-calibration-bad)
- [ ] Run statistical analysis on collected data
- [ ] Generate CALIBRATION_REPORT_v1.md with findings
- [ ] Tune thresholds based on data
- [ ] Test v0.2 prompt improvements
- [ ] Enable Phase 2 v2 blocking mode (opt-in first)
