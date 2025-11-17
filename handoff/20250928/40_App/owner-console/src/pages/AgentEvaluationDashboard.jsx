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
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [evaluations, setEvaluations] = useState([])

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
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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
            Agent Evaluation Dashboard
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-1">
            Monitor AI agent performance metrics and evaluation results
          </p>
        </div>
        <Button onClick={loadEvaluationData} variant="outline" disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadEvaluationData} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              Retry
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
              <CardTitle className="text-sm font-medium">Planner Accuracy</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getMetricColor(metrics.metrics.planner_accuracy, metrics.targets.planner_accuracy)}`}>
                {formatPercentage(metrics.metrics.planner_accuracy)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Target: {formatPercentage(metrics.targets.planner_accuracy)}
              </p>
              <Badge className={`mt-2 ${getMetricBadgeColor(metrics.metrics.planner_accuracy, metrics.targets.planner_accuracy)}`}>
                {metrics.metrics.planner_accuracy >= metrics.targets.planner_accuracy ? 'On Target' : 'Below Target'}
              </Badge>
            </CardContent>
          </Card>

          {/* Self-Healing Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Self-Healing Rate</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getMetricColor(metrics.metrics.self_healing_rate, metrics.targets.self_healing_rate)}`}>
                {formatPercentage(metrics.metrics.self_healing_rate)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Target: {formatPercentage(metrics.targets.self_healing_rate)}
              </p>
              <Badge className={`mt-2 ${getMetricBadgeColor(metrics.metrics.self_healing_rate, metrics.targets.self_healing_rate)}`}>
                {metrics.metrics.self_healing_rate >= metrics.targets.self_healing_rate ? 'On Target' : 'Below Target'}
              </Badge>
            </CardContent>
          </Card>

          {/* Completion Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getMetricColor(metrics.metrics.completion_rate, metrics.targets.completion_rate)}`}>
                {formatPercentage(metrics.metrics.completion_rate)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Target: {formatPercentage(metrics.targets.completion_rate)}
              </p>
              <Badge className={`mt-2 ${getMetricBadgeColor(metrics.metrics.completion_rate, metrics.targets.completion_rate)}`}>
                {metrics.metrics.completion_rate >= metrics.targets.completion_rate ? 'On Target' : 'Below Target'}
              </Badge>
            </CardContent>
          </Card>

          {/* CI Pass Rate */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CI Pass Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getMetricColor(metrics.metrics.ci_pass_rate, metrics.targets.ci_pass_rate)}`}>
                {formatPercentage(metrics.metrics.ci_pass_rate)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Target: {formatPercentage(metrics.targets.ci_pass_rate)}
              </p>
              <Badge className={`mt-2 ${getMetricBadgeColor(metrics.metrics.ci_pass_rate, metrics.targets.ci_pass_rate)}`}>
                {metrics.metrics.ci_pass_rate >= metrics.targets.ci_pass_rate ? 'On Target' : 'Below Target'}
              </Badge>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Evaluation History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Evaluation History
          </CardTitle>
          <CardDescription>
            Recent agent evaluation runs from GitHub Actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {evaluations.length === 0 ? (
            <div className="py-12 text-center">
              <Activity className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
              <p className="text-neutral-600 dark:text-neutral-400">
                No evaluation results available yet
              </p>
              <p className="text-sm text-neutral-500 dark:text-neutral-500 mt-2">
                Evaluations run weekly via GitHub Actions
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
                        Run #{evaluation.run_id}
                      </Badge>
                    </div>
                    <div className="mt-2 grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-neutral-500">Tasks:</span>
                        <span className="ml-1 font-medium">{evaluation.total_tasks}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500">Completed:</span>
                        <span className="ml-1 font-medium">{evaluation.completed}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500">PRs:</span>
                        <span className="ml-1 font-medium">{evaluation.pr_created}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500">CI Passed:</span>
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
                Last evaluation:
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
