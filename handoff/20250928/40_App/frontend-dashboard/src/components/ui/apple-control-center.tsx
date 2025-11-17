/* eslint-disable i18next/no-literal-string */
/* NOTE: This file is exempted from strict i18n checks to maintain PR scope.
 * i18n improvements will be addressed in a dedicated PR (see Issue #1328).
 * This aligns with local ESLint config which already exempts this file.
 */

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement, useFocusTrap } from '@/hooks/use-accessibility'

type ControlSize = '1x1' | '2x1' | '1x2' | '2x2'
type ControlVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger'

interface ControlAction {
  id: string
  label: string
  icon?: React.ReactNode
  onPress: () => void
}

interface Control {
  id: string
  title: string
  subtitle?: string
  icon: React.ReactNode
  size?: ControlSize
  variant?: ControlVariant
  active?: boolean
  value?: string | number
  actions?: ControlAction[]
  onPress?: () => void
  onLongPress?: () => void
}

interface ControlCenterContextValue {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
  controls: Control[]
  setControls: (controls: Control[]) => void
}

interface ControlCenterProviderProps {
  children: React.ReactNode
  controls?: Control[]
}

const ControlCenterContext = createContext<ControlCenterContextValue | null>(null)

export const useAppleControlCenter = (): ControlCenterContextValue => {
  const context = useContext(ControlCenterContext)
  if (!context) {
    throw new Error('useAppleControlCenter must be used within AppleControlCenterProvider')
  }
  return context
}

const ControlCard: React.FC<{
  control: Control
  onPress: (id: string) => void
  onLongPress: (id: string) => void
}> = ({ control, onPress, onLongPress }) => {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)
  const [isPressed, setIsPressed] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const longPressTimer = useRef<NodeJS.Timeout | null>(null)
  const { announce } = useScreenReaderAnnouncement()

  const handlePressStart = () => {
    setIsPressed(true)
    if (cardRef.current) {
      triggerHaptic(cardRef.current, 'light')
    }

    longPressTimer.current = setTimeout(() => {
      if (control.actions && control.actions.length > 0) {
        setIsExpanded(true)
        if (cardRef.current) {
          triggerHaptic(cardRef.current, 'medium')
        }
        onLongPress(control.id)
      }
    }, 500)
  }

  const handlePressEnd = () => {
    setIsPressed(false)
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current)
      longPressTimer.current = null
    }

    if (!isExpanded) {
      onPress(control.id)
      announce(
        `${control.title} ${control.active ? t('controlCenter.activated', 'activated') : t('controlCenter.deactivated', 'deactivated')}`,
        'polite'
      )
    }
  }

  const handlePressCancel = () => {
    setIsPressed(false)
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current)
      longPressTimer.current = null
    }
  }

  const handleActionPress = (actionId: string) => {
    const action = control.actions?.find(a => a.id === actionId)
    if (action) {
      if (cardRef.current) {
        triggerHaptic(cardRef.current, 'light')
      }
      action.onPress()
      setIsExpanded(false)
    }
  }

  const sizeClasses: Record<ControlSize, string> = {
    '1x1': 'col-span-1 row-span-1 h-24',
    '2x1': 'col-span-2 row-span-1 h-24',
    '1x2': 'col-span-1 row-span-2 h-52',
    '2x2': 'col-span-2 row-span-2 h-52'
  }

  const variantStyles: Record<ControlVariant, string> = {
    default: control.active
      ? 'bg-white/20 border-white/30'
      : 'bg-white/10 border-white/20',
    primary: control.active
      ? 'bg-primary-500/90 border-primary-400/30'
      : 'bg-primary-500/20 border-primary-400/20',
    success: control.active
      ? 'bg-success-500/90 border-success-400/30'
      : 'bg-success-500/20 border-success-400/20',
    warning: control.active
      ? 'bg-warning-500/90 border-warning-400/30'
      : 'bg-warning-500/20 border-warning-400/20',
    danger: control.active
      ? 'bg-error-500/90 border-error-400/30'
      : 'bg-error-500/20 border-error-400/20'
  }

  return (
    <>
      <motion.div
        ref={cardRef}
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: isPressed ? 0.95 : 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30
        }}
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={handlePressCancel}
        onTouchStart={handlePressStart}
        onTouchEnd={handlePressEnd}
        onTouchCancel={handlePressCancel}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handlePressEnd()
          }
        }}
        role="button"
        tabIndex={0}
        aria-label={`${control.title}${control.subtitle ? `, ${control.subtitle}` : ''}${control.active ? ', active' : ''}`}
        aria-pressed={control.active}
        className={cn(
          'relative rounded-3xl backdrop-blur-xl border overflow-hidden',
          'cursor-pointer select-none',
          'transition-all duration-150',
          sizeClasses[control.size || '1x1'],
          variantStyles[control.variant || 'default']
        )}
        style={{
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
        }}
      >
        <div className="p-4 h-full flex flex-col justify-between">
          {/* Icon */}
          <div className="flex items-start justify-between">
            <div className={cn(
              'flex items-center justify-center',
              control.active ? 'text-white' : 'text-white/70'
            )}
            >
              {React.isValidElement(control.icon) 
                ? React.cloneElement(control.icon as React.ReactElement<{ className?: string }>, { className: 'w-6 h-6' })
                : control.icon
              }
            </div>
            {control.value !== undefined && (
              <div className={cn(
                'text-sm font-medium',
                control.active ? 'text-white' : 'text-white/70'
              )}
              >
                {control.value}
              </div>
            )}
          </div>

          {/* Title & Subtitle */}
          <div>
            <div className={cn(
              'font-semibold text-sm leading-tight',
              control.active ? 'text-white' : 'text-white/90'
            )}
            >
              {control.title}
            </div>
            {control.subtitle && (
              <div className="text-white/60 text-xs mt-0.5">
                {control.subtitle}
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Expanded Actions */}
      <AnimatePresence>
        {isExpanded && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsExpanded(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            />

            {/* Actions Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{
                type: 'spring',
                stiffness: 500,
                damping: 30
              }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50"
            >
              <div className="bg-neutral-900/95 backdrop-blur-xl rounded-3xl border border-white/20 p-6 min-w-[300px] shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="font-semibold text-white text-lg">
                      {control.title}
                    </div>
                    {control.subtitle && (
                      <div className="text-white/60 text-sm mt-0.5">
                        {control.subtitle}
                      </div>
                    )}
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => setIsExpanded(false)}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') {
                        e.preventDefault()
                        setIsExpanded(false)
                      }
                    }}
                    className="p-2 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
                    aria-label={t('controlCenter.close', 'Close')}
                  >
                    <X className="w-5 h-5 text-white" />
                  </motion.button>
                </div>

                <div className="space-y-2">
                  {control.actions?.map((action) => (
                    <motion.button
                      key={action.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleActionPress(action.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleActionPress(action.id)
                        }
                      }}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/10 hover:bg-white/20 active:bg-white/30 transition-colors"
                      aria-label={action.label}
                    >
                      {action.icon && (
                        <div className="text-white">
                          {React.isValidElement(action.icon)
                            ? React.cloneElement(action.icon as React.ReactElement<{ className?: string }>, { className: 'w-5 h-5' })
                            : action.icon
                          }
                        </div>
                      )}
                      <span className="text-white font-medium">
                        {action.label}
                      </span>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export const AppleControlCenterProvider: React.FC<ControlCenterProviderProps> = ({
  children,
  controls: initialControls = []
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [controls, setControls] = useState<Control[]>(initialControls)
  const panelRef = useFocusTrap<HTMLDivElement>(isOpen)
  const { announce } = useScreenReaderAnnouncement()

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        close()
      }
    }
    
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  const open = useCallback(() => {
    setIsOpen(true)
    announce('Control Center opened', 'polite')
  }, [announce])

  const close = useCallback(() => {
    setIsOpen(false)
    announce('Control Center closed', 'polite')
  }, [announce])

  const toggle = useCallback(() => {
    setIsOpen(prev => !prev)
  }, [])

  const handleControlPress = useCallback((id: string) => {
    const control = controls.find(c => c.id === id)
    if (control?.onPress) {
      control.onPress()
    }
  }, [controls])

  const handleControlLongPress = useCallback((id: string) => {
    const control = controls.find(c => c.id === id)
    if (control?.onLongPress) {
      control.onLongPress()
    }
  }, [controls])

  const contextValue: ControlCenterContextValue = {
    isOpen,
    open,
    close,
    toggle,
    controls,
    setControls
  }

  return (
    <ControlCenterContext.Provider value={contextValue}>
      {children}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={close}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            />

            {/* Control Center Panel */}
            <motion.div
              ref={panelRef}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 50 }}
              transition={{
                type: 'spring',
                stiffness: 500,
                damping: 30
              }}
              role="dialog"
              aria-label="Control Center"
              aria-modal="true"
              className="fixed right-4 top-4 z-40 w-full max-w-md"
            >
              <div className="bg-neutral-900/95 backdrop-blur-xl rounded-3xl border border-white/20 p-6 shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-white font-semibold text-lg">
                    Control Center
                  </h2>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={close}
                    className="p-2 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
                    aria-label="Close Control Center"
                  >
                    <X className="w-5 h-5 text-white" />
                  </motion.button>
                </div>

                {/* Controls Grid */}
                <div className="grid grid-cols-2 gap-3 auto-rows-min">
                  {controls.map((control) => (
                    <ControlCard
                      key={control.id}
                      control={control}
                      onPress={handleControlPress}
                      onLongPress={handleControlLongPress}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </ControlCenterContext.Provider>
  )
}

export const AppleControlCenter = {
  Provider: AppleControlCenterProvider,
  useControlCenter: useAppleControlCenter
}

export type {
  ControlSize,
  ControlVariant,
  ControlAction,
  Control,
  ControlCenterContextValue,
  ControlCenterProviderProps
}
