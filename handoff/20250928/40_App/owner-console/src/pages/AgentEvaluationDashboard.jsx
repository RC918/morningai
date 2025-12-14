import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Badge, 
  Button, 
  Alert, 
  AlertDescription, 
  AlertTitle, 
  Skeleton,
  StatCard,
  SectionCard
} from '@morningai/shared-ui'
import { 
  Activity, 
  Target, 
  TrendingUp, 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  AlertTriangle,
  ExternalLink,
  Calendar
} from 'lucide-react'
import { getAgentEvaluationResults, getAgentEvaluationMetrics } from '@/lib/agent-evaluation-api'
import { AppleButton } from '@/components/apple/apple-button'

const AgentEvaluationDashboard = () => {
  const { t, i18n } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [evaluations, setEvaluations] = useState([])
  
  const hasData = metrics && evaluations.length > 0

  useEffect(() => {
    loadEvaluationData()
  }, [])

  const loadEvaluationData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [metricsResponse, resultsResponse] = await Promise.all([
        getAgentEvaluationMetrics(),
        getAgentEvaluationResults(10)
      ])

      setMetrics(metricsResponse)
      setEvaluations(resultsResponse.evaluations || [])
    } catch (error) {
      console.error('Failed to load evaluation data:', error)
      setError(error.message || 'Failed to load evaluation data')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return t('common.na', 'N/A')
    const date = new Date(dateString)
    const formatter = new Intl.DateTimeFormat(i18n.resolvedLanguage || i18n.language, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
    return formatter.format(date)
  }

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`
  }

  if (loading && !metrics) {
    return (
      <div className="p-8 space-y-6" role="status" aria-live="polite" aria-busy="true">
        {/* Header Skeleton */}
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-9 w-80 mb-2" />
            <Skeleton className="h-5 w-96" />
          </div>
          <Skeleton className="h-10 w-24" />
        </div>

        {/* Metrics Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
              <Skeleton className="h-6 w-32 mb-4" />
              <Skeleton className="h-8 w-20 mb-2" />
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </div>

        {/* Evaluation History Skeleton */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <Skeleton className="h-6 w-48" />
          </div>
          <div className="p-5 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex justify-between">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6" aria-busy={loading}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-large-title font-bold text-neutral-900 dark:text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary-600" />
            {t('agentEvaluation.title', 'Agent Evaluation Dashboard')}
          </h1>
          <p className="text-body text-neutral-600 dark:text-neutral-400 mt-1">
            {t('agentEvaluation.subtitle', 'Monitor AI agent performance metrics and evaluation results')}
          </p>
        </div>
        <AppleButton onClick={loadEvaluationData} variant="outline" haptic="light" disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {t('common.refresh', 'Refresh')}
        </AppleButton>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error', 'Error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadEvaluationData} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              {t('common.retry', 'Retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Planner Accuracy */}
          <StatCard
            label={t('agentEvaluation.metrics.plannerAccuracy', 'Planner Accuracy')}
            value={hasData ? formatPercentage(metrics.metrics.planner_accuracy) : t('common.na', 'N/A')}
            icon={<Target />}
            variant={hasData && metrics.metrics.planner_accuracy >= metrics.targets.planner_accuracy ? 'green' : hasData ? 'red' : 'default'}
            deltaLabel={hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.planner_accuracy)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
            deltaPositive="neutral"
            badge={hasData ? (metrics.metrics.planner_accuracy >= metrics.targets.planner_accuracy ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')) : undefined}
          />

          {/* Self-Healing Rate */}
          <StatCard
            label={t('agentEvaluation.metrics.selfHealingRate', 'Self-Healing Rate')}
            value={hasData ? formatPercentage(metrics.metrics.self_healing_rate) : t('common.na', 'N/A')}
            icon={<Activity />}
            variant={hasData && metrics.metrics.self_healing_rate >= metrics.targets.self_healing_rate ? 'green' : hasData ? 'red' : 'default'}
            deltaLabel={hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.self_healing_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
            deltaPositive="neutral"
            badge={hasData ? (metrics.metrics.self_healing_rate >= metrics.targets.self_healing_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')) : undefined}
          />

          {/* Completion Rate */}
          <StatCard
            label={t('agentEvaluation.metrics.completionRate', 'Completion Rate')}
            value={hasData ? formatPercentage(metrics.metrics.completion_rate) : t('common.na', 'N/A')}
            icon={<CheckCircle2 />}
            variant={hasData && metrics.metrics.completion_rate >= metrics.targets.completion_rate ? 'green' : hasData ? 'red' : 'default'}
            deltaLabel={hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.completion_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
            deltaPositive="neutral"
            badge={hasData ? (metrics.metrics.completion_rate >= metrics.targets.completion_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')) : undefined}
          />

          {/* CI Pass Rate */}
          <StatCard
            label={t('agentEvaluation.metrics.ciPassRate', 'CI Pass Rate')}
            value={hasData ? formatPercentage(metrics.metrics.ci_pass_rate) : t('common.na', 'N/A')}
            icon={<TrendingUp />}
            variant={hasData && metrics.metrics.ci_pass_rate >= metrics.targets.ci_pass_rate ? 'green' : hasData ? 'red' : 'default'}
            deltaLabel={hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.ci_pass_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
            deltaPositive="neutral"
            badge={hasData ? (metrics.metrics.ci_pass_rate >= metrics.targets.ci_pass_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')) : undefined}
          />
        </div>
      )}

      {/* Evaluation History */}
      <SectionCard
        title={t('agentEvaluation.history.title', 'Evaluation History')}
        subtitle={t('agentEvaluation.history.subtitle', 'Recent agent evaluation runs from GitHub Actions')}
        icon={<Calendar className="w-5 h-5" />}
      >
        {evaluations.length === 0 ? (
          <div className="py-8 text-center">
            <Activity className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
            <p className="text-neutral-600 dark:text-neutral-400">
              {t('agentEvaluation.history.noResults', 'No evaluation results available yet')}
            </p>
            <p className="text-callout text-neutral-500 dark:text-neutral-500 mt-2">
              {t('agentEvaluation.history.weeklyRuns', 'Evaluations run weekly via GitHub Actions')}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {evaluations.map((evaluation) => (
              <div 
                key={evaluation.id} 
                className="flex items-center justify-between p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] transition-opacity hover:opacity-80"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {evaluation.status === 'success' ? (
                        <CheckCircle2 className="w-5 h-5 text-success-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-error-600" />
                      )}
                      <span className="font-medium text-callout">
                        {formatDate(evaluation.date)}
                      </span>
                    </div>
                    <Badge variant="outline" className="text-caption-2">
                      {t('agentEvaluation.history.runNumber', 'Run #{{id}}', { id: evaluation.run_id })}
                    </Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-4 gap-4 text-callout">
                    <div>
                      <span className="text-neutral-500">{t('agentEvaluation.history.tasks', 'Tasks')}:</span>
                      <span className="ml-1 font-medium">{evaluation.total_tasks}</span>
                    </div>
                    <div>
                      <span className="text-neutral-500">{t('agentEvaluation.history.completed', 'Completed')}:</span>
                      <span className="ml-1 font-medium">{evaluation.completed}</span>
                    </div>
                    <div>
                      <span className="text-neutral-500">{t('agentEvaluation.history.prs', 'PRs')}:</span>
                      <span className="ml-1 font-medium">{evaluation.pr_created}</span>
                    </div>
                    <div>
                      <span className="text-neutral-500">{t('agentEvaluation.history.ciPassed', 'CI Passed')}:</span>
                      <span className="ml-1 font-medium">{evaluation.ci_passed}</span>
                    </div>
                  </div>
                </div>
                <div className="ml-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(evaluation.run_url, '_blank')}
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Last Evaluation Info */}
      {metrics && metrics.last_evaluation && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card px-5 py-4">
          <div className="flex items-center justify-between text-callout">
            <span className="text-neutral-600 dark:text-neutral-400">
              {t('agentEvaluation.lastEvaluation', 'Last evaluation')}:
            </span>
            <span className="font-medium">
              {formatDate(metrics.last_evaluation)}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default AgentEvaluationDashboard
