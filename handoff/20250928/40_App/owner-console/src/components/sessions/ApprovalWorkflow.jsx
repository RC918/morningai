import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Badge
} from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  FileCode,
  Database,
  Server,
  Key,
  Info
} from 'lucide-react'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'

/**
 * ApprovalWorkflow - Component for handling task approval requests
 * 
 * Features:
 * - Display approval reason and risk level
 * - Show affected resources
 * - Approve or reject with optional comment
 * - Integration with backend API
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const RISK_LEVELS = {
  low: { color: 'bg-growth-10 text-growth border-growth', icon: Info },
  medium: { color: 'bg-wisdom-10 text-wisdom border-wisdom', icon: AlertTriangle },
  high: { color: 'bg-energy-10 text-energy border-energy', icon: Shield },
  critical: { color: 'bg-energy-10 text-energy border-energy', icon: Shield }
}

const RESOURCE_ICONS = {
  database: Database,
  server: Server,
  code: FileCode,
  credentials: Key,
  default: FileCode
}

const ApprovalWorkflow = ({ 
  sessionId,
  taskId,
  isOpen = false,
  onClose,
  onApproved,
  onRejected,
  approvalData = {}
}) => {
  const { t } = useTranslation()
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const {
    reason = '',
    riskLevel = 'medium',
    affectedResources = [],
    taskName = '',
    description = ''
  } = approvalData

  const riskConfig = RISK_LEVELS[riskLevel] || RISK_LEVELS.medium
  const RiskIcon = riskConfig.icon

  const handleApprove = useCallback(async () => {
    try {
      setIsSubmitting(true)
      setError(null)

      await apiClientWithMeta(`/api/sessions/${sessionId}/tasks/${taskId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ comment: comment.trim() || undefined })
      })

      if (onApproved) {
        onApproved(taskId, comment.trim())
      }
      onClose()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.approval.errors.approveFailed', 'Failed to approve task'),
        logContext: 'ApprovalWorkflow.handleApprove'
      })
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }, [sessionId, taskId, comment, onApproved, onClose, t])

  const handleReject = useCallback(async () => {
    try {
      setIsSubmitting(true)
      setError(null)

      await apiClientWithMeta(`/api/sessions/${sessionId}/tasks/${taskId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ comment: comment.trim() || undefined })
      })

      if (onRejected) {
        onRejected(taskId, comment.trim())
      }
      onClose()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.approval.errors.rejectFailed', 'Failed to reject task'),
        logContext: 'ApprovalWorkflow.handleReject'
      })
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }, [sessionId, taskId, comment, onRejected, onClose, t])

  const getResourceIcon = useCallback((resourceType) => {
    const Icon = RESOURCE_ICONS[resourceType] || RESOURCE_ICONS.default
    return <Icon className="w-4 h-4" />
  }, [])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-wisdom" />
            {t('sessions.approval.title', 'Approval Required')}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Task Info */}
          <div className="p-4 rounded-xl bg-neutral-50 dark:bg-neutral-800/50">
            <p className="text-sm font-medium text-[var(--text-primary)]">
              {taskName}
            </p>
            {description && (
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                {description}
              </p>
            )}
          </div>

          {/* Risk Level */}
          <div className={`p-4 rounded-xl border ${riskConfig.color}`}>
            <div className="flex items-start gap-3">
              <RiskIcon className="w-5 h-5 flex-shrink-0 mt-1" />
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">
                    {t('sessions.approval.riskLevel', 'Risk Level')}:
                  </p>
                  <Badge variant={riskLevel === 'high' || riskLevel === 'critical' ? 'destructive' : 'warning'}>
                    {t(`sessions.approval.risk.${riskLevel}`, riskLevel.toUpperCase())}
                  </Badge>
                </div>
                <p className="text-sm mt-1">
                  {reason}
                </p>
              </div>
            </div>
          </div>

          {/* Affected Resources */}
          {affectedResources.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {t('sessions.approval.affectedResources', 'Affected Resources')}
              </p>
              <div className="space-y-2">
                {affectedResources.map((resource, index) => (
                  <div 
                    key={index}
                    className="flex items-center gap-2 p-2 rounded-lg bg-neutral-50 dark:bg-neutral-800"
                  >
                    {getResourceIcon(resource.type)}
                    <span className="text-sm text-[var(--text-primary)]">
                      {resource.name}
                    </span>
                    {resource.action && (
                      <Badge variant="secondary" className="text-xs ml-auto">
                        {resource.action}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Comment */}
          <div className="space-y-2">
            <label 
              htmlFor="approval-comment"
              className="text-sm font-medium text-[var(--text-primary)]"
            >
              {t('sessions.approval.comment', 'Comment')}
              <span className="text-neutral-400 ml-1 text-xs">
                ({t('common.optional', 'optional')})
              </span>
            </label>
            <textarea
              id="approval-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t('sessions.approval.commentPlaceholder', 'Add a comment for the audit log...')}
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 rounded-lg bg-energy-10 border border-energy text-energy-dark text-sm">
              {error}
            </div>
          )}
        </div>

        <DialogFooter className="flex items-center justify-end gap-2">
          <AppleButton
            variant="outline"
            size="sm"
            haptic="light"
            onClick={handleReject}
            disabled={isSubmitting}
            className="text-energy hover:bg-energy-10"
          >
            <XCircle className="w-4 h-4 mr-1" />
            {t('sessions.approval.reject', 'Reject')}
          </AppleButton>
          <AppleButton
            variant="default"
            size="sm"
            haptic="medium"
            onClick={handleApprove}
            disabled={isSubmitting}
          >
            <CheckCircle className="w-4 h-4 mr-1" />
            {t('sessions.approval.approve', 'Approve')}
          </AppleButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ApprovalWorkflow
