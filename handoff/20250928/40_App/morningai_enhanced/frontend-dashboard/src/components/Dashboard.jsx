import { useState, useEffect } from 'react'
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  DollarSign,
  Cpu,
  MemoryStick,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import CloudStatus from './CloudStatus'
import config from '../config'

const Dashboard = () => {
  const [systemMetrics, setSystemMetrics] = useState({
    cpu_usage: 72,
    memory_usage: 68,
    response_time: 145,
    error_rate: 0.02,
    active_strategies: 12,
    pending_approvals: 3,
    cost_today: 45.67,
    cost_saved: 123.45
  })

  const [recentDecisions, setRecentDecisions] = useState([
    {
      id: 1,
      timestamp: '2024-01-01T14:30:00Z',
      strategy: 'CPU優化策略',
      status: 'executed',
      impact: '+15% 性能提升',
      confidence: 0.87
    },
    {
      id: 2,
      timestamp: '2024-01-01T14:15:00Z',
      strategy: '緩存優化',
      status: 'pending',
      impact: '預計 +20% 響應速度',
      confidence: 0.92
    },
    {
      id: 3,
      timestamp: '2024-01-01T14:00:00Z',
      strategy: '自動擴容',
      status: 'executed',
      impact: '處理能力 +50%',
      confidence: 0.78
    }
  ])

  const [performanceData, setPerformanceData] = useState([
    { time: '12:00', cpu: 65, memory: 60, response_time: 120 },
    { time: '12:30', cpu: 70, memory: 65, response_time: 135 },
    { time: '13:00', cpu: 75, memory: 70, response_time: 150 },
    { time: '13:30', cpu: 72, memory: 68, response_time: 145 },
    { time: '14:00', cpu: 68, memory: 65, response_time: 130 },
    { time: '14:30', cpu: 72, memory: 68, response_time: 145 }
  ])

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${config.apiBaseUrl}/api/system/metrics`)
        if (response.ok) {
          const data = await response.json()
          setSystemMetrics(data)
        }
      } catch (error) {
        console.error('Failed to fetch system metrics:', error)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 10000) // Update every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'executed': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'executed': return <CheckCircle className="w-4 h-4" />
      case 'pending': return <Clock className="w-4 h-4" />
      case 'failed': return <AlertTriangle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 頁面標題 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">系統監控儀表板</h1>
        <p className="text-gray-600 mt-2">Morning AI 智能決策系統實時狀態</p>
      </div>

      {/* 關鍵指標卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU 使用率</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.cpu_usage}%</div>
            <Progress value={systemMetrics.cpu_usage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {systemMetrics.cpu_usage > 80 ? (
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

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">內存使用率</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.memory_usage}%</div>
            <Progress value={systemMetrics.memory_usage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              <span className="text-green-600 flex items-center">
                <TrendingDown className="w-3 h-3 mr-1" />
                較昨日 -5%
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">響應時間</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.response_time}ms</div>
            <p className="text-xs text-muted-foreground mt-2">
              <span className="text-green-600 flex items-center">
                <TrendingDown className="w-3 h-3 mr-1" />
                較昨日 -12%
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">今日成本</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${systemMetrics.cost_today}</div>
            <p className="text-xs text-muted-foreground mt-2">
              <span className="text-green-600 flex items-center">
                <TrendingDown className="w-3 h-3 mr-1" />
                節省 ${systemMetrics.cost_saved}
              </span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 圖表區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 性能趨勢圖 */}
        <Card>
          <CardHeader>
            <CardTitle>性能趨勢</CardTitle>
            <CardDescription>過去6小時的系統性能指標</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
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

        {/* 響應時間圖 */}
        <Card>
          <CardHeader>
            <CardTitle>響應時間趨勢</CardTitle>
            <CardDescription>系統響應時間變化</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="response_time" 
                  stroke="#f59e0b" 
                  fill="#fef3c7"
                  name="響應時間 (ms)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 最近決策 */}
      <Card>
        <CardHeader>
          <CardTitle>最近決策</CardTitle>
          <CardDescription>AI系統最近執行的決策和策略</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentDecisions.map((decision) => (
              <div key={decision.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-full ${getStatusColor(decision.status)}`}>
                    {getStatusIcon(decision.status)}
                  </div>
                  <div>
                    <h4 className="font-medium">{decision.strategy}</h4>
                    <p className="text-sm text-gray-600">{decision.impact}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(decision.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="outline" className={getStatusColor(decision.status)}>
                    {decision.status === 'executed' ? '已執行' : 
                     decision.status === 'pending' ? '待審批' : '失敗'}
                  </Badge>
                  <p className="text-sm text-gray-600 mt-1">
                    信心度: {(decision.confidence * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 雲端服務狀態 */}
      <CloudStatus />

      {/* 系統狀態摘要 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">活躍策略</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {systemMetrics.active_strategies}
            </div>
            <p className="text-sm text-gray-600 mt-2">個策略正在運行</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">待審批</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {systemMetrics.pending_approvals}
            </div>
            <p className="text-sm text-gray-600 mt-2">個決策等待審批</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">錯誤率</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {(systemMetrics.error_rate * 100).toFixed(2)}%
            </div>
            <p className="text-sm text-gray-600 mt-2">系統運行穩定</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard

