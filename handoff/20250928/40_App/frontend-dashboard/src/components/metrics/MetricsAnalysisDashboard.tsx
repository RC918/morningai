/**
 * Metrics Analysis Dashboard
 * 
 * Displays performance metrics, trends, and regression analysis.
 * 
 * @component
 */

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui'
import { AppleButton } from '@/components/ui/apple-button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@morningai/shared-ui'
import { Alert, AlertDescription } from '@morningai/shared-ui'
import { Badge } from '@morningai/shared-ui'
import { 
  Download, 
  TrendingUp, 
  TrendingDown,
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Zap
} from 'lucide-react'
import { getMetricsReport, exportMetricsData, MetricsCollector } from '@/lib/metrics-analysis'
import { useTranslation } from 'react-i18next'

type MetricStatus = 'good' | 'excellent' | 'needs_improvement' | 'poor'

interface WebVitalData {
  status: MetricStatus
  current: number
  average: number
  p90: number
  count: number
}

interface UXMetricsTTV {
  status: MetricStatus
  average: number
  median: number
  p90: number
  count: number
}

interface TaskPerformance {
  success_rate: number
  successful_tasks: number
  total_tasks: number
  avg_completion_time: number
  avg_duration: number
  status: MetricStatus
  failed_tasks: number
}

interface ErrorData {
  error_rate: number
  total_errors: number
}

interface RegressionData {
  baseline: number
  current: number
  improved: boolean
  change_percent: number
}

interface Recommendation {
  priority: 'high' | 'medium' | 'low'
  message: string
  suggestion: string
}

interface MetricsReport {
  generated_at: string
  summary: {
    total_metrics: number
    categories: string[]
  }
  task_performance?: TaskPerformance
  web_vitals?: Record<string, WebVitalData>
  ux_metrics?: {
    ttv?: UXMetricsTTV
  }
  errors?: ErrorData
  trends?: Record<string, unknown>
  regression?: {
    web_vitals?: Record<string, RegressionData>
    task_success_rate?: RegressionData
  }
  recommendations?: Recommendation[]
}

export function MetricsAnalysisDashboard(): React.ReactElement {
  const { t } = useTranslation()
  const [report, setReport] = useState<MetricsReport | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [baseline, setBaseline] = useState<MetricsReport | null>(null)

  useEffect(() => {
    loadReport()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadReport = (): void => {
    setLoading(true)
    try {
      const metrics: unknown[] = MetricsCollector.loadMetrics()
      if (metrics.length === 0) {
        setReport(null)
        setLoading(false)
        return
      }

      const analysisReport: MetricsReport = getMetricsReport(baseline)
      setReport(analysisReport)
    } catch (error) {
      console.error('Failed to generate report:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = (): void => {
    const data: unknown = exportMetricsData()
    const blob: Blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url: string = URL.createObjectURL(blob)
    const a: HTMLAnchorElement = document.createElement('a')
    a.href = url
    a.download = `metrics-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSetBaseline = (): void => {
    if (report) {
      setBaseline(report)
      alert(t('metrics.analysis.baselineSetSuccess'))
      loadReport()
    }
  }

  const handleClearBaseline = (): void => {
    setBaseline(null)
    loadReport()
  }

  const handleClearMetrics = (): void => {
    if (confirm(t('metrics.analysis.confirmClear'))) {
      MetricsCollector.clearMetrics()
      setReport(null)
      setBaseline(null)
    }
  }

  const getStatusIcon = (status: MetricStatus): React.ReactElement => {
    switch (status) {
      case 'good':
      case 'excellent':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'needs_improvement':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case 'poor':
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getStatusBadge = (status: MetricStatus): React.ReactElement => {
    const variants: Record<MetricStatus, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      good: 'default',
      excellent: 'default',
      needs_improvement: 'secondary',
      poor: 'destructive'
    }
    return (
      <Badge variant={variants[status] || 'outline'}>
        {status?.replace('_', ' ')}
      </Badge>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p>{t('metrics.analysis.loading')}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardHeader>
            <CardTitle>{t('metrics.analysis.noData')}</CardTitle>
            <CardDescription>
              {t('metrics.analysis.noDataDescription')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {t('metrics.analysis.autoCollectionMessage')}
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{t('metrics.analysis.title')}</h1>
          <p className="text-muted-foreground">
            {t('metrics.analysis.description')}
          </p>
        </div>
        <div className="flex gap-2">
          {!baseline ? (
            <AppleButton onClick={handleSetBaseline} variant="outline">
              {t('metrics.analysis.setBaseline')}
            </AppleButton>
          ) : (
            <AppleButton onClick={handleClearBaseline} variant="outline">
              {t('metrics.analysis.clearBaseline')}
            </AppleButton>
          )}
          <AppleButton onClick={handleExport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            {t('metrics.analysis.export')}
          </AppleButton>
          <AppleButton onClick={handleClearMetrics} variant="destructive">
            {t('metrics.analysis.clearData')}
          </AppleButton>
        </div>
      </div>

      {baseline && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>{t('metrics.analysis.baselineActive')}</strong> {t('metrics.analysis.baselineComparison', { date: new Date(baseline.generated_at).toLocaleString() })}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              {t('metrics.analysis.totalMetrics')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{report.summary.total_metrics}</div>
            <p className="text-xs text-muted-foreground">
              {t('metrics.analysis.categories', { count: report.summary.categories.length })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              {t('metrics.analysis.taskSuccess')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {report.task_performance?.success_rate?.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {t('metrics.analysis.tasks', { successful: report.task_performance?.successful_tasks || 0, total: report.task_performance?.total_tasks || 0 })}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              {t('metrics.analysis.avgTTV')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {report.ux_metrics?.ttv ? 
                `${(report.ux_metrics.ttv.average / 60000).toFixed(1)}m` : 
                'N/A'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              {t('metrics.analysis.timeToValue')}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              {t('metrics.analysis.errorRate')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {report.errors?.error_rate || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {t('metrics.analysis.errors', { count: report.errors?.total_errors || 0 })}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="web-vitals" className="w-full">
        <TabsList>
          <TabsTrigger value="web-vitals">{t('metrics.analysis.tabs.webVitals')}</TabsTrigger>
          <TabsTrigger value="ux-metrics">{t('metrics.analysis.tabs.uxMetrics')}</TabsTrigger>
          <TabsTrigger value="tasks">{t('metrics.analysis.tabs.tasks')}</TabsTrigger>
          <TabsTrigger value="regression">{t('metrics.analysis.tabs.regression')}</TabsTrigger>
          <TabsTrigger value="recommendations">{t('metrics.analysis.tabs.recommendations')}</TabsTrigger>
        </TabsList>

        <TabsContent value="web-vitals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('metrics.analysis.webVitals.title')}</CardTitle>
              <CardDescription>
                {t('metrics.analysis.webVitals.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(report.web_vitals || {}).map(([vital, data]) => (
                <div key={vital} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        {vital}
                        {getStatusIcon(data.status)}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {vital === 'LCP' && t('metrics.analysis.webVitals.lcp')}
                        {vital === 'CLS' && t('metrics.analysis.webVitals.cls')}
                        {vital === 'INP' && t('metrics.analysis.webVitals.inp')}
                        {vital === 'FCP' && t('metrics.analysis.webVitals.fcp')}
                        {vital === 'TTFB' && t('metrics.analysis.webVitals.ttfb')}
                      </p>
                    </div>
                    {getStatusBadge(data.status)}
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.webVitals.current')}</div>
                      <div className="font-medium">{data.current.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.webVitals.average')}</div>
                      <div className="font-medium">{data.average.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.webVitals.p90')}</div>
                      <div className="font-medium">{data.p90.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.webVitals.samples')}</div>
                      <div className="font-medium">{data.count}</div>
                    </div>
                  </div>
                </div>
              ))}

              {Object.keys(report.web_vitals || {}).length === 0 && (
                <p className="text-muted-foreground text-center py-4">
                  {t('metrics.analysis.webVitals.noData')}
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ux-metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('metrics.analysis.uxMetrics.title')}</CardTitle>
              <CardDescription>
                {t('metrics.analysis.uxMetrics.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.ux_metrics?.ttv && (
                <div className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        {t('metrics.analysis.uxMetrics.ttv')}
                        {getStatusIcon(report.ux_metrics.ttv.status)}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {t('metrics.analysis.uxMetrics.ttvDescription')}
                      </p>
                    </div>
                    {getStatusBadge(report.ux_metrics.ttv.status)}
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.uxMetrics.average')}</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.average / 60000).toFixed(1)} {t('metrics.analysis.uxMetrics.min')}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.uxMetrics.median')}</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.median / 60000).toFixed(1)} {t('metrics.analysis.uxMetrics.min')}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.uxMetrics.p90')}</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.p90 / 60000).toFixed(1)} {t('metrics.analysis.uxMetrics.min')}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">{t('metrics.analysis.uxMetrics.samples')}</div>
                      <div className="font-medium">{report.ux_metrics.ttv.count}</div>
                    </div>
                  </div>
                </div>
              )}

              {!report.ux_metrics?.ttv && (
                <p className="text-muted-foreground text-center py-4">
                  {t('metrics.analysis.uxMetrics.noData')}
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('metrics.analysis.taskPerformance.title')}</CardTitle>
              <CardDescription>
                {t('metrics.analysis.taskPerformance.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.task_performance && (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">{t('metrics.analysis.taskPerformance.totalTasks')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {report.task_performance.total_tasks}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">{t('metrics.analysis.taskPerformance.successRate')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {report.task_performance.success_rate.toFixed(1)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">{t('metrics.analysis.taskPerformance.avgDuration')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {t('metrics.analysis.taskPerformance.avgDurationValue', { 
                            duration: (report.task_performance.avg_duration / 1000).toFixed(1) 
                          })}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">{t('metrics.analysis.taskPerformance.status')}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {getStatusBadge(report.task_performance.status)}
                      </CardContent>
                    </Card>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h3 className="font-semibold mb-3">{t('metrics.analysis.taskPerformance.taskBreakdown')}</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">{t('metrics.analysis.taskPerformance.successfulTasks')}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full"
                              style={{ 
                                width: `${(report.task_performance.successful_tasks / report.task_performance.total_tasks * 100)}%` 
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {report.task_performance.successful_tasks}
                          </span>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">{t('metrics.analysis.taskPerformance.failedTasks')}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-red-500 h-2 rounded-full"
                              style={{ 
                                width: `${(report.task_performance.failed_tasks / report.task_performance.total_tasks * 100)}%` 
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {report.task_performance.failed_tasks}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regression" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('metrics.analysis.regression.title')}</CardTitle>
              <CardDescription>
                {t('metrics.analysis.regression.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report.regression ? (
                <div className="space-y-4">
                  {report.regression.web_vitals && (
                    <div>
                      <h3 className="font-semibold mb-3">{t('metrics.analysis.regression.webVitalsChanges')}</h3>
                      <div className="space-y-2">
                        {Object.entries(report.regression.web_vitals).map(([vital, data]) => (
                          <div key={vital} className="flex justify-between items-center p-3 border rounded">
                            <div>
                              <div className="font-medium">{vital}</div>
                              <div className="text-sm text-muted-foreground">
                                {data.baseline.toFixed(2)} → {data.current.toFixed(2)}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {data.improved ? (
                                <TrendingDown className="h-4 w-4 text-green-600" />
                              ) : (
                                <TrendingUp className="h-4 w-4 text-red-600" />
                              )}
                              <span className={data.improved ? 'text-green-600' : 'text-red-600'}>
                                {data.change_percent > 0 ? '+' : ''}{data.change_percent}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {report.regression.task_success_rate && (
                    <div>
                      <h3 className="font-semibold mb-3">{t('metrics.analysis.regression.taskSuccessRateChange')}</h3>
                      <div className="flex justify-between items-center p-3 border rounded">
                        <div>
                          <div className="font-medium">{t('metrics.analysis.regression.successRate')}</div>
                          <div className="text-sm text-muted-foreground">
                            {t('metrics.analysis.regression.successRateChange', {
                              baseline: report.regression.task_success_rate.baseline.toFixed(1),
                              current: report.regression.task_success_rate.current.toFixed(1)
                            })}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {report.regression.task_success_rate.improved ? (
                            <TrendingUp className="h-4 w-4 text-green-600" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-600" />
                          )}
                          <span className={report.regression.task_success_rate.improved ? 'text-green-600' : 'text-red-600'}>
                            {report.regression.task_success_rate.change_percent > 0 ? '+' : ''}{report.regression.task_success_rate.change_percent}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {t('metrics.analysis.regression.noBaseline')}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('metrics.analysis.recommendations.title')}</CardTitle>
              <CardDescription>
                {t('metrics.analysis.recommendations.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report.recommendations && report.recommendations.length > 0 ? (
                <div className="space-y-3">
                  {report.recommendations.map((rec, index) => (
                    <Alert key={index} variant={rec.priority === 'high' ? 'destructive' : 'default'}>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <div className="flex justify-between items-start mb-2">
                          <strong>{rec.message}</strong>
                          <Badge variant={rec.priority === 'high' ? 'destructive' : 'secondary'}>
                            {rec.priority}
                          </Badge>
                        </div>
                        <p className="text-sm">{rec.suggestion}</p>
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              ) : (
                <Alert>
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertDescription>
                    <strong>{t('metrics.analysis.recommendations.greatJob')}</strong> {t('metrics.analysis.recommendations.allGood')}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default MetricsAnalysisDashboard
