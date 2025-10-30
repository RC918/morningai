/**
 * Type Tests for Spring Animation
 * 
 * These tests verify that spring-animation types are compatible with Framer Motion.
 * They will fail at compile-time if there are type incompatibilities.
 */

import { describe, it, expectTypeOf } from 'vitest'
import type { Variants, Transition, TargetAndTransition } from 'framer-motion'
import {
  getSpringConfig,
  getSpringVariants,
  getHapticAnimation,
  type HapticType,
  type SpringPresetName,
  type AnimationVariantType,
} from '../spring-animation'

describe('Spring Animation Type Tests', () => {
  describe('getSpringConfig', () => {
    it('should return Framer Motion Transition type', () => {
      const config = getSpringConfig('default')
      expectTypeOf(config).toMatchTypeOf<Transition>()
    })

    it('should accept SpringPresetName', () => {
      const presets: SpringPresetName[] = ['gentle', 'default', 'bouncy', 'snappy', 'smooth', 'wobbly']
      presets.forEach(preset => {
        expectTypeOf(getSpringConfig(preset)).toMatchTypeOf<Transition>()
      })
    })

    it('should accept undefined', () => {
      expectTypeOf(getSpringConfig()).toMatchTypeOf<Transition>()
    })
  })

  describe('getSpringVariants', () => {
    it('should return Framer Motion Variants type', () => {
      const variants = getSpringVariants('fade', 'default')
      expectTypeOf(variants).toMatchTypeOf<Variants>()
    })

    it('should accept AnimationVariantType', () => {
      const types: AnimationVariantType[] = [
        'fade', 'scale', 'pop', 'bounce', 
        'slideUp', 'slideDown', 'slideLeft', 'slideRight',
        'expand', 'rotate', 'shake', 'pulse'
      ]
      types.forEach(type => {
        expectTypeOf(getSpringVariants(type)).toMatchTypeOf<Variants>()
      })
    })

    it('should accept optional parameters', () => {
      expectTypeOf(getSpringVariants()).toMatchTypeOf<Variants>()
      expectTypeOf(getSpringVariants('fade')).toMatchTypeOf<Variants>()
    })
  })

  describe('getHapticAnimation', () => {
    it('should return Framer Motion TargetAndTransition type', () => {
      const animation = getHapticAnimation('light')
      expectTypeOf(animation).toMatchTypeOf<TargetAndTransition>()
    })

    it('should accept HapticType', () => {
      const types: HapticType[] = ['light', 'medium', 'heavy', 'success', 'warning', 'error', 'selection']
      types.forEach(type => {
        expectTypeOf(getHapticAnimation(type)).toMatchTypeOf<TargetAndTransition>()
      })
    })

    it('should accept undefined', () => {
      expectTypeOf(getHapticAnimation()).toMatchTypeOf<TargetAndTransition>()
    })
  })

  describe('Type compatibility with Framer Motion components', () => {
    it('should work with motion component transition prop', () => {
      const config = getSpringConfig('default')
      expectTypeOf(config).toMatchTypeOf<Transition>()
    })

    it('should work with motion component variants prop', () => {
      const variants = getSpringVariants('fade')
      expectTypeOf(variants).toMatchTypeOf<Variants>()
    })

    it('should work with motion component animate prop', () => {
      const animation = getHapticAnimation('light')
      expectTypeOf(animation).toMatchTypeOf<TargetAndTransition>()
    })
  })

  describe('Type literal constraints', () => {
    it('should accept string literals (will be tightened in Issue #936)', () => {
      getSpringConfig('custom-preset')
      getSpringVariants('custom-type')
      getHapticAnimation('custom-haptic')
    })
  })
})
