/**
 * Metrics Analysis Framework
 * 
 * Collects and analyzes performance and UX metrics:
 * - Web Vitals (LCP, CLS, INP, FCP, TTFB)
 * - Custom metrics (TTV, task completion rates)
 * - Regression analysis and trend detection
 * - Automated reporting
 * 
 * @module metrics-analysis
 */

import * as Sentry from '@sentry/react'

interface Metric {
  category: string
  name: string
  value: number
  timestamp: number
  url: string
  [key: string]: any
}

interface WebVitals {
  [key: string]: number
}

interface PerformanceEntry {
  name: string
  duration: number
  entryType: string
  startTime: number
  renderTime?: number
  loadTime?: number
  hadRecentInput?: boolean
  value?: number
}

/**
 * Metrics Collector
 */
class MetricsCollector {
  metrics: Metric[]
  webVitals: WebVitals
  customMetrics: Record<string, any>
  isCollecting: boolean

  constructor() {
    this.metrics = []
    this.webVitals = {}
    this.customMetrics = {}
    this.isCollecting = false
  }

  /**
   * Start collecting metrics
   */
  startCollection(): void {
    this.isCollecting = true
    this._initWebVitalsObserver()
    this._initPerformanceObserver()
    console.log('[Metrics] Collection started')
  }

  /**
   * Stop collecting metrics
   */
  stopCollection(): void {
    this.isCollecting = false
    console.log('[Metrics] Collection stopped')
  }

  /**
   * Initialize Web Vitals observer
   * @private
   */
  _initWebVitalsObserver(): void {
    if (typeof window === 'undefined') return

    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          const lastEntry = entries[entries.length - 1] as any
          this.recordWebVital('LCP', lastEntry.renderTime || lastEntry.loadTime)
        })
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
      } catch (e) {
        console.warn('[Metrics] LCP observer failed:', e)
      }

      try {
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          entries.forEach((entry: any) => {
            if (entry.name === 'first-contentful-paint') {
              this.recordWebVital('FCP', entry.startTime)
            }
          })
        })
        fcpObserver.observe({ entryTypes: ['paint'] })
      } catch (e) {
        console.warn('[Metrics] FCP observer failed:', e)
      }

      try {
        let clsValue = 0
        const clsObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries() as any[]) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value
              this.recordWebVital('CLS', clsValue)
            }
          }
        })
        clsObserver.observe({ entryTypes: ['layout-shift'] })
      } catch (e) {
        console.warn('[Metrics] CLS observer failed:', e)
      }

      try {
        const inpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries()
          entries.forEach((entry: any) => {
            this.recordWebVital('INP', entry.duration)
          })
        })
        inpObserver.observe({ entryTypes: ['event'] })
      } catch (e) {
        console.warn('[Metrics] INP observer failed:', e)
      }
    }

    if (window.performance && (window.performance as any).timing) {
      const timing = (window.performance as any).timing
      const ttfb = timing.responseStart - timing.requestStart
      this.recordWebVital('TTFB', ttfb)
    }
  }

  /**
   * Initialize Performance Observer
   * @private
   */
  _initPerformanceObserver(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return

    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordMetric('performance', entry.name, entry.duration, {
            entry_type: entry.entryType,
            start_time: entry.startTime
          })
        }
      })
      observer.observe({ entryTypes: ['measure', 'navigation'] })
    } catch (e) {
      console.warn('[Metrics] Performance observer failed:', e)
    }
  }

  /**
   * Record a Web Vital metric
   * @param {string} name - Metric name (LCP, CLS, INP, FCP, TTFB)
   * @param {number} value - Metric value
   */
  recordWebVital(name: string, value: number): void {
    if (!this.isCollecting) return

    this.webVitals[name] = value

    this.recordMetric('web_vital', name, value, {
      timestamp: Date.now(),
      url: window.location.href
    })

    Sentry.captureMessage(`Web Vital: ${name}`, {
      level: 'info',
      tags: {
        type: 'web_vital',
        metric: name
      },
      extra: {
        value,
        url: window.location.href
      }
    })
  }

  /**
   * Record a custom metric
   * @param {string} category - Metric category
   * @param {string} name - Metric name
   * @param {number} value - Metric value
   * @param {object} metadata - Additional metadata
   */
  recordMetric(category: string, name: string, value: number, metadata: Record<string, any> = {}): void {
    if (!this.isCollecting) return

    const metric: Metric = {
      category,
      name,
      value,
      timestamp: Date.now(),
      url: window.location.href,
      ...metadata
    }

    this.metrics.push(metric)
    this._saveMetrics()
  }

  /**
   * Record Time to Value (TTV)
   * @param {number} ttv - Time to value in milliseconds
   * @param {object} metadata - Additional metadata
   */
  recordTTV(ttv: number, metadata: Record<string, any> = {}): void {
    this.recordMetric('ux', 'TTV', ttv, metadata)
  }

  /**
   * Record task completion
   * @param {string} taskId - Task identifier
   * @param {boolean} success - Whether task was successful
   * @param {number} duration - Task duration in milliseconds
   */
  recordTaskCompletion(taskId: string, success: boolean, duration: number): void {
    this.recordMetric('task', taskId, duration, {
      success,
      success_rate: success ? 100 : 0
    })
  }

  /**
   * Record error
   * @param {string} errorType - Error type
   * @param {string} message - Error message
   */
  recordError(errorType: string, message: string): void {
    this.recordMetric('error', errorType, 1, { message })
  }

  /**
   * Get all metrics
   * @returns {Array} Array of metrics
   */
  getAllMetrics(): Metric[] {
    return this.metrics
  }

  /**
   * Get metrics by category
   * @param {string} category - Category name
   * @returns {Array} Filtered metrics
   */
  getMetricsByCategory(category: string): Metric[] {
    return this.metrics.filter((m: Metric) => m.category === category)
  }

  /**
   * Get Web Vitals summary
   * @returns {object} Web Vitals data
   */
  getWebVitals(): WebVitals {
    return { ...this.webVitals }
  }

  /**
   * Save metrics to localStorage
   * @private
   */
  _saveMetrics(): void {
    try {
      const key = 'metrics_data'
      const existing = JSON.parse(localStorage.getItem(key) || '[]')
      const combined = [...existing, ...this.metrics]
      
      const trimmed = combined.slice(-1000)
      
      localStorage.setItem(key, JSON.stringify(trimmed))
      this.metrics = []
    } catch (error) {
      console.error('[Metrics] Failed to save metrics:', error)
    }
  }

  /**
   * Load metrics from localStorage
   * @returns {Array} Loaded metrics
   */
  static loadMetrics(): Metric[] {
    try {
      const key = 'metrics_data'
      return JSON.parse(localStorage.getItem(key) || '[]')
    } catch (error) {
      console.error('[Metrics] Failed to load metrics:', error)
      return []
    }
  }

  /**
   * Clear all metrics
   */
  static clearMetrics(): void {
    localStorage.removeItem('metrics_data')
  }

  /**
   * Export metrics data
   * @returns {object} Exported data
   */
  exportData(): any {
    return {
      web_vitals: this.webVitals,
      metrics: MetricsCollector.loadMetrics(),
      exported_at: new Date().toISOString()
    }
  }
}

/**
 * Metrics Analyzer
 */
class MetricsAnalyzer {
  /**
   * Analyze metrics and generate report
   * @param {Array} metrics - Array of metrics
   * @param {object} baseline - Baseline metrics for comparison
   * @returns {object} Analysis report
   */
  static analyze(metrics: Metric[], baseline: any = null): any {
    const report: any = {
      summary: this._generateSummary(metrics),
      web_vitals: this._analyzeWebVitals(metrics),
      ux_metrics: this._analyzeUXMetrics(metrics),
      task_performance: this._analyzeTaskPerformance(metrics),
      errors: this._analyzeErrors(metrics),
      trends: this._analyzeTrends(metrics),
      regression: baseline ? this._analyzeRegression(metrics, baseline) : null,
      recommendations: [],
      generated_at: new Date().toISOString()
    }

    report.recommendations = this._generateRecommendations(report)

    return report
  }

  /**
   * Generate summary statistics
   * @private
   */
  static _generateSummary(metrics: Metric[]): any {
    return {
      total_metrics: metrics.length,
      categories: [...new Set(metrics.map((m: Metric) => m.category))],
      time_range: {
        start: metrics.length > 0 ? new Date(Math.min(...metrics.map((m: Metric) => m.timestamp))).toISOString() : null,
        end: metrics.length > 0 ? new Date(Math.max(...metrics.map((m: Metric) => m.timestamp))).toISOString() : null
      }
    }
  }

  /**
   * Analyze Web Vitals
   * @private
   */
  static _analyzeWebVitals(metrics: Metric[]): any {
    const webVitals = metrics.filter((m: Metric) => m.category === 'web_vital')
    const vitals: Record<string, any> = {}

    const vitalNames = ['LCP', 'CLS', 'INP', 'FCP', 'TTFB']
    vitalNames.forEach((name: string) => {
      const values = webVitals.filter((m: Metric) => m.name === name).map((m: Metric) => m.value)
      if (values.length > 0) {
        vitals[name] = {
          current: values[values.length - 1],
          average: this._average(values),
          median: this._median(values),
          p90: this._percentile(values, 90),
          p95: this._percentile(values, 95),
          count: values.length,
          status: this._getWebVitalStatus(name, values[values.length - 1])
        }
      }
    })

    return vitals
  }

  /**
   * Analyze UX metrics
   * @private
   */
  static _analyzeUXMetrics(metrics: Metric[]): any {
    const uxMetrics = metrics.filter((m: Metric) => m.category === 'ux')
    
    const ttvValues = uxMetrics.filter((m: Metric) => m.name === 'TTV').map((m: Metric) => m.value)
    
    return {
      ttv: ttvValues.length > 0 ? {
        average: this._average(ttvValues),
        median: this._median(ttvValues),
        p90: this._percentile(ttvValues, 90),
        count: ttvValues.length,
        status: this._average(ttvValues) < 600000 ? 'good' : 'needs_improvement' // < 10 minutes
      } : null
    }
  }

  /**
   * Analyze task performance
   * @private
   */
  static _analyzeTaskPerformance(metrics: Metric[]): any {
    const taskMetrics = metrics.filter((m: Metric) => m.category === 'task')
    
    const totalTasks = taskMetrics.length
    const successfulTasks = taskMetrics.filter((m: any) => m.success).length
    const successRate = totalTasks > 0 ? (successfulTasks / totalTasks * 100).toFixed(2) : 0

    const durations = taskMetrics.map((m: Metric) => m.value)

    return {
      total_tasks: totalTasks,
      successful_tasks: successfulTasks,
      failed_tasks: totalTasks - successfulTasks,
      success_rate: parseFloat(successRate as string),
      avg_duration: durations.length > 0 ? this._average(durations) : 0,
      median_duration: durations.length > 0 ? this._median(durations) : 0,
      status: parseFloat(successRate as string) >= 90 ? 'excellent' : parseFloat(successRate as string) >= 75 ? 'good' : 'needs_improvement'
    }
  }

  /**
   * Analyze errors
   * @private
   */
  static _analyzeErrors(metrics: Metric[]): any {
    const errorMetrics = metrics.filter((m: Metric) => m.category === 'error')
    
    const errorsByType: Record<string, number> = {}
    errorMetrics.forEach((m: Metric) => {
      if (!errorsByType[m.name]) {
        errorsByType[m.name] = 0
      }
      errorsByType[m.name]++
    })

    return {
      total_errors: errorMetrics.length,
      errors_by_type: errorsByType,
      error_rate: metrics.length > 0 ? (errorMetrics.length / metrics.length * 100).toFixed(2) : 0
    }
  }

  /**
   * Analyze trends over time
   * @private
   */
  static _analyzeTrends(metrics: Metric[]): any {
    const metricsByDay: Record<string, Metric[]> = {}
    
    metrics.forEach((m: Metric) => {
      const date = new Date(m.timestamp).toISOString().split('T')[0]
      if (!metricsByDay[date]) {
        metricsByDay[date] = []
      }
      metricsByDay[date].push(m)
    })

    const days = Object.keys(metricsByDay).sort()
    
    return {
      daily_counts: days.map((day: string) => ({
        date: day,
        count: metricsByDay[day].length
      })),
      trend: days.length >= 2 ? 
        (metricsByDay[days[days.length - 1]].length > metricsByDay[days[0]].length ? 'increasing' : 'decreasing') 
        : 'stable'
    }
  }

  /**
   * Analyze regression compared to baseline
   * @private
   */
  static _analyzeRegression(metrics: Metric[], baseline: any): any {
    const current = this.analyze(metrics)
    const regression: any = {}

    if (baseline.web_vitals && current.web_vitals) {
      regression.web_vitals = {}
      Object.keys(baseline.web_vitals).forEach((vital: string) => {
        if (current.web_vitals[vital]) {
          const baselineValue = baseline.web_vitals[vital].average
          const currentValue = current.web_vitals[vital].average
          const change = ((currentValue - baselineValue) / baselineValue * 100).toFixed(2)
          
          regression.web_vitals[vital] = {
            baseline: baselineValue,
            current: currentValue,
            change_percent: parseFloat(change),
            improved: this._isWebVitalImproved(vital, baselineValue, currentValue)
          }
        }
      })
    }

    if (baseline.task_performance && current.task_performance) {
      const baselineRate = baseline.task_performance.success_rate
      const currentRate = current.task_performance.success_rate
      const change = currentRate - baselineRate

      regression.task_success_rate = {
        baseline: baselineRate,
        current: currentRate,
        change_percent: change.toFixed(2),
        improved: change > 0
      }
    }

    return regression
  }

  /**
   * Generate recommendations based on analysis
   * @private
   */
  static _generateRecommendations(report: any): any[] {
    const recommendations: any[] = []

    if (report.web_vitals) {
      Object.entries(report.web_vitals).forEach(([vital, data]: [string, any]) => {
        if (data.status === 'needs_improvement' || data.status === 'poor') {
          recommendations.push({
            category: 'web_vitals',
            priority: 'high',
            metric: vital,
            message: `${vital} needs improvement (current: ${data.current.toFixed(2)})`,
            suggestion: this._getWebVitalSuggestion(vital)
          })
        }
      })
    }

    if (report.task_performance && report.task_performance.success_rate < 90) {
      recommendations.push({
        category: 'task_performance',
        priority: 'high',
        message: `Task success rate is ${report.task_performance.success_rate}% (target: >90%)`,
        suggestion: 'Review failed tasks and identify common pain points. Consider usability testing.'
      })
    }

    if (report.errors && parseFloat(report.errors.error_rate) > 5) {
      recommendations.push({
        category: 'errors',
        priority: 'high',
        message: `Error rate is ${report.errors.error_rate}% (target: <5%)`,
        suggestion: 'Investigate and fix the most common errors. Improve error handling and user feedback.'
      })
    }

    return recommendations
  }

  /**
   * Get Web Vital status
   * @private
   */
  static _getWebVitalStatus(name: string, value: number): string {
    const thresholds: Record<string, { good: number; needs_improvement: number }> = {
      LCP: { good: 2500, needs_improvement: 4000 },
      CLS: { good: 0.1, needs_improvement: 0.25 },
      INP: { good: 200, needs_improvement: 500 },
      FCP: { good: 1800, needs_improvement: 3000 },
      TTFB: { good: 800, needs_improvement: 1800 }
    }

    const threshold = thresholds[name]
    if (!threshold) return 'unknown'

    if (value <= threshold.good) return 'good'
    if (value <= threshold.needs_improvement) return 'needs_improvement'
    return 'poor'
  }

  /**
   * Check if Web Vital improved
   * @private
   */
  static _isWebVitalImproved(name: string, baseline: number, current: number): boolean {
    return current < baseline
  }

  /**
   * Get Web Vital suggestion
   * @private
   */
  static _getWebVitalSuggestion(vital: string): string {
    const suggestions: Record<string, string> = {
      LCP: 'Optimize images, use CDN, implement lazy loading, reduce server response time',
      CLS: 'Set explicit dimensions for images/videos, avoid inserting content above existing content',
      INP: 'Optimize JavaScript execution, reduce main thread work, use web workers',
      FCP: 'Reduce render-blocking resources, optimize CSS delivery, use font-display: swap',
      TTFB: 'Optimize server response time, use CDN, implement caching'
    }
    return suggestions[vital] || 'Review performance best practices'
  }

  /**
   * Calculate average
   * @private
   */
  static _average(values: number[]): number {
    return values.reduce((sum: number, v: number) => sum + v, 0) / values.length
  }

  /**
   * Calculate median
   * @private
   */
  static _median(values: number[]): number {
    const sorted = [...values].sort((a: number, b: number) => a - b)
    const mid = Math.floor(sorted.length / 2)
    return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
  }

  /**
   * Calculate percentile
   * @private
   */
  static _percentile(values: number[], p: number): number {
    const sorted = [...values].sort((a: number, b: number) => a - b)
    const index = Math.ceil((p / 100) * sorted.length) - 1
    return sorted[index]
  }
}

const metricsCollector = new MetricsCollector()

/**
 * Start metrics collection
 */
export function startMetricsCollection(): void {
  metricsCollector.startCollection()
}

/**
 * Stop metrics collection
 */
export function stopMetricsCollection(): void {
  metricsCollector.stopCollection()
}

/**
 * Record a custom metric
 */
export function recordMetric(category: string, name: string, value: number, metadata?: Record<string, any>): void {
  metricsCollector.recordMetric(category, name, value, metadata)
}

/**
 * Get metrics analysis report
 */
export function getMetricsReport(baseline: any = null): any {
  const metrics = MetricsCollector.loadMetrics()
  return MetricsAnalyzer.analyze(metrics, baseline)
}

/**
 * Export metrics data
 */
export function exportMetricsData(): any {
  return metricsCollector.exportData()
}

export { MetricsCollector, MetricsAnalyzer }
export default metricsCollector
