/**
 * Accessibility Utilities for WCAG AAA Compliance
 * 
 * This module provides utilities for ensuring WCAG AAA accessibility standards
 * including color contrast, keyboard navigation, screen reader support, and more.
 * 
 * @module accessibility
 */

/**
 * Color Contrast Utilities
 * WCAG AAA requires 7:1 contrast ratio for normal text, 4.5:1 for large text
 */

/**
 * Calculate relative luminance of a color
 * @param r - Red value (0-255)
 * @param g - Green value (0-255)
 * @param b - Blue value (0-255)
 * @returns Relative luminance (0-1)
 */
function getRelativeLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    const sRGB = c / 255
    return sRGB <= 0.03928 ? sRGB / 12.92 : Math.pow((sRGB + 0.055) / 1.055, 2.4)
  })
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
}

/**
 * Calculate contrast ratio between two colors
 * @param color1 - First color in hex format (#RRGGBB)
 * @param color2 - Second color in hex format (#RRGGBB)
 * @returns Contrast ratio (1-21)
 */
export function getContrastRatio(color1: string, color2: string): number {
  const hex1 = color1.replace('#', '')
  const hex2 = color2.replace('#', '')
  
  const r1 = parseInt(hex1.substring(0, 2), 16)
  const g1 = parseInt(hex1.substring(2, 4), 16)
  const b1 = parseInt(hex1.substring(4, 6), 16)
  
  const r2 = parseInt(hex2.substring(0, 2), 16)
  const g2 = parseInt(hex2.substring(2, 4), 16)
  const b2 = parseInt(hex2.substring(4, 6), 16)
  
  const l1 = getRelativeLuminance(r1, g1, b1)
  const l2 = getRelativeLuminance(r2, g2, b2)
  
  const lighter = Math.max(l1, l2)
  const darker = Math.min(l1, l2)
  
  return (lighter + 0.05) / (darker + 0.05)
}

/**
 * Check if color combination meets WCAG AAA standards
 * @param foreground - Foreground color in hex format
 * @param background - Background color in hex format
 * @param isLargeText - Whether the text is large (18pt+ or 14pt+ bold)
 * @returns Object with compliance status and contrast ratio
 */
export function checkWCAGAAA(
  foreground: string,
  background: string,
  isLargeText: boolean = false
): { compliant: boolean; ratio: number; level: 'AAA' | 'AA' | 'Fail' } {
  const ratio = getContrastRatio(foreground, background)
  const requiredRatio = isLargeText ? 4.5 : 7.0
  const aaRatio = isLargeText ? 3.0 : 4.5
  
  if (ratio >= requiredRatio) {
    return { compliant: true, ratio, level: 'AAA' }
  } else if (ratio >= aaRatio) {
    return { compliant: false, ratio, level: 'AA' }
  } else {
    return { compliant: false, ratio, level: 'Fail' }
  }
}

/**
 * Get accessible text color for a given background
 * @param background - Background color in hex format
 * @returns Accessible text color (#000000 or #FFFFFF)
 */
export function getAccessibleTextColor(background: string): string {
  const whiteContrast = getContrastRatio(background, '#FFFFFF')
  const blackContrast = getContrastRatio(background, '#000000')
  
  return whiteContrast > blackContrast ? '#FFFFFF' : '#000000'
}

/**
 * Keyboard Navigation Utilities
 */

/**
 * Trap focus within a container (for modals, dialogs)
 * @param container - Container element
 * @returns Cleanup function
 */
export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = container.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  
  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]
  
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return
    
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault()
        lastElement?.focus()
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault()
        firstElement?.focus()
      }
    }
  }
  
  container.addEventListener('keydown', handleKeyDown)
  firstElement?.focus()
  
  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

/**
 * Get all focusable elements within a container
 * @param container - Container element
 * @returns Array of focusable elements
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  return Array.from(container.querySelectorAll<HTMLElement>(selector))
}

/**
 * Screen Reader Utilities
 */

/**
 * Announce message to screen readers
 * @param message - Message to announce
 * @param priority - Priority level (polite or assertive)
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message
  
  document.body.appendChild(announcement)
  
  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

/**
 * Create visually hidden element for screen readers
 * @param text - Text content
 * @returns HTMLElement
 */
export function createScreenReaderOnly(text: string): HTMLSpanElement {
  const span = document.createElement('span')
  span.className = 'sr-only'
  span.textContent = text
  return span
}

/**
 * Motion Preferences
 */

/**
 * Check if user prefers reduced motion
 * @returns boolean
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Listen for motion preference changes
 * @param callback - Callback function
 * @returns Cleanup function
 */
export function onMotionPreferenceChange(callback: (prefersReduced: boolean) => void): () => void {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  
  const handler = (e: MediaQueryListEvent) => {
    callback(e.matches)
  }
  
  mediaQuery.addEventListener('change', handler)
  
  return () => {
    mediaQuery.removeEventListener('change', handler)
  }
}

/**
 * Focus Management
 */

/**
 * Save current focus and restore later
 * @returns Restore function
 */
export function saveFocus(): () => void {
  const activeElement = document.activeElement as HTMLElement
  
  return () => {
    activeElement?.focus()
  }
}

/**
 * Move focus to element with optional delay
 * @param element - Element to focus
 * @param delay - Delay in milliseconds
 */
export function moveFocusTo(element: HTMLElement | null, delay: number = 0): void {
  if (!element) return
  
  if (delay > 0) {
    setTimeout(() => element.focus(), delay)
  } else {
    element.focus()
  }
}

/**
 * ARIA Utilities
 */

/**
 * Set ARIA attributes on element
 * @param element - Target element
 * @param attributes - ARIA attributes object
 */
export function setAriaAttributes(
  element: HTMLElement,
  attributes: Record<string, string | boolean | number>
): void {
  Object.entries(attributes).forEach(([key, value]) => {
    const ariaKey = key.startsWith('aria-') ? key : `aria-${key}`
    element.setAttribute(ariaKey, String(value))
  })
}

/**
 * Create accessible label for element
 * @param element - Target element
 * @param label - Label text
 * @param method - Labeling method (label, aria-label, or aria-labelledby)
 */
export function createAccessibleLabel(
  element: HTMLElement,
  label: string,
  method: 'label' | 'aria-label' | 'aria-labelledby' = 'aria-label'
): void {
  if (method === 'aria-label') {
    element.setAttribute('aria-label', label)
  } else if (method === 'aria-labelledby') {
    const id = `label-${Math.random().toString(36).substr(2, 9)}`
    const labelElement = document.createElement('span')
    labelElement.id = id
    labelElement.className = 'sr-only'
    labelElement.textContent = label
    element.parentElement?.insertBefore(labelElement, element)
    element.setAttribute('aria-labelledby', id)
  } else {
    const labelElement = document.createElement('label')
    labelElement.textContent = label
    labelElement.htmlFor = element.id || `input-${Math.random().toString(36).substr(2, 9)}`
    if (!element.id) element.id = labelElement.htmlFor
    element.parentElement?.insertBefore(labelElement, element)
  }
}

/**
 * Keyboard Shortcuts
 */

/**
 * Register keyboard shortcut
 * @param key - Key combination (e.g., 'Ctrl+K', 'Cmd+Shift+P')
 * @param handler - Handler function
 * @param options - Options
 * @returns Cleanup function
 */
export function registerKeyboardShortcut(
  key: string,
  handler: (e: KeyboardEvent) => void,
  options: { preventDefault?: boolean; stopPropagation?: boolean } = {}
): () => void {
  const { preventDefault = true, stopPropagation = false } = options
  
  const handleKeyDown = (e: KeyboardEvent) => {
    const parts = key.split('+').map(k => k.trim().toLowerCase())
    const keyPressed = e.key.toLowerCase()
    
    const modifiers = {
      ctrl: e.ctrlKey,
      cmd: e.metaKey,
      alt: e.altKey,
      shift: e.shiftKey,
    }
    
    const requiredModifiers = parts.filter(p => p in modifiers)
    const requiredKey = parts.find(p => !(p in modifiers))
    
    const modifiersMatch = requiredModifiers.every(mod => modifiers[mod as keyof typeof modifiers])
    const keyMatches = !requiredKey || keyPressed === requiredKey
    
    if (modifiersMatch && keyMatches) {
      if (preventDefault) e.preventDefault()
      if (stopPropagation) e.stopPropagation()
      handler(e)
    }
  }
  
  document.addEventListener('keydown', handleKeyDown)
  
  return () => {
    document.removeEventListener('keydown', handleKeyDown)
  }
}

/**
 * Accessibility Testing Utilities
 */

/**
 * Check if element is keyboard accessible
 * @param element - Element to check
 * @returns boolean
 */
export function isKeyboardAccessible(element: HTMLElement): boolean {
  const tabIndex = element.getAttribute('tabindex')
  const isInteractive = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)
  
  return isInteractive || (tabIndex !== null && tabIndex !== '-1')
}

/**
 * Check if element has accessible name
 * @param element - Element to check
 * @returns boolean
 */
export function hasAccessibleName(element: HTMLElement): boolean {
  const ariaLabel = element.getAttribute('aria-label')
  const ariaLabelledBy = element.getAttribute('aria-labelledby')
  const title = element.getAttribute('title')
  const textContent = element.textContent?.trim()
  
  return !!(ariaLabel || ariaLabelledBy || title || textContent)
}

/**
 * Get accessibility issues for element
 * @param element - Element to check
 * @returns Array of issues
 */
export function getAccessibilityIssues(element: HTMLElement): string[] {
  const issues: string[] = []
  
  if (!isKeyboardAccessible(element) && element.onclick) {
    issues.push('Interactive element is not keyboard accessible')
  }
  
  if (!hasAccessibleName(element) && ['BUTTON', 'A', 'INPUT'].includes(element.tagName)) {
    issues.push('Interactive element lacks accessible name')
  }
  
  const computedStyle = window.getComputedStyle(element)
  const color = computedStyle.color
  const backgroundColor = computedStyle.backgroundColor
  
  if (color && backgroundColor) {
    issues.push('Color contrast should be verified')
  }
  
  if (element.tagName === 'IMG' && !element.getAttribute('alt')) {
    issues.push('Image missing alt text')
  }
  
  return issues
}

/**
 * Voice Control Support
 */

/**
 * Add voice control labels to interactive elements
 * @param container - Container element
 */
export function addVoiceControlLabels(container: HTMLElement): void {
  const interactiveElements = container.querySelectorAll<HTMLElement>(
    'button, a, input, select, textarea, [role="button"], [role="link"]'
  )
  
  interactiveElements.forEach((element) => {
    if (!element.getAttribute('aria-label') && !element.textContent?.trim()) {
      const role = element.getAttribute('role') || element.tagName.toLowerCase()
      element.setAttribute('aria-label', `${role} control`)
    }
  })
}

/**
 * High Contrast Mode Detection
 */

/**
 * Check if high contrast mode is enabled
 * @returns boolean
 */
export function isHighContrastMode(): boolean {
  return window.matchMedia('(prefers-contrast: high)').matches
}

/**
 * Listen for high contrast mode changes
 * @param callback - Callback function
 * @returns Cleanup function
 */
export function onHighContrastModeChange(callback: (isHighContrast: boolean) => void): () => void {
  const mediaQuery = window.matchMedia('(prefers-contrast: high)')
  
  const handler = (e: MediaQueryListEvent) => {
    callback(e.matches)
  }
  
  mediaQuery.addEventListener('change', handler)
  
  return () => {
    mediaQuery.removeEventListener('change', handler)
  }
}
