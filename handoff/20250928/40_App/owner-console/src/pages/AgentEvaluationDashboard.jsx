import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle, 
  Badge, 
  Button, 
  Alert, 
  AlertDescription, 
  AlertTitle, 
  Skeleton 
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

  const getMetricColor = (value, target) => {
    const percentage = (value / target) * 100
    if (percentage >= 90) return 'text-success-600'
    if (percentage >= 70) return 'text-warning-600'
    return 'text-error-600'
  }

  const getMetricBadgeColor = (value, target) => {
    const percentage = (value / target) * 100
    if (percentage >= 90) return 'bg-success-100 text-success-800 border-success-300'
    if (percentage >= 70) return 'bg-warning-100 text-warning-800 border-warning-300'
    return 'bg-error-100 text-error-800 border-error-300'
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
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-20 mb-2" />
                <Skeleton className="h-4 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Evaluation History Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6" aria-busy={loading}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary-600" />
            {t('agentEvaluation.title', 'Agent Evaluation Dashboard')}
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            {t('agentEvaluation.subtitle', 'Monitor AI agent performance metrics and evaluation results')}
          </p>
        </div>
        <Button onClick={loadEvaluationData} variant="outline" disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {t('common.refresh', 'Refresh')}
        </Button>
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
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('agentEvaluation.metrics.plannerAccuracy', 'Planner Accuracy')}</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${hasData ? getMetricColor(metrics.metrics.planner_accuracy, metrics.targets.planner_accuracy) : 'text-neutral-400'}`}>
                {hasData ? formatPercentage(metrics.metrics.planner_accuracy) : t('common.na', 'N/A')}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.planner_accuracy)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
              </p>
              <div className="mt-2 min-h-[24px]">
                {hasData && (
                  <Badge className={getMetricBadgeColor(metrics.metrics.planner_accuracy, metrics.targets.planner_accuracy)}>
                    {metrics.metrics.planner_accuracy >= metrics.targets.planner_accuracy ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Self-Healing Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('agentEvaluation.metrics.selfHealingRate', 'Self-Healing Rate')}</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${hasData ? getMetricColor(metrics.metrics.self_healing_rate, metrics.targets.self_healing_rate) : 'text-neutral-400'}`}>
                {hasData ? formatPercentage(metrics.metrics.self_healing_rate) : t('common.na', 'N/A')}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.self_healing_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
              </p>
              <div className="mt-2 min-h-[24px]">
                {hasData && (
                  <Badge className={getMetricBadgeColor(metrics.metrics.self_healing_rate, metrics.targets.self_healing_rate)}>
                    {metrics.metrics.self_healing_rate >= metrics.targets.self_healing_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Completion Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('agentEvaluation.metrics.completionRate', 'Completion Rate')}</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${hasData ? getMetricColor(metrics.metrics.completion_rate, metrics.targets.completion_rate) : 'text-neutral-400'}`}>
                {hasData ? formatPercentage(metrics.metrics.completion_rate) : t('common.na', 'N/A')}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.completion_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
              </p>
              <div className="mt-2 min-h-[24px]">
                {hasData && (
                  <Badge className={getMetricBadgeColor(metrics.metrics.completion_rate, metrics.targets.completion_rate)}>
                    {metrics.metrics.completion_rate >= metrics.targets.completion_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* CI Pass Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{t('agentEvaluation.metrics.ciPassRate', 'CI Pass Rate')}</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${hasData ? getMetricColor(metrics.metrics.ci_pass_rate, metrics.targets.ci_pass_rate) : 'text-neutral-400'}`}>
                {hasData ? formatPercentage(metrics.metrics.ci_pass_rate) : t('common.na', 'N/A')}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {hasData ? `${t('agentEvaluation.target', 'Target')}: ${formatPercentage(metrics.targets.ci_pass_rate)}` : t('monitoring.noMetricsData', 'No metrics available yet')}
              </p>
              <div className="mt-2 min-h-[24px]">
                {hasData && (
                  <Badge className={getMetricBadgeColor(metrics.metrics.ci_pass_rate, metrics.targets.ci_pass_rate)}>
                    {metrics.metrics.ci_pass_rate >= metrics.targets.ci_pass_rate ? t('agentEvaluation.onTarget', 'On Target') : t('agentEvaluation.belowTarget', 'Below Target')}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Evaluation History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            {t('agentEvaluation.history.title', 'Evaluation History')}
          </CardTitle>
          <CardDescription>
            {t('agentEvaluation.history.subtitle', 'Recent agent evaluation runs from GitHub Actions')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {evaluations.length === 0 ? (
            <div className="py-12 text-center">
              <Activity className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
              <p className="text-neutral-600 dark:text-neutral-400">
                {t('agentEvaluation.history.noResults', 'No evaluation results available yet')}
              </p>
              <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-2">
                {t('agentEvaluation.history.weeklyRuns', 'Evaluations run weekly via GitHub Actions')}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {evaluations.map((evaluation) => (
                <div 
                  key={evaluation.id} 
                  className="flex items-center justify-between p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {evaluation.status === 'success' ? (
                          <CheckCircle2 className="w-5 h-5 text-success-600" />
                        ) : (
                          <XCircle className="w-5 h-5 text-error-600" />
                        )}
                        <span className="font-medium text-sm">
                          {formatDate(evaluation.date)}
                        </span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {t('agentEvaluation.history.runNumber', 'Run #{{id}}', { id: evaluation.run_id })}
                      </Badge>
                    </div>
                    <div className="mt-2 grid grid-cols-4 gap-4 text-sm">
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
        </CardContent>
      </Card>

      {/* Last Evaluation Info */}
      {metrics && metrics.last_evaluation && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-neutral-600 dark:text-neutral-400">
                {t('agentEvaluation.lastEvaluation', 'Last evaluation')}:
              </span>
              <span className="font-medium">
                {formatDate(metrics.last_evaluation)}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default AgentEvaluationDashboard
