import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge } from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  FileCode,
  CheckCircle,
  XCircle,
  MessageSquare,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  GitPullRequest,
  AlertTriangle,
  Clock
} from 'lucide-react'

/**
 * CodeReviewPanel - Display code review results and PR status
 * 
 * Features:
 * - Show PR status and review comments
 * - Display file changes with diff summary
 * - Show review approval status
 * - Link to external PR
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const CodeReviewPanel = ({ 
  prUrl = null,
  prStatus = 'pending',
  reviewComments = [],
  fileChanges = [],
  reviewers = [],
  checksStatus = null
}) => {
  const { t } = useTranslation()
  const [expandedFiles, setExpandedFiles] = useState(new Set())

  const toggleFileExpand = useCallback((filePath) => {
    setExpandedFiles(prev => {
      const next = new Set(prev)
      if (next.has(filePath)) {
        next.delete(filePath)
      } else {
        next.add(filePath)
      }
      return next
    })
  }, [])

  const getPRStatusBadge = useCallback((status) => {
    switch (status) {
      case 'approved':
        return { variant: 'success', icon: CheckCircle, label: t('sessions.codeReview.status.approved', 'Approved') }
      case 'changes_requested':
        return { variant: 'warning', icon: AlertTriangle, label: t('sessions.codeReview.status.changesRequested', 'Changes Requested') }
      case 'pending':
        return { variant: 'secondary', icon: Clock, label: t('sessions.codeReview.status.pending', 'Pending Review') }
      case 'merged':
        return { variant: 'success', icon: GitPullRequest, label: t('sessions.codeReview.status.merged', 'Merged') }
      case 'closed':
        return { variant: 'destructive', icon: XCircle, label: t('sessions.codeReview.status.closed', 'Closed') }
      default:
        return { variant: 'secondary', icon: Clock, label: t('sessions.codeReview.status.draft', 'Draft') }
    }
  }, [t])

  const getChangeTypeColor = useCallback((changeType) => {
    switch (changeType) {
      case 'added':
        return 'text-growth bg-growth-10'
      case 'modified':
        return 'text-wisdom bg-wisdom-10'
      case 'deleted':
        return 'text-energy bg-energy-10'
      default:
        return 'text-neutral-500 bg-neutral-100'
    }
  }, [])

  if (!prUrl && fileChanges.length === 0) {
    return (
      <div className="text-center py-8">
        <GitPullRequest className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
        <p className="text-sm text-[var(--text-secondary)]">
          {t('sessions.codeReview.noPR', 'No pull request created yet')}
        </p>
      </div>
    )
  }

  const statusBadge = getPRStatusBadge(prStatus)
  const StatusIcon = statusBadge.icon

  return (
    <div className="space-y-4">
      {/* PR Header */}
      {prUrl && (
        <div className="flex items-center justify-between p-4 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)]">
          <div className="flex items-center gap-3">
            <GitPullRequest className="w-5 h-5 text-primary-500" />
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">
                {t('sessions.codeReview.pullRequest', 'Pull Request')}
              </p>
              <Badge variant={statusBadge.variant} className="text-xs mt-1">
                <StatusIcon className="w-3 h-3" />
                <span>{statusBadge.label}</span>
              </Badge>
            </div>
          </div>
          <AppleButton
            variant="outline"
            size="sm"
            haptic="light"
            onClick={() => window.open(prUrl, '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            {t('sessions.codeReview.viewPR', 'View PR')}
          </AppleButton>
        </div>
      )}

      {/* CI Checks Status */}
      {checksStatus && (
        <div className="p-4 rounded-lg border border-[var(--border)]">
          <h4 className="text-sm font-medium text-[var(--text-primary)] mb-3">
            {t('sessions.codeReview.ciChecks', 'CI Checks')}
          </h4>
          {/* Summary view when checksStatus has counts */}
          {(checksStatus.passed !== undefined || checksStatus.total !== undefined) && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--text-secondary)]">
                  {t('sessions.codeReview.checksStatus', '{{passed}}/{{total}} checks passed', {
                    passed: checksStatus.passed ?? 0,
                    total: checksStatus.total ?? ((checksStatus.passed ?? 0) + (checksStatus.failed ?? 0) + (checksStatus.pending ?? 0))
                  })}
                </span>
                <Badge 
                  variant={checksStatus.failed > 0 ? 'destructive' : checksStatus.pending > 0 ? 'secondary' : 'success'}
                  className="text-xs"
                >
                  {checksStatus.failed > 0 ? (
                    <XCircle className="w-3 h-3" />
                  ) : checksStatus.pending > 0 ? (
                    <Clock className="w-3 h-3" />
                  ) : (
                    <CheckCircle className="w-3 h-3" />
                  )}
                  <span>
                    {checksStatus.failed > 0 
                      ? t('sessions.codeReview.checksFailed', 'Failed')
                      : checksStatus.pending > 0 
                        ? t('sessions.codeReview.checksPending', 'Pending')
                        : t('sessions.codeReview.checksPassed', 'Passed')}
                  </span>
                </Badge>
              </div>
              {/* Progress bar for checks */}
              <div className="flex gap-1 h-2 rounded-full overflow-hidden bg-neutral-100 dark:bg-neutral-800">
                {(checksStatus.passed ?? 0) > 0 && (
                  <div 
                    className="bg-growth h-full" 
                    style={{ width: `${((checksStatus.passed ?? 0) / (checksStatus.total ?? 1)) * 100}%` }}
                  />
                )}
                {(checksStatus.failed ?? 0) > 0 && (
                  <div 
                    className="bg-energy h-full" 
                    style={{ width: `${((checksStatus.failed ?? 0) / (checksStatus.total ?? 1)) * 100}%` }}
                  />
                )}
                {(checksStatus.pending ?? 0) > 0 && (
                  <div 
                    className="bg-neutral-300 dark:bg-neutral-600 h-full" 
                    style={{ width: `${((checksStatus.pending ?? 0) / (checksStatus.total ?? 1)) * 100}%` }}
                  />
                )}
              </div>
            </div>
          )}
          {/* Detailed view when checksStatus has checks array */}
          {checksStatus.checks && checksStatus.checks.length > 0 && (
            <div className="space-y-2">
              {checksStatus.checks.map((check, index) => (
                <div key={check.name || index} className="flex items-center justify-between text-sm">
                  <span className="text-[var(--text-secondary)]">{check.name}</span>
                  <Badge 
                    variant={check.status === 'success' ? 'success' : check.status === 'failure' ? 'destructive' : 'secondary'}
                    className="text-xs"
                  >
                    {check.status === 'success' ? (
                      <CheckCircle className="w-3 h-3" />
                    ) : check.status === 'failure' ? (
                      <XCircle className="w-3 h-3" />
                    ) : (
                      <Clock className="w-3 h-3" />
                    )}
                    <span>{check.status}</span>
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* File Changes */}
      {fileChanges.length > 0 && (
        <div className="border border-[var(--border)] rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
            <h4 className="text-sm font-medium text-[var(--text-primary)]">
              {t('sessions.codeReview.filesChanged', 'Files Changed')} ({fileChanges.length})
            </h4>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {fileChanges.map((file, index) => (
              <div key={index}>
                <button
                  type="button"
                  onClick={() => toggleFileExpand(file.path)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--surface-elevated)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {expandedFiles.has(file.path) ? (
                      <ChevronDown className="w-4 h-4 text-neutral-400" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-neutral-400" />
                    )}
                    <FileCode className="w-4 h-4 text-neutral-500" />
                    <span className="text-sm text-[var(--text-primary)] font-mono">
                      {file.path}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded ${getChangeTypeColor(file.changeType)}`}>
                      {file.changeType}
                    </span>
                    <span className="text-xs text-growth">+{file.additions}</span>
                    <span className="text-xs text-energy">-{file.deletions}</span>
                  </div>
                </button>
                {expandedFiles.has(file.path) && file.preview && (
                  <div className="px-4 py-3 bg-neutral-50 dark:bg-neutral-900 border-t border-[var(--border)]">
                    <pre className="text-xs font-mono overflow-x-auto whitespace-pre-wrap">
                      {file.preview}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review Comments */}
      {reviewComments.length > 0 && (
        <div className="border border-[var(--border)] rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
            <h4 className="text-sm font-medium text-[var(--text-primary)]">
              {t('sessions.codeReview.comments', 'Review Comments')} ({reviewComments.length})
            </h4>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {reviewComments.map((comment, index) => (
              <div key={index} className="p-4">
                <div className="flex items-start gap-3">
                  <MessageSquare className="w-4 h-4 text-neutral-400 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[var(--text-primary)]">
                        {comment.author}
                      </span>
                      {comment.filePath && (
                        <span className="text-xs text-[var(--text-secondary)] font-mono">
                          {comment.filePath}:{comment.line}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[var(--text-secondary)]">
                      {comment.body}
                    </p>
                    {comment.resolved && (
                      <Badge variant="success" className="text-xs mt-2">
                        <CheckCircle className="w-3 h-3" />
                        <span>{t('sessions.codeReview.resolved', 'Resolved')}</span>
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviewers */}
      {reviewers.length > 0 && (
        <div className="p-4 rounded-lg border border-[var(--border)]">
          <h4 className="text-sm font-medium text-[var(--text-primary)] mb-3">
            {t('sessions.codeReview.reviewers', 'Reviewers')}
          </h4>
          <div className="flex flex-wrap gap-2">
            {reviewers.map((reviewer, index) => (
              <div key={index} className="flex items-center gap-2 px-3 py-2 rounded-full bg-[var(--surface-elevated)] border border-[var(--border)]">
                <span className="text-sm text-[var(--text-primary)]">{reviewer.name}</span>
                {reviewer.status === 'approved' && (
                  <CheckCircle className="w-4 h-4 text-growth" />
                )}
                {reviewer.status === 'changes_requested' && (
                  <AlertTriangle className="w-4 h-4 text-wisdom" />
                )}
                {reviewer.status === 'pending' && (
                  <Clock className="w-4 h-4 text-neutral-400" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CodeReviewPanel
