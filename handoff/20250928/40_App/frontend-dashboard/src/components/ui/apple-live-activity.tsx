import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronDown, ChevronUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { triggerHaptic } from '@/lib/spring-animation'
import { useScreenReaderAnnouncement } from '@/hooks/use-accessibility'

type LiveActivityVariant = 'default' | 'primary' | 'success' | 'warning' | 'error'
type ActionVariant = 'primary' | 'secondary'
type Position = 'top' | 'bottom'

interface LiveActivityAction {
  id: string
  label: string
  variant: ActionVariant
  onPress?: () => void
}

interface LiveActivityConfig {
  id?: string
  title: string
  subtitle?: string
  icon?: React.ReactNode | string
  progress?: number
  status?: string
  variant?: LiveActivityVariant
  expandable?: boolean
  metadata?: Record<string, string>
  actions?: LiveActivityAction[]
}

interface LiveActivityProps extends LiveActivityConfig {
  id: string
  onDismiss: (id: string) => void
  onAction?: (activityId: string, actionId: string) => void
}

interface LiveActivityContextValue {
  addActivity: (options: LiveActivityConfig) => {
    id: string
    update: (updates: Partial<LiveActivityConfig>) => void
    dismiss: () => void
  }
  updateActivity: (id: string, updates: Partial<LiveActivityConfig>) => void
  dismissActivity: (id: string) => void
  dismissAll: () => void
  activities: LiveActivityProps[]
}

interface LiveActivityProviderProps {
  children: React.ReactNode
  position?: Position
}

const LiveActivityContext = createContext<LiveActivityContextValue | null>(null)

export const useAppleLiveActivity = (): LiveActivityContextValue => {
  const context = useContext(LiveActivityContext)
  if (!context) {
    throw new Error('useAppleLiveActivity must be used within AppleLiveActivityProvider')
  }
  return context
}

const LiveActivity: React.FC<LiveActivityProps> = ({
  id,
  title,
  subtitle,
  icon,
  progress,
  status,
  actions = [],
  metadata,
  variant = 'default',
  expandable = true,
  onDismiss,
  onAction
}) => {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)
  const activityRef = useRef<HTMLDivElement>(null)
  const announce = useScreenReaderAnnouncement()
  const previousProgressRef = useRef<number | undefined>(progress)

  useEffect(() => {
    if (progress !== undefined && previousProgressRef.current !== undefined) {
      const diff = Math.abs(progress - previousProgressRef.current)
      if (diff >= 10) {
        announce(
          t('liveActivity.progressUpdate', `Progress: ${Math.round(progress)}%`, { progress: Math.round(progress) }),
          'polite'
        )
      }
    }
    previousProgressRef.current = progress
  }, [progress, announce, t])

  const handleToggleExpand = () => {
    if (!expandable) return
    
    if (activityRef.current) {
      triggerHaptic(activityRef.current, 'light')
    }
    const newState = !isExpanded
    setIsExpanded(newState)
    announce(
      newState 
        ? t('liveActivity.expanded', 'Activity expanded') 
        : t('liveActivity.collapsed', 'Activity collapsed'),
      'polite'
    )
  }

  const handleDismiss = () => {
    if (activityRef.current) {
      triggerHaptic(activityRef.current, 'medium')
    }
    announce(t('liveActivity.dismissed', 'Activity dismissed'), 'polite')
    onDismiss(id)
  }

  const handleAction = (actionId: string) => {
    if (activityRef.current) {
      triggerHaptic(activityRef.current, 'light')
    }
    onAction?.(id, actionId)
  }

  const variantStyles: Record<LiveActivityVariant, string> = {
    default: 'bg-gray-900/90 dark:bg-gray-800/90 border-gray-700/20',
    primary: 'bg-blue-500/90 dark:bg-blue-600/90 border-blue-400/20',
    success: 'bg-green-500/90 dark:bg-green-600/90 border-green-400/20',
    warning: 'bg-orange-500/90 dark:bg-orange-600/90 border-orange-400/20',
    error: 'bg-red-500/90 dark:bg-red-600/90 border-red-400/20'
  }

  return (
    <motion.div
      ref={activityRef}
      layout
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -20 }}
      transition={{
        type: 'spring',
        stiffness: 500,
        damping: 30,
        mass: 1
      }}
      className={cn(
        'relative rounded-3xl backdrop-blur-xl border overflow-hidden',
        'shadow-lg',
        variantStyles[variant] || variantStyles.default
      )}
      style={{
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0, 0, 0, 0.1)'
      }}
    >
      {/* Compact View */}
      <motion.div
        layout
        onClick={handleToggleExpand}
        onKeyDown={(e) => {
          if (expandable && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            handleToggleExpand()
          }
        }}
        role="button"
        tabIndex={0}
        {...(expandable && { 'aria-expanded': isExpanded })}
        aria-label={`${title}${subtitle ? `, ${subtitle}` : ''}`}
        className={cn(
          'px-4 py-3 cursor-pointer',
          expandable && 'hover:bg-white/5 active:bg-white/10 transition-colors'
        )}
      >
        <div className="flex items-center gap-3">
          {/* Icon */}
          {icon && (
            <motion.div
              layout
              className="flex-shrink-0 w-10 h-10 rounded-full bg-white/10 flex items-center justify-center"
            >
              {typeof icon === 'string' ? (
                <span className="text-xl">{icon}</span>
              ) : (
                React.cloneElement(icon as React.ReactElement, { className: 'w-5 h-5 text-white' })
              )}
            </motion.div>
          )}

          {/* Content */}
          <motion.div layout className="flex-1 min-w-0">
            <motion.div layout className="font-semibold text-white text-sm leading-tight">
              {title}
            </motion.div>
            {subtitle && (
              <motion.div layout className="text-white/70 text-xs mt-0.5">
                {subtitle}
              </motion.div>
            )}
            
            {/* Progress Bar */}
            {progress !== undefined && (
              <motion.div layout className="mt-2">
                <div className="h-1.5 bg-white/20 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                    transition={{
                      type: 'spring',
                      stiffness: 300,
                      damping: 30
                    }}
                    className="h-full bg-white rounded-full"
                  />
                </div>
                <motion.div layout className="text-white/60 text-xs mt-1">
                  {Math.round(progress)}%
                </motion.div>
              </motion.div>
            )}

            {/* Status */}
            {status && (
              <motion.div layout className="text-white/60 text-xs mt-1">
                {status}
              </motion.div>
            )}
          </motion.div>

          {/* Controls */}
          <motion.div layout className="flex items-center gap-2">
            {expandable && (
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    e.stopPropagation()
                    handleToggleExpand()
                  }
                }}
                className="p-1.5 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
                aria-label={isExpanded ? t('liveActivity.collapse', 'Collapse') : t('liveActivity.expand', 'Expand')}
              >
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-white" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white" />
                )}
              </motion.button>
            )}
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={(e) => {
                e.stopPropagation()
                handleDismiss()
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  e.stopPropagation()
                  handleDismiss()
                }
              }}
              className="p-1.5 rounded-full hover:bg-white/10 active:bg-white/20 transition-colors"
              aria-label={t('liveActivity.dismiss', 'Dismiss')}
            >
              <X className="w-4 h-4 text-white" />
            </motion.button>
          </motion.div>
        </div>
      </motion.div>

      {/* Expanded View */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{
              type: 'spring',
              stiffness: 500,
              damping: 30
            }}
            className="border-t border-white/10"
          >
            <div className="px-4 py-3 space-y-3">
              {/* Metadata */}
              {metadata && (
                <div className="space-y-2">
                  {Object.entries(metadata).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="text-white/60 text-xs">{key}</span>
                      <span className="text-white text-xs font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              {actions.length > 0 && (
                <div className="flex gap-2">
                  {actions.map((action) => (
                    <motion.button
                      key={action.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleAction(action.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleAction(action.id)
                        }
                      }}
                      className={cn(
                        'flex-1 px-4 py-2 rounded-xl font-medium text-sm',
                        'transition-colors duration-150',
                        action.variant === 'primary'
                          ? 'bg-white text-gray-900 hover:bg-white/90 active:bg-white/80'
                          : 'bg-white/10 text-white hover:bg-white/20 active:bg-white/30'
                      )}
                      aria-label={action.label}
                    >
                      {action.label}
                    </motion.button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

const MAX_ACTIVITIES = 3

export const AppleLiveActivityProvider: React.FC<LiveActivityProviderProps> = ({ 
  children, 
  position = 'top' 
}) => {
  const [activities, setActivities] = useState<LiveActivityProps[]>([])
  const announce = useScreenReaderAnnouncement()

  const dismissActivity = useCallback((id: string) => {
    setActivities(prev => prev.filter(a => a.id !== id))
  }, [])

  const addActivity = useCallback((options: LiveActivityConfig) => {
    const id = options.id || Math.random().toString(36).substr(2, 9)
    const newActivity: LiveActivityProps = {
      id,
      title: options.title,
      subtitle: options.subtitle,
      icon: options.icon,
      progress: options.progress,
      status: options.status,
      actions: options.actions || [],
      metadata: options.metadata,
      variant: options.variant || 'default',
      expandable: options.expandable !== false,
      onDismiss: dismissActivity
    }
    
    setActivities(prev => {
      const filtered = prev.filter(a => a.id !== id)
      const updated = [...filtered, newActivity]
      return updated.slice(-MAX_ACTIVITIES)
    })
    
    announce(
      `${options.title}${options.subtitle ? `, ${options.subtitle}` : ''}`,
      'polite'
    )
    
    return {
      id,
      update: (updates: Partial<LiveActivityConfig>) => updateActivity(id, updates),
      dismiss: () => dismissActivity(id)
    }
  }, [announce, dismissActivity])

  const updateActivity = useCallback((id: string, updates: Partial<LiveActivityConfig>) => {
    setActivities(prev =>
      prev.map(activity =>
        activity.id === id ? { ...activity, ...updates } : activity
      )
    )
  }, [])

  const dismissAll = useCallback(() => {
    setActivities([])
  }, [])

  const handleAction = useCallback((activityId: string, actionId: string) => {
    const activity = activities.find(a => a.id === activityId)
    const action = activity?.actions?.find(a => a.id === actionId)
    action?.onPress?.()
  }, [activities])

  const contextValue: LiveActivityContextValue = {
    addActivity,
    updateActivity,
    dismissActivity,
    dismissAll,
    activities
  }

  const positionStyles: Record<Position, string> = {
    top: 'top-4',
    bottom: 'bottom-4'
  }

  return (
    <LiveActivityContext.Provider value={contextValue}>
      {children}
      <div
        className={cn(
          'fixed left-1/2 -translate-x-1/2 z-50 w-full max-w-md px-4',
          'flex flex-col gap-2 pointer-events-none',
          positionStyles[position] || positionStyles.top
        )}
        aria-live="polite"
        aria-atomic="false"
      >
        <AnimatePresence mode="popLayout">
          {activities.map((activity) => (
            <div key={activity.id} className="pointer-events-auto">
              <LiveActivity
                {...activity}
                onDismiss={dismissActivity}
                onAction={handleAction}
              />
            </div>
          ))}
        </AnimatePresence>
      </div>
    </LiveActivityContext.Provider>
  )
}

export const AppleLiveActivity = {
  Provider: AppleLiveActivityProvider,
  useLiveActivity: useAppleLiveActivity
}

export type {
  LiveActivityVariant,
  ActionVariant,
  Position,
  LiveActivityAction,
  LiveActivityConfig,
  LiveActivityProps,
  LiveActivityContextValue,
  LiveActivityProviderProps
}
