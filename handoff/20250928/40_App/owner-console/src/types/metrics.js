/**
 * Type definitions for UX Metrics data structures
 * 
 * This file provides JSDoc type definitions for metrics data to enable
 * better IDE support and runtime validation.
 */

/**
 * @typedef {Object} MetricValue
 * @property {'parsed' | 'available' | 'unavailable'} status - Status of the metric
 * @property {number} [value] - Numeric value (only present when status is 'parsed')
 * @property {boolean} [passed] - Whether the metric passed threshold (only when parsed)
 */

/**
 * @typedef {Object} AppMetrics
 * @property {MetricValue} [i18n] - i18n coverage metric
 * @property {MetricValue} [a11y] - Accessibility metric
 * @property {MetricValue} [motion] - Motion performance metric
 * @property {MetricValue} [vrt] - Visual regression test metric
 */

/**
 * @typedef {Object} LighthouseMetrics
 * @property {number} fcp - First Contentful Paint (ms)
 * @property {number} lcp - Largest Contentful Paint (ms)
 */

/**
 * @typedef {Object} PRMetric
 * @property {number} pr - PR number
 * @property {string} title - PR title
 * @property {string} author - PR author
 * @property {string} merged_at - ISO timestamp of merge
 * @property {string} url - GitHub URL
 * @property {LighthouseMetrics} [lighthouse] - Lighthouse metrics
 * @property {Object.<string, AppMetrics>} apps - Metrics by app name
 */

/**
 * @typedef {Object} AppSummaryMetrics
 * @property {number} total_prs - Total PRs for this app
 * @property {Object} [i18n] - i18n summary
 * @property {number} i18n.available - Number of PRs with i18n data
 * @property {number} i18n.parsed - Number of PRs with parsed i18n values
 * @property {number|null} i18n.avg_coverage - Average coverage percentage
 * @property {number|null} i18n.pass_rate - Pass rate percentage
 * @property {Object} [a11y] - Accessibility summary
 * @property {number} a11y.available - Number of PRs with a11y data
 * @property {number} a11y.parsed - Number of PRs with parsed a11y values
 * @property {number|null} a11y.avg_critical - Average critical violations
 * @property {number|null} a11y.avg_serious - Average serious violations
 * @property {Object} [motion] - Motion performance summary
 * @property {number} motion.available - Number of PRs with motion data
 * @property {number} motion.parsed - Number of PRs with parsed motion values
 * @property {number|null} motion.avg_p95 - Average P95 frame time
 * @property {Object} [vrt] - VRT summary
 * @property {number} vrt.available - Number of PRs with VRT data
 * @property {number} vrt.parsed - Number of PRs with parsed VRT values
 * @property {number|null} vrt.avg_mismatch - Average mismatch percentage
 */

/**
 * @typedef {Object} MetricsSummary
 * @property {Object.<string, AppSummaryMetrics>} apps - Summary by app name
 * @property {Object} [lighthouse] - Lighthouse summary
 * @property {number} lighthouse.fcp_avg - Average FCP
 * @property {number} lighthouse.lcp_avg - Average LCP
 */

/**
 * @typedef {Object} MetricsThresholds
 * @property {Object} i18n - i18n thresholds
 * @property {number} i18n.target - Target coverage percentage
 * @property {Object} a11y - Accessibility thresholds
 * @property {number} a11y.critical - Max critical violations
 * @property {number} a11y.serious - Max serious violations
 * @property {Object} motion - Motion performance thresholds
 * @property {number} motion.p95 - Max P95 frame time (ms)
 * @property {Object} vrt - VRT thresholds
 * @property {number} vrt.mismatch - Max mismatch percentage
 * @property {Object} lighthouse - Lighthouse thresholds
 * @property {number} lighthouse.fcp - Max FCP (ms)
 * @property {number} lighthouse.lcp - Max LCP (ms)
 */

/**
 * @typedef {Object} MetricsData
 * @property {string} generated_at - ISO timestamp of generation
 * @property {number} total_prs - Total number of PRs
 * @property {PRMetric[]} metrics - Array of PR metrics
 * @property {MetricsSummary} summary - Aggregated summary
 * @property {MetricsThresholds} thresholds - Quality thresholds
 */

export {}
