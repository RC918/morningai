/**
 * A/B Testing Framework
 * 
 * Provides a simple, lightweight A/B testing system for frontend experiments:
 * - Variant assignment and persistence
 * - Event tracking and analytics
 * - Statistical significance calculation
 * - Integration with analytics platforms
 * 
 * @module ab-testing
 */

import * as Sentry from '@sentry/react'

interface Variant {
  id: string
  name: string
  weight?: number
}

interface ABTestOptions {
  persistVariant?: boolean
  trackingEnabled?: boolean
}

interface ABTestEvent {
  timestamp: number
  event: string
  variant?: string
  test_id?: string
  [key: string]: any
}

/**
 * A/B Test Manager
 */
class ABTest {
  testId: string
  variants: Variant[]
  options: Required<ABTestOptions>
  assignedVariant: string | null
  events: ABTestEvent[]

  constructor(testId: string, variants: Variant[], options: ABTestOptions = {}) {
    this.testId = testId
    this.variants = variants
    this.options = {
      persistVariant: true,
      trackingEnabled: true,
      ...options
    }
    
    this.assignedVariant = null
    this.events = []
    
    this._loadOrAssignVariant()
  }

  /**
   * Load existing variant assignment or assign a new one
   * @private
   */
  _loadOrAssignVariant(): void {
    if (this.options.persistVariant) {
      const stored = localStorage.getItem(`ab_test_${this.testId}`)
      if (stored && this.variants.some((v: Variant) => v.id === stored)) {
        this.assignedVariant = stored
        return
      }
    }

    const totalWeight = this.variants.reduce((sum: number, v: Variant) => sum + (v.weight || 1), 0)
    const random = Math.random() * totalWeight
    
    let cumulativeWeight = 0
    for (const variant of this.variants) {
      cumulativeWeight += variant.weight || 1
      if (random <= cumulativeWeight) {
        this.assignedVariant = variant.id
        break
      }
    }

    if (this.options.persistVariant && this.assignedVariant) {
      localStorage.setItem(`ab_test_${this.testId}`, this.assignedVariant)
    }

    if (this.options.trackingEnabled) {
      this._trackEvent('variant_assigned', {
        variant: this.assignedVariant,
        test_id: this.testId
      })
    }
  }

  /**
   * Get the assigned variant
   * @returns {string} Variant ID
   */
  getVariant(): string | null {
    return this.assignedVariant
  }

  /**
   * Get the variant configuration
   * @returns {object} Variant configuration
   */
  getVariantConfig(): Variant | undefined {
    return this.variants.find((v: Variant) => v.id === this.assignedVariant)
  }

  /**
   * Check if current variant matches the given variant ID
   * @param {string} variantId - Variant ID to check
   * @returns {boolean}
   */
  isVariant(variantId: string): boolean {
    return this.assignedVariant === variantId
  }

  /**
   * Track an event for this A/B test
   * @param {string} eventName - Event name
   * @param {object} metadata - Additional event metadata
   */
  trackEvent(eventName: string, metadata: Record<string, any> = {}): void {
    if (!this.options.trackingEnabled) return

    this._trackEvent(eventName, {
      variant: this.assignedVariant,
      test_id: this.testId,
      ...metadata
    })
  }

  /**
   * Track conversion event
   * @param {object} metadata - Additional metadata
   */
  trackConversion(metadata: Record<string, any> = {}): void {
    this.trackEvent('conversion', metadata)
  }

  /**
   * Track click event
   * @param {string} target - Click target
   * @param {object} metadata - Additional metadata
   */
  trackClick(target: string, metadata: Record<string, any> = {}): void {
    this.trackEvent('click', { target, ...metadata })
  }

  /**
   * Internal event tracking
   * @private
   */
  _trackEvent(eventName: string, data: Record<string, any>): void {
    const event: ABTestEvent = {
      timestamp: Date.now(),
      event: eventName,
      ...data
    }

    this.events.push(event)

    Sentry.captureMessage(`AB Test Event: ${eventName}`, {
      level: 'info',
      tags: {
        type: 'ab_test',
        test_id: this.testId,
        variant: this.assignedVariant || undefined,
        event: eventName
      },
      extra: data
    })

    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', eventName, {
        event_category: 'ab_test',
        event_label: this.testId,
        ab_test_id: this.testId,
        ab_test_variant: this.assignedVariant,
        ...data
      })
    }

    this._saveEvents()
  }

  /**
   * Save events to localStorage
   * @private
   */
  _saveEvents(): void {
    try {
      const key = `ab_test_events_${this.testId}`
      const existing = JSON.parse(localStorage.getItem(key) || '[]')
      existing.push(...this.events)
      localStorage.setItem(key, JSON.stringify(existing))
      this.events = []
    } catch (error) {
      console.error('[AB Test] Failed to save events:', error)
    }
  }

  /**
   * Get all events for this test
   * @returns {Array} Array of events
   */
  getEvents(): ABTestEvent[] {
    try {
      const key = `ab_test_events_${this.testId}`
      return JSON.parse(localStorage.getItem(key) || '[]')
    } catch (error) {
      console.error('[AB Test] Failed to load events:', error)
      return []
    }
  }

  /**
   * Export test data for analysis
   * @returns {object} Test data
   */
  exportData(): any {
    return {
      test_id: this.testId,
      assigned_variant: this.assignedVariant,
      variants: this.variants,
      events: this.getEvents(),
      exported_at: new Date().toISOString()
    }
  }

  /**
   * Reset variant assignment (for testing)
   */
  reset(): void {
    localStorage.removeItem(`ab_test_${this.testId}`)
    this._loadOrAssignVariant()
  }
}

/**
 * A/B Test Manager - Manages multiple tests
 */
class ABTestManager {
  tests: Map<string, ABTest>

  constructor() {
    this.tests = new Map()
  }

  /**
   * Create or get an A/B test
   * @param {string} testId - Unique test identifier
   * @param {Array} variants - Array of variant configurations
   * @param {object} options - Test options
   * @returns {ABTest}
   */
  createTest(testId: string, variants: Variant[], options: ABTestOptions = {}): ABTest {
    if (this.tests.has(testId)) {
      return this.tests.get(testId)!
    }

    const test = new ABTest(testId, variants, options)
    this.tests.set(testId, test)
    return test
  }

  /**
   * Get an existing test
   * @param {string} testId - Test ID
   * @returns {ABTest|null}
   */
  getTest(testId: string): ABTest | null {
    return this.tests.get(testId) || null
  }

  /**
   * Get all active tests
   * @returns {Array<ABTest>}
   */
  getAllTests(): ABTest[] {
    return Array.from(this.tests.values())
  }

  /**
   * Export all test data
   * @returns {object}
   */
  exportAllData(): any {
    const data = {
      tests: Array.from(this.tests.values()).map((test: ABTest) => test.exportData()),
      exported_at: new Date().toISOString()
    }
    return data
  }

  /**
   * Calculate test results and statistical significance
   * @param {string} testId - Test ID
   * @returns {object} Test results
   */
  calculateResults(testId: string): any {
    const test = this.getTest(testId)
    if (!test) {
      throw new Error(`Test ${testId} not found`)
    }

    const events = test.getEvents()
    const variantStats: Record<string, any> = {}

    test.variants.forEach((variant: Variant) => {
      variantStats[variant.id] = {
        variant_id: variant.id,
        variant_name: variant.name,
        assignments: 0,
        conversions: 0,
        clicks: 0,
        conversion_rate: 0,
        click_rate: 0
      }
    })

    events.forEach((event: ABTestEvent) => {
      const variant = event.variant
      if (!variant || !variantStats[variant]) return

      if (event.event === 'variant_assigned') {
        variantStats[variant].assignments++
      } else if (event.event === 'conversion') {
        variantStats[variant].conversions++
      } else if (event.event === 'click') {
        variantStats[variant].clicks++
      }
    })

    Object.values(variantStats).forEach((stats: any) => {
      if (stats.assignments > 0) {
        stats.conversion_rate = (stats.conversions / stats.assignments * 100).toFixed(2)
        stats.click_rate = (stats.clicks / stats.assignments * 100).toFixed(2)
      }
    })

    const variants = Object.values(variantStats)
    let significance = null

    if (variants.length === 2) {
      const [variantA, variantB] = variants
      
      const n1 = variantA.assignments
      const n2 = variantB.assignments
      const x1 = variantA.conversions
      const x2 = variantB.conversions

      if (n1 > 0 && n2 > 0) {
        const p1 = x1 / n1
        const p2 = x2 / n2
        const pPool = (x1 + x2) / (n1 + n2)
        
        const se = Math.sqrt(pPool * (1 - pPool) * (1/n1 + 1/n2))
        const zScore = (p1 - p2) / se
        const pValue = 2 * (1 - this._normalCDF(Math.abs(zScore)))

        significance = {
          z_score: zScore.toFixed(4),
          p_value: pValue.toFixed(4),
          is_significant: pValue < 0.05,
          confidence_level: ((1 - pValue) * 100).toFixed(1) + '%',
          winner: p1 > p2 ? variantA.variant_id : variantB.variant_id,
          lift: ((Math.abs(p1 - p2) / Math.min(p1, p2)) * 100).toFixed(2) + '%'
        }
      }
    }

    return {
      test_id: testId,
      variants: variantStats,
      significance,
      total_assignments: Object.values(variantStats).reduce((sum: number, v: any) => sum + v.assignments, 0),
      total_conversions: Object.values(variantStats).reduce((sum: number, v: any) => sum + v.conversions, 0),
      calculated_at: new Date().toISOString()
    }
  }

  /**
   * Normal CDF approximation for p-value calculation
   * @private
   */
  _normalCDF(x: number): number {
    const t = 1 / (1 + 0.2316419 * Math.abs(x))
    const d = 0.3989423 * Math.exp(-x * x / 2)
    const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    return x > 0 ? 1 - p : p
  }
}

const abTestManager = new ABTestManager()

/**
 * Create an A/B test
 * @param {string} testId - Unique test identifier
 * @param {Array} variants - Array of variant configurations
 * @param {object} options - Test options
 * @returns {ABTest}
 * 
 * @example
 * const test = createABTest('dashboard-cta', [
 *   { id: 'control', name: 'Original', weight: 1 },
 *   { id: 'variant-a', name: 'New CTA', weight: 1 }
 * ])
 * 
 * if (test.isVariant('variant-a')) {
 *   // Show new CTA
 * }
 * 
 * test.trackConversion()
 */
export function createABTest(testId: string, variants: Variant[], options: ABTestOptions = {}): ABTest {
  return abTestManager.createTest(testId, variants, options)
}

/**
 * Get an existing A/B test
 * @param {string} testId - Test ID
 * @returns {ABTest|null}
 */
export function getABTest(testId: string): ABTest | null {
  return abTestManager.getTest(testId)
}

/**
 * Calculate results for an A/B test
 * @param {string} testId - Test ID
 * @returns {object} Test results
 */
export function calculateABTestResults(testId: string): any {
  return abTestManager.calculateResults(testId)
}

/**
 * Export all A/B test data
 * @returns {object}
 */
export function exportAllABTestData(): any {
  return abTestManager.exportAllData()
}

/**
 * React hook for A/B testing
 * @param {string} testId - Test ID
 * @param {Array} variants - Variant configurations
 * @param {object} options - Test options
 * @returns {object} { variant, isVariant, trackEvent, trackConversion, trackClick }
 */
export function useABTest(testId: string, variants: Variant[], options: ABTestOptions = {}): any {
  const test = createABTest(testId, variants, options)
  
  return {
    variant: test.getVariant(),
    variantConfig: test.getVariantConfig(),
    isVariant: (variantId: string) => test.isVariant(variantId),
    trackEvent: (eventName: string, metadata?: Record<string, any>) => test.trackEvent(eventName, metadata),
    trackConversion: (metadata?: Record<string, any>) => test.trackConversion(metadata),
    trackClick: (target: string, metadata?: Record<string, any>) => test.trackClick(target, metadata)
  }
}

export { ABTest, ABTestManager }
export default abTestManager
