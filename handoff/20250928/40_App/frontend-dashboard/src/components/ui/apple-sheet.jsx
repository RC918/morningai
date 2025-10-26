import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useMotionValue, useTransform } from 'framer-motion'
import { X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'

const SheetContext = createContext(null)

export const useAppleSheet = () => {
  const context = useContext(SheetContext)
  if (!context) {
    throw new Error('useAppleSheet must be used within AppleSheetProvider')
  }
  return context
}

const sheetSizes = {
  sm: 'max-h-[40vh]',
  md: 'max-h-[60vh]',
  lg: 'max-h-[80vh]',
  full: 'h-[calc(100vh-2rem)]'
}

const Sheet = ({ 
  id, 
  title, 
  description, 
  children, 
  size = 'md',
  showClose = true,
  showHandle = true,
  onClose 
}) => {
  const { t } = useTranslation()
  const sheetRef = useRef(null)
  const y = useMotionValue(0)
  const opacity = useTransform(y, [0, 300], [1, 0])

  const handleClose = () => {
    if (sheetRef.current) {
      triggerHaptic(sheetRef.current, 'light')
    }
    onClose(id)
  }

  const handleDragEnd = (event, info) => {
    const shouldClose = info.velocity.y > 500 || info.offset.y > 150
    if (shouldClose) {
      if (sheetRef.current) {
        triggerHaptic(sheetRef.current, 'medium')
      }
      onClose(id)
    }
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
      className="fixed inset-0 z-50 flex items-end justify-center"
      onClick={handleOverlayClick}
    >
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{ opacity }}
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
      />

      {/* Sheet Content */}
      <motion.div
        ref={sheetRef}
        drag="y"
        dragConstraints={{ top: 0, bottom: 0 }}
        dragElastic={0.2}
        onDragEnd={handleDragEnd}
        style={{ y }}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30,
          mass: 1
        }}
        className={cn(
          'relative z-10 w-full rounded-t-3xl bg-white dark:bg-gray-900',
          'shadow-2xl border-t border-gray-200/20 dark:border-gray-700/20',
          'flex flex-col',
          sheetSizes[size]
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag Handle */}
        {showHandle && (
          <div className="flex justify-center pt-3 pb-2">
            <div className="w-10 h-1 rounded-full bg-gray-300 dark:bg-gray-700" />
          </div>
        )}

        {/* Header */}
        {(title || showClose) && (
          <div className="flex items-start justify-between px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
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
                aria-label={t('sheet.close', 'Close sheet')}
              >
                <X className="h-5 w-5" />
              </motion.button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {children}
        </div>
      </motion.div>
    </motion.div>
  )
}

export const AppleSheetProvider = ({ children }) => {
  const [sheets, setSheets] = useState([])

  const openSheet = useCallback((options) => {
    const id = Math.random().toString(36).substr(2, 9)
    const newSheet = {
      id,
      ...options
    }
    
    setSheets(prev => [...prev, newSheet])
    
    return {
      id,
      close: () => setSheets(prev => prev.filter(s => s.id !== id))
    }
  }, [])

  const closeSheet = useCallback((id) => {
    setSheets(prev => prev.filter(s => s.id !== id))
  }, [])

  const closeAll = useCallback(() => {
    setSheets([])
  }, [])

  const contextValue = {
    openSheet,
    closeSheet,
    closeAll,
    sheets
  }

  return (
    <SheetContext.Provider value={contextValue}>
      {children}
      <AnimatePresence mode="wait">
        {sheets.map((sheet) => (
          <Sheet key={sheet.id} {...sheet} onClose={closeSheet} />
        ))}
      </AnimatePresence>
    </SheetContext.Provider>
  )
}

export const AppleSheet = {
  Provider: AppleSheetProvider,
  useSheet: useAppleSheet
}
