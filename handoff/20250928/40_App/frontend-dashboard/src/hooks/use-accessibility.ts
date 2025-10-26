/**
 * React Hooks for Accessibility Features
 * 
 * This module provides React hooks for implementing WCAG AAA accessibility features
 * including keyboard navigation, screen reader support, focus management, and more.
 * 
 * @module use-accessibility
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import {
  prefersReducedMotion,
  onMotionPreferenceChange,
  trapFocus,
  announceToScreenReader,
  registerKeyboardShortcut,
  isHighContrastMode,
  onHighContrastModeChange,
} from '@/lib/accessibility'

/**
 * Hook for managing reduced motion preference
 * @returns Object with prefersReduced state and setter
 */
export function useReducedMotion() {
  const [prefersReduced, setPrefersReduced] = useState(prefersReducedMotion())
  
  useEffect(() => {
    const cleanup = onMotionPreferenceChange(setPrefersReduced)
    return cleanup
  }, [])
  
  return { prefersReduced, setPrefersReduced }
}

/**
 * Hook for managing high contrast mode
 * @returns Object with isHighContrast state
 */
export function useHighContrastMode() {
  const [isHighContrast, setIsHighContrast] = useState(isHighContrastMode())
  
  useEffect(() => {
    const cleanup = onHighContrastModeChange(setIsHighContrast)
    return cleanup
  }, [])
  
  return { isHighContrast }
}

/**
 * Hook for trapping focus within a container
 * @param enabled - Whether focus trap is enabled
 * @returns Ref to attach to container
 */
export function useFocusTrap<T extends HTMLElement>(enabled: boolean = true) {
  const containerRef = useRef<T>(null)
  
  useEffect(() => {
    if (!enabled || !containerRef.current) return
    
    const cleanup = trapFocus(containerRef.current)
    return cleanup
  }, [enabled])
  
  return containerRef
}

/**
 * Hook for announcing messages to screen readers
 * @returns Function to announce messages
 */
export function useScreenReaderAnnouncement() {
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announceToScreenReader(message, priority)
  }, [])
  
  return { announce }
}

/**
 * Hook for managing keyboard shortcuts
 * @param shortcuts - Object mapping keys to handlers
 * @param enabled - Whether shortcuts are enabled
 */
export function useKeyboardShortcuts(
  shortcuts: Record<string, (e: KeyboardEvent) => void>,
  enabled: boolean = true
) {
  useEffect(() => {
    if (!enabled) return
    
    const cleanups = Object.entries(shortcuts).map(([key, handler]) =>
      registerKeyboardShortcut(key, handler)
    )
    
    return () => {
      cleanups.forEach(cleanup => cleanup())
    }
  }, [shortcuts, enabled])
}

/**
 * Hook for managing focus restoration
 * @returns Object with save and restore functions
 */
export function useFocusRestore() {
  const previousFocusRef = useRef<HTMLElement | null>(null)
  
  const save = useCallback(() => {
    previousFocusRef.current = document.activeElement as HTMLElement
  }, [])
  
  const restore = useCallback(() => {
    previousFocusRef.current?.focus()
    previousFocusRef.current = null
  }, [])
  
  return { save, restore }
}

/**
 * Hook for managing roving tabindex (for keyboard navigation in lists)
 * @param itemsCount - Number of items in the list
 * @returns Object with current index and navigation functions
 */
export function useRovingTabIndex(itemsCount: number) {
  const [currentIndex, setCurrentIndex] = useState(0)
  
  const moveNext = useCallback(() => {
    setCurrentIndex(prev => (prev + 1) % itemsCount)
  }, [itemsCount])
  
  const movePrevious = useCallback(() => {
    setCurrentIndex(prev => (prev - 1 + itemsCount) % itemsCount)
  }, [itemsCount])
  
  const moveToIndex = useCallback((index: number) => {
    if (index >= 0 && index < itemsCount) {
      setCurrentIndex(index)
    }
  }, [itemsCount])
  
  const getTabIndex = useCallback((index: number) => {
    return index === currentIndex ? 0 : -1
  }, [currentIndex])
  
  return {
    currentIndex,
    moveNext,
    movePrevious,
    moveToIndex,
    getTabIndex,
  }
}

/**
 * Hook for managing skip links
 * @param mainContentId - ID of main content element
 * @returns Function to skip to main content
 */
export function useSkipLink(mainContentId: string = 'main-content') {
  const skipToMainContent = useCallback(() => {
    const mainContent = document.getElementById(mainContentId)
    if (mainContent) {
      mainContent.focus()
      mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [mainContentId])
  
  return { skipToMainContent }
}

/**
 * Hook for managing live regions (for dynamic content updates)
 * @param priority - Priority level (polite or assertive)
 * @returns Ref to attach to live region and function to update content
 */
export function useLiveRegion(priority: 'polite' | 'assertive' = 'polite') {
  const liveRegionRef = useRef<HTMLDivElement>(null)
  const [content, setContent] = useState('')
  
  useEffect(() => {
    if (liveRegionRef.current) {
      liveRegionRef.current.setAttribute('role', 'status')
      liveRegionRef.current.setAttribute('aria-live', priority)
      liveRegionRef.current.setAttribute('aria-atomic', 'true')
    }
  }, [priority])
  
  const announce = useCallback((message: string) => {
    setContent(message)
    setTimeout(() => setContent(''), 1000)
  }, [])
  
  return { liveRegionRef, content, announce }
}

/**
 * Hook for managing accessible dialogs
 * @param isOpen - Whether dialog is open
 * @returns Object with dialog props and functions
 */
export function useAccessibleDialog(isOpen: boolean) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const { save, restore } = useFocusRestore()
  
  useEffect(() => {
    if (isOpen) {
      save()
    } else {
      restore()
    }
  }, [isOpen, save, restore])
  
  useEffect(() => {
    if (!isOpen || !dialogRef.current) return
    
    const cleanup = trapFocus(dialogRef.current)
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        restore()
      }
    }
    
    document.addEventListener('keydown', handleEscape)
    
    return () => {
      cleanup()
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, restore])
  
  const dialogProps = {
    ref: dialogRef,
    role: 'dialog',
    'aria-modal': true,
    tabIndex: -1,
  }
  
  return { dialogProps, dialogRef }
}

/**
 * Hook for managing accessible tooltips
 * @returns Object with tooltip props and state
 */
export function useAccessibleTooltip() {
  const [isVisible, setIsVisible] = useState(false)
  const [tooltipId] = useState(() => `tooltip-${Math.random().toString(36).substr(2, 9)}`)
  const timeoutRef = useRef<NodeJS.Timeout>()
  
  const show = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    setIsVisible(true)
  }, [])
  
  const hide = useCallback(() => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(false)
    }, 200)
  }, [])
  
  const toggle = useCallback(() => {
    setIsVisible(prev => !prev)
  }, [])
  
  const triggerProps = {
    'aria-describedby': isVisible ? tooltipId : undefined,
    onMouseEnter: show,
    onMouseLeave: hide,
    onFocus: show,
    onBlur: hide,
  }
  
  const tooltipProps = {
    id: tooltipId,
    role: 'tooltip',
    'aria-hidden': !isVisible,
  }
  
  return {
    isVisible,
    show,
    hide,
    toggle,
    triggerProps,
    tooltipProps,
  }
}

/**
 * Hook for managing accessible tabs
 * @param tabsCount - Number of tabs
 * @returns Object with tab navigation functions and props
 */
export function useAccessibleTabs(tabsCount: number) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  
  const selectTab = useCallback((index: number) => {
    if (index >= 0 && index < tabsCount) {
      setSelectedIndex(index)
    }
  }, [tabsCount])
  
  const selectNext = useCallback(() => {
    setSelectedIndex(prev => (prev + 1) % tabsCount)
  }, [tabsCount])
  
  const selectPrevious = useCallback(() => {
    setSelectedIndex(prev => (prev - 1 + tabsCount) % tabsCount)
  }, [tabsCount])
  
  const selectFirst = useCallback(() => {
    setSelectedIndex(0)
  }, [])
  
  const selectLast = useCallback(() => {
    setSelectedIndex(tabsCount - 1)
  }, [tabsCount])
  
  const getTabProps = useCallback((index: number) => ({
    role: 'tab',
    'aria-selected': index === selectedIndex,
    tabIndex: index === selectedIndex ? 0 : -1,
    onClick: () => selectTab(index),
    onKeyDown: (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowRight':
          e.preventDefault()
          selectNext()
          break
        case 'ArrowLeft':
          e.preventDefault()
          selectPrevious()
          break
        case 'Home':
          e.preventDefault()
          selectFirst()
          break
        case 'End':
          e.preventDefault()
          selectLast()
          break
      }
    },
  }), [selectedIndex, selectTab, selectNext, selectPrevious, selectFirst, selectLast])
  
  const getTabPanelProps = useCallback((index: number) => ({
    role: 'tabpanel',
    'aria-hidden': index !== selectedIndex,
    tabIndex: 0,
  }), [selectedIndex])
  
  return {
    selectedIndex,
    selectTab,
    selectNext,
    selectPrevious,
    selectFirst,
    selectLast,
    getTabProps,
    getTabPanelProps,
  }
}

/**
 * Hook for managing accessible combobox (autocomplete)
 * @param options - Array of options
 * @returns Object with combobox state and props
 */
export function useAccessibleCombobox<T>(options: T[]) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [inputValue, setInputValue] = useState('')
  const comboboxId = useRef(`combobox-${Math.random().toString(36).substr(2, 9)}`)
  const listboxId = useRef(`listbox-${Math.random().toString(36).substr(2, 9)}`)
  
  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => {
    setIsOpen(false)
    setSelectedIndex(-1)
  }, [])
  
  const selectNext = useCallback(() => {
    setSelectedIndex(prev => Math.min(prev + 1, options.length - 1))
  }, [options.length])
  
  const selectPrevious = useCallback(() => {
    setSelectedIndex(prev => Math.max(prev - 1, -1))
  }, [])
  
  const selectOption = useCallback((index: number) => {
    if (index >= 0 && index < options.length) {
      setSelectedIndex(index)
      close()
    }
  }, [options.length, close])
  
  const inputProps = {
    id: comboboxId.current,
    role: 'combobox',
    'aria-expanded': isOpen,
    'aria-controls': listboxId.current,
    'aria-activedescendant': selectedIndex >= 0 ? `${listboxId.current}-option-${selectedIndex}` : undefined,
    'aria-autocomplete': 'list' as const,
    value: inputValue,
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(e.target.value)
      open()
    },
    onKeyDown: (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          if (!isOpen) open()
          else selectNext()
          break
        case 'ArrowUp':
          e.preventDefault()
          if (isOpen) selectPrevious()
          break
        case 'Enter':
          e.preventDefault()
          if (selectedIndex >= 0) selectOption(selectedIndex)
          break
        case 'Escape':
          e.preventDefault()
          close()
          break
      }
    },
  }
  
  const listboxProps = {
    id: listboxId.current,
    role: 'listbox',
    'aria-labelledby': comboboxId.current,
  }
  
  const getOptionProps = useCallback((index: number) => ({
    id: `${listboxId.current}-option-${index}`,
    role: 'option',
    'aria-selected': index === selectedIndex,
    onClick: () => selectOption(index),
  }), [selectedIndex, selectOption])
  
  return {
    isOpen,
    selectedIndex,
    inputValue,
    setInputValue,
    open,
    close,
    selectNext,
    selectPrevious,
    selectOption,
    inputProps,
    listboxProps,
    getOptionProps,
  }
}
