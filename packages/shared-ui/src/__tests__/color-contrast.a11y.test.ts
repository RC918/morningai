/**
 * Color Contrast Accessibility Tests
 * 
 * Tests for WCAG 2.1 Success Criteria:
 * - 1.4.3 Contrast (Minimum) (Level AA) - 4.5:1 for normal text, 3:1 for large text
 * - 1.4.6 Contrast (Enhanced) (Level AAA) - 7:1 for normal text, 4.5:1 for large text
 * - 1.4.11 Non-text Contrast (Level AA) - 3:1 for UI components
 * 
 * @module color-contrast.a11y.test
 */

import { describe, it, expect } from 'vitest'
import tokens from '../tokens.json'

/**
 * Calculate relative luminance of a color
 * Based on WCAG 2.1 definition
 */
function getRelativeLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    const sRGB = c / 255
    return sRGB <= 0.03928 ? sRGB / 12.92 : Math.pow((sRGB + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

/**
 * Parse hex color to RGB values
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const cleanHex = hex.replace('#', '')
  return {
    r: parseInt(cleanHex.substring(0, 2), 16),
    g: parseInt(cleanHex.substring(2, 4), 16),
    b: parseInt(cleanHex.substring(4, 6), 16),
  }
}

/**
 * Calculate contrast ratio between two colors
 * Returns value between 1 and 21
 */
function getContrastRatio(color1: string, color2: string): number {
  const rgb1 = hexToRgb(color1)
  const rgb2 = hexToRgb(color2)
  
  const l1 = getRelativeLuminance(rgb1.r, rgb1.g, rgb1.b)
  const l2 = getRelativeLuminance(rgb2.r, rgb2.g, rgb2.b)
  
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  
  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * Check if contrast meets WCAG level
 */
function meetsContrastLevel(
  ratio: number,
  level: 'AA' | 'AAA',
  isLargeText: boolean = false
): boolean {
  if (level === 'AAA') {
    return isLargeText ? ratio >= 4.5 : ratio >= 7
  }
  return isLargeText ? ratio >= 3 : ratio >= 4.5
}

describe('Color Contrast Accessibility', () => {
  describe('WCAG AAA Text Contrast (7:1)', () => {
    const whiteBackground = '#FFFFFF'
    const darkBackground = '#000000'
    
    it('should have AAA compliant primary text color', () => {
      const primaryText = tokens.accessibility['wcag-aaa'].colors['primary-text']
      const ratio = getContrastRatio(primaryText, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
      expect(meetsContrastLevel(ratio, 'AAA', false)).toBe(true)
    })

    it('should have AAA compliant success text color', () => {
      const successText = tokens.accessibility['wcag-aaa'].colors['success-text']
      const ratio = getContrastRatio(successText, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
      expect(meetsContrastLevel(ratio, 'AAA', false)).toBe(true)
    })

    it('should have AAA compliant error text color', () => {
      const errorText = tokens.accessibility['wcag-aaa'].colors['error-text']
      const ratio = getContrastRatio(errorText, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
      expect(meetsContrastLevel(ratio, 'AAA', false)).toBe(true)
    })

    it('should have AAA compliant warning text color', () => {
      const warningText = tokens.accessibility['wcag-aaa'].colors['warning-text']
      const ratio = getContrastRatio(warningText, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
      expect(meetsContrastLevel(ratio, 'AAA', false)).toBe(true)
    })

    it('should have AAA compliant info text color', () => {
      const infoText = tokens.accessibility['wcag-aaa'].colors['info-text']
      const ratio = getContrastRatio(infoText, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
      expect(meetsContrastLevel(ratio, 'AAA', false)).toBe(true)
    })
  })

  describe('Focus Indicator Contrast', () => {
    const whiteBackground = '#FFFFFF'
    
    it('should have sufficient contrast for focus outline color', () => {
      const focusColor = tokens.accessibility.focus['outline-color']
      const ratio = getContrastRatio(focusColor, whiteBackground)
      
      // Focus indicators need at least 3:1 contrast (WCAG 1.4.11)
      expect(ratio).toBeGreaterThanOrEqual(3)
    })

    it('should have sufficient contrast for primary focus color', () => {
      const focusPrimary = tokens.accessibility.focus.primary
      const ratio = getContrastRatio(focusPrimary, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(3)
    })

    it('should have sufficient contrast for light focus color', () => {
      const focusLight = tokens.accessibility.focus.light
      const ratio = getContrastRatio(focusLight, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(3)
    })
  })

  describe('Primary Color Palette Contrast', () => {
    const whiteBackground = '#FFFFFF'
    const darkBackground = '#1E1B4B' // primary-900
    
    it('should have AA compliant primary-500 on white', () => {
      const primary500 = tokens.color.primary['500']
      const ratio = getContrastRatio(primary500, whiteBackground)
      
      // Primary colors should meet at least AA for large text
      expect(ratio).toBeGreaterThanOrEqual(3)
    })

    it('should have AA compliant primary-600 on white', () => {
      const primary600 = tokens.color.primary['600']
      const ratio = getContrastRatio(primary600, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(4.5)
    })

    it('should have AA compliant primary-700 on white', () => {
      const primary700 = tokens.color.primary['700']
      const ratio = getContrastRatio(primary700, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(4.5)
    })

    it('should have AA compliant white text on primary-500', () => {
      const primary500 = tokens.color.primary['500']
      const ratio = getContrastRatio(whiteBackground, primary500)
      
      expect(ratio).toBeGreaterThanOrEqual(3)
    })
  })

  describe('Semantic Color Contrast', () => {
    const whiteBackground = '#FFFFFF'
    
    describe('Success Colors', () => {
      it('should have AA compliant success-text-aaa color', () => {
        const successTextAaa = tokens.color.semantic.success['text-aaa']
        const ratio = getContrastRatio(successTextAaa, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(4.5)
      })

      it('should have AAA compliant success text color', () => {
        const successText = tokens.accessibility['wcag-aaa'].colors['success-text']
        const ratio = getContrastRatio(successText, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(7)
      })
    })

    describe('Error Colors', () => {
      it('should have AA compliant error-600 on white', () => {
        const error600 = tokens.color.semantic.error['600']
        const ratio = getContrastRatio(error600, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(4.5)
      })

      it('should have AAA compliant error text color', () => {
        const errorText = tokens.accessibility['wcag-aaa'].colors['error-text']
        const ratio = getContrastRatio(errorText, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(7)
      })
    })

    describe('Warning Colors', () => {
      it('should have sufficient contrast for warning-700 on white (large text)', () => {
        const warning700 = tokens.color.semantic.warning['700']
        const ratio = getContrastRatio(warning700, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(3)
      })

      it('should have AAA compliant warning text color', () => {
        const warningText = tokens.accessibility['wcag-aaa'].colors['warning-text']
        const ratio = getContrastRatio(warningText, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(7)
      })
    })

    describe('Info Colors', () => {
      it('should have sufficient contrast for info-600 on white (large text)', () => {
        const info600 = tokens.color.semantic.info['600']
        const ratio = getContrastRatio(info600, whiteBackground)
        
        expect(ratio).toBeGreaterThanOrEqual(3)
      })
    })
  })

  describe('Neutral Color Contrast', () => {
    const whiteBackground = '#FFFFFF'
    
    it('should have AA compliant neutral-600 on white', () => {
      const neutral600 = tokens.color.neutral['600']
      const ratio = getContrastRatio(neutral600, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(4.5)
    })

    it('should have AA compliant neutral-700 on white', () => {
      const neutral700 = tokens.color.neutral['700']
      const ratio = getContrastRatio(neutral700, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(4.5)
    })

    it('should have AAA compliant neutral-800 on white', () => {
      const neutral800 = tokens.color.neutral['800']
      const ratio = getContrastRatio(neutral800, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
    })

    it('should have AAA compliant neutral-900 on white', () => {
      const neutral900 = tokens.color.neutral['900']
      const ratio = getContrastRatio(neutral900, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(7)
    })
  })

  describe('UI Component Contrast (WCAG 1.4.11)', () => {
    const whiteBackground = '#FFFFFF'
    const minUIContrast = 3 // 3:1 for UI components
    
    it('should have sufficient contrast for focus indicators', () => {
      const focusColor = tokens.accessibility.focus['outline-color']
      const ratio = getContrastRatio(focusColor, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(minUIContrast)
    })

    it('should have sufficient contrast for primary buttons', () => {
      const primary500 = tokens.color.primary['500']
      const ratio = getContrastRatio(primary500, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(minUIContrast)
    })

    it('should have sufficient contrast for error states', () => {
      const error500 = tokens.color.semantic.error['500']
      const ratio = getContrastRatio(error500, whiteBackground)
      
      expect(ratio).toBeGreaterThanOrEqual(minUIContrast)
    })
  })

  describe('Large Text Contrast (WCAG 1.4.3)', () => {
    const whiteBackground = '#FFFFFF'
    const minLargeTextAA = 3
    const minLargeTextAAA = 4.5
    
    it('should meet AA for large text with primary-500', () => {
      const primary500 = tokens.color.primary['500']
      const ratio = getContrastRatio(primary500, whiteBackground)
      
      expect(meetsContrastLevel(ratio, 'AA', true)).toBe(true)
    })

    it('should meet AAA for large text with primary-600', () => {
      const primary600 = tokens.color.primary['600']
      const ratio = getContrastRatio(primary600, whiteBackground)
      
      expect(meetsContrastLevel(ratio, 'AAA', true)).toBe(true)
    })
  })

  describe('Contrast Ratio Calculations', () => {
    it('should calculate maximum contrast for black on white', () => {
      const ratio = getContrastRatio('#000000', '#FFFFFF')
      expect(ratio).toBeCloseTo(21, 0)
    })

    it('should calculate minimum contrast for same colors', () => {
      const ratio = getContrastRatio('#FFFFFF', '#FFFFFF')
      expect(ratio).toBe(1)
    })

    it('should be symmetric (order independent)', () => {
      const ratio1 = getContrastRatio('#000000', '#FFFFFF')
      const ratio2 = getContrastRatio('#FFFFFF', '#000000')
      expect(ratio1).toBe(ratio2)
    })
  })
})

describe('Design Token Accessibility Compliance', () => {
  it('should have all required WCAG AAA colors defined', () => {
    const wcagColors = tokens.accessibility['wcag-aaa'].colors
    
    expect(wcagColors).toHaveProperty('primary-text')
    expect(wcagColors).toHaveProperty('success-text')
    expect(wcagColors).toHaveProperty('error-text')
    expect(wcagColors).toHaveProperty('warning-text')
    expect(wcagColors).toHaveProperty('info-text')
  })

  it('should have all required focus tokens defined', () => {
    const focusTokens = tokens.accessibility.focus
    
    expect(focusTokens).toHaveProperty('outline-width')
    expect(focusTokens).toHaveProperty('outline-offset')
    expect(focusTokens).toHaveProperty('outline-color')
    expect(focusTokens).toHaveProperty('primary')
    expect(focusTokens).toHaveProperty('light')
  })

  it('should have touch target size defined', () => {
    const touchTarget = tokens.accessibility['touch-target']
    
    expect(touchTarget).toHaveProperty('min-size')
    expect(touchTarget['min-size']).toBe('44px')
  })

  it('should have reduced motion duration defined', () => {
    const animation = tokens.accessibility.animation
    
    expect(animation).toHaveProperty('reduced-motion-duration')
    expect(animation['reduced-motion-duration']).toBe('0.01ms')
  })
})
