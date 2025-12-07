import { useState, useCallback, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Badge,
  Skeleton,
  Progress
} from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  Lightbulb,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Target,
  TrendingUp,
  Clock
} from 'lucide-react'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'

/**
 * SessionInsights - Display DeepWiki-generated insights for a session
 * 
 * Features:
 * - Display session analysis summary
 * - Show actionable recommendations
 * - Display session metrics
 * - Support for cached vs generated insights
 * - Collapsible sections for better UX
 * 
 * Issue: #2159
 * Phase: M5 - Meta Agent (Tier 5)
 * PR: PR 10 - DeepWiki Frontend UI
 */

const SessionInsights = ({ 
  sessionId,
  isOpen = true,
  onToggle,
  className = ''
}) => {
  const { t } = useTranslation()
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isExpanded, setIsExpanded] = useState(true)

  const fetchInsights = useCallback(async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)

    try {
      const response = await apiClientWithMeta(`/api/deepwiki/insights/${sessionId}`, {
        method: 'GET'
      })
      setInsights(response.data)
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.insights.fetchError', 'Failed to load session insights'),
        logContext: 'SessionInsights.fetchInsights',
        statusMessages: {
          503: t('sessions.insights.serviceUnavailable', 'DeepWiki service is not available')
        }
      })
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [sessionId, t])

  useEffect(() => {
    if (isOpen && sessionId) {
      fetchInsights()
    }
  }, [isOpen, sessionId, fetchInsights])

  const handleRefresh = useCallback(() => {
    fetchInsights()
  }, [fetchInsights])

  const handleToggleExpand = useCallback(() => {
    setIsExpanded(prev => !prev)
  }, [])

  const getSourceBadge = useCallback((source) => {
    if (source === 'cached') {
      return (
        <Badge variant="secondary" className="text-xs">
          <Clock className="w-3 h-3 mr-1" />
          {t('sessions.insights.cached', 'Cached')}
        </Badge>
      )
    }
    return (
      <Badge variant="outline" className="text-xs">
        <RefreshCw className="w-3 h-3 mr-1" />
        {t('sessions.insights.generated', 'Generated')}
      </Badge>
    )
  }, [t])

  if (!isOpen) return null

  if (loading) {
    return (
      <div className={`p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-6 w-20" />
        </div>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4 mb-4" />
        <div className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 rounded-lg border border-energy bg-energy-10 ${className}`}>
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-energy flex-shrink-0 mt-1" />
          <div className="flex-1">
            <p className="text-sm font-medium text-energy-dark">
              {t('sessions.insights.errorTitle', 'Unable to load insights')}
            </p>
            <p className="text-xs text-energy-dark mt-1">{error}</p>
          </div>
          <AppleButton
            variant="ghost"
            size="sm"
            haptic="light"
            onClick={handleRefresh}
          >
            <RefreshCw className="w-4 h-4" />
          </AppleButton>
        </div>
      </div>
    )
  }

  if (!insights) {
    return (
      <div className={`p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] ${className}`}>
        <div className="flex items-center gap-2 text-[var(--text-secondary)]">
          <BookOpen className="w-4 h-4" />
          <span className="text-sm">
            {t('sessions.insights.noInsights', 'No insights available for this session')}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden ${className}`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-[var(--surface-elevated)] transition-colors"
        onClick={handleToggleExpand}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && handleToggleExpand()}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-wisdom" />
          <h3 className="text-sm font-medium text-[var(--text-primary)]">
            {t('sessions.insights.title', 'Session Insights')}
          </h3>
          {getSourceBadge(insights.source)}
        </div>
        <div className="flex items-center gap-2">
          <AppleButton
            variant="ghost"
            size="sm"
            haptic="light"
            onClick={(e) => {
              e.stopPropagation()
              handleRefresh()
            }}
            aria-label={t('sessions.insights.refresh', 'Refresh insights')}
          >
            <RefreshCw className="w-4 h-4" />
          </AppleButton>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-[var(--text-secondary)]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[var(--text-secondary)]" />
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* Summary */}
          {insights.summary && (
            <div className="p-3 rounded-lg bg-[var(--surface-elevated)]">
              <div className="flex items-start gap-2">
                <Target className="w-4 h-4 text-primary-500 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">
                    {t('sessions.insights.summary', 'Summary')}
                  </p>
                  <p className="text-sm text-[var(--text-primary)]">
                    {insights.summary}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Metrics */}
          {insights.metrics && Object.keys(insights.metrics).length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {insights.metrics.tasks_completed !== undefined && (
                <div className="p-3 rounded-lg bg-growth-10 border border-growth">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-growth" />
                    <span className="text-xs text-growth-dark">
                      {t('sessions.insights.tasksCompleted', 'Completed')}
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-growth">
                    {insights.metrics.tasks_completed}
                  </p>
                </div>
              )}
              {insights.metrics.tasks_failed !== undefined && (
                <div className="p-3 rounded-lg bg-energy-10 border border-energy">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertCircle className="w-4 h-4 text-energy" />
                    <span className="text-xs text-energy-dark">
                      {t('sessions.insights.tasksFailed', 'Failed')}
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-energy">
                    {insights.metrics.tasks_failed}
                  </p>
                </div>
              )}
              {insights.metrics.duration_seconds !== undefined && (
                <div className="p-3 rounded-lg bg-wisdom-10 border border-wisdom">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-wisdom" />
                    <span className="text-xs text-wisdom-dark">
                      {t('sessions.insights.duration', 'Duration')}
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-wisdom">
                    {t('sessions.insights.durationValue', '{{count}}m', { count: Math.round(insights.metrics.duration_seconds / 60) })}
                  </p>
                </div>
              )}
              {insights.metrics.confidence !== undefined && (
                <div className="p-3 rounded-lg bg-primary-10 border border-primary-500">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="w-4 h-4 text-primary-500" />
                    <span className="text-xs text-primary-600">
                      {t('sessions.insights.confidence', 'Confidence')}
                    </span>
                  </div>
                  <p className="text-lg font-semibold text-primary-500">
                    {Math.round(insights.metrics.confidence * 100)}%
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Recommendations */}
          {insights.recommendations && insights.recommendations.length > 0 && (
            <div className="border border-[var(--border)] rounded-lg overflow-hidden">
              <div className="px-4 py-2 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
                <h4 className="text-sm font-medium text-[var(--text-primary)]">
                  {t('sessions.insights.recommendations', 'Recommendations')}
                </h4>
              </div>
              <ul className="divide-y divide-[var(--border)]">
                {insights.recommendations.map((recommendation, index) => (
                  <li key={index} className="px-4 py-3 flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-wisdom-10 flex items-center justify-center flex-shrink-0 mt-1">
                      <span className="text-xs font-medium text-wisdom">{index + 1}</span>
                    </div>
                    <p className="text-sm text-[var(--text-primary)]">
                      {recommendation}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Timestamp */}
          {insights.timestamp && (
            <p className="text-xs text-[var(--text-secondary)] text-right">
              {t('sessions.insights.lastUpdated', 'Last updated')}: {new Date(insights.timestamp).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default SessionInsights
