/**
 * Tests for Accessibility Hooks - Phase 2 Coverage (#1924)
 *
 * Comprehensive test suite for use-accessibility.ts hooks.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import {
  useReducedMotion,
  useHighContrastMode,
  useFocusTrap,
  useScreenReaderAnnouncement,
  useKeyboardShortcuts,
  useFocusRestore,
  useRovingTabIndex,
  useSkipLink,
  useLiveRegion,
  useAccessibleDialog,
  useAccessibleTooltip,
  useAccessibleTabs,
  useAccessibleCombobox,
} from '../use-accessibility'

// Mock the accessibility lib
vi.mock('@/lib/accessibility', () => ({
  prefersReducedMotion: vi.fn(() => false),
  onMotionPreferenceChange: vi.fn((callback) => {
    return () => {} // cleanup function
  }),
  trapFocus: vi.fn(() => () => {}),
  announceToScreenReader: vi.fn(),
  registerKeyboardShortcut: vi.fn(() => () => {}),
  isHighContrastMode: vi.fn(() => false),
  onHighContrastModeChange: vi.fn((callback) => {
    return () => {} // cleanup function
  }),
}))

describe('useReducedMotion', () => {
  it('returns initial reduced motion preference', () => {
    const { result } = renderHook(() => useReducedMotion())

    expect(result.current.prefersReduced).toBe(false)
    expect(typeof result.current.setPrefersReduced).toBe('function')
  })

  it('allows setting reduced motion preference', () => {
    const { result } = renderHook(() => useReducedMotion())

    act(() => {
      result.current.setPrefersReduced(true)
    })

    expect(result.current.prefersReduced).toBe(true)
  })
})

describe('useHighContrastMode', () => {
  it('returns initial high contrast mode state', () => {
    const { result } = renderHook(() => useHighContrastMode())

    expect(result.current.isHighContrast).toBe(false)
  })
})

describe('useFocusTrap', () => {
  it('returns a ref', () => {
    const { result } = renderHook(() => useFocusTrap<HTMLDivElement>())

    expect(result.current).toBeDefined()
    expect(result.current.current).toBeNull()
  })

  it('accepts enabled parameter', () => {
    const { result } = renderHook(() => useFocusTrap<HTMLDivElement>(false))

    expect(result.current).toBeDefined()
  })
})

describe('useScreenReaderAnnouncement', () => {
  it('returns announce function', () => {
    const { result } = renderHook(() => useScreenReaderAnnouncement())

    expect(typeof result.current.announce).toBe('function')
  })

  it('announce function can be called', () => {
    const { result } = renderHook(() => useScreenReaderAnnouncement())

    // Should not throw
    act(() => {
      result.current.announce('Test message')
    })
  })

  it('announce function accepts priority parameter', () => {
    const { result } = renderHook(() => useScreenReaderAnnouncement())

    // Should not throw
    act(() => {
      result.current.announce('Urgent message', 'assertive')
    })
  })
})

describe('useKeyboardShortcuts', () => {
  it('accepts shortcuts object', () => {
    const shortcuts = {
      'ctrl+s': vi.fn(),
      'ctrl+z': vi.fn(),
    }

    // Should not throw
    const { result } = renderHook(() => useKeyboardShortcuts(shortcuts))
    expect(result).toBeDefined()
  })

  it('accepts enabled parameter', () => {
    const shortcuts = { 'ctrl+s': vi.fn() }

    // Should not throw
    const { result } = renderHook(() => useKeyboardShortcuts(shortcuts, false))
    expect(result).toBeDefined()
  })
})

describe('useFocusRestore', () => {
  it('returns save and restore functions', () => {
    const { result } = renderHook(() => useFocusRestore())

    expect(typeof result.current.save).toBe('function')
    expect(typeof result.current.restore).toBe('function')
  })

  it('save and restore can be called', () => {
    const { result } = renderHook(() => useFocusRestore())

    // Should not throw
    act(() => {
      result.current.save()
      result.current.restore()
    })
  })
})

describe('useRovingTabIndex', () => {
  it('returns initial state with currentIndex 0', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    expect(result.current.currentIndex).toBe(0)
  })

  it('moveNext increments index', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    act(() => {
      result.current.moveNext()
    })

    expect(result.current.currentIndex).toBe(1)
  })

  it('moveNext wraps around', () => {
    const { result } = renderHook(() => useRovingTabIndex(3))

    act(() => {
      result.current.moveNext()
      result.current.moveNext()
      result.current.moveNext()
    })

    expect(result.current.currentIndex).toBe(0)
  })

  it('movePrevious decrements index', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    act(() => {
      result.current.moveNext()
      result.current.movePrevious()
    })

    expect(result.current.currentIndex).toBe(0)
  })

  it('movePrevious wraps around', () => {
    const { result } = renderHook(() => useRovingTabIndex(3))

    act(() => {
      result.current.movePrevious()
    })

    expect(result.current.currentIndex).toBe(2)
  })

  it('moveToIndex sets specific index', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    act(() => {
      result.current.moveToIndex(3)
    })

    expect(result.current.currentIndex).toBe(3)
  })

  it('moveToIndex ignores invalid index', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    act(() => {
      result.current.moveToIndex(10)
    })

    expect(result.current.currentIndex).toBe(0)
  })

  it('getTabIndex returns 0 for current, -1 for others', () => {
    const { result } = renderHook(() => useRovingTabIndex(5))

    expect(result.current.getTabIndex(0)).toBe(0)
    expect(result.current.getTabIndex(1)).toBe(-1)
    expect(result.current.getTabIndex(2)).toBe(-1)
  })
})

describe('useSkipLink', () => {
  it('returns skipToMainContent function', () => {
    const { result } = renderHook(() => useSkipLink())

    expect(typeof result.current.skipToMainContent).toBe('function')
  })

  it('accepts custom mainContentId', () => {
    const { result } = renderHook(() => useSkipLink('custom-main'))

    expect(typeof result.current.skipToMainContent).toBe('function')
  })

  it('skipToMainContent can be called', () => {
    const { result } = renderHook(() => useSkipLink())

    // Should not throw even if element doesn't exist
    act(() => {
      result.current.skipToMainContent()
    })
  })
})

describe('useLiveRegion', () => {
  it('returns liveRegionRef, content, and announce', () => {
    const { result } = renderHook(() => useLiveRegion())

    expect(result.current.liveRegionRef).toBeDefined()
    expect(result.current.content).toBe('')
    expect(typeof result.current.announce).toBe('function')
  })

  it('announce updates content', async () => {
    const { result } = renderHook(() => useLiveRegion())

    act(() => {
      result.current.announce('Test announcement')
    })

    expect(result.current.content).toBe('Test announcement')
  })

  it('accepts priority parameter', () => {
    const { result } = renderHook(() => useLiveRegion('assertive'))

    expect(result.current.liveRegionRef).toBeDefined()
  })
})

describe('useAccessibleDialog', () => {
  it('returns dialogProps and dialogRef', () => {
    const { result } = renderHook(() => useAccessibleDialog(false))

    expect(result.current.dialogProps).toBeDefined()
    expect(result.current.dialogRef).toBeDefined()
    expect(result.current.dialogProps.role).toBe('dialog')
    expect(result.current.dialogProps['aria-modal']).toBe(true)
  })

  it('dialogProps has correct attributes', () => {
    const { result } = renderHook(() => useAccessibleDialog(true))

    expect(result.current.dialogProps.role).toBe('dialog')
    expect(result.current.dialogProps['aria-modal']).toBe(true)
    expect(result.current.dialogProps.tabIndex).toBe(-1)
  })
})

describe('useAccessibleTooltip', () => {
  it('returns tooltip state and functions', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    expect(result.current.isVisible).toBe(false)
    expect(typeof result.current.show).toBe('function')
    expect(typeof result.current.hide).toBe('function')
    expect(typeof result.current.toggle).toBe('function')
  })

  it('show makes tooltip visible', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    act(() => {
      result.current.show()
    })

    expect(result.current.isVisible).toBe(true)
  })

  it('toggle toggles visibility', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isVisible).toBe(true)

    act(() => {
      result.current.toggle()
    })
    expect(result.current.isVisible).toBe(false)
  })

  it('triggerProps has correct attributes', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    expect(result.current.triggerProps.onMouseEnter).toBeDefined()
    expect(result.current.triggerProps.onMouseLeave).toBeDefined()
    expect(result.current.triggerProps.onFocus).toBeDefined()
    expect(result.current.triggerProps.onBlur).toBeDefined()
  })

  it('tooltipProps has correct attributes', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    expect(result.current.tooltipProps.role).toBe('tooltip')
    expect(result.current.tooltipProps['aria-hidden']).toBe(true)
  })

  it('tooltipProps aria-hidden is false when visible', () => {
    const { result } = renderHook(() => useAccessibleTooltip())

    act(() => {
      result.current.show()
    })

    expect(result.current.tooltipProps['aria-hidden']).toBe(false)
  })
})

describe('useAccessibleTabs', () => {
  it('returns tab navigation state and functions', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    expect(result.current.selectedIndex).toBe(0)
    expect(typeof result.current.selectTab).toBe('function')
    expect(typeof result.current.selectNext).toBe('function')
    expect(typeof result.current.selectPrevious).toBe('function')
    expect(typeof result.current.selectFirst).toBe('function')
    expect(typeof result.current.selectLast).toBe('function')
  })

  it('selectTab changes selected index', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    act(() => {
      result.current.selectTab(2)
    })

    expect(result.current.selectedIndex).toBe(2)
  })

  it('selectNext increments and wraps', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    act(() => {
      result.current.selectNext()
    })
    expect(result.current.selectedIndex).toBe(1)

    act(() => {
      result.current.selectNext()
      result.current.selectNext()
    })
    expect(result.current.selectedIndex).toBe(0)
  })

  it('selectPrevious decrements and wraps', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    act(() => {
      result.current.selectPrevious()
    })

    expect(result.current.selectedIndex).toBe(2)
  })

  it('selectFirst selects first tab', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    act(() => {
      result.current.selectTab(2)
      result.current.selectFirst()
    })

    expect(result.current.selectedIndex).toBe(0)
  })

  it('selectLast selects last tab', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    act(() => {
      result.current.selectLast()
    })

    expect(result.current.selectedIndex).toBe(2)
  })

  it('getTabProps returns correct attributes', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    const tabProps = result.current.getTabProps(0)
    expect(tabProps.role).toBe('tab')
    expect(tabProps['aria-selected']).toBe(true)
    expect(tabProps.tabIndex).toBe(0)

    const inactiveTabProps = result.current.getTabProps(1)
    expect(inactiveTabProps['aria-selected']).toBe(false)
    expect(inactiveTabProps.tabIndex).toBe(-1)
  })

  it('getTabPanelProps returns correct attributes', () => {
    const { result } = renderHook(() => useAccessibleTabs(3))

    const panelProps = result.current.getTabPanelProps(0)
    expect(panelProps.role).toBe('tabpanel')
    expect(panelProps['aria-hidden']).toBe(false)
    expect(panelProps.tabIndex).toBe(0)

    const hiddenPanelProps = result.current.getTabPanelProps(1)
    expect(hiddenPanelProps['aria-hidden']).toBe(true)
  })
})

describe('useAccessibleCombobox', () => {
  const options = ['Option 1', 'Option 2', 'Option 3']

  it('returns combobox state and functions', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    expect(result.current.isOpen).toBe(false)
    expect(result.current.selectedIndex).toBe(-1)
    expect(result.current.inputValue).toBe('')
    expect(typeof result.current.open).toBe('function')
    expect(typeof result.current.close).toBe('function')
  })

  it('open opens the listbox', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
    })

    expect(result.current.isOpen).toBe(true)
  })

  it('close closes the listbox', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.close()
    })

    expect(result.current.isOpen).toBe(false)
    expect(result.current.selectedIndex).toBe(-1)
  })

  it('selectNext increments selected index', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.selectNext()
    })

    expect(result.current.selectedIndex).toBe(0)

    act(() => {
      result.current.selectNext()
    })

    expect(result.current.selectedIndex).toBe(1)
  })

  it('selectNext stops at last option', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.selectNext()
      result.current.selectNext()
      result.current.selectNext()
      result.current.selectNext()
    })

    expect(result.current.selectedIndex).toBe(2)
  })

  it('selectPrevious decrements selected index', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.selectNext()
      result.current.selectNext()
      result.current.selectPrevious()
    })

    expect(result.current.selectedIndex).toBe(0)
  })

  it('selectOption selects and closes', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.selectOption(1)
    })

    expect(result.current.isOpen).toBe(false)
  })

  it('setInputValue updates input value', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.setInputValue('test')
    })

    expect(result.current.inputValue).toBe('test')
  })

  it('inputProps has correct attributes', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    expect(result.current.inputProps.role).toBe('combobox')
    expect(result.current.inputProps['aria-expanded']).toBe(false)
    expect(result.current.inputProps['aria-autocomplete']).toBe('list')
  })

  it('listboxProps has correct attributes', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    expect(result.current.listboxProps.role).toBe('listbox')
  })

  it('getOptionProps returns correct attributes', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    const optionProps = result.current.getOptionProps(0)
    expect(optionProps.role).toBe('option')
    expect(optionProps['aria-selected']).toBe(false)
  })

  it('getOptionProps shows selected state', () => {
    const { result } = renderHook(() => useAccessibleCombobox(options))

    act(() => {
      result.current.open()
      result.current.selectNext()
    })

    const optionProps = result.current.getOptionProps(0)
    expect(optionProps['aria-selected']).toBe(true)
  })
})

describe('Edge Cases', () => {
  it('useRovingTabIndex handles zero items', () => {
    const { result } = renderHook(() => useRovingTabIndex(0))

    // Should not throw
    act(() => {
      result.current.moveNext()
      result.current.movePrevious()
    })
  })

  it('useAccessibleTabs handles single tab', () => {
    const { result } = renderHook(() => useAccessibleTabs(1))

    act(() => {
      result.current.selectNext()
    })

    expect(result.current.selectedIndex).toBe(0)
  })

  it('useAccessibleCombobox handles empty options', () => {
    const { result } = renderHook(() => useAccessibleCombobox([]))

    act(() => {
      result.current.open()
      result.current.selectNext()
    })

    expect(result.current.selectedIndex).toBe(-1)
  })
})
