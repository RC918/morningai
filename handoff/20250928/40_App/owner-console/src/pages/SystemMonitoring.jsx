import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button, Skeleton } from '@morningai/shared-ui'
import { Activity, Server, Database, Zap, Cpu, HardDrive, RefreshCw } from 'lucide-react'
import { getAdminSystemHealth, getAdminSystemMetrics } from '@/lib/generated/admin/admin'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const SystemMonitoring = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    loadSystemData()
  }, [])

  const loadSystemData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [healthResponse, metricsResponse] = await Promise.all([
        getAdminSystemHealth(),
        getAdminSystemMetrics()
      ])

      if (healthResponse.status === 200) {
        setHealth(healthResponse.data)
      } else {
        throw new Error('Failed to load system health')
      }

      if (metricsResponse.status === 200) {
        setMetrics(metricsResponse.data)
      } else {
        throw new Error('Failed to load system metrics')
      }
    } catch (error) {
      console.error('Failed to load system data:', error)
      setError(error.message || 'Failed to load system data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    // Emotional Color Mapping:
    // - healthy → growth (綠) - 成功/健康
    // - degraded → joy (橙) - 警告/注意
    // - unhealthy → energy (紅) - 錯誤/危險
    // - unknown → calm (藍) - 正常/穩定
    switch (status) {
      case 'healthy':
        return 'bg-growth-10 text-growth'
      case 'degraded':
        return 'bg-joy-10 text-joy'
      case 'unhealthy':
        return 'bg-energy-10 text-energy'
      default:
        return 'bg-calm-10 text-calm'
    }
  }

  const formatUptime = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`
    if (hours < 24) return `${Math.round(hours)}h`
    return `${Math.round(hours / 24)}d`
  }

  const isEmptyValue = (value) => {
    if (value == null) return true
    if (Array.isArray(value)) return value.length === 0
    if (typeof value === 'object') return Object.keys(value).length === 0
    return false
  }

  const generateTrendData = (currentValue) => {
    const data = []
    const variance = 5 // +/- 5% variance
    
    for (let i = 0; i < 24; i++) {
      const randomVariance = (Math.random() - 0.5) * variance * 2
      const value = Math.max(0, Math.min(100, currentValue + randomVariance))
      data.push({ value: parseFloat(value.toFixed(1)) })
    }
    
    return data
  }

  const showSkeleton = loading && isEmptyValue(health) && isEmptyValue(metrics)

  if (showSkeleton) {
    return (
      <div className="p-8 space-y-6" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        {/* Header Skeleton */}
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-9 w-64 mb-2" aria-hidden="true" />
            <Skeleton className="h-5 w-96" aria-hidden="true" />
          </div>
          <Skeleton className="h-10 w-24" aria-hidden="true" />
        </div>

        {/* System Health Card Skeleton */}
        <Card className="material-card hover-lift">
          <CardHeader>
            <Skeleton className="h-6 w-48" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <Skeleton className="h-6 w-32" aria-hidden="true" />
              <Skeleton className="h-6 w-24" aria-hidden="true" />
            </div>
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton className="h-4 w-24" aria-hidden="true" />
                  <Skeleton className="h-4 w-20" aria-hidden="true" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Metrics Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="material-card hover-lift">
              <CardHeader>
                <Skeleton className="h-6 w-32" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <Skeleton className="h-4 w-16" aria-hidden="true" />
                    <Skeleton className="h-4 w-12" aria-hidden="true" />
                  </div>
                  <div className="flex justify-between">
                    <Skeleton className="h-4 w-20" aria-hidden="true" />
                    <Skeleton className="h-4 w-24" aria-hidden="true" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6" aria-busy={loading} data-testid="system-monitoring">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-large-title font-bold text-neutral-900 dark:text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-growth" />
            {t('monitoring.title')}
          </h1>
          <p className="text-body text-neutral-600 dark:text-neutral-400 mt-1">{t('monitoring.subtitle')}</p>
        </div>
        <AppleButton onClick={loadSystemData} variant="outline" haptic="light" disabled={loading} data-testid="refresh-metrics">
          <RefreshCw className="w-4 h-4 mr-2" />
          {t('common.refresh')}
        </AppleButton>
      </div>

      {error && (
        <AppleErrorBanner
          title={t('common.error')}
          message={error}
          onRetry={loadSystemData}
        />
      )}

      {!error && !loading && isEmptyValue(health) && (
        <Card className="material-card hover-lift">
          <CardContent className="py-12 text-center" role="region" aria-labelledby="empty-health-title" aria-describedby="empty-health-desc">
            <Activity className="w-12 h-12 text-neutral-400 mx-auto mb-4" aria-hidden="true" />
            <p id="empty-health-title" className="text-neutral-600 dark:text-neutral-400">{t('monitoring.noHealthData')}</p>
            <AppleButton 
              onClick={loadSystemData} 
              variant="outline" 
              haptic="light"
              className="mt-4"
              aria-label={t('monitoring.retryLoadHealth', { defaultValue: 'Retry loading system health' })}
            >
              {t('common.refresh')}
            </AppleButton>
          </CardContent>
        </Card>
      )}

      {health && (
        <Card className="material-card hover-lift" data-testid="system-health">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              {t('monitoring.systemHealth')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <span className="text-title-3 font-medium">{t('monitoring.overallStatus')}</span>
              <Badge className={getStatusColor(health.status)}>
                {health.status?.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-callout text-neutral-600 dark:text-neutral-400">{t('monitoring.uptime')}</span>
                <span className="text-callout font-semibold">{formatUptime(health.uptime_hours)}</span>
              </div>
              {health.services && Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex justify-between">
                  <span className="text-callout text-neutral-600 dark:text-neutral-400 capitalize">{service}</span>
                  <Badge className={getStatusColor(status)} variant="outline">
                    {status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!error && !loading && isEmptyValue(metrics) && (
        <Card className="material-card hover-lift">
          <CardContent className="py-12 text-center" role="region" aria-labelledby="empty-metrics-title" aria-describedby="empty-metrics-desc">
            <Database className="w-12 h-12 text-neutral-400 mx-auto mb-4" aria-hidden="true" />
            <p id="empty-metrics-title" className="text-neutral-600 dark:text-neutral-400">{t('monitoring.noMetricsData')}</p>
            <AppleButton 
              onClick={loadSystemData} 
              variant="outline" 
              haptic="light"
              className="mt-4"
              aria-label={t('monitoring.retryLoadMetrics', { defaultValue: 'Retry loading system metrics' })}
            >
              {t('common.refresh')}
            </AppleButton>
          </CardContent>
        </Card>
      )}

      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="material-card hover-lift" data-testid="cpu-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="w-5 h-5" />
                {t('monitoring.cpuUsage')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-callout">{t('common.usage')}</span>
                    <span className="text-callout font-semibold">{metrics.cpu?.usage_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-callout">{t('monitoring.cores')}</span>
                    <span className="text-callout font-semibold">{metrics.cpu?.count}</span>
                  </div>
                </div>
                {metrics.cpu?.usage_percent != null && (
                  <div className="space-y-1">
                    <div className="h-16" aria-label={t('monitoring.cpuTrend')} data-testid="cpu-trend">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={generateTrendData(metrics.cpu.usage_percent)}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="rgb(var(--color-calm))" 
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    {USE_MOCK && (
                      <Badge variant="outline" className="text-xs" data-testid="mock-badge">
                        {t('monitoring.mockDataLabel')}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="material-card hover-lift" data-testid="memory-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                {t('monitoring.memory')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-callout">{t('common.usage')}</span>
                    <span className="text-callout font-semibold">{metrics.memory?.usage_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-callout">{t('monitoring.usedTotal')}</span>
                    <span className="text-callout font-semibold">
                      {t('monitoring.gbFormat', { used: metrics.memory?.used_gb, total: metrics.memory?.total_gb })}
                    </span>
                  </div>
                </div>
                {metrics.memory?.usage_percent != null && (
                  <div className="space-y-1">
                    <div className="h-16" aria-label={t('monitoring.memoryTrend')} data-testid="memory-trend">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={generateTrendData(metrics.memory.usage_percent)}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="rgb(var(--color-growth))" 
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    {USE_MOCK && (
                      <Badge variant="outline" className="text-xs" data-testid="mock-badge">
                        {t('monitoring.mockDataLabel')}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="material-card hover-lift" data-testid="disk-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="w-5 h-5" />
                {t('monitoring.disk')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-callout">{t('common.usage')}</span>
                    <span className="text-callout font-semibold">{metrics.disk?.usage_percent}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-callout">{t('monitoring.usedTotal')}</span>
                    <span className="text-callout font-semibold">
                      {t('monitoring.gbFormat', { used: metrics.disk?.used_gb, total: metrics.disk?.total_gb })}
                    </span>
                  </div>
                </div>
                {metrics.disk?.usage_percent != null && (
                  <div className="space-y-1">
                    <div className="h-16" aria-label={t('monitoring.diskTrend')} data-testid="disk-trend">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={generateTrendData(metrics.disk.usage_percent)}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="rgb(var(--color-joy))" 
                            strokeWidth={2}
                            dot={false}
                            isAnimationActive={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    {USE_MOCK && (
                      <Badge variant="outline" className="text-xs" data-testid="mock-badge">
                        {t('monitoring.mockDataLabel')}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default SystemMonitoring
