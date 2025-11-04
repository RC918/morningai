/**
 * Unit tests for safeLocalStorage utility
 * Tests localStorage operations with error handling for private browsing mode
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import safeLocalStorage, { getItem, setItem, removeItem, clear, isAvailable } from '../safeLocalStorage'

describe('safeLocalStorage', () => {
  let consoleWarnSpy

  beforeEach(() => {
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    localStorage.clear()
  })

  afterEach(() => {
    consoleWarnSpy.mockRestore()
  })

  describe('getItem', () => {
    it('should return value when localStorage is available', () => {
      localStorage.setItem('test-key', 'test-value')
      expect(getItem('test-key')).toBe('test-value')
    })

    it('should return null when key does not exist', () => {
      expect(getItem('non-existent-key')).toBeNull()
    })

    it('should return null and log warning when localStorage throws error', () => {
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new DOMException('QuotaExceededError')
      })

      const result = getItem('test-key')
      
      expect(result).toBeNull()
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'localStorage.getItem failed for key "test-key":',
        'QuotaExceededError'
      )
    })
  })

  describe('setItem', () => {
    it('should set value when localStorage is available', () => {
      const result = setItem('test-key', 'test-value')
      
      expect(result).toBe(true)
      expect(localStorage.getItem('test-key')).toBe('test-value')
    })

    it('should return false and log warning when localStorage throws error', () => {
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new DOMException('QuotaExceededError')
      })

      const result = setItem('test-key', 'test-value')
      
      expect(result).toBe(false)
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'localStorage.setItem failed for key "test-key":',
        'QuotaExceededError'
      )
    })
  })

  describe('removeItem', () => {
    it('should remove value when localStorage is available', () => {
      localStorage.setItem('test-key', 'test-value')
      
      const result = removeItem('test-key')
      
      expect(result).toBe(true)
      expect(localStorage.getItem('test-key')).toBeNull()
    })

    it('should return false and log warning when localStorage throws error', () => {
      vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new DOMException('QuotaExceededError')
      })

      const result = removeItem('test-key')
      
      expect(result).toBe(false)
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'localStorage.removeItem failed for key "test-key":',
        'QuotaExceededError'
      )
    })
  })

  describe('clear', () => {
    it('should clear all values when localStorage is available', () => {
      localStorage.setItem('key1', 'value1')
      localStorage.setItem('key2', 'value2')
      
      const result = clear()
      
      expect(result).toBe(true)
      expect(localStorage.length).toBe(0)
    })

    it('should return false and log warning when localStorage throws error', () => {
      vi.spyOn(Storage.prototype, 'clear').mockImplementation(() => {
        throw new DOMException('QuotaExceededError')
      })

      const result = clear()
      
      expect(result).toBe(false)
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'localStorage.clear failed:',
        'QuotaExceededError'
      )
    })
  })

  describe('isAvailable', () => {
    it('should return true when localStorage is available', () => {
      expect(isAvailable()).toBe(true)
    })

    it('should return false when localStorage throws error', () => {
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new DOMException('QuotaExceededError')
      })

      expect(isAvailable()).toBe(false)
    })

    it('should clean up test key after checking availability', () => {
      isAvailable()
      expect(localStorage.getItem('__localStorage_test__')).toBeNull()
    })
  })

  describe('default export', () => {
    it('should export all methods as object', () => {
      expect(safeLocalStorage).toHaveProperty('getItem')
      expect(safeLocalStorage).toHaveProperty('setItem')
      expect(safeLocalStorage).toHaveProperty('removeItem')
      expect(safeLocalStorage).toHaveProperty('clear')
      expect(safeLocalStorage).toHaveProperty('isAvailable')
    })

    it('should work with default export', () => {
      safeLocalStorage.setItem('test-key', 'test-value')
      expect(safeLocalStorage.getItem('test-key')).toBe('test-value')
    })
  })

  describe('private browsing mode simulation', () => {
    it('should handle all operations gracefully when localStorage is disabled', () => {
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new DOMException('SecurityError')
      })
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new DOMException('SecurityError')
      })
      vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new DOMException('SecurityError')
      })

      expect(getItem('key')).toBeNull()
      expect(setItem('key', 'value')).toBe(false)
      expect(removeItem('key')).toBe(false)
      expect(isAvailable()).toBe(false)
      
      expect(consoleWarnSpy).toHaveBeenCalledTimes(4)
    })
  })
})
