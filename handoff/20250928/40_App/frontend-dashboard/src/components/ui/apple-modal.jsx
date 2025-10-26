import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'

const ModalContext = createContext(null)

export const useAppleModal = () => {
  const context = useContext(ModalContext)
  if (!context) {
    throw new Error('useAppleModal must be used within AppleModalProvider')
  }
  return context
}

const modalSizes = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl',
  full: 'max-w-full mx-4'
}

const Modal = ({ 
  id, 
  title, 
  description, 
  children, 
  size = 'md',
  showClose = true,
  onClose 
}) => {
  const { t } = useTranslation()
  const modalRef = useRef(null)

  const handleClose = () => {
    if (modalRef.current) {
      triggerHaptic(modalRef.current, 'light')
    }
    onClose(id)
  }

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        handleClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [id])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
    >
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
      />

      {/* Modal Content */}
      <motion.div
        ref={modalRef}
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
          mass: 1
        }}
        className={cn(
          'relative z-10 w-full rounded-2xl bg-white dark:bg-gray-900',
          'shadow-2xl border border-gray-200/20 dark:border-gray-700/20',
          'flex flex-col max-h-[90vh]',
          modalSizes[size]
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {(title || showClose) && (
          <div className="flex items-start justify-between p-6 border-b border-gray-200/50 dark:border-gray-700/50">
            <div className="flex-1 min-w-0">
              {title && (
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white leading-tight">
                  {title}
                </h2>
              )}
              {description && (
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {description}
                </p>
              )}
            </div>
            {showClose && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={handleClose}
                className={cn(
                  'ml-4 flex-shrink-0 rounded-full p-2',
                  'hover:bg-gray-100 dark:hover:bg-gray-800',
                  'active:bg-gray-200 dark:active:bg-gray-700',
                  'transition-colors duration-150',
                  'text-gray-500 dark:text-gray-400'
                )}
                aria-label={t('modal.close', 'Close modal')}
              >
                <X className="h-5 w-5" />
              </motion.button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </motion.div>
    </motion.div>
  )
}

export const AppleModalProvider = ({ children }) => {
  const [modals, setModals] = useState([])

  const openModal = useCallback((options) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newModal = {
      id,
      ...options
    }
    
    setModals(prev => [...prev, newModal])
    
    return {
      id,
      close: () => setModals(prev => prev.filter(m => m.id !== id))
    }
  }, [])

  const closeModal = useCallback((id) => {
    setModals(prev => prev.filter(m => m.id !== id))
  }, [])

  const closeAll = useCallback(() => {
    setModals([])
  }, [])

  const contextValue = {
    openModal,
    closeModal,
    closeAll,
    modals
  }

  return (
    <ModalContext.Provider value={contextValue}>
      {children}
      <AnimatePresence mode="wait">
        {modals.map((modal) => (
          <Modal key={modal.id} {...modal} onClose={closeModal} />
        ))}
      </AnimatePresence>
    </ModalContext.Provider>
  )
}

export const AppleModal = {
  Provider: AppleModalProvider,
  useModal: useAppleModal
}
