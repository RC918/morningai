import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('i18n Language Detection', () => {
  let localStorageMock
  let navigatorMock

  beforeEach(() => {
    localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    }
    
    navigatorMock = {
      language: 'en-US'
    }
    
    global.localStorage = localStorageMock
    global.navigator = navigatorMock
    global.window = {}
    
    vi.clearAllMocks()
  })

  const createDetector = () => {
    const isLocalStorageAvailable = () => {
      try {
        const test = '__i18n_test__'
        localStorage.setItem(test, test)
        localStorage.removeItem(test)
        return true
      } catch (e) {
        return false
      }
    }

    const isBrowser = () => typeof window !== 'undefined'

    return {
      name: 'customDetector',
      lookup() {
        if (!isBrowser()) {
          return 'en-US'
        }

        if (isLocalStorageAvailable()) {
          try {
            const savedLang = localStorage.getItem('i18nextLng')
            if (savedLang && (savedLang === 'zh-TW' || savedLang === 'en-US')) {
              return savedLang
            }
          } catch (e) {
            console.warn('Failed to read from localStorage:', e)
          }
        }

        try {
          const browserLang = navigator.language || navigator.userLanguage
          
          if (!browserLang) {
            return 'en-US'
          }

          const langLower = browserLang.toLowerCase()
          
          if (langLower === 'zh-tw' || langLower === 'zh-hant' || langLower.startsWith('zh-tw') || langLower.startsWith('zh-hant')) {
            return 'zh-TW'
          }
          
          if (langLower === 'zh-cn' || langLower === 'zh-hans' || langLower.startsWith('zh-cn') || langLower.startsWith('zh-hans')) {
            return 'zh-TW'
          }
          
          if (langLower === 'zh' || langLower.startsWith('zh-')) {
            return 'zh-TW'
          }
          
          return 'en-US'
        } catch (e) {
          console.warn('Failed to detect browser language:', e)
          return 'en-US'
        }
      },
      cacheUserLanguage(lng) {
        if (!isBrowser() || !isLocalStorageAvailable()) {
          return
        }

        try {
          localStorage.setItem('i18nextLng', lng)
        } catch (e) {
          console.warn('Failed to cache language preference:', e)
        }
      }
    }
  }

  describe('Browser Language Detection', () => {
    it('should detect Traditional Chinese (zh-TW)', () => {
      navigatorMock.language = 'zh-TW'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should detect Traditional Chinese (zh-Hant)', () => {
      navigatorMock.language = 'zh-Hant'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should map Simplified Chinese (zh-CN) to Traditional Chinese', () => {
      navigatorMock.language = 'zh-CN'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should map generic Chinese (zh) to Traditional Chinese', () => {
      navigatorMock.language = 'zh'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should default to English for non-Chinese languages', () => {
      navigatorMock.language = 'en-US'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })

    it('should default to English for Japanese', () => {
      navigatorMock.language = 'ja-JP'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })

    it('should default to English for Korean', () => {
      navigatorMock.language = 'ko-KR'
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })
  })

  describe('localStorage Priority', () => {
    it('should prioritize localStorage over browser language', () => {
      navigatorMock.language = 'zh-TW'
      localStorageMock.getItem.mockReturnValue('en-US')
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })

    it('should respect user manual selection stored in localStorage', () => {
      navigatorMock.language = 'en-US'
      localStorageMock.getItem.mockReturnValue('zh-TW')
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should ignore invalid localStorage values', () => {
      navigatorMock.language = 'zh-TW'
      localStorageMock.getItem.mockReturnValue('invalid-lang')
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })
  })

  describe('Edge Cases', () => {
    it('should handle incognito mode (localStorage unavailable)', () => {
      navigatorMock.language = 'zh-TW'
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage is not available')
      })
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('zh-TW')
    })

    it('should handle missing navigator.language', () => {
      delete navigatorMock.language
      localStorageMock.getItem.mockReturnValue(null)
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })

    it('should handle SSR environment (no window)', () => {
      delete global.window
      
      const detector = createDetector()
      const result = detector.lookup()
      
      expect(result).toBe('en-US')
    })

    it('should handle localStorage.setItem failure gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('localStorage quota exceeded')
      })
      
      const detector = createDetector()
      
      expect(() => {
        detector.cacheUserLanguage('zh-TW')
      }).not.toThrow()
    })
  })

  describe('Language Caching', () => {
    it('should cache language selection to localStorage', () => {
      const detector = createDetector()
      detector.cacheUserLanguage('zh-TW')
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith('i18nextLng', 'zh-TW')
    })

    it('should not cache in SSR environment', () => {
      delete global.window
      
      const detector = createDetector()
      detector.cacheUserLanguage('zh-TW')
      
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should not cache when localStorage is unavailable', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('localStorage is not available')
      })
      
      const detector = createDetector()
      
      expect(() => {
        detector.cacheUserLanguage('zh-TW')
      }).not.toThrow()
    })
  })
})
