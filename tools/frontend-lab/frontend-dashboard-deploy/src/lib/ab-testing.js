/**
 * A/B Testing Framework for Performance Optimization Validation
 * Implements client-side A/B testing with performance metrics tracking
 */

const AB_TEST_STORAGE_KEY = 'morningai_ab_test';
const AB_TEST_METRICS_KEY = 'morningai_ab_metrics';

/**
 * A/B Test Configuration
 */
export const AB_TESTS = {
  PERFORMANCE_OPTIMIZATIONS: {
    id: 'perf_opt_v1',
    name: 'Performance Optimizations',
    variants: {
      CONTROL: 'control',
      OPTIMIZED: 'optimized',
    },
    distribution: {
      control: 0.5,
      optimized: 0.5,
    },
  },
};

/**
 * Get or assign user to A/B test variant
 * @param {string} testId - Test identifier
 * @returns {string} - Assigned variant
 */
export function getABTestVariant(testId) {
  if (typeof window === 'undefined') return null;

  const stored = localStorage.getItem(AB_TEST_STORAGE_KEY);
  let assignments = {};

  if (stored) {
    try {
      assignments = JSON.parse(stored);
    } catch (e) {
      console.error('[AB Test] Failed to parse stored assignments:', e);
    }
  }

  if (assignments[testId]) {
    return assignments[testId];
  }

  const test = Object.values(AB_TESTS).find((t) => t.id === testId);
  if (!test) {
    console.error('[AB Test] Test not found:', testId);
    return null;
  }

  const variant = assignVariant(test.distribution);
  assignments[testId] = variant;

  try {
    localStorage.setItem(AB_TEST_STORAGE_KEY, JSON.stringify(assignments));
  } catch (e) {
    console.error('[AB Test] Failed to store assignment:', e);
  }

  console.log(`[AB Test] Assigned to variant: ${variant} for test: ${testId}`);
  return variant;
}

/**
 * Assign variant based on distribution
 * @param {Object} distribution - Variant distribution
 * @returns {string} - Assigned variant
 */
function assignVariant(distribution) {
  const random = Math.random();
  let cumulative = 0;

  for (const [variant, probability] of Object.entries(distribution)) {
    cumulative += probability;
    if (random <= cumulative) {
      return variant;
    }
  }

  return Object.keys(distribution)[0];
}

/**
 * Track performance metrics for A/B test
 * @param {string} testId - Test identifier
 * @param {Object} metrics - Performance metrics
 */
export function trackABTestMetrics(testId, metrics) {
  if (typeof window === 'undefined') return;

  const variant = getABTestVariant(testId);
  if (!variant) return;

  const stored = localStorage.getItem(AB_TEST_METRICS_KEY);
  let allMetrics = {};

  if (stored) {
    try {
      allMetrics = JSON.parse(stored);
    } catch (e) {
      console.error('[AB Test] Failed to parse stored metrics:', e);
    }
  }

  if (!allMetrics[testId]) {
    allMetrics[testId] = {};
  }

  if (!allMetrics[testId][variant]) {
    allMetrics[testId][variant] = [];
  }

  allMetrics[testId][variant].push({
    ...metrics,
    timestamp: Date.now(),
  });

  try {
    localStorage.setItem(AB_TEST_METRICS_KEY, JSON.stringify(allMetrics));
  } catch (e) {
    console.error('[AB Test] Failed to store metrics:', e);
  }

  console.log(`[AB Test] Tracked metrics for ${testId}/${variant}:`, metrics);
}

/**
 * Collect Web Vitals metrics
 * @returns {Promise<Object>} - Web Vitals metrics
 */
export async function collectWebVitals() {
  if (typeof window === 'undefined') return {};

  const metrics = {};

  if ('performance' in window) {
    const navigation = performance.getEntriesByType('navigation')[0];
    const paint = performance.getEntriesByType('paint');

    if (navigation) {
      metrics.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
      metrics.loadComplete = navigation.loadEventEnd - navigation.loadEventStart;
      metrics.domInteractive = navigation.domInteractive;
    }

    const fcp = paint.find((entry) => entry.name === 'first-contentful-paint');
    if (fcp) {
      metrics.fcp = fcp.startTime;
    }

    const lcp = await getLCP();
    if (lcp) {
      metrics.lcp = lcp;
    }

    const cls = await getCLS();
    if (cls !== null) {
      metrics.cls = cls;
    }

    const fid = await getFID();
    if (fid) {
      metrics.fid = fid;
    }
  }

  return metrics;
}

/**
 * Get Largest Contentful Paint (LCP)
 * @returns {Promise<number>}
 */
function getLCP() {
  return new Promise((resolve) => {
    if (!('PerformanceObserver' in window)) {
      resolve(null);
      return;
    }

    let lcp = null;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      lcp = lastEntry.renderTime || lastEntry.loadTime;
    });

    try {
      observer.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch (e) {
      resolve(null);
      return;
    }

    setTimeout(() => {
      observer.disconnect();
      resolve(lcp);
    }, 5000);
  });
}

/**
 * Get Cumulative Layout Shift (CLS)
 * @returns {Promise<number>}
 */
function getCLS() {
  return new Promise((resolve) => {
    if (!('PerformanceObserver' in window)) {
      resolve(null);
      return;
    }

    let cls = 0;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          cls += entry.value;
        }
      }
    });

    try {
      observer.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {
      resolve(null);
      return;
    }

    setTimeout(() => {
      observer.disconnect();
      resolve(cls);
    }, 5000);
  });
}

/**
 * Get First Input Delay (FID)
 * @returns {Promise<number>}
 */
function getFID() {
  return new Promise((resolve) => {
    if (!('PerformanceObserver' in window)) {
      resolve(null);
      return;
    }

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const firstInput = entries[0];
      const fid = firstInput.processingStart - firstInput.startTime;
      observer.disconnect();
      resolve(fid);
    });

    try {
      observer.observe({ type: 'first-input', buffered: true });
    } catch (e) {
      resolve(null);
      return;
    }

    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, 10000);
  });
}

/**
 * Get A/B test metrics summary
 * @param {string} testId - Test identifier
 * @returns {Object} - Metrics summary by variant
 */
export function getABTestSummary(testId) {
  if (typeof window === 'undefined') return {};

  const stored = localStorage.getItem(AB_TEST_METRICS_KEY);
  if (!stored) return {};

  try {
    const allMetrics = JSON.parse(stored);
    const testMetrics = allMetrics[testId];

    if (!testMetrics) return {};

    const summary = {};

    for (const [variant, metrics] of Object.entries(testMetrics)) {
      const count = metrics.length;
      const avgMetrics = {};

      if (count === 0) {
        summary[variant] = { count: 0 };
        continue;
      }

      const metricKeys = Object.keys(metrics[0]).filter((key) => key !== 'timestamp');

      for (const key of metricKeys) {
        const values = metrics.map((m) => m[key]).filter((v) => v !== null && v !== undefined);
        if (values.length > 0) {
          avgMetrics[key] = values.reduce((sum, v) => sum + v, 0) / values.length;
        }
      }

      summary[variant] = {
        count,
        avg: avgMetrics,
      };
    }

    return summary;
  } catch (e) {
    console.error('[AB Test] Failed to get summary:', e);
    return {};
  }
}

/**
 * Export metrics for analysis
 * @param {string} testId - Test identifier
 * @returns {string} - CSV formatted metrics
 */
export function exportABTestMetrics(testId) {
  if (typeof window === 'undefined') return '';

  const stored = localStorage.getItem(AB_TEST_METRICS_KEY);
  if (!stored) return '';

  try {
    const allMetrics = JSON.parse(stored);
    const testMetrics = allMetrics[testId];

    if (!testMetrics) return '';

    const rows = [];
    rows.push(['variant', 'timestamp', 'fcp', 'lcp', 'cls', 'fid', 'domContentLoaded', 'loadComplete']);

    for (const [variant, metrics] of Object.entries(testMetrics)) {
      for (const metric of metrics) {
        rows.push([
          variant,
          metric.timestamp,
          metric.fcp || '',
          metric.lcp || '',
          metric.cls || '',
          metric.fid || '',
          metric.domContentLoaded || '',
          metric.loadComplete || '',
        ]);
      }
    }

    return rows.map((row) => row.join(',')).join('\n');
  } catch (e) {
    console.error('[AB Test] Failed to export metrics:', e);
    return '';
  }
}

/**
 * Clear A/B test data
 * @param {string} testId - Test identifier (optional, clears all if not provided)
 */
export function clearABTestData(testId = null) {
  if (typeof window === 'undefined') return;

  if (testId) {
    const stored = localStorage.getItem(AB_TEST_METRICS_KEY);
    if (stored) {
      try {
        const allMetrics = JSON.parse(stored);
        delete allMetrics[testId];
        localStorage.setItem(AB_TEST_METRICS_KEY, JSON.stringify(allMetrics));
      } catch (e) {
        console.error('[AB Test] Failed to clear test data:', e);
      }
    }

    const assignments = localStorage.getItem(AB_TEST_STORAGE_KEY);
    if (assignments) {
      try {
        const parsed = JSON.parse(assignments);
        delete parsed[testId];
        localStorage.setItem(AB_TEST_STORAGE_KEY, JSON.stringify(parsed));
      } catch (e) {
        console.error('[AB Test] Failed to clear assignment:', e);
      }
    }
  } else {
    localStorage.removeItem(AB_TEST_STORAGE_KEY);
    localStorage.removeItem(AB_TEST_METRICS_KEY);
  }

  console.log('[AB Test] Cleared data for:', testId || 'all tests');
}
