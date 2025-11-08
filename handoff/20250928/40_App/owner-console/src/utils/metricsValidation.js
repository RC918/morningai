/**
 * Metrics Data Validation Utilities
 * 
 * Provides runtime validation for metrics data structures to prevent
 * TypeError crashes from undefined/null property access.
 */

/**
 * Validate that metrics data has the required structure
 * @param {any} data - Data to validate
 * @returns {boolean} True if valid, false otherwise
 */
export function validateMetricsData(data) {
  if (!data || typeof data !== 'object') {
    console.error('[MetricsValidation] Invalid metrics data: not an object', data)
    return false
  }

  if (!data.generated_at || typeof data.generated_at !== 'string') {
    console.error('[MetricsValidation] Missing or invalid generated_at field')
    return false
  }

  if (typeof data.total_prs !== 'number') {
    console.error('[MetricsValidation] Missing or invalid total_prs field')
    return false
  }

  if (!Array.isArray(data.metrics)) {
    console.error('[MetricsValidation] Missing or invalid metrics array')
    return false
  }

  if (!data.summary || typeof data.summary !== 'object') {
    console.error('[MetricsValidation] Missing or invalid summary object')
    return false
  }

  if (!data.thresholds || typeof data.thresholds !== 'object') {
    console.error('[MetricsValidation] Missing or invalid thresholds object')
    return false
  }

  return true
}

/**
 * Validate app summary structure
 * @param {any} appSummary - App summary to validate
 * @param {string} appName - Name of the app (for logging)
 * @returns {boolean} True if valid, false otherwise
 */
export function validateAppSummary(appSummary, appName) {
  if (!appSummary || typeof appSummary !== 'object') {
    console.warn(`[MetricsValidation] Invalid app summary for ${appName}:`, appSummary)
    return false
  }

  if (typeof appSummary.total_prs !== 'number') {
    console.warn(`[MetricsValidation] Missing total_prs for ${appName}`)
    return false
  }

  return true
}

/**
 * Safely get nested property with optional chaining
 * @param {any} obj - Object to access
 * @param {string} path - Dot-separated path (e.g., 'summary.apps.frontend-dashboard.i18n.avg_coverage')
 * @param {any} defaultValue - Default value if path doesn't exist
 * @returns {any} Value at path or default value
 */
export function safeGet(obj, path, defaultValue = null) {
  if (!obj || typeof obj !== 'object') {
    return defaultValue
  }

  const keys = path.split('.')
  let current = obj

  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return defaultValue
    }
    current = current[key]
  }

  return current !== undefined ? current : defaultValue
}

/**
 * Validate and sanitize metrics data
 * Returns a safe version with guaranteed structure
 * @param {any} data - Raw metrics data
 * @returns {Object} Sanitized metrics data
 */
export function sanitizeMetricsData(data) {
  if (!validateMetricsData(data)) {
    console.error('[MetricsValidation] Data validation failed, returning empty structure')
    return {
      generated_at: new Date().toISOString(),
      total_prs: 0,
      metrics: [],
      summary: {
        apps: {},
        lighthouse: null
      },
      thresholds: {
        i18n: { target: 95 },
        a11y: { critical: 0, serious: 0 },
        motion: { p95: 16.67 },
        vrt: { mismatch: 0.1 },
        lighthouse: { fcp: 1000, lcp: 2500 }
      }
    }
  }

  if (!data.summary.apps || typeof data.summary.apps !== 'object') {
    data.summary.apps = {}
  }

  const appNames = ['frontend-dashboard', 'owner-console']
  appNames.forEach(appName => {
    if (!data.summary.apps[appName]) {
      console.warn(`[MetricsValidation] Missing app summary for ${appName}, creating default`)
      data.summary.apps[appName] = {
        total_prs: 0,
        i18n: { available: 0, parsed: 0, avg_coverage: null, pass_rate: null },
        a11y: { available: 0, parsed: 0, avg_critical: null, avg_serious: null },
        motion: { available: 0, parsed: 0, avg_p95: null },
        vrt: { available: 0, parsed: 0, avg_mismatch: null }
      }
    }
  })

  return data
}

/**
 * Check if a metric value is valid (not null/undefined)
 * @param {any} value - Value to check
 * @returns {boolean} True if valid
 */
export function isValidMetricValue(value) {
  return value !== null && value !== undefined
}

/**
 * Get safe metric value with fallback
 * @param {any} value - Metric value
 * @param {string} fallback - Fallback text
 * @returns {any} Value or fallback
 */
export function getMetricValueOrFallback(value, fallback = 'N/A') {
  return isValidMetricValue(value) ? value : fallback
}
