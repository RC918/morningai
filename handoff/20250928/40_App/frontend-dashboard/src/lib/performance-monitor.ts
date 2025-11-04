/**
 * Performance Monitoring for Accessibility Features
 * 
 * Tracks performance metrics for accessibility-related operations
 * to ensure they don't negatively impact user experience.
 */

interface PerformanceMetric {
  name: string
  duration: number
  timestamp: number
  metadata?: Record<string, any>
}

declare global {
  interface Window {
    __a11yPerformance?: AccessibilityPerformanceMonitor;
  }
}

class AccessibilityPerformanceMonitor {
  private metrics: PerformanceMetric[] = []
  private readonly maxMetrics = 100
  private readonly performanceThresholds = {
    screenReaderAnnouncement: 50, // ms
    focusTrap: 16, // ms (1 frame at 60fps)
    settingsUpdate: 100, // ms
    keyboardNavigation: 16, // ms
    ariaUpdate: 50 // ms
  }

  /**
   * Start measuring a performance metric
   */
  startMeasure(name: string): () => void {
    const startTime = performance.now()
    
    return () => {
      const duration = performance.now() - startTime
      this.recordMetric(name, duration)
      
      // Log warning if exceeds threshold
      const threshold = this.performanceThresholds[name as keyof typeof this.performanceThresholds]
      if (threshold && duration > threshold) {
        console.warn(
          `[A11y Performance] ${name} took ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`
        )
      }
    }
  }

  /**
   * Record a performance metric
   */
  private recordMetric(name: string, duration: number, metadata?: Record<string, any>): void {
    this.metrics.push({
      name,
      duration,
      timestamp: Date.now(),
      metadata
    })

    // Keep only the most recent metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics.shift()
    }
  }

  /**
   * Get performance statistics for a specific metric
   */
  getStats(name: string): {
    count: number
    avg: number
    min: number
    max: number
    p95: number
  } | null {
    const filtered = this.metrics.filter(m => m.name === name)
    
    if (filtered.length === 0) {
      return null
    }

    const durations = filtered.map(m => m.duration).sort((a, b) => a - b)
    const sum = durations.reduce((acc, val) => acc + val, 0)
    
    return {
      count: filtered.length,
      avg: sum / filtered.length,
      min: durations[0],
      max: durations[durations.length - 1],
      p95: durations[Math.floor(durations.length * 0.95)]
    }
  }

  /**
   * Get all metrics
   */
  getAllMetrics(): PerformanceMetric[] {
    return [...this.metrics]
  }

  /**
   * Get summary of all tracked metrics
   */
  getSummary(): Record<string, ReturnType<typeof this.getStats>> {
    const uniqueNames = [...new Set(this.metrics.map(m => m.name))]
    const summary: Record<string, ReturnType<typeof this.getStats>> = {}
    
    uniqueNames.forEach(name => {
      summary[name] = this.getStats(name)
    })
    
    return summary
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = []
  }

  /**
   * Log performance summary to console
   */
  logSummary(): void {
    const summary = this.getSummary()
    
    console.group('🎯 Accessibility Performance Summary')
    
    Object.entries(summary).forEach(([name, stats]) => {
      if (!stats) return
      
      const threshold = this.performanceThresholds[name as keyof typeof this.performanceThresholds]
      const exceedsThreshold = threshold && stats.avg > threshold
      
      console.log(
        `${exceedsThreshold ? '⚠️' : '✅'} ${name}:`,
        `avg=${stats.avg.toFixed(2)}ms`,
        `p95=${stats.p95.toFixed(2)}ms`,
        `count=${stats.count}`,
        threshold ? `(threshold: ${threshold}ms)` : ''
      )
    })
    
    console.groupEnd()
  }

  /**
   * Export metrics as JSON
   */
  exportMetrics(): string {
    return JSON.stringify({
      metrics: this.metrics,
      summary: this.getSummary(),
      timestamp: Date.now()
    }, null, 2)
  }
}

// Singleton instance
export const a11yPerformanceMonitor = new AccessibilityPerformanceMonitor()

// Development-only: Add to window for debugging
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  window.__a11yPerformance = a11yPerformanceMonitor
}

/**
 * Hook for measuring component render performance
 */
export function useA11yPerformance(componentName: string) {
  const measureRender = () => {
    return a11yPerformanceMonitor.startMeasure(`${componentName}:render`)
  }

  const measureInteraction = (interactionName: string) => {
    return a11yPerformanceMonitor.startMeasure(`${componentName}:${interactionName}`)
  }

  return {
    measureRender,
    measureInteraction
  }
}

/**
 * Decorator for measuring function performance
 */
export function measurePerformance(metricName: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value

    descriptor.value = function (...args: any[]) {
      const endMeasure = a11yPerformanceMonitor.startMeasure(metricName)
      try {
        const result = originalMethod.apply(this, args)
        
        // Handle async functions
        if (result instanceof Promise) {
          return result.finally(() => endMeasure())
        }
        
        endMeasure()
        return result
      } catch (error) {
        endMeasure()
        throw error
      }
    }

    return descriptor
  }
}
