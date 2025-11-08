import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

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
      setMetrics(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (value, threshold, comparison = 'lte') => {
    if (value === null || value === undefined) return 'text-gray-400'
    
    const passes = comparison === 'lte' 
      ? value <= threshold 
      : value >= threshold
    
    return passes ? 'text-green-600' : 'text-red-600'
  }

  const getStatusBadge = (value, threshold, comparison = 'lte') => {
    if (value === null || value === undefined) {
      return <span className="px-2 py-1 text-xs rounded bg-gray-200 text-gray-600">{t('common.na')}</span>
    }
    
    const passes = comparison === 'lte' 
      ? value <= threshold 
      : value >= threshold
    
    return passes 
      ? <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">{t('common.pass')}</span>
      : <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-700">{t('common.fail')}</span>
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
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold">{t('uxMetrics.errorLoading')}</h3>
          <p className="text-red-600 mt-2">{error}</p>
          <button 
            onClick={fetchMetrics}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            {t('common.retry')}
          </button>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">{t('uxMetrics.noData')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t('uxMetrics.title')}</h1>
        <p className="text-gray-600 mt-2">
          {t('uxMetrics.subtitle')}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          {t('uxMetrics.lastUpdated', { date: new Date(metrics.generated_at).toLocaleString() })}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase">{t('uxMetrics.totalPRs')}</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">{metrics.total_prs}</p>
        </div>

        {metrics.summary.lighthouse && (
          <>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">{t('uxMetrics.avgFCP')}</h3>
              <p className={`text-3xl font-bold mt-2 ${getStatusColor(metrics.summary.lighthouse.fcp_avg, metrics.thresholds.lighthouse.fcp)}`}>
                {formatValue(metrics.summary.lighthouse.fcp_avg, 'ms')}
              </p>
              <p className="text-xs text-gray-500 mt-1">{t('uxMetrics.target', { value: metrics.thresholds.lighthouse.fcp, unit: 'ms' })}</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">{t('uxMetrics.avgLCP')}</h3>
              <p className={`text-3xl font-bold mt-2 ${getStatusColor(metrics.summary.lighthouse.lcp_avg, metrics.thresholds.lighthouse.lcp)}`}>
                {formatValue(metrics.summary.lighthouse.lcp_avg, 'ms')}
              </p>
              <p className="text-xs text-gray-500 mt-1">{t('uxMetrics.target', { value: metrics.thresholds.lighthouse.lcp, unit: 'ms' })}</p>
            </div>
          </>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase">{t('uxMetrics.i18nCoverage')}</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {metrics.summary.apps['frontend-dashboard'].i18n_available}/{metrics.total_prs}
          </p>
          <p className="text-xs text-gray-500 mt-1">{t('uxMetrics.prsWithData')}</p>
        </div>
      </div>

      {/* Thresholds Reference */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">{t('uxMetrics.qualityThresholds')}</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <span className="font-medium text-blue-800">{t('uxMetrics.i18n')}:</span>
            <span className="text-blue-700 ml-1">≥{metrics.thresholds.i18n.target}%</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">{t('uxMetrics.a11yCritical')}:</span>
            <span className="text-blue-700 ml-1">≤{metrics.thresholds.a11y.critical}</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">{t('uxMetrics.motionP95')}:</span>
            <span className="text-blue-700 ml-1">≤{metrics.thresholds.motion.p95}{t('common.ms')}</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">{t('uxMetrics.vrtMismatch')}:</span>
            <span className="text-blue-700 ml-1">≤{metrics.thresholds.vrt.mismatch}%</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">{t('uxMetrics.lighthouseFCP')}:</span>
            <span className="text-blue-700 ml-1">≤{metrics.thresholds.lighthouse.fcp}{t('common.ms')}</span>
          </div>
        </div>
      </div>

      {/* PR History Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">{t('uxMetrics.recentPRs')}</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.pr')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.prTitle')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.author')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.merged')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.lighthouseFCP')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.i18nFD')}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {t('uxMetrics.i18nOC')}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {metrics.metrics.map((pr) => (
                <tr key={pr.pr} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <a 
                      href={pr.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-purple-600 hover:text-purple-800 font-medium"
                    >
                      #{pr.pr}
                    </a>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-md truncate" title={pr.title}>
                      {pr.title}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {pr.author}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
                      <span className="text-sm text-gray-400">{t('common.na')}</span>
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
                        <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">
                          {t('uxMetrics.available')}
                        </span>
                      )
                    ) : (
                      <span className="px-2 py-1 text-xs rounded bg-gray-200 text-gray-600">
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
                        <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">
                          {t('uxMetrics.available')}
                        </span>
                      )
                    ) : (
                      <span className="px-2 py-1 text-xs rounded bg-gray-200 text-gray-600">
                        {t('common.na')}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* App-Specific Metrics with Pass Rates */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {['frontend-dashboard', 'owner-console'].map((app) => (
          <div key={app} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {app === 'frontend-dashboard' ? t('uxMetrics.frontendDashboard') : t('uxMetrics.ownerConsole')}
            </h3>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('uxMetrics.i18nCoverage')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.i18n?.avg_coverage !== null && metrics.summary?.apps?.[app]?.i18n?.avg_coverage !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].i18n.avg_coverage, metrics.thresholds.i18n.target, 'gte')}`}>
                      {formatValue(metrics.summary.apps[app].i18n.avg_coverage, '%')}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    ({metrics.summary?.apps?.[app]?.i18n?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                  {metrics.summary?.apps?.[app]?.i18n?.pass_rate !== null && metrics.summary?.apps?.[app]?.i18n?.pass_rate !== undefined && (
                    <span className="text-xs text-green-600">
                      {formatValue(metrics.summary.apps[app].i18n.pass_rate, '% pass')}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('uxMetrics.a11yTests')}</span>
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
                  <span className="text-xs text-gray-500">
                    ({metrics.summary?.apps?.[app]?.a11y?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('uxMetrics.motionTests')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.motion?.avg_p95 !== null && metrics.summary?.apps?.[app]?.motion?.avg_p95 !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].motion.avg_p95, metrics.thresholds.motion.p95)}`}>
                      {formatValue(metrics.summary.apps[app].motion.avg_p95, 'ms')}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    ({metrics.summary?.apps?.[app]?.motion?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{t('uxMetrics.vrtTests')}</span>
                <div className="flex items-center gap-2">
                  {metrics.summary?.apps?.[app]?.vrt?.avg_mismatch !== null && metrics.summary?.apps?.[app]?.vrt?.avg_mismatch !== undefined && (
                    <span className={`text-sm font-medium ${getStatusColor(metrics.summary.apps[app].vrt.avg_mismatch, metrics.thresholds.vrt.mismatch)}`}>
                      {formatValue(metrics.summary.apps[app].vrt.avg_mismatch, '%')}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    ({metrics.summary?.apps?.[app]?.vrt?.parsed || 0}/{metrics.summary?.apps?.[app]?.total_prs || 0})
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Trend Charts */}
      {metrics.summary.trends && (
        <div className="mt-8 space-y-8">
          {/* i18n Coverage Trend */}
          {metrics.summary.trends['frontend-dashboard']?.i18n && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('uxMetrics.i18nTrend')}</h3>
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
            </div>
          )}

          {/* Lighthouse Performance Trend */}
          {metrics.summary.trends.lighthouse && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('uxMetrics.lighthouseTrend')}</h3>
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
            </div>
          )}

          {/* Bundle Size Trend */}
          {metrics.summary.trends.bundleSize && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('uxMetrics.bundleSizeTrend')}</h3>
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
                    <span className="text-gray-600">{t('uxMetrics.avgBundleSize')}:</span>
                    <span className="ml-2 font-medium">{formatValue(metrics.summary.bundleSize.avg_size_kb, ' KB')}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">{t('uxMetrics.avgChange')}:</span>
                    <span className={`ml-2 font-medium ${metrics.summary.bundleSize.avg_change_kb > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {metrics.summary.bundleSize.avg_change_kb > 0 ? '+' : ''}{formatValue(metrics.summary.bundleSize.avg_change_kb, ' KB')}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">{t('uxMetrics.totalChange')}:</span>
                    <span className={`ml-2 font-medium ${metrics.summary.bundleSize.total_change_kb > 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {metrics.summary.bundleSize.total_change_kb > 0 ? '+' : ''}{formatValue(metrics.summary.bundleSize.total_change_kb, ' KB')}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
