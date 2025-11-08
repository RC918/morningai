/**
 * Design Tokens Unit Tests
 * 
 * Comprehensive test suite for design token utilities including:
 * - getToken: Token access via dot notation
 * - getCSSVariables: CSS variable generation
 * - applyDesignTokens: DOM injection of CSS variables
 * 
 * Test coverage includes common color systems and spacing values.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { getToken, getCSSVariables, applyDesignTokens, colors, spacing } from '../design-tokens'

describe('Design Tokens', () => {
  describe('getToken', () => {
    it('should retrieve primary color tokens', () => {
      const primary500 = getToken('color.primary.500')
      expect(primary500).toBe('#0ea5e9')
      
      const primary600 = getToken('color.primary.600')
      expect(primary600).toBe('#0284c7')
    })

    it('should retrieve accent color tokens', () => {
      const purple500 = getToken('color.accent.purple.500')
      expect(purple500).toBe('#8b5cf6')
      
      const orange500 = getToken('color.accent.orange.500')
      expect(orange500).toBe('#f59e0b')
    })

    it('should retrieve semantic color tokens', () => {
      const success500 = getToken('color.semantic.success.500')
      expect(success500).toBe('#10b981')
      
      const error500 = getToken('color.semantic.error.500')
      expect(error500).toBe('#ef4444')
      
      const warning500 = getToken('color.semantic.warning.500')
      expect(warning500).toBe('#f59e0b')
      
      const info500 = getToken('color.semantic.info.500')
      expect(info500).toBe('#0ea5e9')
    })

    it('should retrieve spacing tokens', () => {
      const spacingXs = getToken('space.xs')
      expect(spacingXs).toBe('4px')
      
      const spacingSm = getToken('space.sm')
      expect(spacingSm).toBe('8px')
      
      const spacingMd = getToken('space.md')
      expect(spacingMd).toBe('16px')
      
      const spacingLg = getToken('space.lg')
      expect(spacingLg).toBe('24px')
      
      const spacingXl = getToken('space.xl')
      expect(spacingXl).toBe('32px')
    })

    it('should retrieve typography tokens', () => {
      const fontSizeBody = getToken('font.size.body')
      expect(fontSizeBody).toBe('16px')
      
      const fontWeightBold = getToken('font.weight.bold')
      expect(fontWeightBold).toBe('700')
    })

    it('should retrieve radius tokens', () => {
      const radiusMd = getToken('radius.md')
      expect(radiusMd).toBe('8px')
    })

    it('should retrieve shadow tokens', () => {
      const shadowMd = getToken('shadow.md')
      expect(shadowMd).toBeTruthy()
      expect(typeof shadowMd).toBe('string')
    })

    it('should return undefined for non-existent paths', () => {
      const nonExistent = getToken('color.nonexistent.token')
      expect(nonExistent).toBeUndefined()
    })

    it('should handle deep nested paths', () => {
      const wcagColor = getToken('accessibility.wcag-aaa.colors.primary-text')
      expect(wcagColor).toBe('#005A9C')
    })
  })

  describe('getCSSVariables', () => {
    it('should generate CSS variables for all token categories', () => {
      const cssVars = getCSSVariables()
      
      expect(Object.keys(cssVars).length).toBeGreaterThan(100)
      expect(cssVars).toHaveProperty('--color-primary-500')
      expect(cssVars).toHaveProperty('--spacing-md')
      expect(cssVars).toHaveProperty('--radius-md')
      expect(cssVars).toHaveProperty('--shadow-md')
    })

    it('should generate primary color CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--color-primary-50']).toBe('#eff6ff')
      expect(cssVars['--color-primary-500']).toBe('#0ea5e9')
      expect(cssVars['--color-primary-900']).toBe('#0c4a6e')
    })

    it('should generate accent color CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--color-accent-purple-500']).toBe('#8b5cf6')
      expect(cssVars['--color-accent-orange-500']).toBe('#f59e0b')
    })

    it('should generate semantic color CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--color-success-500']).toBe('#10b981')
      expect(cssVars['--color-error-500']).toBe('#ef4444')
      expect(cssVars['--color-warning-500']).toBe('#f59e0b')
      expect(cssVars['--color-info-500']).toBe('#0ea5e9')
    })

    it('should generate spacing CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--spacing-xs']).toBe('4px')
      expect(cssVars['--spacing-sm']).toBe('8px')
      expect(cssVars['--spacing-md']).toBe('16px')
      expect(cssVars['--spacing-lg']).toBe('24px')
      expect(cssVars['--spacing-xl']).toBe('32px')
    })

    it('should generate typography CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars).toHaveProperty('--font-size-body')
      expect(cssVars).toHaveProperty('--font-weight-bold')
      expect(cssVars).toHaveProperty('--line-height-body')
    })

    it('should generate animation CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars).toHaveProperty('--animation-duration-fast')
      expect(cssVars).toHaveProperty('--animation-easing-easeInOut')
    })

    it('should generate accessibility CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars).toHaveProperty('--a11y-color-primary-text')
      expect(cssVars).toHaveProperty('--a11y-focus-outline-width')
    })

    it('should return consistent results on multiple calls', () => {
      const cssVars1 = getCSSVariables()
      const cssVars2 = getCSSVariables()
      
      expect(cssVars1).toEqual(cssVars2)
    })

    it('should generate exactly 148 CSS variables (backward compatibility)', () => {
      const cssVars = getCSSVariables()
      
      // This assertion ensures we maintain the exact same number of CSS variables
      expect(Object.keys(cssVars).length).toBe(148)
    })
  })

  describe('applyDesignTokens', () => {
    beforeEach(() => {
      document.documentElement.removeAttribute('style')
      document.body.innerHTML = ''
    })

    it('should apply CSS variables to document root by default', () => {
      const target = applyDesignTokens()
      
      expect(target).toBe(document.documentElement)
      
      const primaryColor = document.documentElement.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#0ea5e9')
      
      const spacingMd = document.documentElement.style.getPropertyValue('--spacing-md')
      expect(spacingMd).toBe('16px')
    })

    it('should apply CSS variables to element by selector string', () => {
      const container = document.createElement('div')
      container.className = 'theme-container'
      document.body.appendChild(container)
      
      const target = applyDesignTokens('.theme-container')
      
      expect(target).toBe(container)
      
      const primaryColor = container.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#0ea5e9')
    })

    it('should apply CSS variables to element reference', () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      
      const target = applyDesignTokens(container)
      
      expect(target).toBe(container)
      
      const primaryColor = container.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#0ea5e9')
    })

    it('should fallback to document root if selector not found', () => {
      const target = applyDesignTokens('.non-existent-selector')
      
      expect(target).toBe(document.documentElement)
      
      const primaryColor = document.documentElement.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#0ea5e9')
    })

    it('should apply all CSS variables from getCSSVariables', () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      
      applyDesignTokens(container)
      
      const cssVars = getCSSVariables()
      const appliedVarCount = Object.keys(cssVars).filter(varName => {
        return container.style.getPropertyValue(varName) !== ''
      }).length
      
      expect(appliedVarCount).toBe(Object.keys(cssVars).length)
    })

    it('should handle multiple calls to same element', () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      
      applyDesignTokens(container)
      applyDesignTokens(container)
      
      const primaryColor = container.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#0ea5e9')
    })
  })

  describe('Exported Token Objects', () => {
    it('should export colors object with all categories', () => {
      expect(colors).toHaveProperty('primary')
      expect(colors).toHaveProperty('accent')
      expect(colors).toHaveProperty('semantic')
      expect(colors).toHaveProperty('neutral')
      expect(colors).toHaveProperty('background')
    })

    it('should export spacing object', () => {
      expect(spacing).toHaveProperty('xs')
      expect(spacing).toHaveProperty('sm')
      expect(spacing).toHaveProperty('md')
      expect(spacing).toHaveProperty('lg')
      expect(spacing).toHaveProperty('xl')
    })

    it('should have correct primary color values', () => {
      expect(colors.primary['500']).toBe('#0ea5e9')
      expect(colors.primary['600']).toBe('#0284c7')
    })

    it('should have correct accent color values', () => {
      expect(colors.accent.purple['500']).toBe('#8b5cf6')
      expect(colors.accent.orange['500']).toBe('#f59e0b')
    })

    it('should have correct spacing values', () => {
      expect(spacing.xs).toBe('4px')
      expect(spacing.sm).toBe('8px')
      expect(spacing.md).toBe('16px')
      expect(spacing.lg).toBe('24px')
      expect(spacing.xl).toBe('32px')
    })
  })

  describe('Integration Tests', () => {
    it('should work together: getToken -> getCSSVariables -> applyDesignTokens', () => {
      const primary500 = getToken('color.primary.500')
      expect(primary500).toBe('#0ea5e9')
      
      const cssVars = getCSSVariables()
      expect(cssVars['--color-primary-500']).toBe(primary500)
      
      const container = document.createElement('div')
      document.body.appendChild(container)
      applyDesignTokens(container)
      
      const appliedValue = container.style.getPropertyValue('--color-primary-500')
      expect(appliedValue).toBe(primary500)
    })

    it('should maintain consistency across all token access methods', () => {
      const spacingMdDirect = spacing.md
      const spacingMdGetToken = getToken('space.md')
      const cssVars = getCSSVariables()
      const spacingMdCSS = cssVars['--spacing-md']
      
      expect(spacingMdDirect).toBe(spacingMdGetToken)
      expect(spacingMdGetToken).toBe(spacingMdCSS)
    })
  })
})
