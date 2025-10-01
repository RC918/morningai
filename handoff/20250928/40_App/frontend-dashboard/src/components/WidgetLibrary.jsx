import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Cpu, MemoryStick, Zap, Activity, Clock, AlertTriangle, 
  CheckCircle, TrendingUp, TrendingDown, DollarSign 
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

export const WidgetLibrary = {
  cpu_usage: ({ data }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
        <Cpu className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.cpu_usage || 0}%</div>
        <Progress value={data?.system_metrics?.cpu_usage || 0} className="mt-2" />
        <p className="text-xs text-muted-foreground mt-2">
          {(data?.system_metrics?.cpu_usage || 0) > 80 ? (
            <span className="text-red-600 flex items-center">
              <TrendingUp className="w-3 h-3 mr-1" />
              需要關注
            </span>
          ) : (
            <span className="text-green-600 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              正常範圍
            </span>
          )}
        </p>
      </CardContent>
    </Card>
  ),
  
  memory_usage: ({ data }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">內存使用率</CardTitle>
        <MemoryStick className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.memory_usage || 0}%</div>
        <Progress value={data?.system_metrics?.memory_usage || 0} className="mt-2" />
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            較昨日 -5%
          </span>
        </p>
      </CardContent>
    </Card>
  ),
  
  response_time: ({ data }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">響應時間</CardTitle>
        <Zap className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{data?.system_metrics?.response_time || 0}ms</div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            較昨日 -12%
          </span>
        </p>
      </CardContent>
    </Card>
  ),
  
  error_rate: ({ data }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">錯誤率</CardTitle>
        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {((data?.system_metrics?.error_rate || 0) * 100).toFixed(2)}%
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-green-600 flex items-center">
            <CheckCircle className="w-3 h-3 mr-1" />
            系統運行穩定
          </span>
        </p>
      </CardContent>
    </Card>
  ),
  
  active_strategies: ({ data }) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">活躍策略</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-blue-600">
          {data?.system_metrics?.active_strategies || 0}
        </div>
        <p className="text-sm text-gray-600 mt-2">個策略正在運行</p>
      </CardContent>
    </Card>
  ),
  
  pending_approvals: ({ data }) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">待審批</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-orange-600">
          {data?.system_metrics?.pending_approvals || 0}
        </div>
        <p className="text-sm text-gray-600 mt-2">個決策等待審批</p>
      </CardContent>
    </Card>
  ),
  
  cost_today: ({ data }) => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">今日成本</CardTitle>
        <DollarSign className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">${data?.system_metrics?.cost_today || 0}</div>
        <p className="text-xs text-muted-foreground mt-2">
          <span className="text-green-600 flex items-center">
            <TrendingDown className="w-3 h-3 mr-1" />
            節省 $123.45
          </span>
        </p>
      </CardContent>
    </Card>
  ),
  
  task_execution: ({ data }) => (
    <Card>
      <CardHeader>
        <CardTitle>任務執行狀態</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {(data?.task_execution?.recent_tasks || []).map((task, index) => (
            <div key={index} className="flex items-center justify-between p-2 border rounded">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <div>
                  <span className="text-sm font-medium">{task.name}</span>
                  <p className="text-xs text-gray-500">{task.agent} • {task.duration}</p>
                </div>
              </div>
              <Badge variant={
                task.status === 'completed' ? 'default' : 
                task.status === 'running' ? 'secondary' : 'outline'
              }>
                {task.status === 'completed' ? '已完成' : 
                 task.status === 'running' ? '運行中' : '待處理'}
              </Badge>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-bold">{data?.task_execution?.total_tasks_today || 0}</div>
              <div className="text-xs text-gray-500">今日任務</div>
            </div>
            <div>
              <div className="text-lg font-bold text-green-600">
                {((data?.task_execution?.success_rate || 0) * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">成功率</div>
            </div>
            <div>
              <div className="text-lg font-bold">{data?.task_execution?.avg_duration || '0s'}</div>
              <div className="text-xs text-gray-500">平均時長</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  ),
  
  circuit_breakers: ({ data }) => {
    const circuitBreakers = data?.circuit_breakers || {}
    let circuitBreakersArray = []
    
    try {
      if (Array.isArray(circuitBreakers)) {
        circuitBreakersArray = circuitBreakers
      } else if (circuitBreakers && typeof circuitBreakers === 'object') {
        circuitBreakersArray = Object.entries(circuitBreakers).map(([name, state]) => ({ 
          name, 
          state: typeof state === 'string' ? state : (state?.state || 'unknown')
        }))
      }
    } catch (error) {
      console.warn('Error processing circuit breakers data:', error)
      circuitBreakersArray = []
    }
    
    return (
      <Card>
        <CardHeader>
          <CardTitle>熔斷器狀態</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {circuitBreakersArray.map((cb, index) => (
              <div key={index} className="flex items-center justify-between p-2 border rounded">
                <span className="text-sm">{cb?.name || `Circuit ${index + 1}`}</span>
                <Badge variant={cb?.state === 'closed' ? 'default' : 'destructive'}>
                  {cb?.state === 'closed' ? '正常' : 
                   cb?.state === 'open' ? '開啟' : 
                   cb?.state === 'half-open' ? '半開' : '未知'}
                </Badge>
              </div>
            ))}
            {circuitBreakersArray.length === 0 && (
              <div className="col-span-2 text-center text-gray-500 py-4">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                <p className="text-sm">所有熔斷器運行正常</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    )
  },
  
  performance_trend: ({ data }) => (
    <Card>
      <CardHeader>
        <CardTitle>性能趨勢</CardTitle>
        <p className="text-sm text-gray-600">過去6小時的系統性能指標</p>
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
              name="CPU (%)"
            />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="#10b981" 
              strokeWidth={2}
              name="內存 (%)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

export const getWidgetComponent = (widgetId) => {
  return WidgetLibrary[widgetId] || (() => (
    <Card>
      <CardContent className="p-6">
        <div className="text-center text-gray-500">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>未知的組件類型: {widgetId}</p>
        </div>
      </CardContent>
    </Card>
  ))
}
