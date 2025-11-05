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
  if: github.event_name == 'pull_request' && vars.UX_AI_ENABLE == 'true'
  strategy:
    matrix:
      app: [frontend-dashboard]
```

**Features:**
- **Opt-in by default**: Job only runs when `UX_AI_ENABLE` is set to `true`
- Runs on PRs only (cost control)
- Non-blocking (informational only)
- Uploads artifacts (screenshots, reports)
- Displays scores in CI logs

**Environment Variables:**
- `UX_AI_ENABLE`: **Required** - Set to `true` to enable AI Perceptual QA (default: disabled)
- `OPENAI_API_KEY`: Required for AI scoring (GitHub Secret)
- `UX_AI_MODEL`: Model to use (default: gpt-4o-mini)
- `UX_AI_MAX_PAGES`: Max pages per app (default: 3)
- `UX_HARMONY_MIN`: Harmony threshold (default: 70)
- `UX_DELIGHT_MIN`: Delight threshold (default: 75)

### Enabling AI Perceptual QA in CI

AI Perceptual QA is **disabled by default** to control costs. To enable it:

1. **Set Repository Variable:**
   - Go to GitHub repo: Settings > Secrets and variables > Actions > Variables tab
   - Click "New repository variable"
   - Name: `UX_AI_ENABLE`
   - Value: `true`
   - Click "Add variable"

2. **Set OpenAI API Key (if not already set):**
   - Go to Secrets tab (same page)
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: `sk-...` (your OpenAI API key)
   - Click "Add secret"

3. **Create a PR** - AI Perceptual QA will now run automatically

**When to enable:**
- UX-critical changes (design system updates, major UI refactors)
- Before major releases
- When investigating visual regression issues
- During calibration period (collecting baseline data)

**Cost considerations:**
- Each run costs ~$0.01-0.02 per app
- Runs only on PRs (not on every commit)
- Can be disabled anytime by setting `UX_AI_ENABLE` to `false` or removing the variable

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
# 1. Enable AI Perceptual QA
# Settings > Secrets and variables > Actions > Variables tab
# Name: UX_AI_ENABLE
# Value: true

# 2. Set OpenAI API Key (if not already set)
# Settings > Secrets and variables > Actions > Secrets tab
# Name: OPENAI_API_KEY
# Value: sk-...

# 3. Create PR - AI Perceptual QA will run automatically
```

### Skip AI Scoring

```bash
# Run without AI (only motion + aggregation)
SKIP_AI=true pnpm run ux:qa
```

## Calibration Period

**Phase 2 v1 is informational only:**
- AI scores are logged but don't block merges
- Allows calibration of thresholds
- Identifies noisy/inconsistent scoring
- Builds baseline data

**Future (Phase 2 v2):**
- After 2-3 weeks of data collection
- Set conservative thresholds
- Enable blocking on critical violations
- Add label override mechanism

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

### AI Perceptual QA Job Not Running

**Symptom:** The `ai-perceptual-qa` job doesn't appear in CI checks at all.

**Solution:** AI Perceptual QA is disabled by default. Set `UX_AI_ENABLE` repository variable to `true`:
1. Go to Settings > Secrets and variables > Actions > Variables tab
2. Add variable: `UX_AI_ENABLE` = `true`

### AI Scoring Skipped

```
⏭️  Skipping AI Perceptual QA: OPENAI_API_KEY not set
```

**Solution:** Set `OPENAI_API_KEY` secret in GitHub repo settings (Secrets tab).

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
