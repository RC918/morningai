/* eslint-disable i18next/no-literal-string */
/* NOTE: This file is exempted from strict i18n checks to maintain PR scope.
 * i18n improvements will be addressed in a dedicated PR (see Issue #1328).
 * This aligns with local ESLint config which already exempts this file.
 */

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@morningai/shared-ui'
import { AppleButton } from '@/components/ui/apple-button'
import { Badge } from '@morningai/shared-ui'
import { Progress } from '@morningai/shared-ui'
import { 
  Cpu, MemoryStick, Zap, Activity, Clock, AlertTriangle, 
  CheckCircle, TrendingUp, TrendingDown, DollarSign 
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

const CPUUsageWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.cpuUsage.title')}</CardTitle>
        <Cpu className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.cpu_usage || 0}%</div>
        <Progress value={data?.system_metrics?.cpu_usage || 0} className="mt-2" />
        <p className="text-xs text-muted-foreground mt-2">
          {(data?.system_metrics?.cpu_usage || 0) > 80 ? (
            <span className="text-error-600 flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              {t('widgets.cpuUsage.needsAttention')}
            </span>
          ) : (
            <span className="text-success-600 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              {t('widgets.cpuUsage.normalRange')}
            </span>
          )}
        </p>
      </CardContent>
    </Card>
  )
}


const MemoryUsageWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.memoryUsage.title')}</CardTitle>
        <MemoryStick className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.memory_usage || 0}%</div>
        <Progress value={data?.system_metrics?.memory_usage || 0} className="mt-2" />
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-success-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.memoryUsage.comparedYesterday', { percent: 5 })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}


const ResponseTimeWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.responseTime.title')}</CardTitle>
        <Zap className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.response_time || 0}{t('common.units.milliseconds')}</div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-success-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.responseTime.comparedYesterday', { percent: 12 })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}


const ErrorRateWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.errorRate.title')}</CardTitle>
        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {((data?.system_metrics?.error_rate || 0) * 100).toFixed(2)}%
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-success-600 flex items-center">
            <CheckCircle className="w-3 h-3 mr-1" />
            {t('widgets.errorRate.systemStable')}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}

const ActiveStrategiesWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('widgets.activeStrategies.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-primary-500">
          {data?.system_metrics?.active_strategies || 0}
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-600 mt-2">
          {t('widgets.activeStrategies.running', { count: data?.system_metrics?.active_strategies || 0 })}
        </p>
      </CardContent>
    </Card>
  )
}

const PendingApprovalsWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('widgets.pendingApprovals.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-warning-500">
          {data?.system_metrics?.pending_approvals || 0}
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-600 mt-2">
          {t('widgets.pendingApprovals.waiting', { count: data?.system_metrics?.pending_approvals || 0 })}
        </p>
      </CardContent>
    </Card>
  )
}

const CostTodayWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.costToday.title')}</CardTitle>
        <DollarSign className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">${data?.system_metrics?.cost_today || 0}</div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-success-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.costToday.saved', { amount: '123.45' })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}

const CircuitBreakersWidget= ({ data }: { data: any }) => {
  const { t } = useTranslation()
  let circuitBreakersArray = []
  
  try {
    const circuitBreakers = data?.circuit_breakers
    
    if (!circuitBreakers) {
      circuitBreakersArray = []
    }
    else if (Array.isArray(circuitBreakers)) {
      circuitBreakersArray = circuitBreakers.filter(cb => cb && typeof cb === 'object')
    }
    else if (typeof circuitBreakers === 'object') {
      circuitBreakersArray = Object.entries(circuitBreakers)
        .filter(([key, value]) => key && value !== null && value !== undefined)
        .map(([name, state]: [string, any]) => ({
          name: String(name),
          state: typeof state === 'string' ? state : 
                 (state?.state && typeof state.state === 'string' ? state.state : 'unknown')
        }))
    }
    else {
      console.warn('Invalid circuit_breakers data type:', typeof circuitBreakers, circuitBreakers)
      circuitBreakersArray = []
    }
  } catch (error) {
    console.error('Error processing circuit breakers data:', error)
    circuitBreakersArray = []
    
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        tags: { section: 'widget_library', widget: 'circuit_breakers' },
        extra: { data: data?.circuit_breakers }
      })
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('widgets.circuitBreakers.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {circuitBreakersArray.map((cb, index) => (
            <div key={`cb-${index}-${cb?.name || 'unknown'}`} className="flex items-center justify-between p-2 border rounded">
              <span className="text-sm dark:text-white">{cb?.name || `Circuit ${index + 1}`}</span>
              <Badge variant={cb?.state === 'closed' ? 'default' : 'destructive'}>
                {cb?.state === 'closed' ? t('widgets.circuitBreakers.normal') : 
                 cb?.state === 'open' ? t('widgets.circuitBreakers.open') : 
                 cb?.state === 'half-open' ? t('widgets.circuitBreakers.halfOpen') : t('widgets.circuitBreakers.unknown')}
              </Badge>
            </div>
          ))}
          {circuitBreakersArray.length === 0 && (
            <div className="col-span-2 text-center text-neutral-600 dark:text-neutral-600 py-4">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-success-500" />
              <p className="text-sm">{t('widgets.circuitBreakers.allNormal')}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


const PerformanceTrendWidget = ({ data }: { data: any }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('widgets.performanceTrend.title')}</CardTitle>
        <p className="text-sm text-neutral-600 dark:text-neutral-600">{t('widgets.performanceTrend.description')}</p>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data?.performance_data || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="cpu" 
              stroke="var(--color-primary, #007AFF)" 
              strokeWidth={2}
              name={t('widgets.performanceTrend.cpuLabel')}
            />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="var(--color-success, #10b981)" 
              strokeWidth={2}
              name={t('widgets.performanceTrend.memoryLabel')}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

export const WidgetLibrary = {
  cpu_usage: CPUUsageWidget,
  memory_usage: MemoryUsageWidget,
  response_time: ResponseTimeWidget,
  error_rate: ErrorRateWidget,
  active_strategies: ActiveStrategiesWidget,
  pending_approvals: PendingApprovalsWidget,
  cost_today: CostTodayWidget,
  circuit_breakers: CircuitBreakersWidget,
  performance_trend: PerformanceTrendWidget
}

const UnknownWidgetComponent = ({ widgetId }: { widgetId: string }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center text-neutral-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{t('feedback.unknownWidgetType', { widgetId })}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export const getWidgetComponent = (widgetId: string) => {
  return WidgetLibrary[widgetId as keyof typeof WidgetLibrary] || (() => <UnknownWidgetComponent widgetId={widgetId} />)
}
