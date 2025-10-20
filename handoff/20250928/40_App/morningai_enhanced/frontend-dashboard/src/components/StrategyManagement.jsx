import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Settings, 
  Plus, 
  Zap, 
  Clock, 
  CheckCircle,
  AlertCircle 
} from 'lucide-react'
import { EmptyState, ErrorRecovery } from '@/components/feedback'
import { Skeleton } from '@/components/ui/skeleton'

const StrategyManagement = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [strategies, setStrategies] = useState([])
  
  const mockStrategies = [
    {
      id: 1,
      name: 'CPU 優化策略',
      description: '當 CPU 使用率超過 85% 時自動擴容',
      status: 'active',
      triggers: 3,
      lastExecuted: '2 小時前'
    },
    {
      id: 2,
      name: '數據庫連接池優化',
      description: '自動調整連接池大小以應對高並發',
      status: 'active',
      triggers: 8,
      lastExecuted: '30 分鐘前'
    },
    {
      id: 3,
      name: '緩存預熱策略',
      description: '定期預熱熱門數據緩存',
      status: 'paused',
      triggers: 0,
      lastExecuted: '3 天前'
    }
  ]

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'paused':
        return 'bg-gray-100 text-gray-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'paused':
        return <Clock className="w-4 h-4 text-gray-600" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      default:
        return <Settings className="w-4 h-4 text-gray-600" />
    }
  }
  
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        setLoading(true)
        setError(null)
        await new Promise(resolve => setTimeout(resolve, 500))
        setStrategies(mockStrategies)
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }
    
    loadStrategies()
  }, [])
  
  const handleRetry = () => {
    setError(null)
    setLoading(true)
    setTimeout(() => {
      setStrategies(mockStrategies)
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
          <Skeleton className="h-10 w-full sm:w-32" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
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
  
  if (strategies.length === 0) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <EmptyState
          icon={Settings}
          title="尚無策略"
          description="您還沒有建立任何自動化策略。點擊下方按鈕開始建立您的第一個策略。"
          actionLabel="新增策略"
        />
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">策略管理</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">管理與設定自動化策略</p>
        </div>
        <Button className="flex items-center gap-2 w-full sm:w-auto">
          <Plus className="w-4 h-4" />
          新增策略
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">啟用策略</p>
                <p className="text-2xl font-bold text-gray-900">
                  {strategies.filter(s => s.status === 'active').length}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">總觸發次數</p>
                <p className="text-2xl font-bold text-gray-900">
                  {strategies.reduce((sum, s) => sum + s.triggers, 0)}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Zap className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">暫停策略</p>
                <p className="text-2xl font-bold text-gray-900">
                  {strategies.filter(s => s.status === 'paused').length}
                </p>
              </div>
              <div className="p-3 bg-gray-100 rounded-lg">
                <Clock className="w-6 h-6 text-gray-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>策略列表</CardTitle>
          <CardDescription>查看和管理所有自動化策略</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {strategies.map((strategy) => (
              <div
                key={strategy.id}
                className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 sm:p-4 border rounded-lg hover:bg-gray-50 transition-colors gap-3"
              >
                <div className="flex items-start gap-3 sm:gap-4 w-full sm:w-auto">
                  <div className="mt-1">{getStatusIcon(strategy.status)}</div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-sm sm:text-base">{strategy.name}</h3>
                    <p className="text-xs sm:text-sm text-gray-600 mt-1">{strategy.description}</p>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mt-2">
                      <Badge variant="outline" className="text-xs">
                        觸發 {strategy.triggers} 次
                      </Badge>
                      <span className="text-xs text-gray-500">
                        最後執行: {strategy.lastExecuted}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  <Badge className={getStatusColor(strategy.status)}>
                    {strategy.status === 'active' ? '啟用中' : 
                     strategy.status === 'paused' ? '已暫停' : '錯誤'}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default StrategyManagement
