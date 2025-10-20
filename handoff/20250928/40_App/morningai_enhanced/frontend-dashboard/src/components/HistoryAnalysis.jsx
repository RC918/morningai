import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  TrendingUp, 
  TrendingDown,
  Activity,
  Calendar,
  BarChart3,
  Clock
} from 'lucide-react'
import { EmptyState, ErrorRecovery } from '@/components/feedback'
import { Skeleton } from '@/components/ui/skeleton'

const HistoryAnalysis = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  
  const mockHistory = [
    {
      id: 1,
      date: '2024-01-15',
      type: 'optimization',
      title: 'CPU 優化執行',
      impact: 'positive',
      metrics: { cpu: -25, responseTime: -30 },
      status: 'completed'
    },
    {
      id: 2,
      date: '2024-01-14',
      type: 'scaling',
      title: '自動擴容事件',
      impact: 'positive',
      metrics: { instances: +2, cost: +18.5 },
      status: 'completed'
    },
    {
      id: 3,
      date: '2024-01-13',
      type: 'alert',
      title: '記憶體使用率警告',
      impact: 'neutral',
      metrics: { memory: 78 },
      status: 'resolved'
    }
  ]

  const getImpactIcon = (impact) => {
    switch (impact) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-600" />
      default:
        return <Activity className="w-4 h-4 text-gray-600" />
    }
  }

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'positive':
        return 'bg-green-100 text-green-800'
      case 'negative':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }
  
  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true)
        setError(null)
        await new Promise(resolve => setTimeout(resolve, 500))
        setHistory(mockHistory)
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }
    
    loadHistory()
  }, [])
  
  const handleRetry = () => {
    setError(null)
    setLoading(true)
    setTimeout(() => {
      setHistory(mockHistory)
      setLoading(false)
    }, 500)
  }
  
  if (loading) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="w-full">
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
            <Skeleton className="h-10 w-full sm:w-[180px]" />
            <Skeleton className="h-10 w-full sm:w-32" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <ErrorRecovery error={error} onRetry={handleRetry} />
      </div>
    )
  }
  
  if (history.length === 0) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <EmptyState
          icon={Activity}
          title="尚無歷史記錄"
          description="系統還沒有任何歷史事件記錄。當系統開始運行後，您將在這裡看到所有的歷史分析數據。"
        />
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">歷史分析</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">查看系統運行歷史與趨勢分析</p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <Select defaultValue="7d">
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">過去 24 小時</SelectItem>
              <SelectItem value="7d">過去 7 天</SelectItem>
              <SelectItem value="30d">過去 30 天</SelectItem>
              <SelectItem value="90d">過去 90 天</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="w-full sm:w-auto">
            <Calendar className="w-4 h-4 mr-2" />
            自訂範圍
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總事件</p>
                <p className="text-2xl font-bold text-gray-900">156</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">優化執行</p>
                <p className="text-2xl font-bold text-gray-900">23</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">警告事件</p>
                <p className="text-2xl font-bold text-gray-900">8</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均響應時間</p>
                <p className="text-2xl font-bold text-gray-900">245ms</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>事件時間軸</CardTitle>
          <CardDescription>按時間順序查看所有系統事件</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {history.map((event) => (
              <div
                key={event.id}
                className="flex items-start gap-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="p-2 bg-gray-100 rounded-lg">
                  {getImpactIcon(event.impact)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-gray-900">{event.title}</h3>
                    <Badge className={getImpactColor(event.impact)}>
                      {event.impact === 'positive' ? '正面影響' :
                       event.impact === 'negative' ? '負面影響' : '中性'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{event.date}</p>
                  <div className="flex items-center gap-3">
                    {Object.entries(event.metrics).map(([key, value]) => (
                      <Badge key={key} variant="outline" className="text-xs">
                        {key}: {value > 0 ? '+' : ''}{value}{typeof value === 'number' && value < 100 ? '%' : ''}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  查看詳情
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default HistoryAnalysis
