import { useState, useCallback, useMemo, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Badge,
  Progress
} from '@morningai/shared-ui'
import { 
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  FileCode,
  FileText,
  TestTube,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Settings,
  Rocket,
  BadgeCheck,
  Trash2,
  ListTodo,
  Edit3,
  GripVertical
} from 'lucide-react'

/**
 * TaskPlanTimeline - Visual timeline representation of task execution plan
 * 
 * Features:
 * - Vertical timeline with connecting lines
 * - Task status indicators with animations
 * - Expandable task details
 * - Drag-and-drop reordering (when editable)
 * - Progress visualization
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const TaskPlanTimeline = ({ 
  tasks = [], 
  completedTasks = 0,
  totalTasks = 0,
  confidence = 0,
  editable = false,
  onTaskReorder,
  onTaskEdit,
  onTaskApprove
}) => {
  const { t } = useTranslation()
  const [expandedTasks, setExpandedTasks] = useState(new Set())
  const [draggedTask, setDraggedTask] = useState(null)
  // Keyboard accessibility state for drag-and-drop
  const [keyboardGrabbedIndex, setKeyboardGrabbedIndex] = useState(null)
  const [announcement, setAnnouncement] = useState('')

  const toggleTaskExpanded = useCallback((taskId) => {
    setExpandedTasks(prev => {
      const newSet = new Set(prev)
      if (newSet.has(taskId)) {
        newSet.delete(taskId)
      } else {
        newSet.add(taskId)
      }
      return newSet
    })
  }, [])

  const getTaskStatusIcon = useCallback((status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-growth" />
      case 'running':
        return <Activity className="w-5 h-5 text-calm animate-pulse" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-energy" />
      case 'waiting_approval':
        return <AlertTriangle className="w-5 h-5 text-wisdom" />
      case 'paused':
        return <Pause className="w-5 h-5 text-wisdom" />
      default:
        return <Clock className="w-5 h-5 text-neutral-400" />
    }
  }, [])

  const getTaskTypeIcon = useCallback((type) => {
    switch (type) {
      case 'ANALYZE_CODE':
        return <FileCode className="w-4 h-4" />
      case 'WRITE_CODE':
        return <FileCode className="w-4 h-4" />
      case 'WRITE_TEST':
      case 'RUN_TEST':
        return <TestTube className="w-4 h-4" />
      case 'CODE_REVIEW':
        return <ListTodo className="w-4 h-4" />
      case 'SETUP_ENVIRONMENT':
        return <Settings className="w-4 h-4" />
      case 'DEPLOYMENT':
        return <Rocket className="w-4 h-4" />
      case 'VERIFICATION':
        return <BadgeCheck className="w-4 h-4" />
      case 'DOCUMENTATION':
        return <FileText className="w-4 h-4" />
      case 'CLEANUP':
        return <Trash2 className="w-4 h-4" />
      default:
        return <Activity className="w-4 h-4" />
    }
  }, [])

  const getStatusColor = useCallback((status) => {
    switch (status) {
      case 'completed':
        return 'border-growth bg-growth'
      case 'running':
        return 'border-calm bg-calm'
      case 'failed':
        return 'border-energy bg-energy'
      case 'waiting_approval':
        return 'border-wisdom bg-wisdom'
      case 'paused':
        return 'border-wisdom bg-wisdom'
      default:
        return 'border-neutral-300 bg-neutral-300'
    }
  }, [])

  const getLineColor = useCallback((status) => {
    switch (status) {
      case 'completed':
        return 'bg-growth'
      case 'running':
        return 'bg-calm'
      case 'failed':
        return 'bg-energy'
      default:
        return 'bg-neutral-200 dark:bg-neutral-700'
    }
  }, [])

  const getTaskBgColor = useCallback((status) => {
    switch (status) {
      case 'completed':
        return 'bg-growth-10 border-growth-20'
      case 'running':
        return 'bg-calm-10 border-calm'
      case 'failed':
        return 'bg-energy-10 border-energy'
      case 'waiting_approval':
        return 'bg-wisdom-10 border-wisdom'
      case 'paused':
        return 'bg-wisdom-10 border-wisdom'
      default:
        return 'bg-[var(--surface)] border-[var(--border)]'
    }
  }, [])

  const handleDragStart = useCallback((e, task, index) => {
    if (!editable) return
    setDraggedTask({ task, index })
    e.dataTransfer.effectAllowed = 'move'
  }, [editable])

  const handleDragOver = useCallback((e) => {
    if (!editable) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [editable])

  const handleDrop = useCallback((e, targetIndex) => {
    if (!editable || !draggedTask) return
    e.preventDefault()
    
    if (draggedTask.index !== targetIndex && onTaskReorder) {
      onTaskReorder(draggedTask.index, targetIndex)
    }
    setDraggedTask(null)
  }, [editable, draggedTask, onTaskReorder])

    const handleDragEnd = useCallback(() => {
      setDraggedTask(null)
    }, [])

    // Announce changes to screen readers
    const announce = useCallback((message) => {
      setAnnouncement(message)
    }, [])

    // Clear announcement after a short delay to allow re-announcement of same message
    // Using useEffect with cleanup to prevent memory leaks on unmount
    useEffect(() => {
      if (!announcement) return
      const timer = setTimeout(() => setAnnouncement(''), 1000)
      return () => clearTimeout(timer)
    }, [announcement])

    // Handle keyboard-based task reordering (Alt+Up/Down)
    const handleKeyboardReorder = useCallback((e, task, index) => {
      if (!editable) return

      // Alt+Space to grab/release task for reordering (must be checked before generic Space/Enter)
      if (e.altKey && e.key === ' ') {
        e.preventDefault()
        if (keyboardGrabbedIndex === index) {
          // Release the task
          announce(t('sessions.a11y.taskDropped', 'Task {{name}} dropped at position {{position}}', { name: task.name, position: index + 1 }))
          setKeyboardGrabbedIndex(null)
        } else {
          // Grab the task
          announce(t('sessions.a11y.taskGrabbed', 'Task {{name}} grabbed. Use Alt+Up or Alt+Down to move, Alt+Space to drop.', { name: task.name }))
          setKeyboardGrabbedIndex(index)
        }
        return
      }

      // Space or Enter (without Alt): if a task is already grabbed, release it; otherwise let the expand/collapse handler run
      if (!e.altKey && (e.key === ' ' || e.key === 'Enter')) {
        if (keyboardGrabbedIndex === null) {
          // Not currently grabbing - let the expand/collapse handler run
          return
        } else {
          // Release the grabbed task
          e.preventDefault()
          announce(t('sessions.a11y.taskDropped', 'Task {{name}} dropped at position {{position}}', { name: task.name, position: index + 1 }))
          setKeyboardGrabbedIndex(null)
          return
        }
      }

      // Alt+Up to move task up
      if (e.altKey && e.key === 'ArrowUp') {
        e.preventDefault()
        if (index > 0 && onTaskReorder) {
          onTaskReorder(index, index - 1)
          announce(t('sessions.a11y.taskMovedUp', 'Task {{name}} moved up to position {{position}}', { name: task.name, position: index }))
          // Update grabbed index if we're in grab mode
          if (keyboardGrabbedIndex === index) {
            setKeyboardGrabbedIndex(index - 1)
          }
        }
        return
      }

      // Alt+Down to move task down
      if (e.altKey && e.key === 'ArrowDown') {
        e.preventDefault()
        if (index < tasks.length - 1 && onTaskReorder) {
          onTaskReorder(index, index + 1)
          announce(t('sessions.a11y.taskMovedDown', 'Task {{name}} moved down to position {{position}}', { name: task.name, position: index + 2 }))
          // Update grabbed index if we're in grab mode
          if (keyboardGrabbedIndex === index) {
            setKeyboardGrabbedIndex(index + 1)
          }
        }
        return
      }

      // Escape to cancel grab
      if (e.key === 'Escape' && keyboardGrabbedIndex !== null) {
        e.preventDefault()
        announce(t('sessions.a11y.reorderCancelled', 'Reorder cancelled'))
        setKeyboardGrabbedIndex(null)
        return
      }
    }, [editable, keyboardGrabbedIndex, onTaskReorder, tasks.length, announce, t])

  const progressPercentage = useMemo(() => {
    if (totalTasks === 0) return 0
    return Math.round((completedTasks / totalTasks) * 100)
  }, [completedTasks, totalTasks])

  const getConfidenceColor = useCallback((conf) => {
    if (conf >= 0.8) return 'text-growth'
    if (conf >= 0.6) return 'text-wisdom'
    return 'text-energy'
  }, [])

  return (
    <div className="space-y-4">
      {/* Progress Header */}
      <div className="flex items-center justify-between p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                className="text-neutral-200 dark:text-neutral-700"
              />
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                strokeDasharray={`${progressPercentage * 1.76} 176`}
                strokeLinecap="round"
                className="text-growth transition-all duration-500"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-semibold text-[var(--text-primary)]">
                {progressPercentage}%
              </span>
            </div>
          </div>
          <div>
            <p className="text-sm text-[var(--text-secondary)]">
              {t('sessions.plan.progress', 'Progress')}
            </p>
            <p className="text-lg font-semibold text-[var(--text-primary)]">
              {completedTasks} / {totalTasks} {t('sessions.plan.tasks', 'tasks')}
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-[var(--text-secondary)]">
            {t('sessions.confidence', 'Confidence')}
          </p>
          <p className={`text-lg font-semibold ${getConfidenceColor(confidence)}`}>
            {Math.round(confidence * 100)}%
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative pl-8">
        {/* Vertical line */}
        <div className="absolute left-[15px] top-0 bottom-0 w-0.5 bg-neutral-200 dark:bg-neutral-700" />

        {/* Tasks */}
        <div className="space-y-3" role={editable ? 'list' : undefined}>
          {tasks.map((task, index) => {
            const isExpanded = expandedTasks.has(task.id)
            const isLast = index === tasks.length - 1
            const isDragging = draggedTask?.task.id === task.id

            const isKeyboardGrabbed = keyboardGrabbedIndex === index

            return (
              <div
                key={task.id}
                role={editable ? 'listitem' : undefined}
                tabIndex={editable ? 0 : undefined}
                aria-grabbed={editable ? (isKeyboardGrabbed || isDragging) : undefined}
                aria-dropeffect={editable && keyboardGrabbedIndex !== null && keyboardGrabbedIndex !== index ? 'move' : undefined}
                aria-label={editable ? t('sessions.a11y.taskItem', 'Task {{position}}: {{name}}. Press Alt+Space to grab for reordering, Alt+Up/Down to move.', { position: index + 1, name: task.name }) : undefined}
                className={`relative ${isDragging ? 'opacity-50' : ''} ${isKeyboardGrabbed ? 'ring-2 ring-calm ring-offset-2' : ''}`}
                draggable={editable}
                {...(editable ? {
                  onDragStart: (e) => handleDragStart(e, task, index),
                  onDragOver: handleDragOver,
                  onDrop: (e) => handleDrop(e, index),
                  onDragEnd: handleDragEnd,
                  onKeyDown: (e) => {
                    // Handle keyboard reordering first
                    handleKeyboardReorder(e, task, index)
                    // If not handled by reorder, handle expand/collapse
                    if (!e.defaultPrevented && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault()
                      toggleTaskExpanded(task.id)
                    }
                  }
                } : {})}
              >
                {/* Timeline node */}
                <div className={`absolute -left-8 top-4 w-4 h-4 rounded-full border-2 ${getStatusColor(task.status)} z-10`} />
                
                {/* Connecting line segment (colored based on status) */}
                {!isLast && (
                  <div 
                    className={`absolute -left-[25px] top-8 w-0.5 h-[calc(100%+12px)] ${getLineColor(task.status)}`}
                  />
                )}

                {/* Task card */}
                <div 
                  className={`rounded-xl border p-4 transition-all ${getTaskBgColor(task.status)} ${
                    editable ? 'cursor-grab active:cursor-grabbing' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Drag handle */}
                    {editable && (
                      <div className="flex-shrink-0 mt-1 text-neutral-400 hover:text-neutral-600">
                        <GripVertical className="w-4 h-4" />
                      </div>
                    )}

                    {/* Task number */}
                    <div className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-neutral-100 dark:bg-neutral-700 text-xs font-medium">
                      {index + 1}
                    </div>

                    {/* Status icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getTaskStatusIcon(task.status)}
                    </div>

                    {/* Task content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium ${
                            task.status === 'pending' ? 'text-neutral-500' : 'text-[var(--text-primary)]'
                          }`}>
                            {task.name}
                          </p>
                          {task.description && isExpanded && (
                            <p className="text-xs text-[var(--text-secondary)] mt-1">
                              {task.description}
                            </p>
                          )}
                        </div>

                        {/* Task type badge */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Badge variant="secondary" className="text-xs">
                            {getTaskTypeIcon(task.type)}
                            <span className="ml-1">{t(`sessions.taskType.${task.type}`, task.type)}</span>
                          </Badge>
                        </div>
                      </div>

                      {/* Expanded content */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-[var(--border)]">
                          {/* Task metadata */}
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {task.startedAt && (
                              <div>
                                <span className="text-[var(--text-secondary)]">{t('sessions.task.started', 'Started')}:</span>
                                <span className="ml-1 text-[var(--text-primary)]">
                                  {new Date(task.startedAt).toLocaleString()}
                                </span>
                              </div>
                            )}
                            {task.completedAt && (
                              <div>
                                <span className="text-[var(--text-secondary)]">{t('sessions.task.completed', 'Completed')}:</span>
                                <span className="ml-1 text-[var(--text-primary)]">
                                  {new Date(task.completedAt).toLocaleString()}
                                </span>
                              </div>
                            )}
                            {task.duration && (
                              <div>
                                <span className="text-[var(--text-secondary)]">{t('sessions.task.duration', 'Duration')}:</span>
                                <span className="ml-1 text-[var(--text-primary)]">{task.duration}</span>
                              </div>
                            )}
                          </div>

                          {/* Error message */}
                          {task.status === 'failed' && task.errorMessage && (
                            <div className="mt-2 p-2 rounded-lg bg-energy-10 text-energy-dark text-xs">
                              {task.errorMessage}
                            </div>
                          )}

                          {/* Approval action */}
                          {task.status === 'waiting_approval' && onTaskApprove && (
                            <div className="mt-2 flex items-center gap-2">
                              <button
                                onClick={() => onTaskApprove(task.id)}
                                className="px-3 py-2 rounded-lg bg-growth text-white text-xs font-medium hover:bg-growth-dark transition-colors"
                              >
                                <CheckCircle className="w-3 h-3 inline mr-1" />
                                {t('sessions.task.approve', 'Approve')}
                              </button>
                              {task.approvalReason && (
                                <span className="text-xs text-wisdom-dark">{task.approvalReason}</span>
                              )}
                            </div>
                          )}

                          {/* Edit action */}
                          {editable && task.status === 'pending' && onTaskEdit && (
                            <button
                              onClick={() => onTaskEdit(task)}
                              className="mt-2 flex items-center gap-1 text-xs text-primary-500 hover:text-primary-600"
                            >
                              <Edit3 className="w-3 h-3" />
                              {t('sessions.task.edit', 'Edit Task')}
                            </button>
                          )}
                        </div>
                      )}

                      {/* Expand/collapse button */}
                      <button
                        onClick={() => toggleTaskExpanded(task.id)}
                        className="mt-2 flex items-center gap-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-3 h-3" />
                            {t('common.collapse', 'Collapse')}
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-3 h-3" />
                            {t('common.expand', 'Expand')}
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Screen reader live region for announcements */}
      {editable && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {announcement}
        </div>
      )}
    </div>
  )
}

export default TaskPlanTimeline
