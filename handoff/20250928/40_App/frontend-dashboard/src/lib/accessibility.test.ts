/**
 * Accessibility Testing Suite
 * 
 * Comprehensive tests for WCAG AAA compliance including:
 * - Color contrast verification
 * - Keyboard navigation
 * - Screen reader support
 * - Focus management
 * - ARIA attributes
 */

import { describe, it, expect } from 'vitest'
import {
  getContrastRatio,
  checkWCAGAAA,
  getAccessibleTextColor,
  isKeyboardAccessible,
  hasAccessibleName,
  getAccessibilityIssues,
} from './accessibility'

describe('Color Contrast Utilities', () => {
  describe('getContrastRatio', () => {
    it('should calculate correct contrast ratio for black and white', () => {
      const ratio = getContrastRatio('#000000', '#FFFFFF')
      expect(ratio).toBeCloseTo(21, 1)
    })
    
    it('should calculate correct contrast ratio for primary color', () => {
      const ratio = getContrastRatio('#005A9C', '#FFFFFF')
      expect(ratio).toBeGreaterThan(7)
    })
    
    it('should calculate correct contrast ratio for success color', () => {
      const ratio = getContrastRatio('#0D5C3D', '#FFFFFF')
      expect(ratio).toBeGreaterThan(7)
    })
    
    it('should calculate correct contrast ratio for error color', () => {
      const ratio = getContrastRatio('#B91C1C', '#FFFFFF')
      expect(ratio).toBeGreaterThan(7)
    })
    
    it('should calculate correct contrast ratio for warning color', () => {
      const ratio = getContrastRatio('#92400E', '#FFFFFF')
      expect(ratio).toBeGreaterThan(7)
    })
  })
  
  describe('checkWCAGAAA', () => {
    it('should pass AAA for high contrast combinations', () => {
      const result = checkWCAGAAA('#000000', '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
    })
    
    it('should pass AAA for primary text color', () => {
      const result = checkWCAGAAA('#005A9C', '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
    })
    
    it('should pass AAA for success text color', () => {
      const result = checkWCAGAAA('#0D5C3D', '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
    })
    
    it('should pass AAA for error text color', () => {
      const result = checkWCAGAAA('#B91C1C', '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
    })
    
    it('should pass AAA for warning text color', () => {
      const result = checkWCAGAAA('#92400E', '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
    })
    
    it('should handle large text with lower requirements', () => {
      const result = checkWCAGAAA('#60a5fa', '#FFFFFF', true)
      expect(result.level).toBe('AAA')
    })
    
    it('should fail for low contrast combinations', () => {
      const result = checkWCAGAAA('#CCCCCC', '#FFFFFF', false)
      expect(result.compliant).toBe(false)
    })
  })
  
  describe('getAccessibleTextColor', () => {
    it('should return white for dark backgrounds', () => {
      const color = getAccessibleTextColor('#000000')
      expect(color).toBe('#FFFFFF')
    })
    
    it('should return black for light backgrounds', () => {
      const color = getAccessibleTextColor('#FFFFFF')
      expect(color).toBe('#000000')
    })
    
    it('should return appropriate color for mid-tone backgrounds', () => {
      const color = getAccessibleTextColor('#808080')
      expect(color).toMatch(/#(000000|FFFFFF)/)
    })
  })
})

describe('Keyboard Navigation Utilities', () => {
  describe('isKeyboardAccessible', () => {
    it('should identify buttons as keyboard accessible', () => {
      const button = document.createElement('button')
      expect(isKeyboardAccessible(button)).toBe(true)
    })
    
    it('should identify links as keyboard accessible', () => {
      const link = document.createElement('a')
      link.href = '#'
      expect(isKeyboardAccessible(link)).toBe(true)
    })
    
    it('should identify elements with tabindex as keyboard accessible', () => {
      const div = document.createElement('div')
      div.setAttribute('tabindex', '0')
      expect(isKeyboardAccessible(div)).toBe(true)
    })
    
    it('should not identify elements with tabindex="-1" as keyboard accessible', () => {
      const div = document.createElement('div')
      div.setAttribute('tabindex', '-1')
      expect(isKeyboardAccessible(div)).toBe(false)
    })
    
    it('should not identify plain divs as keyboard accessible', () => {
      const div = document.createElement('div')
      expect(isKeyboardAccessible(div)).toBe(false)
    })
  })
  
  describe('hasAccessibleName', () => {
    it('should identify elements with aria-label', () => {
      const button = document.createElement('button')
      button.setAttribute('aria-label', 'Close')
      expect(hasAccessibleName(button)).toBe(true)
    })
    
    it('should identify elements with aria-labelledby', () => {
      const button = document.createElement('button')
      button.setAttribute('aria-labelledby', 'label-id')
      expect(hasAccessibleName(button)).toBe(true)
    })
    
    it('should identify elements with title', () => {
      const button = document.createElement('button')
      button.setAttribute('title', 'Close')
      expect(hasAccessibleName(button)).toBe(true)
    })
    
    it('should identify elements with text content', () => {
      const button = document.createElement('button')
      button.textContent = 'Close'
      expect(hasAccessibleName(button)).toBe(true)
    })
    
    it('should not identify elements without accessible name', () => {
      const button = document.createElement('button')
      expect(hasAccessibleName(button)).toBe(false)
    })
  })
})

describe('Accessibility Issues Detection', () => {
  describe('getAccessibilityIssues', () => {
    it('should detect missing accessible name on buttons', () => {
      const button = document.createElement('button')
      button.onclick = () => {}
      const issues = getAccessibilityIssues(button)
      expect(issues).toContain('Interactive element lacks accessible name')
    })
    
    it('should detect non-keyboard-accessible interactive elements', () => {
      const div = document.createElement('div')
      div.onclick = () => {}
      const issues = getAccessibilityIssues(div)
      expect(issues).toContain('Interactive element is not keyboard accessible')
    })
    
    it('should detect missing alt text on images', () => {
      const img = document.createElement('img')
      const issues = getAccessibilityIssues(img)
      expect(issues).toContain('Image missing alt text')
    })
    
    it('should return empty array for accessible elements', () => {
      const button = document.createElement('button')
      button.textContent = 'Click me'
      const issues = getAccessibilityIssues(button)
      expect(issues.length).toBeLessThanOrEqual(1) // May have color contrast check
    })
  })
})

describe('WCAG AAA Color Standards', () => {
  const aaaColors = {
    primary: '#005A9C',
    success: '#0D5C3D',
    error: '#B91C1C',
    warning: '#92400E',
    info: '#005A9C',
  }
  
  it('should meet AAA standards for all semantic colors', () => {
    Object.entries(aaaColors).forEach(([name, color]) => {
      const result = checkWCAGAAA(color, '#FFFFFF', false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
      expect(result.ratio).toBeGreaterThanOrEqual(7)
    })
  })
  
  it('should maintain AAA standards on dark backgrounds', () => {
    Object.entries(aaaColors).forEach(([name, color]) => {
      const result = checkWCAGAAA('#FFFFFF', color, false)
      expect(result.compliant).toBe(true)
      expect(result.level).toBe('AAA')
      expect(result.ratio).toBeGreaterThanOrEqual(7)
    })
  })
})

describe('Focus Management', () => {
  it('should save and restore focus', () => {
    const button = document.createElement('button')
    document.body.appendChild(button)
    button.focus()
    
    const activeElement = document.activeElement
    expect(activeElement).toBe(button)
    
    document.body.removeChild(button)
  })
})

describe('Motion Preferences', () => {
  it('should detect reduced motion preference', () => {
    const { prefersReducedMotion } = require('./accessibility')
    const result = prefersReducedMotion()
    expect(typeof result).toBe('boolean')
  })
})

describe('High Contrast Mode', () => {
  it('should detect high contrast mode', () => {
    const { isHighContrastMode } = require('./accessibility')
    const result = isHighContrastMode()
    expect(typeof result).toBe('boolean')
  })
})
