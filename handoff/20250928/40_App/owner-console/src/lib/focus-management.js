/**
 * Focus Management Utilities for WCAG 2.1 AA Compliance
 * Provides utilities for managing focus, keyboard navigation, and focus trapping
 */

/**
 * Trap focus within a container (for modals/dialogs)
 * @param {HTMLElement} container - The container element to trap focus within
 * @returns {Function} Cleanup function to remove event listeners
 */
export const trapFocus = (container) => {
  if (!container) return () => {}

  const focusableElements = container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  
  const firstFocusable = focusableElements[0]
  const lastFocusable = focusableElements[focusableElements.length - 1]

  const handleKeyDown = (e) => {
    if (e.key !== 'Tab') return

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstFocusable) {
        e.preventDefault()
        lastFocusable?.focus()
      }
    } else {
      // Tab
      if (document.activeElement === lastFocusable) {
        e.preventDefault()
        firstFocusable?.focus()
      }
    }
  }

  container.addEventListener('keydown', handleKeyDown)
  
  // Focus first element
  firstFocusable?.focus()

  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

/**
 * Store and restore focus (useful for modals)
 */
export class FocusManager {
  constructor() {
    this.previousFocus = null
  }

  saveFocus() {
    this.previousFocus = document.activeElement
  }

  restoreFocus() {
    if (this.previousFocus && typeof this.previousFocus.focus === 'function') {
      this.previousFocus.focus()
    }
  }
}

/**
 * Get all focusable elements within a container
 * @param {HTMLElement} container
 * @returns {NodeList}
 */
export const getFocusableElements = (container) => {
  if (!container) return []
  
  return container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
}

/**
 * Check if element is visible and focusable
 * @param {HTMLElement} element
 * @returns {boolean}
 */
export const isFocusable = (element) => {
  if (!element) return false
  
  const style = window.getComputedStyle(element)
  return (
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    !element.hasAttribute('disabled') &&
    element.tabIndex !== -1
  )
}

/**
 * Move focus to next/previous focusable element
 * @param {HTMLElement} container
 * @param {boolean} reverse - Move backwards if true
 */
export const moveFocus = (container, reverse = false) => {
  const focusableElements = Array.from(getFocusableElements(container))
  const currentIndex = focusableElements.indexOf(document.activeElement)
  
  let nextIndex = reverse ? currentIndex - 1 : currentIndex + 1
  
  if (nextIndex < 0) nextIndex = focusableElements.length - 1
  if (nextIndex >= focusableElements.length) nextIndex = 0
  
  focusableElements[nextIndex]?.focus()
}

/**
 * Add visible focus indicator to element
 * @param {HTMLElement} element
 */
export const addFocusIndicator = (element) => {
  if (!element) return
  
  element.style.outline = '2px solid #3b82f6'
  element.style.outlineOffset = '2px'
}

/**
 * Remove focus indicator from element
 * @param {HTMLElement} element
 */
export const removeFocusIndicator = (element) => {
  if (!element) return
  
  element.style.outline = ''
  element.style.outlineOffset = ''
}
