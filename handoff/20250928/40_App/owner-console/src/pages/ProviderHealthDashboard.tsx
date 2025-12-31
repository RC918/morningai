/**
 * Provider Health Dashboard - EPIC I-3c
 * 
 * Displays real-time health status for all LLM providers.
 * Observe-only: Does not affect routing decisions.
 * 
 * Features:
 * - Provider health scores with visual indicators
 * - System-wide health summary
 * - Alert status and cooldown information
 * - Optional Grafana deep-link integration
 */
import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge, SectionCard, Skeleton, Progress } from '@morningai/shared-ui'
import { 
  Activity, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  ExternalLink,
  Zap
} from 'lucide-react'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'

interface ProviderHealthData {
  health_score: number
  latency_ms: number
  error_rate: number
  drift_rate: number
  request_count: number
  last_updated: string
}

interface ProviderHealthResponse {
  available: boolean
  timestamp: string
  window_minutes: number
  system_status: 'healthy' | 'degraded' | 'critical'
  summary: {
    average_health: number
    total_providers: number
    healthy: number
    degraded: number
    critical: number
  }
  providers: Record<string, ProviderHealthData>
  ranking: string[]
  alerting: {
    enabled: boolean
    cooldown_status: Record<string, unknown>
  }
  error?: string
  message?: string
}

const TRACE_VIEWER_URL = (import.meta as any).env?.VITE_TRACE_VIEWER_URL || ''

const ProviderHealthDashboard = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [healthData, setHealthData] = useState<ProviderHealthResponse | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [windowMinutes, setWindowMinutes] = useState(15)

  const loadHealthData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await apiClientWithMeta<ProviderHealthResponse>(
        `/api/governance/providers/health?window=${windowMinutes}`,
        { method: 'GET' }
      )

      if (result.status === 200 && result.data) {
        if (result.data.available === false) {
          setError(result.data.message || t('providerHealth.metricsUnavailable'))
          setHealthData(null)
        } else {
          setHealthData(result.data)
        }
      } else if (result.status === 503) {
        setError(t('providerHealth.serviceUnavailable'))
        setHealthData(null)
      } else {
        throw new Error(`API returned status ${result.status}`)
      }
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('providerHealth.loadError'),
        statusMessages: {
          503: t('providerHealth.serviceUnavailable'),
          401: t('common.unauthorized')
        },
        logContext: 'loadProviderHealthData'
      })
      setError(errorMessage)
      setHealthData(null)
    } finally {
      setLoading(false)
    }
  }, [windowMinutes, t])

  useEffect(() => {
    loadHealthData()

    const interval = autoRefresh ? setInterval(loadHealthData, 30000) : null

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, loadHealthData])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-growth-10 text-growth'
      case 'degraded':
        return 'bg-joy-10 text-joy'
      case 'critical':
        return 'bg-energy-10 text-energy'
      default:
        return 'bg-calm-10 text-calm'
    }
  }

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-growth'
    if (score >= 60) return 'text-joy'
    return 'text-energy'
  }

  const getHealthBgColor = (score: number) => {
    if (score >= 80) return 'bg-growth'
    if (score >= 60) return 'bg-joy'
    return 'bg-energy'
  }

  const getHealthIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-5 h-5 text-growth" />
    if (score >= 60) return <AlertTriangle className="w-5 h-5 text-joy" />
    return <XCircle className="w-5 h-5 text-energy" />
  }

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatPercentage = (rate: number) => {
    return `${(rate * 100).toFixed(1)}%`
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return timestamp
    }
  }

  const showSkeleton = loading && !healthData

  if (showSkeleton) {
    return (
      <div className="space-y-8" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        <div className="flex items-center justify-between">
          <div className="flex flex-col">
            <Skeleton className="h-7 w-56 mb-2" aria-hidden="true" />
            <Skeleton className="h-5 w-80" aria-hidden="true" />
          </div>
          <Skeleton className="h-10 w-24" aria-hidden="true" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
              <Skeleton className="h-5 w-24 mb-4" aria-hidden="true" />
              <Skeleton className="h-8 w-16" aria-hidden="true" />
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
              <Skeleton className="h-5 w-32 mb-4" aria-hidden="true" />
              <div className="space-y-3">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j} className="flex justify-between">
                    <Skeleton className="h-4 w-20" aria-hidden="true" />
                    <Skeleton className="h-4 w-16" aria-hidden="true" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8" aria-busy={loading} data-testid="provider-health-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            {t('providerHealth.title')}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {t('providerHealth.subtitle')}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {healthData && (
            <Badge 
              className={getStatusColor(healthData.system_status)}
              data-testid="system-status-badge"
            >
              <Activity className="h-3 w-3 mr-1" />
              {healthData.system_status.toUpperCase()}
            </Badge>
          )}
          <select
            value={windowMinutes}
            onChange={(e) => setWindowMinutes(Number(e.target.value))}
            className="text-sm border border-[var(--border)] rounded-lg px-3 py-2 bg-[var(--surface)]"
            aria-label={t('providerHealth.windowSelect')}
          >
            <option value={5}>5 {t('providerHealth.minutes')}</option>
            <option value={15}>15 {t('providerHealth.minutes')}</option>
            <option value={30}>30 {t('providerHealth.minutes')}</option>
            <option value={60}>60 {t('providerHealth.minutes')}</option>
          </select>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            {autoRefresh ? t('providerHealth.autoRefreshOn') : t('providerHealth.autoRefreshOff')}
          </button>
          <AppleButton 
            onClick={loadHealthData} 
            variant="outline" 
            haptic="light" 
            disabled={loading}
            data-testid="refresh-button"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {t('common.refresh')}
          </AppleButton>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <AppleErrorBanner
          title={t('common.error')}
          message={error}
          onRetry={loadHealthData}
        />
      )}

      {/* Summary Cards */}
      {healthData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SectionCard data-testid="avg-health-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-secondary)]">{t('providerHealth.averageHealth')}</p>
                <p className={`text-2xl font-bold ${getHealthColor(healthData.summary.average_health)}`}>
                  {healthData.summary.average_health.toFixed(1)}
                </p>
              </div>
              <div className={`p-3 rounded-full ${getHealthBgColor(healthData.summary.average_health)} bg-opacity-10`}>
                <Zap className={`w-6 h-6 ${getHealthColor(healthData.summary.average_health)}`} />
              </div>
            </div>
          </SectionCard>

          <SectionCard data-testid="healthy-count-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-secondary)]">{t('providerHealth.healthyProviders')}</p>
                <p className="text-2xl font-bold text-growth">{healthData.summary.healthy}</p>
              </div>
              <div className="p-3 rounded-full bg-growth bg-opacity-10">
                <CheckCircle className="w-6 h-6 text-growth" />
              </div>
            </div>
          </SectionCard>

          <SectionCard data-testid="degraded-count-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-secondary)]">{t('providerHealth.degradedProviders')}</p>
                <p className="text-2xl font-bold text-joy">{healthData.summary.degraded}</p>
              </div>
              <div className="p-3 rounded-full bg-joy bg-opacity-10">
                <AlertTriangle className="w-6 h-6 text-joy" />
              </div>
            </div>
          </SectionCard>

          <SectionCard data-testid="critical-count-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[var(--text-secondary)]">{t('providerHealth.criticalProviders')}</p>
                <p className="text-2xl font-bold text-energy">{healthData.summary.critical}</p>
              </div>
              <div className="p-3 rounded-full bg-energy bg-opacity-10">
                <XCircle className="w-6 h-6 text-energy" />
              </div>
            </div>
          </SectionCard>
        </div>
      )}

      {/* Provider Cards */}
      {healthData && Object.keys(healthData.providers).length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-[var(--text-primary)]">
              {t('providerHealth.providerDetails')}
            </h2>
            {TRACE_VIEWER_URL && (
              <a
                href={TRACE_VIEWER_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-sm text-calm hover:text-calm-dark"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                {t('providerHealth.viewInGrafana')}
              </a>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {healthData.ranking.map((providerName) => {
              const provider = healthData.providers[providerName]
              if (!provider) return null

              return (
                <SectionCard 
                  key={providerName}
                  data-testid={`provider-card-${providerName}`}
                >
                  <div className="space-y-4">
                    {/* Provider Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getHealthIcon(provider.health_score)}
                        <h3 className="font-medium text-[var(--text-primary)] capitalize">
                          {providerName}
                        </h3>
                      </div>
                      <Badge className={getStatusColor(
                        provider.health_score >= 80 ? 'healthy' : 
                        provider.health_score >= 60 ? 'degraded' : 'critical'
                      )}>
                        {provider.health_score.toFixed(0)}
                      </Badge>
                    </div>

                    {/* Health Score Progress */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-[var(--text-secondary)]">{t('providerHealth.healthScore')}</span>
                        <span className={`font-medium ${getHealthColor(provider.health_score)}`}>
                          {provider.health_score.toFixed(1)}%
                        </span>
                      </div>
                      <Progress 
                        value={provider.health_score} 
                        className={getHealthBgColor(provider.health_score)}
                      />
                    </div>

                    {/* Metrics */}
                    <div className="space-y-2 pt-2 border-t border-[var(--border)]">
                      <div className="flex justify-between text-sm">
                        <span className="text-[var(--text-secondary)] flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {t('providerHealth.latency')}
                        </span>
                        <span className="font-medium text-[var(--text-primary)]">
                          {formatLatency(provider.latency_ms)}
                        </span>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span className="text-[var(--text-secondary)] flex items-center">
                          <TrendingDown className="w-3 h-3 mr-1" />
                          {t('providerHealth.errorRate')}
                        </span>
                        <span className={`font-medium ${provider.error_rate > 0.05 ? 'text-energy' : 'text-[var(--text-primary)]'}`}>
                          {formatPercentage(provider.error_rate)}
                        </span>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span className="text-[var(--text-secondary)] flex items-center">
                          <TrendingUp className="w-3 h-3 mr-1" />
                          {t('providerHealth.driftRate')}
                        </span>
                        <span className={`font-medium ${provider.drift_rate > 0.1 ? 'text-joy' : 'text-[var(--text-primary)]'}`}>
                          {formatPercentage(provider.drift_rate)}
                        </span>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span className="text-[var(--text-secondary)]">
                          {t('providerHealth.requests')}
                        </span>
                        <span className="font-medium text-[var(--text-primary)]">
                          {provider.request_count}
                        </span>
                      </div>
                    </div>

                    {/* Last Updated */}
                    <div className="text-xs text-[var(--text-secondary)] pt-2 border-t border-[var(--border)]">
                      {t('providerHealth.lastUpdated')}: {formatTimestamp(provider.last_updated)}
                    </div>
                  </div>
                </SectionCard>
              )
            })}
          </div>
        </div>
      )}

      {/* Empty State */}
      {healthData && Object.keys(healthData.providers).length === 0 && (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <div className="py-8 text-center">
            <Activity className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
            <p className="text-[var(--text-secondary)]">{t('providerHealth.noProviders')}</p>
            <p className="text-sm text-[var(--text-secondary)] mt-2">
              {t('providerHealth.noProvidersHint')}
            </p>
          </div>
        </div>
      )}

      {/* Alerting Status */}
      {healthData && (
        <SectionCard title={t('providerHealth.alertingStatus')} data-testid="alerting-status">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="text-sm text-[var(--text-secondary)] mr-2">
                {t('providerHealth.alertingEnabled')}:
              </span>
              <Badge className={healthData.alerting.enabled ? 'bg-growth-10 text-growth' : 'bg-neutral-100 text-neutral-500'}>
                {healthData.alerting.enabled ? t('common.yes') : t('common.no')}
              </Badge>
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              {t('providerHealth.windowLabel')}: {healthData.window_minutes} {t('providerHealth.minutes')}
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              {t('providerHealth.lastRefresh')}: {formatTimestamp(healthData.timestamp)}
            </div>
          </div>
        </SectionCard>
      )}
    </div>
  )
}

export default ProviderHealthDashboard
