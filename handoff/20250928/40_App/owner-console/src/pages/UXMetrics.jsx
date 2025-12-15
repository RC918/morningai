/**
 * UX Metrics Dashboard
 * 
 * Displays UX quality metrics across recent PRs with comprehensive error handling.
 * 
 * Long-term improvements implemented:
 * 1. Data validation with validateMetricsData() to prevent undefined access
 * 2. Data sanitization with sanitizeMetricsData() to ensure safe structure
 * 3. Enhanced Sentry context for better debugging
 * 4. Type definitions in src/types/metrics.js for IDE support
 * 5. Defensive null checks throughout with optional chaining
 * 
 * @see src/types/metrics.js for type definitions
 * @see src/utils/metricsValidation.js for validation utilities
 */
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import * as Sentry from '@sentry/react'
import { SectionCard, StatCard, Skeleton } from '@morningai/shared-ui'
import { validateMetricsData, sanitizeMetricsData, safeGet, isValidMetricValue } from '../utils/metricsValidation'

/**
 * @typedef {import('../types/metrics').MetricsData} MetricsData
 */

export default function UXMetrics() {
  const { t } = useTranslation()
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      const response = await fetch('/metrics/ux-metrics.json')
      if (!response.ok) {
        throw new Error('Failed to fetch metrics')
      }
      const data = await response.json()
      
      const isValid = validateMetricsData(data)
      const sanitizedData = sanitizeMetricsData(data)
      
      Sentry.setContext('metrics', {
        isValid,
        hasSummary: !!data?.summary,
        hasApps: !!data?.summary?.apps,
        appKeys: Object.keys(data?.summary?.apps || {}),
        totalPRs: data?.total_prs || 0,
        metricsCount: data?.metrics?.length || 0,
        generatedAt: data?.generated_at
      })
      
      if (!isValid) {
        Sentry.captureMessage('Metrics data validation failed', {
          level: 'warning',
          tags: {
            component: 'UXMetrics',
            action: 'fetchMetrics'
          },
          extra: {
            dataStructure: {
              hasSummary: !!data?.summary,
              hasApps: !!data?.summary?.apps,
              hasMetrics: !!data?.metrics,
              hasThresholds: !!data?.thresholds
            }
          }
        })
      }
      
      setMetrics(sanitizedData)
    } catch (err) {
      setError(err.message)
      
      Sentry.captureException(err, {
        tags: {
          component: 'UXMetrics',
          action: 'fetchMetrics'
        },
        extra: {
          errorMessage: err.message
        }
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (value, threshold, comparison = 'lte') => {
    if (value === null || value === undefined) return 'text-neutral-400'
    
    const passes = comparison === 'lte' 
      ? value <= threshold 
      : value >= threshold
    
    return passes ? 'text-success-600' : 'text-error-600'
  }

  const getStatusBadge = (value, threshold, comparison = 'lte') => {
    if (value === null || value === undefined) {
      return <span className="px-2 py-1 text-xs rounded bg-neutral-200 text-neutral-600">{t('common.na')}</span>
    }
    
    const passes = comparison === 'lte' 
      ? value <= threshold 
      : value >= threshold
    
    return passes 
      ? <span className="px-2 py-1 text-xs rounded bg-success-100 text-success-700">{t('common.pass')}</span>
      : <span className="px-2 py-1 text-xs rounded bg-error-100 text-error-700">{t('common.fail')}</span>
  }

  const formatValue = (value, unit = '') => {
    if (value === null || value === undefined) return t('common.na')
    if (typeof value === 'number') {
      return `${value.toFixed(2)}${unit}`
    }
    return value
  }

  if (loading) {
    return (
      <div className="space-y-8" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        {/* Header Skeleton */}
        <div>
          <Skeleton className="h-7 w-48 mb-2" aria-hidden="true" />
          <Skeleton className="h-5 w-96" aria-hidden="true" />
          <Skeleton className="h-4 w-64 mt-1" aria-hidden="true" />
        </div>

        {/* Summary Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-6">
              <Skeleton className="h-4 w-24 mb-2" aria-hidden="true" />
              <Skeleton className="h-8 w-20" aria-hidden="true" />
            </div>
          ))}
        </div>

        {/* Table Skeleton */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <Skeleton className="h-6 w-32" aria-hidden="true" />
          </div>
          <div className="p-5 space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" aria-hidden="true" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="bg-error-50 border border-error-200 rounded-lg p-4">
          <h3 className="text-error-800 font-semibold">{t('uxMetrics.errorLoading')}</h3>
          <p className="text-error-600 mt-2">{error}</p>
          <button 
            onClick={fetchMetrics}
            className="mt-4 px-4 py-2 bg-error-600 text-white rounded hover:bg-error-700"
          >
            {t('common.retry')}
          </button>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="space-y-8">
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <p className="text-warning-800">{t('uxMetrics.noData')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8" data-testid="ux-metrics">
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)]">{t('uxMetrics.title')}</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          {t('uxMetrics.subtitle')}
        </p>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          {t('uxMetrics.lastUpdated', { date: new Date(metrics.generated_at).toLocaleString() })}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label={t('uxMetrics.totalPRs')}
          value={String(metrics.total_prs)}
          variant="default"
        />

        {metrics.summary.lighthouse && (
          <>
            <StatCard
              label={t('uxMetrics.avgFCP')}
              value={formatValue(metrics.summary.lighthouse.fcp_avg, 'ms')}
              deltaLabel={t('uxMetrics.target', { value: metrics.thresholds.lighthouse.fcp, unit: 'ms' })}
              deltaPositive="neutral"
              variant={metrics.summary.lighthouse.fcp_avg <= metrics.thresholds.lighthouse.fcp ? 'green' : 'red'}
            />

            <StatCard
              label={t('uxMetrics.avgLCP')}
              value={formatValue(metrics.summary.lighthouse.lcp_avg, 'ms')}
              deltaLabel={t('uxMetrics.target', { value: metrics.thresholds.lighthouse.lcp, unit: 'ms' })}
              deltaPositive="neutral"
              variant={metrics.summary.lighthouse.lcp_avg <= metrics.thresholds.lighthouse.lcp ? 'green' : 'red'}
            />
          </>
        )}

        <StatCard
          label={t('uxMetrics.i18nCoverage')}
          value={`${metrics.summary.apps['frontend-dashboard'].i18n_available}/${metrics.total_prs}`}
          deltaLabel={t('uxMetrics.prsWithData')}
          deltaPositive="neutral"
          variant="default"
        />
      </div>

      {/* Thresholds Reference */}
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-primary-900 mb-2">{t('uxMetrics.qualityThresholds')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <span className="font-medium text-primary-800">{t('uxMetrics.i18n')}:</span>
            <span className="text-primary-700 ml-1">≥{metrics.thresholds.i18n.target}%</span>
          </div>
          <div>
            <span className="font-medium text-primary-800">{t('uxMetrics.a11yCritical')}:</span>
            <span className="text-primary-700 ml-1">≤{metrics.thresholds.a11y.critical}</span>
          </div>
          <div>
            <span className="font-medium text-primary-800">{t('uxMetrics.motionP95')}:</span>
            <span className="text-primary-700 ml-1">≤{metrics.thresholds.motion.p95}{t('common.ms')}</span>
          </div>
          <div>
            <span className="font-medium text-primary-800">{t('uxMetrics.vrtMismatch')}:</span>
            <span className="text-primary-700 ml-1">≤{metrics.thresholds.vrt.mismatch}%</span>
          </div>
          <div>
            <span className="font-medium text-primary-800">{t('uxMetrics.lighthouseFCP')}:</span>
            <span className="text-primary-700 ml-1">≤{metrics.thresholds.lighthouse.fcp}{t('common.ms')}</span>
          </div>
        </div>
      </div>

      {/* PR History Table */}
      <SectionCard title={t('uxMetrics.recentPRs')} data-testid="pr-history-table" className="overflow-hidden">
        
        <div className="overflow-x-auto -mx-4">
          <table className="min-w-full divide-y divide-neutral-200">
            <thead className="bg-neutral-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.pr')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.prTitle')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.author')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.merged')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.lighthouseFCP')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.i18nFD')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  {t('uxMetrics.i18nOC')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-neutral-200">
              {metrics.metrics.map((pr) => (
                <tr key={pr.pr} className="hover:bg-neutral-50 dark:hover:bg-neutral-800">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <a 
                      href={pr.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-accent-600 hover:text-accent-800 font-medium"
                    >
                      #{pr.pr}
                    </a>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-neutral-900 dark:text-white max-w-md truncate" title={pr.title}>
                      {pr.title}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-500 dark:text-neutral-400">
                    {pr.author}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-500 dark:text-neutral-400">
                    {new Date(pr.merged_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {pr.lighthouse ? (
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${getStatusColor(pr.lighthouse.fcp, metrics.thresholds.lighthouse.fcp)}`}>
                          {formatValue(pr.lighthouse.fcp, 'ms')}
                        </span>
                        {getStatusBadge(pr.lighthouse.fcp, metrics.thresholds.lighthouse.fcp)}
                      </div>
                    ) : (
                      <span className="text-sm text-neutral-400">{t('common.na')}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {pr.apps['frontend-dashboard']?.i18n ? (
                      pr.apps['frontend-dashboard'].i18n.status === 'parsed' ? (
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-medium ${getStatusColor(pr.apps['frontend-dashboard'].i18n.value, metrics.thresholds.i18n.target, 'gte')}`}>
                            {formatValue(pr.apps['frontend-dashboard'].i18n.value, '%')}
                          </span>
                          {getStatusBadge(pr.apps['frontend-dashboard'].i18n.value, metrics.thresholds.i18n.target, 'gte')}
                        </div>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded bg-success-100 text-success-700">
                          {t('uxMetrics.available')}
                        </span>
                      )
                    ) : (
                      <span className="px-2 py-1 text-xs rounded bg-neutral-200 text-neutral-600">
                        {t('common.na')}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {pr.apps['owner-console']?.i18n ? (
                      pr.apps['owner-console'].i18n.status === 'parsed' ? (
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-medium ${getStatusColor(pr.apps['owner-console'].i18n.value, metrics.thresholds.i18n.target, 'gte')}`}>
                            {formatValue(pr.apps['owner-console'].i18n.value, '%')}
                          </span>
                          {getStatusBadge(pr.apps['owner-console'].i18n.value, metrics.thresholds.i18n.target, 'gte')}
                        </div>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded bg-success-100 text-success-700">
                          {t('uxMetrics.available')}
                        </span>
                      )
                    ) : (
                      <span className="px-2 py-1 text-xs rounded bg-neutral-200 text-neutral-600">
                        {t('common.na')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* App-Specific Metrics with Pass Rates */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {['frontend-dashboard', 'owner-console'].map((app) => (
          <SectionCard 
            key={app} 
            title={app === 'frontend-dashboard' ? t('uxMetrics.frontendDashboard') : t('uxMetrics.ownerConsole')}
            data-testid={`app-metrics-${app}`}
          >
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--text-secondary)]">{t('uxMetrics.i18nCoverage')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.i18n?.avg_coverage !== null && metrics.summary?.apps?.[app]?.i18n?.avg_coverage !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].i18n.avg_coverage, metrics.thresholds.i18n.target, 'gte')}`}>
                      {formatValue(metrics.summary.apps[app].i18n.avg_coverage, '%')}
                    </span>
                  )}
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    ({metrics.summary?.apps?.[app]?.i18n?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                  {metrics.summary?.apps?.[app]?.i18n?.pass_rate !== null && metrics.summary?.apps?.[app]?.i18n?.pass_rate !== undefined && (
                    <span className="text-xs text-success-600">
                      {formatValue(metrics.summary.apps[app].i18n.pass_rate, '% pass')}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--text-secondary)]">{t('uxMetrics.a11yTests')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.a11y?.avg_critical !== null && metrics.summary?.apps?.[app]?.a11y?.avg_critical !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].a11y.avg_critical, metrics.thresholds.a11y.critical)}`}>
                      {t('uxMetrics.critical')}:{formatValue(metrics.summary.apps[app].a11y.avg_critical)}
                    </span>
                  )}
                  {metrics.summary?.apps?.[app]?.a11y?.avg_serious !== null && metrics.summary?.apps?.[app]?.a11y?.avg_serious !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].a11y.avg_serious, metrics.thresholds.a11y.serious)}`}>
                      {t('uxMetrics.serious')}:{formatValue(metrics.summary.apps[app].a11y.avg_serious)}
                    </span>
                  )}
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    ({metrics.summary?.apps?.[app]?.a11y?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--text-secondary)]">{t('uxMetrics.motionTests')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.motion?.avg_p95 !== null && metrics.summary?.apps?.[app]?.motion?.avg_p95 !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].motion.avg_p95, metrics.thresholds.motion.p95)}`}>
                      {formatValue(metrics.summary.apps[app].motion.avg_p95, 'ms')}
                    </span>
                  )}
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    ({metrics.summary?.apps?.[app]?.motion?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-[var(--text-secondary)]">{t('uxMetrics.vrtTests')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.vrt?.avg_mismatch !== null && metrics.summary?.apps?.[app]?.vrt?.avg_mismatch !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].vrt.avg_mismatch, metrics.thresholds.vrt.mismatch)}`}>
                      {formatValue(metrics.summary.apps[app].vrt.avg_mismatch, '%')}
                    </span>
                  )}
                  <span className="text-xs text-neutral-500 dark:text-neutral-400">
                    ({metrics.summary?.apps?.[app]?.vrt?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
            </div>
          </SectionCard>
        ))}
      </div>

      {/* Trend Charts */}
      {metrics.summary.trends && (
        <div className="space-y-8">
          {/* i18n Coverage Trend */}
          {metrics.summary.trends['frontend-dashboard']?.i18n && (
            <SectionCard title={t('uxMetrics.i18nTrend')} data-testid="i18n-trend-chart">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metrics.summary.trends['frontend-dashboard'].i18n.filter(d => d.value !== null)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="pr" label={{ value: 'PR #', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Coverage (%)', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#8b5cf6" name="Frontend Dashboard" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </SectionCard>
          )}

          {/* Lighthouse Performance Trend */}
          {metrics.summary.trends.lighthouse && (
            <SectionCard title={t('uxMetrics.lighthouseTrend')} data-testid="lighthouse-trend-chart">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metrics.summary.trends.lighthouse.filter(d => d.fcp !== null || d.lcp !== null)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="pr" label={{ value: 'PR #', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="fcp" stroke="#10b981" name="FCP" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="lcp" stroke="#f59e0b" name="LCP" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </SectionCard>
          )}

          {/* Bundle Size Trend */}
          {metrics.summary.trends.bundleSize && (
            <SectionCard title={t('uxMetrics.bundleSizeTrend')} data-testid="bundle-size-trend-chart">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={metrics.summary.trends.bundleSize.filter(d => d.change_kb !== null)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="pr" label={{ value: 'PR #', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Change (KB)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="change_kb" fill="#8b5cf6" name="Bundle Size Change" />
                </BarChart>
              </ResponsiveContainer>
              {metrics.summary.bundleSize && (
                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-[var(--text-secondary)]">{t('uxMetrics.avgBundleSize')}:</span>
                    <span className="ml-2 font-medium">{formatValue(metrics.summary.bundleSize.avg_size_kb, ' KB')}</span>
                  </div>
                  <div>
                    <span className="text-[var(--text-secondary)]">{t('uxMetrics.avgChange')}:</span>
                    <span className={`ml-2 font-medium ${metrics.summary.bundleSize.avg_change_kb > 0 ? 'text-error-600' : 'text-success-600'}`}>
                      {metrics.summary.bundleSize.avg_change_kb > 0 ? '+' : ''}{formatValue(metrics.summary.bundleSize.avg_change_kb, ' KB')}
                    </span>
                  </div>
                  <div>
                    <span className="text-[var(--text-secondary)]">{t('uxMetrics.totalChange')}:</span>
                    <span className={`ml-2 font-medium ${metrics.summary.bundleSize.total_change_kb > 0 ? 'text-error-600' : 'text-success-600'}`}>
                      {metrics.summary.bundleSize.total_change_kb > 0 ? '+' : ''}{formatValue(metrics.summary.bundleSize.total_change_kb, ' KB')}
                    </span>
                  </div>
                </div>
              )}
            </SectionCard>
          )}
        </div>
      )}
    </div>
  )
}
