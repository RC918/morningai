# AI Perceptual QA - Phase 2 Implementation

**Date:** November 5, 2025  
**Status:** Implemented  
**Part of:** UX Ops Pipeline Phase 2

## Overview

AI Perceptual QA uses OpenAI's Vision API to analyze screenshots of key pages and score visual harmony based on design system tokens. Combined with motion performance metrics, it calculates a **Delight Index** that provides a holistic measure of UX quality.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UX QA Pipeline                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Screenshot Capture (capture.mjs)                        │
│     └─ Playwright captures key pages                        │
│     └─ Light theme, en-US, 1366x900 viewport               │
│     └─ Outputs: screenshots/*.jpg + manifest.json          │
│                                                              │
│  2. AI Visual Harmony Scoring (score-ai.mjs)               │
│     └─ OpenAI Vision API analyzes screenshots              │
│     └─ Scores: color, spacing, typography, alignment       │
│     └─ Outputs: harmony.json with 0-100 scores             │
│                                                              │
│  3. Motion Score Normalization (aggregate.mjs)              │
│     └─ Reads motion-test-report.json                       │
│     └─ Normalizes FPS, P95, dropped frames to 0-100        │
│                                                              │
│  4. Delight Index Calculation (aggregate.mjs)               │
│     └─ Delight = (Harmony × 0.5) + (Motion × 0.5)         │
│     └─ Outputs: ux-report.json + ux-report.html           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Configuration (`scripts/ux/config.js`)

Defines:
- **Pages to analyze** per app (routes, viewport, auth requirements)
- **Design tokens subset** (colors, spacing, typography)
- **AI model settings** (gpt-4o-mini, temperature 0)
- **Thresholds** (harmony min: 70, delight min: 75)
- **Budget controls** (max pages, image quality)

### 2. Screenshot Capture (`scripts/ux/capture.mjs`)

- Uses Playwright to capture screenshots
- Forces light theme and en-US locale for consistency
- Hides dynamic elements (timestamps, animations)
- Saves JPEG images with configurable quality
- Outputs manifest with metadata

**Usage:**
```bash
BASE_URL=http://localhost:4173 APP_NAME=frontend-dashboard pnpm run ux:capture
```

### 3. AI Scoring (`scripts/ux/score-ai.mjs`)

- Calls OpenAI Vision API with screenshot + tokens
- Evaluates 5 dimensions (0-100 scale):
  - **Color Harmony**: Token adherence, contrast, brand consistency
  - **Spacing Consistency**: Spacing scale adherence, vertical rhythm
  - **Typography Consistency**: Font sizes, weights, line-height
  - **Alignment & Grid**: Element alignment, grid consistency
  - **Contrast Quality**: Readability, visual hierarchy
- Returns actionable findings (3-5 specific issues)
- Outputs JSON with per-page and overall scores

**Usage:**
```bash
OPENAI_API_KEY=sk-... APP_NAME=frontend-dashboard pnpm run ux:score
```

### 4. Aggregation (`scripts/ux/aggregate.mjs`)

- Reads harmony report and motion test results
- Normalizes motion metrics to 0-100:
  - FPS Score: `(fps / 60) × 100`
  - P95 Score: `(16.67 / p95_ms) × 100`
  - Dropped Score: `(1 - dropped_rate) × 100`
  - Motion Overall: `fps × 0.4 + p95 × 0.4 + dropped × 0.2`
- Calculates Delight Index with configurable weights
- Generates JSON report + HTML dashboard

**Usage:**
```bash
APP_NAME=frontend-dashboard pnpm run ux:aggregate
```

### 5. Orchestrator (`scripts/ux/run-qa.mjs`)

Runs the complete pipeline:
1. Capture screenshots
2. AI scoring (if OPENAI_API_KEY set)
3. Aggregate metrics

**Usage:**
```bash
BASE_URL=http://localhost:4173 \
APP_NAME=frontend-dashboard \
OPENAI_API_KEY=sk-... \
pnpm run ux:qa
```

## Metrics

### Visual Harmony Score (0-100)

Weighted average of 5 dimensions:
- Color: 25%
- Spacing: 20%
- Typography: 20%
- Alignment: 20%
- Contrast: 15%

**Thresholds:**
- Target: 85
- Minimum: 70

### Motion Performance Score (0-100)

Normalized from motion test metrics:
- FPS (40% weight)
- P95 Frame Time (40% weight)
- Dropped Frames (20% weight)

**Thresholds:**
- Target: 80
- Minimum: 60

### Delight Index (0-100)

Combined UX quality score:
```
Delight = (Harmony × 0.5) + (Motion × 0.5)
```

**Thresholds:**
- Target: 90
- Minimum: 75

## CI Integration

Added to `.github/workflows/ux-pipeline.yml`:

```yaml
ai-perceptual-qa:
  name: AI Perceptual QA
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  strategy:
    matrix:
      app: [frontend-dashboard]
```

**Features:**
- Runs on PRs only (cost control)
- Optional (skips if OPENAI_API_KEY not set)
- Non-blocking (informational only)
- Uploads artifacts (screenshots, reports)
- Displays scores in CI logs

**Environment Variables:**
- `OPENAI_API_KEY`: Required for AI scoring
- `UX_AI_MODEL`: Model to use (default: gpt-4o-mini)
- `UX_AI_MAX_PAGES`: Max pages per app (default: 3)
- `UX_HARMONY_MIN`: Harmony threshold (default: 70)
- `UX_DELIGHT_MIN`: Delight threshold (default: 75)

## Cost Management

**Budget Controls:**
- Max 3 pages per app (configurable)
- gpt-4o-mini model (cheaper than gpt-4o)
- JPEG compression (85% quality)
- Max image width: 1366px
- Temperature: 0 (deterministic)
- Rate limiting: 1s between requests

**Estimated Cost per Run:**
- ~3 images × ~1500 tokens = ~$0.01-0.02 per app
- PR-only execution (not on every commit)

## Output Files

```
ux-qa-results/
├── screenshots/
│   └── frontend-dashboard/
│       ├── landing-page.jpg
│       ├── login-page.jpg
│       └── dashboard.jpg
├── frontend-dashboard-screenshots.json
├── frontend-dashboard-harmony.json
├── frontend-dashboard-ux-report.json
└── frontend-dashboard-ux-report.html
```

## Usage Examples

### Local Testing

```bash
# 1. Start preview server
cd handoff/20250928/40_App/frontend-dashboard
pnpm run build
pnpm run preview --port 4173

# 2. Run UX QA (in another terminal)
cd /path/to/morningai
BASE_URL=http://localhost:4173 \
APP_NAME=frontend-dashboard \
OPENAI_API_KEY=sk-... \
pnpm run ux:qa

# 3. View results
open ux-qa-results/frontend-dashboard-ux-report.html
```

### CI Testing

```bash
# Set secret in GitHub repo settings
# Settings > Secrets and variables > Actions > New repository secret
# Name: OPENAI_API_KEY
# Value: sk-...

# Create PR - AI Perceptual QA will run automatically
```

### Skip AI Scoring

```bash
# Run without AI (only motion + aggregation)
SKIP_AI=true pnpm run ux:qa
```

## Calibration Process

**Current Status:** Phase 2 v1 (Informational Only)

AI Perceptual QA is currently in **calibration mode** - scores are logged but don't block merges. Before enabling Phase 2 v2 (blocking thresholds), we need to collect baseline data and tune thresholds based on real-world usage.

### Why Calibration is Needed

AI scoring can be subjective and context-dependent. Without calibration:
- Thresholds may be too strict (false positives - good UX flagged as bad)
- Thresholds may be too lenient (false negatives - bad UX passing checks)
- Score variance may be too high (inconsistent scoring)
- Team may lose trust in the system

### Calibration Methodology

#### Phase 1: Data Collection (2-4 weeks)

**Goal:** Collect 20-30 PR samples to understand score distributions.

**Process:**
1. **Enable AI Perceptual QA** on all UX-critical PRs:
   - Design system updates
   - Major UI refactors
   - New page implementations
   - Component library changes

2. **Record scores** in a tracking spreadsheet:
   ```
   | PR # | Page | Harmony | Motion | Delight | Notes |
   |------|------|---------|--------|---------|-------|
   | 1234 | Landing | 82 | 95 | 88.5 | Good |
   | 1235 | Dashboard | 68 | 88 | 78 | Color issues |
   ```

3. **Categorize PRs** by outcome:
   - ✅ **Good UX** (team agrees quality is high)
   - ⚠️ **Acceptable UX** (minor issues, but mergeable)
   - ❌ **Poor UX** (should have been caught)

4. **Document patterns**:
   - Which pages typically score lower?
   - Which dimensions (color, spacing, etc.) are most variable?
   - Are there systematic biases? (e.g., dark mode always scores lower)

#### Phase 2: Statistical Analysis

**Goal:** Determine realistic thresholds based on collected data.

**Analysis Steps:**

1. **Calculate percentiles** for each metric:
   ```
   Visual Harmony:
   - P10: 65
   - P25: 72
   - P50 (median): 78
   - P75: 85
   - P90: 92
   
   Delight Index:
   - P10: 70
   - P25: 76
   - P50: 82
   - P75: 88
   - P90: 94
   ```

2. **Correlate scores with outcomes**:
   - What % of "Good UX" PRs scored above 80?
   - What % of "Poor UX" PRs scored below 70?
   - Where is the optimal threshold to minimize false positives/negatives?

3. **Identify outliers**:
   - PRs with high scores but poor UX (false negatives)
   - PRs with low scores but good UX (false positives)
   - Investigate root causes (AI misunderstanding, edge cases, etc.)

4. **Set thresholds** based on data:
   - **Minimum threshold**: P25-P30 (catches bottom 25-30% of PRs)
   - **Target threshold**: P75-P80 (aspirational, not blocking)
   - **Critical threshold**: P10 (absolute minimum, blocks merge)

**Example threshold tuning:**
```javascript
// Current (uncalibrated)
THRESHOLDS: {
  harmony: { min: 70, target: 85 },
  delight: { min: 75, target: 90 },
}

// After calibration (example)
THRESHOLDS: {
  harmony: { critical: 60, min: 72, target: 85 },
  delight: { critical: 65, min: 76, target: 88 },
}
```

#### Phase 3: Validation (1 week)

**Goal:** Test thresholds on historical PRs to verify accuracy.

**Process:**
1. **Backtest** on collected data:
   - Apply new thresholds to all 20-30 PRs
   - Count false positives (good UX blocked)
   - Count false negatives (poor UX passed)
   - Target: <10% false positive rate

2. **Dry-run mode**:
   - Enable blocking in CI but with `continue-on-error: true`
   - Log which PRs would have been blocked
   - Review with team for 1 week

3. **Adjust thresholds** based on feedback:
   - If too many false positives: lower thresholds
   - If too many false negatives: raise thresholds
   - If high variance: investigate AI prompt or scoring logic

#### Phase 4: Phase 2 v2 Rollout

**Goal:** Enable blocking mode with confidence.

**Implementation:**
1. **Update workflow** (`.github/workflows/ux-pipeline.yml`):
   ```yaml
   - name: Run AI Perceptual QA
     run: pnpm run ux:qa
     continue-on-error: false  # Change from true to false
   ```

2. **Add override mechanism**:
   - Label: `ux-qa-override` to bypass checks
   - Requires approval from design lead
   - Document reason in PR description

3. **Monitor for 1 week**:
   - Track override usage (should be <5% of PRs)
   - Collect feedback from team
   - Fine-tune thresholds if needed

4. **Document final thresholds** in this file

### Score Interpretation Guide

Understanding what scores mean in practice:

**Visual Harmony Scores:**
- **90-100**: Exceptional - Perfect adherence to design system
- **80-89**: Good - Minor deviations, acceptable quality
- **70-79**: Acceptable - Some issues, but not critical
- **60-69**: Poor - Multiple violations, needs review
- **<60**: Critical - Significant design system violations

**Motion Performance Scores:**
- **90-100**: Excellent - Smooth, no dropped frames
- **80-89**: Good - Occasional frame drops, acceptable
- **70-79**: Acceptable - Noticeable jank, but usable
- **60-69**: Poor - Frequent frame drops, poor UX
- **<60**: Critical - Severe performance issues

**Delight Index:**
- **85-100**: Delightful - High-quality UX
- **75-84**: Good - Solid UX, minor improvements possible
- **65-74**: Acceptable - Meets minimum standards
- **55-64**: Poor - Below standards, needs improvement
- **<55**: Critical - Unacceptable UX quality

### Threshold Adjustment Process

When to adjust thresholds:

1. **Too many false positives** (>10% of PRs):
   - Lower minimum thresholds by 5 points
   - Review AI prompt for biases
   - Consider page-specific thresholds

2. **Too many false negatives** (poor UX passing):
   - Raise minimum thresholds by 5 points
   - Add more specific scoring criteria
   - Review design token coverage

3. **High score variance** (same page, different scores):
   - Investigate AI model consistency
   - Add more context to prompts
   - Consider averaging multiple runs

4. **Team feedback** (scores don't match perception):
   - Collect specific examples
   - Adjust dimension weights
   - Refine scoring rubric

### Override Procedures

For Phase 2 v2 (blocking mode), when a PR fails AI Perceptual QA:

1. **Review findings** in HTML report:
   ```bash
   open ux-qa-results/frontend-dashboard-ux-report.html
   ```

2. **Assess validity**:
   - Are the findings accurate?
   - Are they critical enough to block merge?
   - Is this a false positive?

3. **Fix issues** (preferred):
   - Address color/spacing/typography violations
   - Improve motion performance
   - Re-run QA to verify fixes

4. **Request override** (if false positive):
   - Add label: `ux-qa-override`
   - Document reason in PR description
   - Get approval from design lead
   - Merge with override

5. **Report false positives**:
   - Create issue with PR link and screenshots
   - Help improve calibration
   - Adjust thresholds if pattern emerges

### Historical Data Tracking

**Recommended tracking spreadsheet:**

| Date | PR # | App | Page | Harmony | Motion | Delight | Outcome | Notes |
|------|------|-----|------|---------|--------|---------|---------|-------|
| 2025-11-05 | 1234 | dashboard | Landing | 82 | 95 | 88.5 | ✅ Good | Clean design |
| 2025-11-06 | 1235 | dashboard | Dashboard | 68 | 88 | 78 | ⚠️ Acceptable | Color issues |
| 2025-11-07 | 1236 | dashboard | Settings | 55 | 92 | 73.5 | ❌ Poor | Off-scale spacing |

**Metrics to track:**
- Score distributions (P10, P25, P50, P75, P90)
- False positive rate (good UX blocked)
- False negative rate (poor UX passed)
- Override usage (% of PRs)
- Team satisfaction (survey)

**Future:** Consider building a dashboard in Owner Console to visualize trends and track calibration progress.

## Extending

### Add New Pages

Edit `scripts/ux/config.js`:

```javascript
PAGES: {
  'frontend-dashboard': [
    // ... existing pages
    {
      name: 'Settings Page',
      path: '/settings',
      description: 'User settings',
      requiresAuth: true,
      viewport: { width: 1366, height: 900 },
    },
  ],
}
```

### Add New App

```javascript
PAGES: {
  // ... existing apps
  'owner-console': [
    {
      name: 'Login Page',
      path: '/login',
      description: 'Owner console login',
      requiresAuth: false,
      viewport: { width: 1366, height: 900 },
    },
  ],
}
```

### Adjust Thresholds

Via environment variables:

```bash
UX_HARMONY_MIN=75 \
UX_DELIGHT_MIN=80 \
UX_DELIGHT_W_HARMONY=0.6 \
UX_DELIGHT_W_MOTION=0.4 \
pnpm run ux:qa
```

### Change AI Model

```bash
UX_AI_MODEL=gpt-4o pnpm run ux:qa
```

## Troubleshooting

### AI Scoring Skipped

```
⏭️  Skipping AI Perceptual QA: OPENAI_API_KEY not set
```

**Solution:** Set `OPENAI_API_KEY` environment variable.

### Screenshot Capture Failed

```
❌ Error: Development server not running on http://localhost:4173
```

**Solution:** Start preview server first:
```bash
pnpm run build && pnpm run preview --port 4173
```

### JSON Parse Error

```
❌ Error: Unexpected token in JSON
```

**Solution:** AI response was not valid JSON. Script retries once automatically. If persistent, check model output.

### Low Harmony Score

Review findings in HTML report:
```bash
open ux-qa-results/frontend-dashboard-ux-report.html
```

Common issues:
- Non-token colors used
- Inconsistent spacing
- Off-scale font sizes
- Poor alignment

## Next Steps (Phase 3)

- [ ] UX Dashboard in Owner Console
- [ ] Real-time KPI monitoring
- [ ] Supabase ux_events table
- [ ] Alert mechanism for threshold violations
- [ ] Historical trend tracking
- [ ] Multi-theme analysis (light + dark)

## References

- UX Strategy Implementation: `docs/UX_STRATEGY_IMPLEMENTATION.md`
- Design Tokens: `packages/shared-ui/src/tokens.json`
- Motion Tests: `handoff/20250928/40_App/*/scripts/test-motion.cjs`
- UX Pipeline: `.github/workflows/ux-pipeline.yml`
