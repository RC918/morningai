import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Cpu, MemoryStick, Zap, Activity, Clock, AlertTriangle, 
  CheckCircle, TrendingUp, TrendingDown, DollarSign 
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

const CPUUsageWidget = ({ data }) => {
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
            <span className="text-red-600 flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              {t('widgets.cpuUsage.needsAttention')}
            </span>
          ) : (
            <span className="text-green-600 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              {t('widgets.cpuUsage.normalRange')}
            </span>
          )}
        </p>
      </CardContent>
    </Card>
  )
}


const MemoryUsageWidget = ({ data }) => {
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
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.memoryUsage.comparedYesterday', { percent: 5 })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}


const ResponseTimeWidget = ({ data }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{t('widgets.responseTime.title')}</CardTitle>
        <Zap className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.response_time || 0}ms</div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.responseTime.comparedYesterday', { percent: 12 })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}


const ErrorRateWidget = ({ data }) => {
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
          <span className="text-green-600 flex items-center">
            <CheckCircle className="w-3 h-3 mr-1" />
            {t('widgets.errorRate.systemStable')}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}

const ActiveStrategiesWidget = ({ data }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('widgets.activeStrategies.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-blue-600">
          {data?.system_metrics?.active_strategies || 0}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-600 mt-2">
          {t('widgets.activeStrategies.running', { count: data?.system_metrics?.active_strategies || 0 })}
        </p>
      </CardContent>
    </Card>
  )
}

const PendingApprovalsWidget = ({ data }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{t('widgets.pendingApprovals.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-orange-600">
          {data?.system_metrics?.pending_approvals || 0}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-600 mt-2">
          {t('widgets.pendingApprovals.waiting', { count: data?.system_metrics?.pending_approvals || 0 })}
        </p>
      </CardContent>
    </Card>
  )
}

const CostTodayWidget = ({ data }) => {
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
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            {t('widgets.costToday.saved', { amount: '123.45' })}
          </span>
        </p>
      </CardContent>
    </Card>
  )
}


const TaskExecutionWidget = ({ data }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('widgets.taskExecution.title')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {(Array.isArray(data?.task_execution?.recent_tasks) ? data.task_execution.recent_tasks : []).map((task, index) => (
            <div key={index} className="flex items-center justify-between p-2 border rounded">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <div>
                  <span className="text-sm font-medium">{task?.name || 'Unknown Task'}</span>
                  <p className="text-xs text-gray-600 dark:text-gray-600">{task?.agent || 'Unknown'} • {task?.duration || 'N/A'}</p>
                </div>
              </div>
              <Badge variant={
                task?.status === 'completed' ? 'default' : 
                task?.status === 'running' ? 'secondary' : 'outline'
              }>
                {task?.status === 'completed' ? t('widgets.taskExecution.completed') : 
                 task?.status === 'running' ? t('widgets.taskExecution.running') : t('widgets.taskExecution.pending')}
              </Badge>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-bold dark:text-white">{data?.task_execution?.total_tasks_today || 0}</div>
              <div className="text-xs text-gray-600 dark:text-gray-600">{t('widgets.taskExecution.todayTasks')}</div>
            </div>
            <div>
              <div className="text-lg font-bold text-green-600">
                {((data?.task_execution?.success_rate || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-600">{t('widgets.taskExecution.successRate')}</div>
            </div>
            <div>
              <div className="text-lg font-bold dark:text-white">{data?.task_execution?.avg_duration || '0s'}</div>
              <div className="text-xs text-gray-600 dark:text-gray-600">{t('widgets.taskExecution.avgDuration')}</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


const CircuitBreakersWidget = ({ data }) => {
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
        .map(([name, state]) => ({
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
            <div className="col-span-2 text-center text-gray-600 dark:text-gray-600 py-4">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="text-sm">{t('widgets.circuitBreakers.allNormal')}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


const PerformanceTrendWidget = ({ data }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('widgets.performanceTrend.title')}</CardTitle>
        <p className="text-sm text-gray-600 dark:text-gray-600">{t('widgets.performanceTrend.description')}</p>
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
              stroke="#3b82f6" 
              strokeWidth={2}
              name={t('widgets.performanceTrend.cpuLabel')}
            />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="#10b981" 
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
  task_execution: TaskExecutionWidget,
  circuit_breakers: CircuitBreakersWidget,
  performance_trend: PerformanceTrendWidget
}

const UnknownWidgetComponent = ({ widgetId }) => {
  const { t } = useTranslation()
  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center text-gray-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{t('feedback.unknownWidgetType', { widgetId })}</p>
        </div>
      </CardContent>
    </Card>
  )
}

export const getWidgetComponent = (widgetId) => {
  return WidgetLibrary[widgetId] || (() => <UnknownWidgetComponent widgetId={widgetId} />)
}
