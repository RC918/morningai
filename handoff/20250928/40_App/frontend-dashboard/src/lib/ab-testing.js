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

/**
 * A/B Test Manager
 */
class ABTest {
  constructor(testId, variants, options = {}) {
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
  _loadOrAssignVariant() {
    if (this.options.persistVariant) {
      const stored = localStorage.getItem(`ab_test_${this.testId}`)
      if (stored && this.variants.some(v => v.id === stored)) {
        this.assignedVariant = stored
        return
      }
    }

    const totalWeight = this.variants.reduce((sum, v) => sum + (v.weight || 1), 0)
    const random = Math.random() * totalWeight
    
    let cumulativeWeight = 0
    for (const variant of this.variants) {
      cumulativeWeight += variant.weight || 1
      if (random <= cumulativeWeight) {
        this.assignedVariant = variant.id
        break
      }
    }

    if (this.options.persistVariant) {
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
  getVariant() {
    return this.assignedVariant
  }

  /**
   * Get the variant configuration
   * @returns {object} Variant configuration
   */
  getVariantConfig() {
    return this.variants.find(v => v.id === this.assignedVariant)
  }

  /**
   * Check if current variant matches the given variant ID
   * @param {string} variantId - Variant ID to check
   * @returns {boolean}
   */
  isVariant(variantId) {
    return this.assignedVariant === variantId
  }

  /**
   * Track an event for this A/B test
   * @param {string} eventName - Event name
   * @param {object} metadata - Additional event metadata
   */
  trackEvent(eventName, metadata = {}) {
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
  trackConversion(metadata = {}) {
    this.trackEvent('conversion', metadata)
  }

  /**
   * Track click event
   * @param {string} target - Click target
   * @param {object} metadata - Additional metadata
   */
  trackClick(target, metadata = {}) {
    this.trackEvent('click', { target, ...metadata })
  }

  /**
   * Internal event tracking
   * @private
   */
  _trackEvent(eventName, data) {
    const event = {
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
        variant: this.assignedVariant,
        event: eventName
      },
      extra: data
    })

    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', eventName, {
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
  _saveEvents() {
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
  getEvents() {
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
  exportData() {
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
  reset() {
    localStorage.removeItem(`ab_test_${this.testId}`)
    this._loadOrAssignVariant()
  }
}

/**
 * A/B Test Manager - Manages multiple tests
 */
class ABTestManager {
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
  createTest(testId, variants, options = {}) {
    if (this.tests.has(testId)) {
      return this.tests.get(testId)
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
  getTest(testId) {
    return this.tests.get(testId) || null
  }

  /**
   * Get all active tests
   * @returns {Array<ABTest>}
   */
  getAllTests() {
    return Array.from(this.tests.values())
  }

  /**
   * Export all test data
   * @returns {object}
   */
  exportAllData() {
    const data = {
      tests: Array.from(this.tests.values()).map(test => test.exportData()),
      exported_at: new Date().toISOString()
    }
    return data
  }

  /**
   * Calculate test results and statistical significance
   * @param {string} testId - Test ID
   * @returns {object} Test results
   */
  calculateResults(testId) {
    const test = this.getTest(testId)
    if (!test) {
      throw new Error(`Test ${testId} not found`)
    }

    const events = test.getEvents()
    const variantStats = {}

    test.variants.forEach(variant => {
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

    events.forEach(event => {
      const variant = event.variant
      if (!variantStats[variant]) return

      if (event.event === 'variant_assigned') {
        variantStats[variant].assignments++
      } else if (event.event === 'conversion') {
        variantStats[variant].conversions++
      } else if (event.event === 'click') {
        variantStats[variant].clicks++
      }
    })

    Object.values(variantStats).forEach(stats => {
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
      total_assignments: Object.values(variantStats).reduce((sum, v) => sum + v.assignments, 0),
      total_conversions: Object.values(variantStats).reduce((sum, v) => sum + v.conversions, 0),
      calculated_at: new Date().toISOString()
    }
  }

  /**
   * Normal CDF approximation for p-value calculation
   * @private
   */
  _normalCDF(x) {
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
export function createABTest(testId, variants, options = {}) {
  return abTestManager.createTest(testId, variants, options)
}

/**
 * Get an existing A/B test
 * @param {string} testId - Test ID
 * @returns {ABTest|null}
 */
export function getABTest(testId) {
  return abTestManager.getTest(testId)
}

/**
 * Calculate results for an A/B test
 * @param {string} testId - Test ID
 * @returns {object} Test results
 */
export function calculateABTestResults(testId) {
  return abTestManager.calculateResults(testId)
}

/**
 * Export all A/B test data
 * @returns {object}
 */
export function exportAllABTestData() {
  return abTestManager.exportAllData()
}

/**
 * React hook for A/B testing
 * @param {string} testId - Test ID
 * @param {Array} variants - Variant configurations
 * @param {object} options - Test options
 * @returns {object} { variant, isVariant, trackEvent, trackConversion, trackClick }
 */
export function useABTest(testId, variants, options = {}) {
  const test = createABTest(testId, variants, options)
  
  return {
    variant: test.getVariant(),
    variantConfig: test.getVariantConfig(),
    isVariant: (variantId) => test.isVariant(variantId),
    trackEvent: (eventName, metadata) => test.trackEvent(eventName, metadata),
    trackConversion: (metadata) => test.trackConversion(metadata),
    trackClick: (target, metadata) => test.trackClick(target, metadata)
  }
}

export { ABTest, ABTestManager }
export default abTestManager
