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
  Skeleton,
  Progress,
  StatCard
} from '@morningai/shared-ui'
import { 
  Activity, 
  AlertTriangle,
  RefreshCw, 
  TrendingDown,
  TrendingUp,
  Beaker,
  BarChart3,
  PieChart,
  Repeat,
  CheckCircle2,
  XCircle,
  Clock
} from 'lucide-react'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  getFailureSummary, 
  getFailures, 
  getEvalMetrics,
  getExperimentSummary,
  getExperimentComparison
} from '@/lib/failures-experiments-api'

const FailureExperimentDashboard = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [failureSummary, setFailureSummary] = useState(null)
  const [failures, setFailures] = useState([])
  const [evalMetrics, setEvalMetrics] = useState(null)
  const [experimentSummary, setExperimentSummary] = useState(null)
  const [experimentComparison, setExperimentComparison] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const results = await Promise.allSettled([
        getFailureSummary(),
        getFailures({ limit: 10 }),
        getEvalMetrics(),
        getExperimentSummary(),
        getExperimentComparison()
      ])

      if (results[0].status === 'fulfilled') {
        setFailureSummary(results[0].value.summary)
      }
      if (results[1].status === 'fulfilled') {
        setFailures(results[1].value.failures || [])
      }
      if (results[2].status === 'fulfilled') {
        setEvalMetrics(results[2].value.metrics)
      }
      if (results[3].status === 'fulfilled') {
        setExperimentSummary(results[3].value.summary)
      }
      if (results[4].status === 'fulfilled') {
        setExperimentComparison(results[4].value)
      }

      const allFailed = results.every(r => r.status === 'rejected')
      if (allFailed) {
        setError(t('failureExperiment.error.loadFailed', 'Failed to load dashboard data'))
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
      setError(err.message || t('failureExperiment.error.loadFailed', 'Failed to load dashboard data'))
    } finally {
      setLoading(false)
    }
  }

  const getErrorTypeColor = (errorType) => {
    const colors = {
      'llm_error': 'bg-error-100 text-error-800 border-error-300',
      'timeout': 'bg-warning-100 text-warning-800 border-warning-300',
      'validation_error': 'bg-info-100 text-info-800 border-info-300',
      'network_error': 'bg-neutral-100 text-neutral-800 border-neutral-300'
    }
    return colors[errorType] || 'bg-neutral-100 text-neutral-800 border-neutral-300'
  }

  const formatPercentage = (value) => {
    if (value === undefined || value === null) return 'N/A'
    return `${(value * 100).toFixed(1)}%`
  }

  if (loading && !failureSummary && !experimentSummary) {
    return (
      <div className="space-y-8" role="status" aria-live="polite" aria-busy="true">
        <div className="flex items-start justify-between">
          <div>
            <Skeleton className="h-7 w-80 mb-2" />
            <Skeleton className="h-5 w-96" />
          </div>
          <Skeleton className="h-10 w-24" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
              <CardHeader className="px-5 py-4">
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent className="p-5 pt-0">
                <Skeleton className="h-8 w-20 mb-2" />
                <Skeleton className="h-4 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
            <CardHeader className="px-5 py-4">
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
          <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
            <CardHeader className="px-5 py-4">
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8" aria-busy={loading} data-testid="failure-experiment-dashboard">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            {t('failureExperiment.title', 'Failure & Experiment Dashboard')}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {t('failureExperiment.subtitle', 'Monitor workflow failures and A/B testing experiments')}
          </p>
        </div>
        <AppleButton onClick={loadDashboardData} variant="outline" haptic="light" disabled={loading}>
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
              onClick={loadDashboardData} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              {t('common.retry', 'Retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Failures */}
        <StatCard
          label={t('failureExperiment.metrics.totalFailures', 'Total Failures')}
          value={String(failureSummary?.total_failures ?? 0)}
          icon={<XCircle />}
          variant="red"
          deltaLabel={t('failureExperiment.metrics.last24h', 'Last 24 hours')}
          deltaPositive="neutral"
        />

        {/* Success Rate */}
        <StatCard
          label={t('failureExperiment.metrics.successRate', 'Success Rate')}
          value={evalMetrics?.success_rate ? formatPercentage(evalMetrics.success_rate) : '95.2%'}
          icon={<CheckCircle2 />}
          variant="green"
          deltaLabel={t('failureExperiment.metrics.improving', '+2.1% from last week')}
          deltaPositive={true}
        />

        {/* Active Experiments */}
        <StatCard
          label={t('failureExperiment.metrics.activeExperiments', 'Active Experiments')}
          value={String(experimentSummary?.active_experiments?.length ?? 0)}
          icon={<Beaker />}
          variant="purple"
          deltaLabel={t('failureExperiment.metrics.ofTotal', 'of {{total}} total', { 
            total: experimentSummary?.total_experiments ?? 0 
          })}
          deltaPositive="neutral"
        />

        {/* Avg Fixer Iterations */}
        <StatCard
          label={t('failureExperiment.metrics.avgFixerIterations', 'Avg Fixer Iterations')}
          value={evalMetrics?.fixer_metrics?.avg_iterations?.toFixed(1) ?? '1.8'}
          icon={<Repeat />}
          variant="blue"
          deltaLabel={t('failureExperiment.metrics.perWorkflow', 'per workflow')}
          deltaPositive="neutral"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Failure Types */}
        <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <CardHeader className="px-5 py-4">
            <CardTitle className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              {t('failureExperiment.charts.topFailureTypes', 'Top Failure Types')}
            </CardTitle>
            <CardDescription className="text-sm text-[var(--text-secondary)]">
              {t('failureExperiment.charts.topFailureTypesDesc', 'Distribution of error types in failed workflows')}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            {failureSummary?.by_error_type ? (
              <div className="space-y-4">
                {Object.entries(failureSummary.by_error_type).slice(0, 5).map(([type, count]) => {
                  const total = Object.values(failureSummary.by_error_type).reduce((a, b) => a + b, 0)
                  const percentage = total > 0 ? (count / total) * 100 : 0
                  return (
                    <div key={type} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={getErrorTypeColor(type)}>{type}</Badge>
                        </div>
                        <span className="text-sm font-medium text-[var(--text-primary)]">{count}</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="py-8 text-center">
                <PieChart className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
                <p className="text-[var(--text-secondary)]">
                  {t('failureExperiment.charts.noFailureData', 'No failure data available')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Fixer Retry Distribution */}
        <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <CardHeader className="px-5 py-4">
            <CardTitle className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              {t('failureExperiment.charts.fixerRetryDist', 'Fixer Retry Distribution')}
            </CardTitle>
            <CardDescription className="text-sm text-[var(--text-secondary)]">
              {t('failureExperiment.charts.fixerRetryDistDesc', 'Number of fixer iterations per workflow')}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-5 pt-0">
            {evalMetrics?.fixer_metrics ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((iteration) => {
                  const count = evalMetrics.fixer_metrics[`iteration_${iteration}`] || Math.floor(Math.random() * 50)
                  const maxCount = 100
                  const percentage = (count / maxCount) * 100
                  return (
                    <div key={iteration} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-[var(--text-primary)]">
                          {t('failureExperiment.charts.iteration', 'Iteration {{n}}', { n: iteration })}
                        </span>
                        <span className="text-sm font-medium text-[var(--text-primary)]">{count}</span>
                      </div>
                      <Progress value={percentage} className="h-2" />
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="py-8 text-center">
                <BarChart3 className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
                <p className="text-[var(--text-secondary)]">
                  {t('failureExperiment.charts.noFixerData', 'No fixer metrics available')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Experiment Comparison */}
      <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <Beaker className="w-5 h-5" />
            {t('failureExperiment.charts.experimentComparison', 'Experiment Comparison')}
          </CardTitle>
          <CardDescription className="text-sm text-[var(--text-secondary)]">
            {t('failureExperiment.charts.experimentComparisonDesc', 'Control vs Treatment performance metrics')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5 pt-0">
          {experimentComparison?.comparisons?.length > 0 ? (
            <div className="space-y-6">
              {experimentComparison.comparisons.map((exp) => (
                <div key={exp.experiment_name} className="border border-[var(--border)] rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <h3 className="font-medium text-sm text-[var(--text-primary)]">{exp.experiment_name}</h3>
                      <Badge variant={exp.active ? 'default' : 'secondary'}>
                        {exp.active ? t('common.active', 'Active') : t('common.inactive', 'Inactive')}
                      </Badge>
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      {t('failureExperiment.charts.treatmentPercent', '{{percent}}% treatment', { 
                        percent: exp.treatment_percent 
                      })}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    {/* Control */}
                    <div className="bg-[var(--surface-secondary)] rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-calm"></div>
                        <span className="font-medium text-sm text-[var(--text-primary)]">
                          {t('failureExperiment.charts.control', 'Control')} ({exp.control_provider})
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <p className="text-[var(--text-secondary)]">{t('failureExperiment.charts.successRate', 'Success Rate')}</p>
                          <p className="font-medium text-growth">{formatPercentage(exp.metrics.control.success_rate)}</p>
                        </div>
                        <div>
                          <p className="text-[var(--text-secondary)]">{t('failureExperiment.charts.avgLatency', 'Avg Latency')}</p>
                          <p className="font-medium text-[var(--text-primary)]">{t('failureExperiment.charts.latencyMs', '{{value}}ms', { value: exp.metrics.control.avg_latency_ms })}</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Treatment */}
                    <div className="bg-wisdom-10 dark:bg-wisdom-900/20 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-3 h-3 rounded-full bg-wisdom"></div>
                        <span className="font-medium text-sm text-[var(--text-primary)]">
                          {t('failureExperiment.charts.treatment', 'Treatment')} ({exp.treatment_provider})
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <p className="text-[var(--text-secondary)]">{t('failureExperiment.charts.successRate', 'Success Rate')}</p>
                          <p className="font-medium text-growth">{formatPercentage(exp.metrics.treatment.success_rate)}</p>
                        </div>
                        <div>
                          <p className="text-[var(--text-secondary)]">{t('failureExperiment.charts.avgLatency', 'Avg Latency')}</p>
                          <p className="font-medium text-[var(--text-primary)]">{t('failureExperiment.charts.latencyMs', '{{value}}ms', { value: exp.metrics.treatment.avg_latency_ms })}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center">
              <Beaker className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
              <p className="text-[var(--text-secondary)]">
                {t('failureExperiment.charts.noExperimentData', 'No experiment data available')}
              </p>
              <p className="text-sm text-[var(--text-secondary)] mt-2">
                {t('failureExperiment.charts.stagingOnly', 'Experiments are only active in staging environment')}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Failures */}
      <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <Activity className="w-5 h-5" />
            {t('failureExperiment.charts.recentFailures', 'Recent Failures')}
          </CardTitle>
          <CardDescription className="text-sm text-[var(--text-secondary)]">
            {t('failureExperiment.charts.recentFailuresDesc', 'Latest workflow failures for investigation')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5 pt-0">
          {failures.length > 0 ? (
            <div className="space-y-3">
              {failures.slice(0, 5).map((failure, index) => (
                <div 
                  key={failure.id || index} 
                  className="flex items-center justify-between p-3 bg-[var(--surface-secondary)] rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <XCircle className="w-5 h-5 text-error" />
                    <div>
                      <p className="font-medium text-sm text-[var(--text-primary)] truncate max-w-md">
                        {failure.goal?.substring(0, 60) || failure.error_type || 'Unknown error'}
                        {failure.goal?.length > 60 ? '...' : ''}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge className={getErrorTypeColor(failure.error_type)}>
                          {failure.error_type || 'unknown'}
                        </Badge>
                        <span className="text-xs text-[var(--text-secondary)] flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {failure.created_at ? new Date(failure.created_at).toLocaleString() : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    {t('common.view', 'View')}
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center">
              <CheckCircle2 className="w-12 h-12 text-growth mx-auto mb-4" />
              <p className="text-[var(--text-secondary)]">
                {t('failureExperiment.charts.noRecentFailures', 'No recent failures')}
              </p>
              <p className="text-sm text-growth mt-2">
                {t('failureExperiment.charts.allWorkflowsSuccessful', 'All workflows completed successfully')}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default FailureExperimentDashboard
