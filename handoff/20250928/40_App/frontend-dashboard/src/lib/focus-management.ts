/**
 * Focus Management Utilities for WCAG 2.1 AA Compliance
 * Provides utilities for managing focus, keyboard navigation, and focus trapping
 */

/**
 * Trap focus within a container (for modals/dialogs)
 * @param {HTMLElement} container - The container element to trap focus within
 * @returns {Function} Cleanup function to remove event listeners
 */
export const trapFocus = (container: HTMLElement): (() => void) => {
  if (!container) return () => {}

  const focusableElements = container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  
  const firstFocusable = focusableElements[0] as HTMLElement
  const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement

  const handleKeyDown = (e: KeyboardEvent): void => {
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
  previousFocus: Element | null

  constructor() {
    this.previousFocus = null
  }

  saveFocus(): void {
    this.previousFocus = document.activeElement
  }

  restoreFocus(): void {
    if (this.previousFocus && typeof (this.previousFocus as HTMLElement).focus === 'function') {
      (this.previousFocus as HTMLElement).focus()
    }
  }
}

/**
 * Get all focusable elements within a container
 * @param {HTMLElement} container
 * @returns {NodeList}
 */
export const getFocusableElements = (container: HTMLElement): NodeListOf<Element> | Element[] => {
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
export const isFocusable = (element: HTMLElement): boolean => {
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
export const moveFocus = (container: HTMLElement, reverse: boolean = false): void => {
  const focusableElements = Array.from(getFocusableElements(container))
  const currentIndex = focusableElements.indexOf(document.activeElement as Element)
  
  let nextIndex = reverse ? currentIndex - 1 : currentIndex + 1
  
  if (nextIndex < 0) nextIndex = focusableElements.length - 1
  if (nextIndex >= focusableElements.length) nextIndex = 0
  
  const nextElement = focusableElements[nextIndex] as HTMLElement
  if (nextElement && typeof nextElement.focus === 'function') {
    nextElement.focus()
  }
}

/**
 * Add visible focus indicator to element
 * @param {HTMLElement} element
 */
export const addFocusIndicator = (element: HTMLElement): void => {
  if (!element) return
  
  element.style.outline = '2px solid #0051D0'
  element.style.outlineOffset = '2px'
}

/**
 * Remove focus indicator from element
 * @param {HTMLElement} element
 */
export const removeFocusIndicator = (element: HTMLElement): void => {
  if (!element) return
  
  element.style.outline = ''
  element.style.outlineOffset = ''
}
