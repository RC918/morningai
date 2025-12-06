import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  FileCode,
  FileText,
  TestTube,
  Settings,
  Rocket,
  BadgeCheck,
  Trash2,
  ListTodo,
  Activity,
  X,
  Save
} from 'lucide-react'

/**
 * TaskEditor - Modal dialog for editing task details
 * 
 * Features:
 * - Edit task name and description
 * - Change task type
 * - Add/remove tasks from plan
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const TASK_TYPES = [
  { value: 'ANALYZE_CODE', icon: FileCode, label: 'Analyze Code' },
  { value: 'WRITE_CODE', icon: FileCode, label: 'Write Code' },
  { value: 'WRITE_TEST', icon: TestTube, label: 'Write Test' },
  { value: 'RUN_TEST', icon: TestTube, label: 'Run Test' },
  { value: 'CODE_REVIEW', icon: ListTodo, label: 'Code Review' },
  { value: 'SETUP_ENVIRONMENT', icon: Settings, label: 'Setup Environment' },
  { value: 'DEPLOYMENT', icon: Rocket, label: 'Deployment' },
  { value: 'VERIFICATION', icon: BadgeCheck, label: 'Verification' },
  { value: 'DOCUMENTATION', icon: FileText, label: 'Documentation' },
  { value: 'CLEANUP', icon: Trash2, label: 'Cleanup' }
]

const TaskEditor = ({ 
  task = null,
  isOpen = false,
  onClose,
  onSave,
  onDelete,
  isNewTask = false
}) => {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    name: task?.name || '',
    description: task?.description || '',
    type: task?.type || 'WRITE_CODE'
  })
  const [errors, setErrors] = useState({})

  const handleInputChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
  }, [errors])

  const validateForm = useCallback(() => {
    const newErrors = {}
    if (!formData.name.trim()) {
      newErrors.name = t('sessions.taskEditor.errors.nameRequired', 'Task name is required')
    }
    if (formData.name.length > 200) {
      newErrors.name = t('sessions.taskEditor.errors.nameTooLong', 'Task name must be less than 200 characters')
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [formData, t])

  const handleSave = useCallback(() => {
    if (!validateForm()) return
    
    onSave({
      ...task,
      name: formData.name.trim(),
      description: formData.description.trim(),
      type: formData.type
    })
    onClose()
  }, [formData, task, onSave, onClose, validateForm])

  const handleDelete = useCallback(() => {
    if (onDelete && task) {
      onDelete(task.id)
      onClose()
    }
  }, [task, onDelete, onClose])

  const getTypeIcon = useCallback((type) => {
    const taskType = TASK_TYPES.find(t => t.value === type)
    if (taskType) {
      const Icon = taskType.icon
      return <Icon className="w-4 h-4" />
    }
    return <Activity className="w-4 h-4" />
  }, [])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isNewTask 
              ? t('sessions.taskEditor.titleNew', 'Add New Task')
              : t('sessions.taskEditor.titleEdit', 'Edit Task')
            }
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Task Name */}
          <div className="space-y-2">
            <label 
              htmlFor="task-name"
              className="text-sm font-medium text-[var(--text-primary)]"
            >
              {t('sessions.taskEditor.name', 'Task Name')}
              <span className="text-energy ml-1">*</span>
            </label>
            <input
              id="task-name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder={t('sessions.taskEditor.namePlaceholder', 'Enter task name...')}
              className={`w-full px-3 py-2 rounded-lg border bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                errors.name ? 'border-energy' : 'border-[var(--border)]'
              }`}
            />
            {errors.name && (
              <p className="text-xs text-energy">{errors.name}</p>
            )}
          </div>

          {/* Task Description */}
          <div className="space-y-2">
            <label 
              htmlFor="task-description"
              className="text-sm font-medium text-[var(--text-primary)]"
            >
              {t('sessions.taskEditor.description', 'Description')}
              <span className="text-neutral-400 ml-1 text-xs">
                ({t('common.optional', 'optional')})
              </span>
            </label>
            <textarea
              id="task-description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder={t('sessions.taskEditor.descriptionPlaceholder', 'Add details about this task...')}
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          {/* Task Type */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--text-primary)]">
              {t('sessions.taskEditor.type', 'Task Type')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {TASK_TYPES.map(({ value, icon: Icon, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => handleInputChange('type', value)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-all ${
                    formData.type === value
                      ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                      : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:border-primary-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{t(`sessions.taskType.${value}`, label)}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div>
            {!isNewTask && onDelete && (
              <AppleButton
                variant="outline"
                size="sm"
                haptic="light"
                onClick={handleDelete}
                className="text-energy hover:bg-energy-10"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                {t('common.delete', 'Delete')}
              </AppleButton>
            )}
          </div>
          <div className="flex items-center gap-2">
            <AppleButton
              variant="outline"
              size="sm"
              haptic="light"
              onClick={onClose}
            >
              <X className="w-4 h-4 mr-1" />
              {t('common.cancel', 'Cancel')}
            </AppleButton>
            <AppleButton
              variant="default"
              size="sm"
              haptic="medium"
              onClick={handleSave}
            >
              <Save className="w-4 h-4 mr-1" />
              {t('common.save', 'Save')}
            </AppleButton>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default TaskEditor
