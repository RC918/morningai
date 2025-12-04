import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, renderHook, act } from '@testing-library/react'
import { ThemeProvider, useTheme, type Theme } from '../ThemeContext'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

// Mock matchMedia
const matchMediaMock = vi.fn().mockImplementation((query: string) => ({
  matches: query === '(prefers-color-scheme: dark)' ? false : false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
}))

describe('ThemeContext', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', localStorageMock)
    vi.stubGlobal('matchMedia', matchMediaMock)
    localStorageMock.clear()
    document.documentElement.classList.remove('light', 'dark')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('ThemeProvider', () => {
    it('should render children', () => {
      const { container } = render(
        <ThemeProvider>
          <div data-testid="test-child" />
        </ThemeProvider>
      )
      expect(container.querySelector('[data-testid="test-child"]')).toBeTruthy()
    })

    it('should use default theme when no localStorage value', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })
      expect(result.current.theme).toBe('system')
    })

    it('should use custom default theme', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider defaultTheme="dark">{children}</ThemeProvider>
        ),
      })
      expect(result.current.theme).toBe('dark')
    })

    it('should read theme from localStorage', () => {
      localStorageMock.setItem('ui-theme', 'dark')
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })
      expect(result.current.theme).toBe('dark')
    })

    it('should use custom storage key', () => {
      localStorageMock.setItem('custom-theme-key', 'light')
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider storageKey="custom-theme-key">{children}</ThemeProvider>
        ),
      })
      expect(result.current.theme).toBe('light')
    })
  })

  describe('setTheme', () => {
    it('should update theme to light', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      act(() => {
        result.current.setTheme('light')
      })

      expect(result.current.theme).toBe('light')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('ui-theme', 'light')
    })

    it('should update theme to dark', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      act(() => {
        result.current.setTheme('dark')
      })

      expect(result.current.theme).toBe('dark')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('ui-theme', 'dark')
    })

    it('should update theme to system', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider defaultTheme="light">{children}</ThemeProvider>
        ),
      })

      act(() => {
        result.current.setTheme('system')
      })

      expect(result.current.theme).toBe('system')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('ui-theme', 'system')
    })
  })

  describe('toggleTheme', () => {
    it('should toggle from light to dark', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider defaultTheme="light">{children}</ThemeProvider>
        ),
      })

      act(() => {
        result.current.toggleTheme()
      })

      expect(result.current.theme).toBe('dark')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('ui-theme', 'dark')
    })

    it('should toggle from dark to light', () => {
      localStorageMock.setItem('ui-theme', 'dark')
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      act(() => {
        result.current.toggleTheme()
      })

      expect(result.current.theme).toBe('light')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('ui-theme', 'light')
    })

    it('should toggle from system to light (system is not equal to light)', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider defaultTheme="system">{children}</ThemeProvider>
        ),
      })

      act(() => {
        result.current.toggleTheme()
      })

      // system !== 'light', so toggleTheme returns 'light' (ternary: theme === 'light' ? 'dark' : 'light')
      expect(result.current.theme).toBe('light')
    })
  })

  describe('useTheme hook', () => {
    it('should return theme context value', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      expect(result.current).toHaveProperty('theme')
      expect(result.current).toHaveProperty('setTheme')
      expect(result.current).toHaveProperty('toggleTheme')
    })

    it('should have setTheme as a function', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      expect(typeof result.current.setTheme).toBe('function')
    })

    it('should have toggleTheme as a function', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
      })

      expect(typeof result.current.toggleTheme).toBe('function')
    })
  })

  describe('DOM class manipulation', () => {
    it('should add light class to document when theme is light', () => {
      render(
        <ThemeProvider defaultTheme="light">
          <div data-testid="test-element" />
        </ThemeProvider>
      )

      expect(document.documentElement.classList.contains('light')).toBe(true)
      expect(document.documentElement.classList.contains('dark')).toBe(false)
    })

    it('should add dark class to document when theme is dark', () => {
      render(
        <ThemeProvider defaultTheme="dark">
          <div data-testid="test-element" />
        </ThemeProvider>
      )

      expect(document.documentElement.classList.contains('dark')).toBe(true)
      expect(document.documentElement.classList.contains('light')).toBe(false)
    })

    it('should remove previous theme class when changing theme', () => {
      const { result } = renderHook(() => useTheme(), {
        wrapper: ({ children }) => (
          <ThemeProvider defaultTheme="light">{children}</ThemeProvider>
        ),
      })

      expect(document.documentElement.classList.contains('light')).toBe(true)

      act(() => {
        result.current.setTheme('dark')
      })

      expect(document.documentElement.classList.contains('dark')).toBe(true)
      expect(document.documentElement.classList.contains('light')).toBe(false)
    })
  })

  describe('System theme detection', () => {
    it('should detect system dark preference', () => {
      // Mock matchMedia to return dark preference
      vi.stubGlobal(
        'matchMedia',
        vi.fn().mockImplementation((query: string) => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }))
      )

      render(
        <ThemeProvider defaultTheme="system">
          <div data-testid="test-element" />
        </ThemeProvider>
      )

      // When system prefers dark, should add dark class
      expect(document.documentElement.classList.contains('dark')).toBe(true)
    })

    it('should detect system light preference', () => {
      // Mock matchMedia to return light preference
      vi.stubGlobal(
        'matchMedia',
        vi.fn().mockImplementation((query: string) => ({
          matches: false, // Not dark = light
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }))
      )

      render(
        <ThemeProvider defaultTheme="system">
          <div data-testid="test-element" />
        </ThemeProvider>
      )

      // When system prefers light, should add light class
      expect(document.documentElement.classList.contains('light')).toBe(true)
    })
  })
})
