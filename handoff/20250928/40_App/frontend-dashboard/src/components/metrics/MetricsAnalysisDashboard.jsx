/**
 * Metrics Analysis Dashboard
 * 
 * Displays performance metrics, trends, and regression analysis.
 * 
 * @component
 */

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
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

export function MetricsAnalysisDashboard() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [baseline, setBaseline] = useState(null)

  useEffect(() => {
    loadReport()
  }, [])

  const loadReport = () => {
    setLoading(true)
    try {
      const metrics = MetricsCollector.loadMetrics()
      if (metrics.length === 0) {
        setReport(null)
        setLoading(false)
        return
      }

      const analysisReport = getMetricsReport(baseline)
      setReport(analysisReport)
    } catch (error) {
      console.error('Failed to generate report:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    const data = exportMetricsData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `metrics-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSetBaseline = () => {
    if (report) {
      setBaseline(report)
      alert('Baseline set successfully! Future reports will compare against this baseline.')
      loadReport()
    }
  }

  const handleClearBaseline = () => {
    setBaseline(null)
    loadReport()
  }

  const handleClearMetrics = () => {
    if (confirm('Are you sure you want to clear all metrics data? This cannot be undone.')) {
      MetricsCollector.clearMetrics()
      setReport(null)
      setBaseline(null)
    }
  }

  const getStatusIcon = (status) => {
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

  const getStatusBadge = (status) => {
    const variants = {
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
            <p>Loading metrics...</p>
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
            <CardTitle>No Metrics Data</CardTitle>
            <CardDescription>
              Start collecting metrics to see performance analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Metrics collection is automatic when you use the application. 
                Come back after using the app for a while to see your performance data.
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
          <h1 className="text-3xl font-bold">Metrics Analysis</h1>
          <p className="text-muted-foreground">
            Performance and UX metrics analysis
          </p>
        </div>
        <div className="flex gap-2">
          {!baseline ? (
            <Button onClick={handleSetBaseline} variant="outline">
              Set as Baseline
            </Button>
          ) : (
            <Button onClick={handleClearBaseline} variant="outline">
              Clear Baseline
            </Button>
          )}
          <Button onClick={handleExport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={handleClearMetrics} variant="destructive">
            Clear Data
          </Button>
        </div>
      </div>

      {baseline && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Baseline Active:</strong> Comparing current metrics against baseline from {new Date(baseline.generated_at).toLocaleString()}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Total Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{report.summary.total_metrics}</div>
            <p className="text-xs text-muted-foreground">
              {report.summary.categories.length} categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Task Success
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {report.task_performance?.success_rate?.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {report.task_performance?.successful_tasks || 0}/{report.task_performance?.total_tasks || 0} tasks
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Avg TTV
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
              Time to Value
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="h-4 w-4" />
              Error Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {report.errors?.error_rate || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              {report.errors?.total_errors || 0} errors
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="web-vitals" className="w-full">
        <TabsList>
          <TabsTrigger value="web-vitals">Web Vitals</TabsTrigger>
          <TabsTrigger value="ux-metrics">UX Metrics</TabsTrigger>
          <TabsTrigger value="tasks">Task Performance</TabsTrigger>
          <TabsTrigger value="regression">Regression Analysis</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="web-vitals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Core Web Vitals</CardTitle>
              <CardDescription>
                Performance metrics that measure user experience
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
                        {vital === 'LCP' && 'Largest Contentful Paint'}
                        {vital === 'CLS' && 'Cumulative Layout Shift'}
                        {vital === 'INP' && 'Interaction to Next Paint'}
                        {vital === 'FCP' && 'First Contentful Paint'}
                        {vital === 'TTFB' && 'Time to First Byte'}
                      </p>
                    </div>
                    {getStatusBadge(data.status)}
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Current</div>
                      <div className="font-medium">{data.current.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Average</div>
                      <div className="font-medium">{data.average.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">P90</div>
                      <div className="font-medium">{data.p90.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Samples</div>
                      <div className="font-medium">{data.count}</div>
                    </div>
                  </div>
                </div>
              ))}

              {Object.keys(report.web_vitals || {}).length === 0 && (
                <p className="text-muted-foreground text-center py-4">
                  No Web Vitals data collected yet
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ux-metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Experience Metrics</CardTitle>
              <CardDescription>
                Custom UX metrics and measurements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.ux_metrics?.ttv && (
                <div className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold flex items-center gap-2">
                        Time to Value (TTV)
                        {getStatusIcon(report.ux_metrics.ttv.status)}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Time until user achieves first value
                      </p>
                    </div>
                    {getStatusBadge(report.ux_metrics.ttv.status)}
                  </div>

                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Average</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.average / 60000).toFixed(1)} min
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Median</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.median / 60000).toFixed(1)} min
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">P90</div>
                      <div className="font-medium">
                        {(report.ux_metrics.ttv.p90 / 60000).toFixed(1)} min
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Samples</div>
                      <div className="font-medium">{report.ux_metrics.ttv.count}</div>
                    </div>
                  </div>
                </div>
              )}

              {!report.ux_metrics?.ttv && (
                <p className="text-muted-foreground text-center py-4">
                  No UX metrics data collected yet
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Task Performance</CardTitle>
              <CardDescription>
                User task completion metrics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {report.task_performance && (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Total Tasks</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {report.task_performance.total_tasks}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Success Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                          {report.task_performance.success_rate.toFixed(1)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Avg Duration</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {(report.task_performance.avg_duration / 1000).toFixed(1)}s
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Status</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {getStatusBadge(report.task_performance.status)}
                      </CardContent>
                    </Card>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h3 className="font-semibold mb-3">Task Breakdown</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Successful Tasks</span>
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
                        <span className="text-sm">Failed Tasks</span>
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
              <CardTitle>Regression Analysis</CardTitle>
              <CardDescription>
                Comparison with baseline metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              {report.regression ? (
                <div className="space-y-4">
                  {report.regression.web_vitals && (
                    <div>
                      <h3 className="font-semibold mb-3">Web Vitals Changes</h3>
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
                      <h3 className="font-semibold mb-3">Task Success Rate Change</h3>
                      <div className="flex justify-between items-center p-3 border rounded">
                        <div>
                          <div className="font-medium">Success Rate</div>
                          <div className="text-sm text-muted-foreground">
                            {report.regression.task_success_rate.baseline.toFixed(1)}% → {report.regression.task_success_rate.current.toFixed(1)}%
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
                    No baseline set. Click "Set as Baseline" to enable regression analysis.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recommendations</CardTitle>
              <CardDescription>
                Suggested improvements based on analysis
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
                    <strong>Great job!</strong> All metrics are within acceptable ranges. No immediate action required.
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
