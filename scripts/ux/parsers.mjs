/**
 * UX Metrics Parsers
 * 
 * Pure functions for parsing UX metrics from CI check run outputs.
 * These functions extract numeric values from various text formats.
 */

/**
 * Parse i18n coverage percentage from text
 * @param {string} text - Check run output text
 * @returns {number|null} - Coverage percentage (0-100) or null if not found
 * 
 * Supported formats:
 * - "coverage: 96.2%"
 * - "Coverage 96%"
 * - "i18n coverage – 95.00 %"
 */
export function parseI18nCoverage(text) {
  if (!text || typeof text !== 'string') return null;
  
  const coverageMatch = text.match(/coverage[:\s–-]+(\d+(?:\.\d+)?)\s*%/i);
  return coverageMatch ? parseFloat(coverageMatch[1]) : null;
}

/**
 * Parse a11y violations from text
 * @param {string} text - Check run output text
 * @returns {{critical: number, serious: number}|null} - Violation counts or null
 * 
 * Supported formats:
 * - "critical: 0, serious: 2"
 * - "Critical Issues: 1; Serious: 0"
 * - Multi-line: "Critical 2\nSerious 1"
 */
export function parseA11yViolations(text) {
  if (!text || typeof text !== 'string') return null;
  
  const criticalMatch = text.match(/critical(?:\s+issues)?[:\s]+(\d+)/i);
  const seriousMatch = text.match(/serious(?:\s+issues)?[:\s]+(\d+)/i);
  
  if (!criticalMatch && !seriousMatch) return null;
  
  return {
    critical: criticalMatch ? parseInt(criticalMatch[1], 10) : 0,
    serious: seriousMatch ? parseInt(seriousMatch[1], 10) : 0
  };
}

/**
 * Parse motion P95 frame time from text
 * @param {string} text - Check run output text
 * @returns {number|null} - P95 frame time in milliseconds or null
 * 
 * Supported formats:
 * - "p95: 16.5ms"
 * - "P95 = 17 ms"
 * - "p95 17" (assumes ms)
 * - "p95FrameTime: 16.67"
 */
export function parseMotionP95(text) {
  if (!text || typeof text !== 'string') return null;
  
  const p95Match = text.match(/p95(?:\s*frame\s*time)?[:\s=]+(\d+(?:\.\d+)?)\s*(?:ms)?/i);
  return p95Match ? parseFloat(p95Match[1]) : null;
}

/**
 * Parse VRT mismatch percentage from text
 * @param {string} text - Check run output text
 * @returns {number|null} - Mismatch percentage (0-100) or null
 * 
 * Supported formats:
 * - "mismatch: 0.12%"
 * - "Mismatch 0.5 %"
 * - "visual mismatch: 0.05%"
 */
export function parseVrtMismatch(text) {
  if (!text || typeof text !== 'string') return null;
  
  const mismatchMatch = text.match(/(?:visual\s+)?mismatch[:\s]+(\d+(?:\.\d+)?)\s*%/i);
  return mismatchMatch ? parseFloat(mismatchMatch[1]) : null;
}

/**
 * Evaluate if a metric passes the threshold
 * @param {number} value - Metric value
 * @param {number} threshold - Threshold value
 * @param {string} comparison - 'lte' (less than or equal) or 'gte' (greater than or equal)
 * @returns {boolean} - True if metric passes threshold
 */
export function evaluateThreshold(value, threshold, comparison = 'lte') {
  if (value === null || value === undefined || threshold === null || threshold === undefined) {
    return false;
  }
  
  if (comparison === 'lte') {
    return value <= threshold;
  } else if (comparison === 'gte') {
    return value >= threshold;
  }
  
  return false;
}
