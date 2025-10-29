/**
 * Safe localStorage wrapper that handles private browsing mode and other exceptions
 * 
 * In private browsing mode, localStorage operations throw DOMException.
 * This wrapper provides graceful degradation by catching errors and logging warnings.
 * 
 * @module safeLocalStorage
 */

/**
 * Safely get an item from localStorage
 * @param {string} key - The key to retrieve
 * @returns {string|null} The value, or null if not found or error occurred
 */
export const getItem = (key) => {
  try {
    return localStorage.getItem(key)
  } catch (e) {
    console.warn(`localStorage.getItem failed for key "${key}":`, e.message)
    return null
  }
}

/**
 * Safely set an item in localStorage
 * @param {string} key - The key to set
 * @param {string} value - The value to store
 * @returns {boolean} True if successful, false otherwise
 */
export const setItem = (key, value) => {
  try {
    localStorage.setItem(key, value)
    return true
  } catch (e) {
    console.warn(`localStorage.setItem failed for key "${key}":`, e.message)
    return false
  }
}

/**
 * Safely remove an item from localStorage
 * @param {string} key - The key to remove
 * @returns {boolean} True if successful, false otherwise
 */
export const removeItem = (key) => {
  try {
    localStorage.removeItem(key)
    return true
  } catch (e) {
    console.warn(`localStorage.removeItem failed for key "${key}":`, e.message)
    return false
  }
}

/**
 * Safely clear all items from localStorage
 * @returns {boolean} True if successful, false otherwise
 */
export const clear = () => {
  try {
    localStorage.clear()
    return true
  } catch (e) {
    console.warn('localStorage.clear failed:', e.message)
    return false
  }
}

/**
 * Check if localStorage is available
 * @returns {boolean} True if localStorage is available and working
 */
export const isAvailable = () => {
  try {
    const testKey = '__localStorage_test__'
    localStorage.setItem(testKey, 'test')
    localStorage.removeItem(testKey)
    return true
  } catch (e) {
    return false
  }
}

/**
 * Default export as object for backward compatibility
 */
export default {
  getItem,
  setItem,
  removeItem,
  clear,
  isAvailable
}
