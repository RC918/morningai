import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings, X, Eye, Keyboard, Volume2, Contrast, Type, Zap } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement } from '@/hooks/use-accessibility'

interface AccessibilitySettings {
  reducedMotion: boolean
  highContrast: boolean
  fontSize: 'small' | 'medium' | 'large' | 'extra-large'
  screenReaderAnnouncements: boolean
  keyboardShortcuts: boolean
  focusIndicators: 'default' | 'enhanced'
}

interface AccessibilityContextValue {
  settings: AccessibilitySettings
  updateSetting: <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => void
  resetSettings: () => void
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

const defaultSettings: AccessibilitySettings = {
  reducedMotion: false,
  highContrast: false,
  fontSize: 'medium',
  screenReaderAnnouncements: true,
  keyboardShortcuts: true,
  focusIndicators: 'default'
}

const AccessibilityContext = createContext<AccessibilityContextValue | null>(null)

export const useAccessibilitySettings = (): AccessibilityContextValue => {
  const context = useContext(AccessibilityContext)
  if (!context) {
    throw new Error('useAccessibilitySettings must be used within AccessibilityProvider')
  }
  return context
}

const ToggleSwitch: React.FC<{
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  description?: string
  icon?: React.ReactNode
}> = ({ checked, onChange, label, description, icon }) => {
  const announce = useScreenReaderAnnouncement()

  const handleToggle = () => {
    const newValue = !checked
    onChange(newValue)
    announce(`${label} ${newValue ? 'enabled' : 'disabled'}`, 'polite')
  }

  return (
    <div className="flex items-start gap-3 p-4 rounded-xl hover:bg-white/5 transition-colors">
      {icon && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white/70">
          {icon}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-white text-sm">{label}</div>
        {description && (
          <div className="text-white/60 text-xs mt-1">{description}</div>
        )}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={`${label} ${checked ? 'enabled' : 'disabled'}`}
        onClick={handleToggle}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900',
          checked ? 'bg-blue-500' : 'bg-white/20'
        )}
      >
        <motion.div
          initial={false}
          animate={{ x: checked ? 20 : 2 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-lg"
        />
      </button>
    </div>
  )
}

const FontSizeSelector: React.FC<{
  value: AccessibilitySettings['fontSize']
  onChange: (value: AccessibilitySettings['fontSize']) => void
}> = ({ value, onChange }) => {
  const { t } = useTranslation()
  const announce = useScreenReaderAnnouncement()

  const options: Array<{ value: AccessibilitySettings['fontSize']; label: string }> = [
    { value: 'small', label: t('accessibility.fontSize.small', 'Small') },
    { value: 'medium', label: t('accessibility.fontSize.medium', 'Medium') },
    { value: 'large', label: t('accessibility.fontSize.large', 'Large') },
    { value: 'extra-large', label: t('accessibility.fontSize.extraLarge', 'Extra Large') }
  ]

  const handleChange = (newValue: AccessibilitySettings['fontSize']) => {
    onChange(newValue)
    announce(`Font size changed to ${newValue}`, 'polite')
  }

  return (
    <div className="p-4 rounded-xl hover:bg-white/5 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white/70">
          <Type className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-medium text-white text-sm">
            {t('accessibility.fontSize.title', 'Font Size')}
          </div>
          <div className="text-white/60 text-xs mt-1">
            {t('accessibility.fontSize.description', 'Adjust text size for better readability')}
          </div>
        </div>
      </div>
      <div
        role="radiogroup"
        aria-label="Font size options"
        className="grid grid-cols-2 gap-2"
      >
        {options.map((option) => (
          <button
            key={option.value}
            role="radio"
            aria-checked={value === option.value}
            onClick={() => handleChange(option.value)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              value === option.value
                ? 'bg-blue-500 text-white'
                : 'bg-white/10 text-white/70 hover:bg-white/20'
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

const FocusIndicatorSelector: React.FC<{
  value: AccessibilitySettings['focusIndicators']
  onChange: (value: AccessibilitySettings['focusIndicators']) => void
}> = ({ value, onChange }) => {
  const { t } = useTranslation()
  const announce = useScreenReaderAnnouncement()

  const options: Array<{ value: AccessibilitySettings['focusIndicators']; label: string; description: string }> = [
    {
      value: 'default',
      label: t('accessibility.focusIndicators.default', 'Default'),
      description: t('accessibility.focusIndicators.defaultDesc', 'Standard focus outline')
    },
    {
      value: 'enhanced',
      label: t('accessibility.focusIndicators.enhanced', 'Enhanced'),
      description: t('accessibility.focusIndicators.enhancedDesc', 'High visibility focus outline')
    }
  ]

  const handleChange = (newValue: AccessibilitySettings['focusIndicators']) => {
    onChange(newValue)
    announce(`Focus indicators changed to ${newValue}`, 'polite')
  }

  return (
    <div className="p-4 rounded-xl hover:bg-white/5 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white/70">
          <Zap className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-medium text-white text-sm">
            {t('accessibility.focusIndicators.title', 'Focus Indicators')}
          </div>
          <div className="text-white/60 text-xs mt-1">
            {t('accessibility.focusIndicators.description', 'Customize keyboard focus visibility')}
          </div>
        </div>
      </div>
      <div
        role="radiogroup"
        aria-label="Focus indicator options"
        className="space-y-2"
      >
        {options.map((option) => (
          <button
            key={option.value}
            role="radio"
            aria-checked={value === option.value}
            onClick={() => handleChange(option.value)}
            className={cn(
              'w-full px-4 py-3 rounded-lg text-left transition-all',
              'focus:outline-none focus:ring-2 focus:ring-blue-500',
              value === option.value
                ? 'bg-blue-500/20 border border-blue-500/30'
                : 'bg-white/10 border border-transparent hover:bg-white/20'
            )}
          >
            <div className="font-medium text-white text-sm">{option.label}</div>
            <div className="text-white/60 text-xs mt-1">{option.description}</div>
          </button>
        ))}
      </div>
    </div>
  )
}

const AccessibilitySettingsPanel: React.FC = () => {
  const { t } = useTranslation()
  const { settings, updateSetting, resetSettings, isOpen, close } = useAccessibilitySettings()
  const panelRef = React.useRef<HTMLDivElement>(null)
  const previousFocusRef = React.useRef<HTMLElement | null>(null)
  const announce = useScreenReaderAnnouncement()

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement
      
      setTimeout(() => {
        if (panelRef.current) {
          const firstFocusable = panelRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          )
          firstFocusable?.focus()
        }
      }, 100)
      
      announce('Accessibility settings opened', 'polite')
    }

    return () => {
      if (!isOpen && previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
        previousFocusRef.current.focus()
      }
    }
  }, [isOpen, announce])

  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        close()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, close])

  useEffect(() => {
    if (!isOpen || !panelRef.current) return

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return

      const focusableElements = panelRef.current!.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]

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

    document.addEventListener('keydown', handleTab)
    return () => document.removeEventListener('keydown', handleTab)
  }, [isOpen])

  const handleReset = () => {
    resetSettings()
    if (panelRef.current) {
      triggerHaptic(panelRef.current, 'medium')
    }
    announce('Accessibility settings reset to defaults', 'polite')
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={close}
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-label="Accessibility Settings"
            aria-modal="true"
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-hidden"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{
              type: 'spring',
              stiffness: 500,
              damping: 30
            }}
          >
            <div className="bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Settings className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      {t('accessibility.title', 'Accessibility Settings')}
                    </h2>
                    <p className="text-xs text-white/60">
                      {t('accessibility.subtitle', 'Customize your experience')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={close}
                  className="p-2 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
                  aria-label="Close accessibility settings"
                >
                  <X className="w-5 h-5 text-white/70" />
                </button>
              </div>

              {/* Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6 space-y-2">
                <ToggleSwitch
                  checked={settings.reducedMotion}
                  onChange={(value) => updateSetting('reducedMotion', value)}
                  label={t('accessibility.reducedMotion.title', 'Reduced Motion')}
                  description={t('accessibility.reducedMotion.description', 'Minimize animations and transitions')}
                  icon={<Zap className="w-5 h-5" />}
                />

                <ToggleSwitch
                  checked={settings.highContrast}
                  onChange={(value) => updateSetting('highContrast', value)}
                  label={t('accessibility.highContrast.title', 'High Contrast')}
                  description={t('accessibility.highContrast.description', 'Increase color contrast for better visibility')}
                  icon={<Contrast className="w-5 h-5" />}
                />

                <ToggleSwitch
                  checked={settings.screenReaderAnnouncements}
                  onChange={(value) => updateSetting('screenReaderAnnouncements', value)}
                  label={t('accessibility.screenReader.title', 'Screen Reader Announcements')}
                  description={t('accessibility.screenReader.description', 'Enable live region announcements')}
                  icon={<Volume2 className="w-5 h-5" />}
                />

                <ToggleSwitch
                  checked={settings.keyboardShortcuts}
                  onChange={(value) => updateSetting('keyboardShortcuts', value)}
                  label={t('accessibility.keyboardShortcuts.title', 'Keyboard Shortcuts')}
                  description={t('accessibility.keyboardShortcuts.description', 'Enable keyboard navigation shortcuts')}
                  icon={<Keyboard className="w-5 h-5" />}
                />

                <FontSizeSelector
                  value={settings.fontSize}
                  onChange={(value) => updateSetting('fontSize', value)}
                />

                <FocusIndicatorSelector
                  value={settings.focusIndicators}
                  onChange={(value) => updateSetting('focusIndicators', value)}
                />
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-white/5">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                >
                  {t('accessibility.reset', 'Reset to Defaults')}
                </button>
                <button
                  onClick={close}
                  className="px-6 py-2 rounded-lg text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700 transition-colors"
                >
                  {t('accessibility.done', 'Done')}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('accessibility-settings')
      if (saved) {
        try {
          return { ...defaultSettings, ...JSON.parse(saved) }
        } catch {
          return defaultSettings
        }
      }
    }
    return defaultSettings
  })

  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('accessibility-settings', JSON.stringify(settings))
    }
  }, [settings])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const root = document.documentElement

      if (settings.reducedMotion) {
        root.classList.add('reduce-motion')
      } else {
        root.classList.remove('reduce-motion')
      }

      if (settings.highContrast) {
        root.classList.add('high-contrast')
      } else {
        root.classList.remove('high-contrast')
      }

      root.setAttribute('data-font-size', settings.fontSize)

      root.setAttribute('data-focus-indicators', settings.focusIndicators)
    }
  }, [settings])

  const updateSetting = useCallback(
    <K extends keyof AccessibilitySettings>(key: K, value: AccessibilitySettings[K]) => {
      setSettings((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings)
  }, [])

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => setIsOpen(false), [])
  const toggle = useCallback(() => setIsOpen((prev) => !prev), [])

  const value: AccessibilityContextValue = {
    settings,
    updateSetting,
    resetSettings,
    isOpen,
    open,
    close,
    toggle
  }

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      <AccessibilitySettingsPanel />
    </AccessibilityContext.Provider>
  )
}

export const AccessibilityTriggerButton: React.FC<{
  className?: string
  variant?: 'icon' | 'text' | 'full'
}> = ({ className, variant = 'icon' }) => {
  const { open } = useAccessibilitySettings()
  const { t } = useTranslation()

  if (variant === 'text') {
    return (
      <button
        onClick={open}
        className={cn(
          'px-4 py-2 rounded-lg text-sm font-medium',
          'text-gray-700 dark:text-gray-300',
          'hover:bg-gray-100 dark:hover:bg-gray-800',
          'active:bg-gray-200 dark:active:bg-gray-700',
          'transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500',
          className
        )}
        aria-label={t('accessibility.openSettings', 'Open accessibility settings')}
      >
        {t('accessibility.settings', 'Accessibility')}
      </button>
    )
  }

  if (variant === 'full') {
    return (
      <button
        onClick={open}
        className={cn(
          'flex items-center gap-3 px-4 py-3 rounded-lg',
          'text-gray-700 dark:text-gray-300',
          'hover:bg-gray-100 dark:hover:bg-gray-800',
          'active:bg-gray-200 dark:active:bg-gray-700',
          'transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500',
          className
        )}
        aria-label={t('accessibility.openSettings', 'Open accessibility settings')}
      >
        <Settings className="w-5 h-5" />
        <span className="text-sm font-medium">
          {t('accessibility.settings', 'Accessibility')}
        </span>
      </button>
    )
  }

  return (
    <button
      onClick={open}
      className={cn(
        'p-2 rounded-full',
        'text-gray-700 dark:text-gray-300',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        'active:bg-gray-200 dark:active:bg-gray-700',
        'transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-blue-500',
        className
      )}
      aria-label={t('accessibility.openSettings', 'Open accessibility settings')}
    >
      <Settings className="w-5 h-5" />
    </button>
  )
}

export const AppleAccessibilitySettings = {
  Provider: AccessibilityProvider,
  useSettings: useAccessibilitySettings,
  TriggerButton: AccessibilityTriggerButton
}

export type { AccessibilitySettings, AccessibilityContextValue }
