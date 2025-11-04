import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button, Alert, AlertDescription, AlertTitle } from '@morningai/shared-ui'
import { Activity, Server, Database, Zap, AlertTriangle, Cpu, HardDrive, RefreshCw } from 'lucide-react'
import { getAdminSystemHealth, getAdminSystemMetrics } from '@/lib/generated/admin/admin'

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
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const formatUptime = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`
    if (hours < 24) return `${Math.round(hours)}h`
    return `${Math.round(hours / 24)}d`
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Activity className="w-8 h-8 text-green-600" />
            {t('monitoring.title')}
          </h1>
          <p className="text-gray-600 mt-1">{t('monitoring.subtitle')}</p>
        </div>
        <Button onClick={loadSystemData} variant="outline" disabled={loading}>
          <RefreshCw className="w-4 h-4 mr-2" />
          {t('common.refresh')}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadSystemData} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              {t('common.refresh')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              {t('monitoring.systemHealth')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <span className="text-lg font-medium">{t('monitoring.overallStatus')}</span>
              <Badge className={getStatusColor(health.status)}>
                {health.status?.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.uptime')}</span>
                <span className="text-sm font-semibold">{formatUptime(health.uptime_hours)}</span>
              </div>
              {health.services && Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex justify-between">
                  <span className="text-sm text-gray-600 capitalize">{service}</span>
                  <Badge className={getStatusColor(status)} variant="outline">
                    {status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Cpu className="w-5 h-5" />
                {t('monitoring.cpuUsage')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{t('common.usage')}</span>
                  <span className="text-sm font-semibold">{metrics.cpu?.usage_percent}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">{t('monitoring.cores')}</span>
                  <span className="text-sm font-semibold">{metrics.cpu?.count}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                {t('monitoring.memory')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{t('common.usage')}</span>
                  <span className="text-sm font-semibold">{metrics.memory?.usage_percent}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">{t('monitoring.usedTotal')}</span>
                  <span className="text-sm font-semibold">
                    {t('monitoring.gbFormat', { used: metrics.memory?.used_gb, total: metrics.memory?.total_gb })}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="w-5 h-5" />
                {t('monitoring.disk')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">{t('common.usage')}</span>
                  <span className="text-sm font-semibold">{metrics.disk?.usage_percent}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">{t('monitoring.usedTotal')}</span>
                  <span className="text-sm font-semibold">
                    {t('monitoring.gbFormat', { used: metrics.disk?.used_gb, total: metrics.disk?.total_gb })}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default SystemMonitoring
