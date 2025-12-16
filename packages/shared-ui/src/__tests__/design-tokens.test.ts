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
      expect(primary500).toBe('#4D7CFE')
      
      const primary600 = getToken('color.primary.600')
      expect(primary600).toBe('#4338CA')
    })

    it('should retrieve accent color tokens', () => {
      const purple500 = getToken('color.accent.purple.500')
      expect(purple500).toBe('#8b5cf6')
      
      const orange500 = getToken('color.accent.orange.500')
      expect(orange500).toBe('#FFAB2B')
    })

    it('should retrieve semantic color tokens', () => {
      const success500 = getToken('color.semantic.success.500')
      expect(success500).toBe('#6DD230')
      
      const error500 = getToken('color.semantic.error.500')
      expect(error500).toBe('#ef4444')
      
      const warning500 = getToken('color.semantic.warning.500')
      expect(warning500).toBe('#FFAB2B')
      
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
      
      expect(cssVars['--color-primary-50']).toBe('#EEF2FF')
      expect(cssVars['--color-primary-500']).toBe('#4D7CFE')
      expect(cssVars['--color-primary-900']).toBe('#1E1B4B')
    })

    it('should generate accent color CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--color-accent-purple-500']).toBe('#8b5cf6')
      expect(cssVars['--color-accent-orange-500']).toBe('#FFAB2B')
    })

    it('should generate semantic color CSS variables', () => {
      const cssVars = getCSSVariables()
      
      expect(cssVars['--color-success-500']).toBe('#6DD230')
      expect(cssVars['--color-error-500']).toBe('#ef4444')
      expect(cssVars['--color-warning-500']).toBe('#FFAB2B')
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
      
      // Focus color tokens added for Issue #2291 (Design Token source unification)
      expect(cssVars['--a11y-focus-primary']).toBe('#0051D0')
      expect(cssVars['--a11y-focus-light']).toBe('#0284c7')
    })

    it('should return consistent results on multiple calls', () => {
      const cssVars1 = getCSSVariables()
      const cssVars2 = getCSSVariables()
      
      expect(cssVars1).toEqual(cssVars2)
    })

    it('should generate exactly 179 CSS variables (backward compatibility)', () => {
      const cssVars = getCSSVariables()
      
      // This assertion ensures we maintain the exact same number of CSS variables
      // Updated from 148 to 169 after adding iotask accent colors (pink, cyan)
      // Updated from 169 to 171 after adding accessibility focus.primary/light tokens (Issue #2291)
      // Updated from 171 to 179 after adding card.icon KPI/Status archetype tokens (Issue #2294)
      expect(Object.keys(cssVars).length).toBe(179)
      
      // Verify card icon tokens are included
      expect(cssVars['--card-icon-kpi-size']).toBeDefined()
      expect(cssVars['--card-icon-status-size']).toBeDefined()
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
      expect(primaryColor).toBe('#4D7CFE')
      
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
      expect(primaryColor).toBe('#4D7CFE')
    })

    it('should apply CSS variables to element reference', () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      
      const target = applyDesignTokens(container)
      
      expect(target).toBe(container)
      
      const primaryColor = container.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#4D7CFE')
    })

    it('should fallback to document root if selector not found', () => {
      const target = applyDesignTokens('.non-existent-selector')
      
      expect(target).toBe(document.documentElement)
      
      const primaryColor = document.documentElement.style.getPropertyValue('--color-primary-500')
      expect(primaryColor).toBe('#4D7CFE')
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
      expect(primaryColor).toBe('#4D7CFE')
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
      expect(colors.primary['500']).toBe('#4D7CFE')
      expect(colors.primary['600']).toBe('#4338CA')
    })

    it('should have correct accent color values', () => {
      expect(colors.accent.purple['500']).toBe('#8b5cf6')
      expect(colors.accent.orange['500']).toBe('#FFAB2B')
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
      expect(primary500).toBe('#4D7CFE')
      
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

  /**
   * Focus Outline Snapshot Tests (Issue #2292)
   * 
   * These tests verify that accessibility focus CSS variables are correctly
   * generated and maintain WCAG AAA compliance. The snapshot approach ensures
   * no regressions occur when modifying focus styles.
   */
  describe('Focus Outline Snapshot Tests (Issue #2292)', () => {
    it('should generate all required --a11y-focus-* CSS variables', () => {
      const cssVars = getCSSVariables()
      
      // Verify all required focus variables exist
      const requiredFocusVars = [
        '--a11y-focus-outline-width',
        '--a11y-focus-outline-offset',
        '--a11y-focus-outline-color',
        '--a11y-focus-primary',
        '--a11y-focus-light'
      ]
      
      requiredFocusVars.forEach(varName => {
        expect(cssVars).toHaveProperty(varName)
      })
    })

    it('should have WCAG AAA compliant focus outline values (snapshot)', () => {
      const cssVars = getCSSVariables()
      
      // Snapshot of expected focus values for regression testing
      const focusSnapshot = {
        '--a11y-focus-outline-width': '3px',      // AAA requires visible outline
        '--a11y-focus-outline-offset': '2px',     // Offset from element edge
        '--a11y-focus-outline-color': '#0284c7',  // Sky blue - high contrast
        '--a11y-focus-primary': '#0051D0',        // Primary blue - 7.12:1 contrast on white
        '--a11y-focus-light': '#0284c7'           // Sky blue - used in accessibility.css
      }
      
      Object.entries(focusSnapshot).forEach(([varName, expectedValue]) => {
        expect(cssVars[varName]).toBe(expectedValue)
      })
    })

    it('should apply focus CSS variables to DOM elements', () => {
      const container = document.createElement('div')
      document.body.appendChild(container)
      
      applyDesignTokens(container)
      
      // Verify focus variables are applied to DOM
      expect(container.style.getPropertyValue('--a11y-focus-outline-width')).toBe('3px')
      expect(container.style.getPropertyValue('--a11y-focus-outline-offset')).toBe('2px')
      expect(container.style.getPropertyValue('--a11y-focus-outline-color')).toBe('#0284c7')
      expect(container.style.getPropertyValue('--a11y-focus-primary')).toBe('#0051D0')
      expect(container.style.getPropertyValue('--a11y-focus-light')).toBe('#0284c7')
    })

    it('should retrieve focus tokens via getToken', () => {
      // Verify tokens can be accessed via dot notation
      expect(getToken('accessibility.focus.outline-width')).toBe('3px')
      expect(getToken('accessibility.focus.outline-offset')).toBe('2px')
      expect(getToken('accessibility.focus.outline-color')).toBe('#0284c7')
      expect(getToken('accessibility.focus.primary')).toBe('#0051D0')
      expect(getToken('accessibility.focus.light')).toBe('#0284c7')
    })

    it('should maintain focus outline width >= 3px for AAA compliance', () => {
      const outlineWidth = getToken('accessibility.focus.outline-width')
      expect(outlineWidth).toBeDefined()
      const widthValue = parseInt(outlineWidth!, 10)
      
      // WCAG AAA requires visible focus indicators
      // 3px is the minimum recommended for AAA compliance
      expect(widthValue).toBeGreaterThanOrEqual(3)
    })

    it('should maintain focus outline offset >= 2px for visibility', () => {
      const outlineOffset = getToken('accessibility.focus.outline-offset')
      expect(outlineOffset).toBeDefined()
      const offsetValue = parseInt(outlineOffset!, 10)
      
      // 2px offset ensures focus ring doesn't overlap content
      expect(offsetValue).toBeGreaterThanOrEqual(2)
    })
  })
})
