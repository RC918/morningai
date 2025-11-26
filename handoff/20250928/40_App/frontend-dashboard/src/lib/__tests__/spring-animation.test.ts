/**
 * Unit Tests for Spring Animation System
 * 
 * Tests core functionality of spring animation helpers including:
 * - Spring configuration generation
 * - Haptic feedback triggering
 * - Reduced motion support
 * - Animation variant generation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  getSpringConfig,
  getSpringVariants,
  triggerHaptic,
  getHapticAnimation,
  springPresets,
  hapticTypes,
  getUserContext,
  getContextualAnimation,
  createAnimationSequence,
  getStaggerConfig,
  trackAnimation,
  getAnimationMetrics,
  resetAnimationMetrics,
} from '../spring-animation'

describe('Spring Animation System', () => {
  describe('getSpringConfig', () => {
    it('should return default spring config when no preset specified', () => {
      const config = getSpringConfig()
      expect(config).toEqual(springPresets.default)
    })

    it('should return correct spring config for each preset', () => {
      const presets = ['gentle', 'default', 'bouncy', 'snappy', 'smooth', 'wobbly'] as const
      
      presets.forEach(preset => {
        const config = getSpringConfig(preset)
        expect(config).toEqual(springPresets[preset])
        expect(config).toHaveProperty('type', 'spring')
        expect(config).toHaveProperty('stiffness')
        expect(config).toHaveProperty('damping')
        expect(config).toHaveProperty('mass')
      })
    })

    it('should return default config for unknown preset', () => {
      const config = getSpringConfig('unknown-preset')
      expect(config).toEqual(springPresets.default)
    })

    it('should return zero duration when prefers-reduced-motion is enabled', () => {
      // Mock matchMedia to return prefers-reduced-motion: reduce
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const config = getSpringConfig('default')
      expect(config).toEqual({ duration: 0 })

      vi.unstubAllGlobals()
    })
  })

  describe('getSpringVariants', () => {
    it('should return fade variant by default', () => {
      const variants = getSpringVariants()
      expect(variants).toHaveProperty('initial')
      expect(variants).toHaveProperty('animate')
      expect(variants.initial).toHaveProperty('opacity', 0)
      expect(variants.animate).toHaveProperty('opacity', 1)
    })

    it('should return correct variants for each animation type', () => {
      const types = [
        'fade', 'scale', 'pop', 'bounce', 
        'slideUp', 'slideDown', 'slideLeft', 'slideRight',
        'expand', 'rotate', 'shake', 'pulse'
      ] as const

      types.forEach(type => {
        const variants = getSpringVariants(type)
        expect(variants).toHaveProperty('initial')
        expect(variants).toHaveProperty('animate')
      })
    })

    it('should apply spring config to animation variants', () => {
      const variants = getSpringVariants('scale', 'bouncy')
      expect(variants.animate).toHaveProperty('transition')
      expect(variants.animate.transition).toEqual(springPresets.bouncy)
    })

    it('should return static variants when prefers-reduced-motion is enabled', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const variants = getSpringVariants('scale')
      expect(variants.initial).toEqual({ opacity: 1 })
      expect(variants.animate).toEqual({ opacity: 1 })

      vi.unstubAllGlobals()
    })
  })

  describe('triggerHaptic', () => {
    let mockElement: HTMLElement

    beforeEach(() => {
      mockElement = document.createElement('div')
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should add and remove haptic class', async () => {
      const promise = triggerHaptic(mockElement, 'light')
      
      expect(mockElement.classList.contains('haptic-light')).toBe(true)
      
      vi.advanceTimersByTime(10) // light haptic duration
      await promise
      
      expect(mockElement.classList.contains('haptic-light')).toBe(false)
    })

    it('should handle different haptic types with correct durations', async () => {
      const types: Array<[string, number]> = [
        ['light', 10],
        ['medium', 15],
        ['heavy', 20],
        ['success', 25],
        ['warning', 30],
        ['error', 35],
        ['selection', 8],
      ]

      for (const [type, duration] of types) {
        const promise = triggerHaptic(mockElement, type)
        expect(mockElement.classList.contains(`haptic-${type}`)).toBe(true)
        
        vi.advanceTimersByTime(duration)
        await promise
        
        expect(mockElement.classList.contains(`haptic-${type}`)).toBe(false)
      }
    })

    it('should resolve immediately when prefers-reduced-motion is enabled', async () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const promise = triggerHaptic(mockElement, 'medium')
      await promise
      
      expect(mockElement.classList.contains('haptic-medium')).toBe(false)

      vi.unstubAllGlobals()
    })

    it('should resolve immediately when element is null', async () => {
      const promise = triggerHaptic(null as any, 'light')
      await expect(promise).resolves.toBeUndefined()
    })
  })

  describe('getHapticAnimation', () => {
    it('should return animation properties for each haptic type', () => {
      const types = ['light', 'medium', 'heavy', 'success', 'warning', 'error', 'selection'] as const

      types.forEach(type => {
        const animation = getHapticAnimation(type)
        expect(animation).toHaveProperty('transition')
      })
    })

    it('should return light animation by default', () => {
      const animation = getHapticAnimation()
      const lightAnimation = getHapticAnimation('light')
      expect(animation).toEqual(lightAnimation)
    })

    it('should return empty object when prefers-reduced-motion is enabled', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const animation = getHapticAnimation('heavy')
      expect(animation).toEqual({})

      vi.unstubAllGlobals()
    })
  })

  describe('getUserContext', () => {
    it('should detect mobile devices', () => {
      const originalUserAgent = navigator.userAgent
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        configurable: true,
      })

      const context = getUserContext()
      expect(context.isMobile).toBe(true)

      Object.defineProperty(navigator, 'userAgent', {
        value: originalUserAgent,
        configurable: true,
      })
    })

    it('should detect desktop devices', () => {
      const context = getUserContext()
      expect(context).toHaveProperty('isMobile')
      expect(context).toHaveProperty('isLowPower')
      expect(context).toHaveProperty('connectionSpeed')
      expect(context).toHaveProperty('userPreference')
    })
  })

  describe('getContextualAnimation', () => {
    it('should return appropriate animation for mobile context', () => {
      const animation = getContextualAnimation('fade', { isMobile: true })
      expect(animation).toHaveProperty('initial')
      expect(animation).toHaveProperty('animate')
    })

    it('should return appropriate animation for low power context', () => {
      const animation = getContextualAnimation('scale', { isLowPower: true })
      expect(animation).toHaveProperty('initial')
      expect(animation).toHaveProperty('animate')
    })

    it('should return static animation when prefers-reduced-motion is enabled', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const animation = getContextualAnimation('bounce')
      expect(animation).toEqual({ initial: {}, animate: { duration: 0 } })

      vi.unstubAllGlobals()
    })
  })

  describe('createAnimationSequence', () => {
    it('should create animation sequence with correct timing', () => {
      const steps = [
        { opacity: 0, duration: 0.2 },
        { opacity: 1, duration: 0.3 },
      ]

      const sequence = createAnimationSequence(steps, 'default')
      expect(sequence).toHaveProperty('duration')
      expect(sequence).toHaveProperty('times')
    })

    it('should return zero duration when prefers-reduced-motion is enabled', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const steps = [{ opacity: 0 }, { opacity: 1 }]
      const sequence = createAnimationSequence(steps)
      expect(sequence).toEqual({ duration: 0 })

      vi.unstubAllGlobals()
    })
  })

  describe('getStaggerConfig', () => {
    it('should return stagger configuration with default delay', () => {
      const config = getStaggerConfig()
      expect(config).toHaveProperty('staggerChildren', 0.05)
      expect(config).toHaveProperty('delayChildren', 0.1)
      expect(config).toHaveProperty('transition')
    })

    it('should accept custom stagger delay', () => {
      const config = getStaggerConfig('default', 0.1)
      expect(config).toHaveProperty('staggerChildren', 0.1)
    })

    it('should return zero stagger when prefers-reduced-motion is enabled', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }))

      vi.stubGlobal('matchMedia', mockMatchMedia)

      const config = getStaggerConfig()
      expect(config).toEqual({ staggerChildren: 0 })

      vi.unstubAllGlobals()
    })
  })

  describe('Animation Performance Tracking', () => {
    beforeEach(() => {
      resetAnimationMetrics()
    })

    it('should track animation and update metrics', () => {
      const cleanup = trackAnimation('test-animation')
      
      const metrics = getAnimationMetrics()
      expect(metrics.totalAnimations).toBe(1)
      expect(metrics.activeAnimations).toBe(1)
      
      cleanup()
      
      const metricsAfter = getAnimationMetrics()
      expect(metricsAfter.activeAnimations).toBe(0)
    })

    it('should reset animation metrics', () => {
      trackAnimation('test-1')
      trackAnimation('test-2')
      
      let metrics = getAnimationMetrics()
      expect(metrics.totalAnimations).toBeGreaterThan(0)
      
      resetAnimationMetrics()
      
      metrics = getAnimationMetrics()
      expect(metrics.totalAnimations).toBe(0)
      expect(metrics.activeAnimations).toBe(0)
      expect(metrics.droppedFrames).toBe(0)
      expect(metrics.averageFPS).toBe(60)
    })

    it('should handle multiple concurrent animations', () => {
      const cleanup1 = trackAnimation('anim-1')
      const cleanup2 = trackAnimation('anim-2')
      const cleanup3 = trackAnimation('anim-3')
      
      const metrics = getAnimationMetrics()
      expect(metrics.totalAnimations).toBe(3)
      expect(metrics.activeAnimations).toBe(3)
      
      cleanup1()
      cleanup2()
      cleanup3()
      
      const metricsAfter = getAnimationMetrics()
      expect(metricsAfter.activeAnimations).toBe(0)
    })
  })

  describe('Spring Presets', () => {
    it('should have all required spring presets', () => {
      expect(springPresets).toHaveProperty('gentle')
      expect(springPresets).toHaveProperty('default')
      expect(springPresets).toHaveProperty('bouncy')
      expect(springPresets).toHaveProperty('snappy')
      expect(springPresets).toHaveProperty('smooth')
      expect(springPresets).toHaveProperty('wobbly')
    })

    it('should have valid spring parameters for each preset', () => {
      Object.values(springPresets).forEach(preset => {
        expect(preset.type).toBe('spring')
        expect(preset.stiffness).toBeGreaterThan(0)
        expect(preset.damping).toBeGreaterThan(0)
        expect(preset.mass).toBeGreaterThan(0)
      })
    })
  })

  describe('Haptic Types', () => {
    it('should have all required haptic types', () => {
      expect(hapticTypes).toHaveProperty('light')
      expect(hapticTypes).toHaveProperty('medium')
      expect(hapticTypes).toHaveProperty('heavy')
      expect(hapticTypes).toHaveProperty('success')
      expect(hapticTypes).toHaveProperty('warning')
      expect(hapticTypes).toHaveProperty('error')
      expect(hapticTypes).toHaveProperty('selection')
    })

    it('should have valid haptic parameters for each type', () => {
      Object.values(hapticTypes).forEach(haptic => {
        expect(haptic.intensity).toBeGreaterThan(0)
        expect(haptic.intensity).toBeLessThanOrEqual(1)
        expect(haptic.duration).toBeGreaterThan(0)
      })
    })
  })
})
