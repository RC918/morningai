import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement } from '@/hooks/use-accessibility'

const ToastContext = createContext(null)

export const useAppleToast = () => {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useAppleToast must be used within AppleToastProvider')
  }
  return context
}

const toastVariants = {
  success: {
    icon: CheckCircle2,
    bgColor: 'bg-green-500/90 dark:bg-green-600/90',
    iconColor: 'text-white',
    borderColor: 'border-green-400/20'
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-500/90 dark:bg-red-600/90',
    iconColor: 'text-white',
    borderColor: 'border-red-400/20'
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-orange-500/90 dark:bg-orange-600/90',
    iconColor: 'text-white',
    borderColor: 'border-orange-400/20'
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-500/90 dark:bg-blue-600/90',
    iconColor: 'text-white',
    borderColor: 'border-blue-400/20'
  },
  default: {
    icon: null,
    bgColor: 'bg-gray-900/90 dark:bg-gray-800/90',
    iconColor: 'text-white',
    borderColor: 'border-gray-700/20'
  }
}

const Toast = ({ id, title, description, variant = 'default', duration = 5000, onDismiss }) => {
  const { t } = useTranslation()
  const toastRef = useRef(null)
  const { announce } = useScreenReaderAnnouncement()
  const variantConfig = toastVariants[variant] || toastVariants.default
  const Icon = variantConfig.icon

  useEffect(() => {
    const message = `${title}${description ? ': ' + description : ''}`
    const priority = variant === 'error' ? 'assertive' : 'polite'
    announce(message, priority)
  }, [title, description, variant, announce])

  useEffect(() => {
    if (duration) {
      const timer = setTimeout(() => {
        onDismiss(id)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [id, duration, onDismiss])

  const handleDismiss = () => {
    if (toastRef.current) {
      triggerHaptic(toastRef.current, 'light')
    }
    onDismiss(id)
  }

  return (
    <motion.div
      ref={toastRef}
      layout
      initial={{ opacity: 0, y: -50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{
        type: 'spring',
        stiffness: 500,
        damping: 30,
        mass: 1
      }}
      drag="y"
      dragConstraints={{ top: 0, bottom: 0 }}
      dragElastic={0.2}
      onDragEnd={(e, { offset, velocity }) => {
        if (offset.y < -50 || velocity.y < -500) {
          if (toastRef.current) {
            triggerHaptic(toastRef.current, 'medium')
          }
          onDismiss(id)
        }
      }}
      className={cn(
        'relative flex items-start gap-3 rounded-2xl px-4 py-3 shadow-lg',
        'backdrop-blur-xl border',
        'min-w-[320px] max-w-[420px]',
        'cursor-grab active:cursor-grabbing',
        variantConfig.bgColor,
        variantConfig.borderColor
      )}
      style={{
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1)'
      }}
    >
      {Icon && (
        <div className={cn('flex-shrink-0 mt-0.5', variantConfig.iconColor)}>
          <Icon className="h-5 w-5" />
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        {title && (
          <div className="font-semibold text-white text-sm leading-tight mb-0.5">
            {title}
          </div>
        )}
        {description && (
          <div className="text-white/90 text-xs leading-relaxed">
            {description}
          </div>
        )}
      </div>

      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handleDismiss}
        className={cn(
          'flex-shrink-0 rounded-full p-1',
          'hover:bg-white/20 active:bg-white/30',
          'transition-colors duration-150',
          variantConfig.iconColor
        )}
        aria-label={t('toast.closeNotification', 'Close notification')}
      >
        <X className="h-4 w-4" />
      </motion.button>
    </motion.div>
  )
}

const MAX_TOASTS = 5

export const AppleToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((options) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newToast = {
      id,
      title: options.title || options,
      description: options.description,
      variant: options.variant || 'default',
      duration: options.duration !== undefined ? options.duration : 5000
    }
    
    setToasts(prev => {
      const updated = [...prev, newToast]
      return updated.slice(-MAX_TOASTS)
    })
    
    return {
      id,
      dismiss: () => setToasts(prev => prev.filter(t => t.id !== id))
    }
  }, [])

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const dismissAll = useCallback(() => {
    setToasts([])
  }, [])

  const contextValue = {
    toast,
    success: (title, description) => toast({ title, description, variant: 'success' }),
    error: (title, description) => toast({ title, description, variant: 'error' }),
    warning: (title, description) => toast({ title, description, variant: 'warning' }),
    info: (title, description) => toast({ title, description, variant: 'info' }),
    dismiss,
    dismissAll,
    toasts
  }

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div
        className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none"
        aria-live="polite"
        aria-atomic="false"
      >
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => (
            <div key={toast.id} className="pointer-events-auto">
              <Toast {...toast} onDismiss={dismiss} />
            </div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

export const AppleToast = {
  Provider: AppleToastProvider,
  useToast: useAppleToast
}
