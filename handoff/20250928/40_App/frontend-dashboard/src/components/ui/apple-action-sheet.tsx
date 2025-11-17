import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement } from '@/hooks/use-accessibility'

export type ActionSheetAction = {
  id: string
  label: string
  icon?: React.ReactNode
  destructive?: boolean
  disabled?: boolean
  onSelect: () => void
}

export type ActionSheetOptions = {
  title?: string
  message?: string
  actions: ActionSheetAction[]
  cancelLabel?: string
  onCancel?: () => void
}

type ActionSheetContextValue = {
  show: (options: ActionSheetOptions) => void
  hide: () => void
  isVisible: boolean
}

const ActionSheetContext = createContext<ActionSheetContextValue | null>(null)

export const useAppleActionSheet = () => {
  const context = useContext(ActionSheetContext)
  if (!context) {
    throw new Error('useAppleActionSheet must be used within AppleActionSheetProvider')
  }
  return context
}

const ActionSheet = ({ 
  options, 
  onClose 
}: { 
  options: ActionSheetOptions
  onClose: () => void 
}) => {
  const sheetRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)
  const { announce } = useScreenReaderAnnouncement()

  const handleClose = useCallback(() => {
    if (sheetRef.current) {
      triggerHaptic(sheetRef.current, 'light')
    }
    announce('Action sheet closed', 'polite')
    if (options.onCancel) {
      options.onCancel()
    }
    onClose()
  }, [onClose, options, announce])

  const handleActionSelect = useCallback((action: ActionSheetAction) => {
    if (action.disabled) return
    
    if (sheetRef.current) {
      triggerHaptic(sheetRef.current, action.destructive ? 'medium' : 'light')
    }
    
    announce(`${action.label} selected`, 'polite')
    action.onSelect()
    onClose()
  }, [onClose, announce])

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }

  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement

    if (sheetRef.current) {
      const firstButton = sheetRef.current.querySelector('button')
      firstButton?.focus()
    }

    const message = options.title 
      ? `Action sheet opened: ${options.title}` 
      : 'Action sheet opened'
    announce(message, 'polite')

    return () => {
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
        previousFocusRef.current.focus()
      }
    }
  }, [announce, options.title])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [handleClose])

  useEffect(() => {
    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !sheetRef.current) return

      const focusableElements = sheetRef.current.querySelectorAll<HTMLElement>(
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
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex items-end justify-center p-4"
      onClick={handleOverlayClick}
    >
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
      />

      {/* Action Sheet Container */}
      <motion.div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={options.title ? 'action-sheet-title' : undefined}
        aria-describedby={options.message ? 'action-sheet-message' : undefined}
        initial={{ y: '100%', opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: '100%', opacity: 0 }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
          mass: 1
        }}
        className="relative z-10 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Actions Card */}
        <div className="bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl rounded-2xl overflow-hidden shadow-2xl border border-white/20 dark:border-neutral-700/20">
          {/* Header */}
          {(options.title || options.message) && (
            <div className="px-6 py-4 text-center border-b border-neutral-200/50 dark:border-neutral-700/50">
              {options.title && (
                <h2 
                  id="action-sheet-title"
                  className="text-base font-semibold text-neutral-900 dark:text-white"
                >
                  {options.title}
                </h2>
              )}
              {options.message && (
                <p 
                  id="action-sheet-message"
                  className={cn(
                    'text-sm text-neutral-600 dark:text-neutral-400',
                    options.title && 'mt-1'
                  )}
                >
                  {options.message}
                </p>
              )}
            </div>
          )}

          {/* Actions List */}
          <div className="divide-y divide-gray-200/50 dark:divide-gray-700/50">
            {options.actions.map((action, index) => (
              <motion.button
                key={action.id}
                onClick={() => handleActionSelect(action)}
                disabled={action.disabled}
                aria-label={action.destructive ? `${action.label} (destructive action)` : action.label}
                aria-disabled={action.disabled}
                whileHover={!action.disabled ? { scale: 1.02 } : undefined}
                whileTap={!action.disabled ? { scale: 0.98 } : undefined}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  'w-full px-6 py-4 flex items-center justify-center gap-3',
                  'text-base font-medium transition-colors',
                  'hover:bg-neutral-100/50 dark:hover:bg-neutral-800/50',
                  'active:bg-neutral-200/50 dark:active:bg-neutral-700/50',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  action.destructive 
                    ? 'text-error-600 dark:text-error-500' 
                    : 'text-primary-600 dark:text-primary-500'
                )}
              >
                {action.icon && (
                  <span className="flex-shrink-0">
                    {action.icon}
                  </span>
                )}
                <span className="flex-1 text-center">
                  {action.label}
                </span>
                {action.destructive && (
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                )}
              </motion.button>
            ))}
          </div>
        </div>

        <motion.button
          onClick={handleClose}
          aria-label="Cancel"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: options.actions.length * 0.05 + 0.1 }}
          className={cn(
            'mt-2 w-full px-6 py-4 rounded-2xl',
            'bg-white/95 dark:bg-neutral-900/95 backdrop-blur-xl',
            'border border-white/20 dark:border-neutral-700/20',
            'shadow-xl',
            'text-base font-semibold text-primary-600 dark:text-primary-500',
            'hover:bg-neutral-100/50 dark:hover:bg-neutral-800/50',
            'active:bg-neutral-200/50 dark:active:bg-neutral-700/50',
            'transition-colors'
          )}
        >
          {options.cancelLabel || 'Cancel'}
        </motion.button>
      </motion.div>
    </motion.div>
  )
}

export const AppleActionSheetProvider = ({ children }: { children: React.ReactNode }) => {
  const [options, setOptions] = useState<ActionSheetOptions | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  const show = useCallback((newOptions: ActionSheetOptions) => {
    setOptions(newOptions)
    setIsVisible(true)
  }, [])

  const hide = useCallback(() => {
    setIsVisible(false)
    setTimeout(() => setOptions(null), 300) // Wait for exit animation
  }, [])

  const contextValue: ActionSheetContextValue = {
    show,
    hide,
    isVisible
  }

  return (
    <ActionSheetContext.Provider value={contextValue}>
      {children}
      <AnimatePresence mode="wait">
        {isVisible && options && (
          <ActionSheet options={options} onClose={hide} />
        )}
      </AnimatePresence>
    </ActionSheetContext.Provider>
  )
}

export const AppleActionSheet = {
  Provider: AppleActionSheetProvider,
  useActionSheet: useAppleActionSheet
}
