# A/B Testing Guide for Performance Optimizations

## Overview

This guide explains how to use the A/B testing framework to validate performance optimizations in the MorningAI dashboard.

## Architecture

The A/B testing framework consists of:

1. **Test Configuration** (`src/lib/ab-testing.js`)
   - Test definitions and variant distributions
   - Variant assignment logic
   - Metrics collection and storage

2. **Integration** (`src/App.jsx`)
   - Automatic variant assignment on app load
   - Web Vitals collection after page load
   - Metrics tracking to localStorage

3. **Performance Metrics**
   - First Contentful Paint (FCP)
   - Largest Contentful Paint (LCP)
   - Cumulative Layout Shift (CLS)
   - First Input Delay (FID)
   - DOM Content Loaded
   - Load Complete

## Current Tests

### Performance Optimizations Test (perf_opt_v1)

**Variants:**
- `control` (50%): Original implementation
- `optimized` (50%): With all performance optimizations

**Optimizations in "optimized" variant:**
1. Font optimization with `font-display: swap`
2. Critical CSS inlining
3. Image optimization (WebP + lazy loading)
4. Service Worker for caching
5. Code splitting and minification

## Usage

### Viewing Test Assignment

Check the browser console for:
```
[AB Test] Performance optimization variant: optimized
```

Or check localStorage:
```javascript
localStorage.getItem('morningai_ab_test')
// Returns: {"perf_opt_v1":"optimized"}
```

### Viewing Collected Metrics

```javascript
import { getABTestSummary } from '@/lib/ab-testing'

const summary = getABTestSummary('perf_opt_v1')
console.log(summary)
```

Output example:
```javascript
{
  control: {
    count: 10,
    avg: {
      fcp: 1200,
      lcp: 2500,
      cls: 0.05,
      fid: 50
    }
  },
  optimized: {
    count: 12,
    avg: {
      fcp: 900,    // -300ms improvement
      lcp: 2300,   // -200ms improvement
      cls: 0.04,
      fid: 45
    }
  }
}
```

### Exporting Metrics for Analysis

```javascript
import { exportABTestMetrics } from '@/lib/ab-testing'

const csv = exportABTestMetrics('perf_opt_v1')
console.log(csv)

// Download as CSV file
const blob = new Blob([csv], { type: 'text/csv' })
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = 'ab-test-metrics.csv'
a.click()
```

### Clearing Test Data

```javascript
import { clearABTestData } from '@/lib/ab-testing'

// Clear specific test
clearABTestData('perf_opt_v1')

// Clear all tests
clearABTestData()
```

## Statistical Significance

To determine if results are statistically significant, use a t-test calculator with:

1. Sample size for each variant
2. Mean values for each metric
3. Standard deviation (calculate from raw data)

**Recommended minimum sample size:** 100 users per variant

**Significance level:** p < 0.05

## Expected Results

Based on the optimizations implemented:

| Metric | Control | Optimized | Expected Improvement |
|--------|---------|-----------|---------------------|
| FCP    | ~1500ms | ~900ms    | -600ms (-40%)       |
| LCP    | ~2500ms | ~2300ms   | -200ms (-8%)        |
| CLS    | ~0.05   | ~0.04     | -0.01 (-20%)        |
| FID    | ~50ms   | ~45ms     | -5ms (-10%)         |

## Monitoring in Production

1. **Google Analytics Integration** (recommended)
   ```javascript
   import { getABTestVariant } from '@/lib/ab-testing'
   
   const variant = getABTestVariant('perf_opt_v1')
   gtag('event', 'ab_test_assignment', {
     test_id: 'perf_opt_v1',
     variant: variant
   })
   ```

2. **Custom Analytics Dashboard**
   - Export metrics daily
   - Calculate statistical significance
   - Monitor conversion rates by variant

3. **Lighthouse CI Integration**
   - Run Lighthouse tests for both variants
   - Compare scores in CI/CD pipeline

## Best Practices

1. **Run tests for at least 2 weeks** to account for:
   - Different user behaviors
   - Peak vs. off-peak traffic
   - Weekday vs. weekend patterns

2. **Monitor both performance and business metrics:**
   - Page load times
   - User engagement
   - Conversion rates
   - Bounce rates

3. **Avoid peeking at results too early:**
   - Wait for minimum sample size
   - Don't stop test based on early trends

4. **Document findings:**
   - Record final metrics
   - Note any anomalies
   - Share learnings with team

## Troubleshooting

### Metrics not being collected

Check:
1. Browser console for errors
2. localStorage quota (may be full)
3. Performance API availability

### Variant assignment not working

Check:
1. localStorage is enabled
2. No browser extensions blocking storage
3. Test ID matches configuration

### Inconsistent results

Consider:
1. Cache effects (clear browser cache)
2. Network conditions
3. Device capabilities
4. Browser differences

## Next Steps

After validating optimizations:

1. **If optimized variant wins:**
   - Roll out to 100% of users
   - Remove A/B test code
   - Document improvements

2. **If control variant wins:**
   - Investigate why optimizations didn't help
   - Consider device/network-specific optimizations
   - Test individual optimizations separately

3. **If results are inconclusive:**
   - Extend test duration
   - Increase sample size
   - Refine optimizations
