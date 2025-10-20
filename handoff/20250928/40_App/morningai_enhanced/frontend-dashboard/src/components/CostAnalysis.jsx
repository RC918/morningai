import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { 
  DollarSign, 
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Calendar,
  Download
} from 'lucide-react'
import { EmptyState, ErrorRecovery } from '@/components/feedback'
import { Skeleton } from '@/components/ui/skeleton'

const CostAnalysis = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [costData, setCostData] = useState(null)
  
  const mockCostData = {
    currentMonth: 1245.50,
    lastMonth: 980.30,
    budget: 2000,
    trend: 'up',
    breakdown: [
      { category: 'AI 服務', cost: 680.20, percentage: 54.6, trend: 'up' },
      { category: '計算資源', cost: 345.80, percentage: 27.8, trend: 'stable' },
      { category: '儲存空間', cost: 142.50, percentage: 11.4, trend: 'down' },
      { category: '網路流量', cost: 77.00, percentage: 6.2, trend: 'up' }
    ],
    alerts: [
      { type: 'warning', message: 'AI 服務成本較上月增加 35%' },
      { type: 'info', message: '預計本月總成本將超出預算 10%' }
    ]
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-red-600" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-green-600" />
      default:
        return <span className="text-gray-600 text-sm">→</span>
    }
  }
  
  useEffect(() => {
    const loadCostData = async () => {
      try {
        setLoading(true)
        setError(null)
        await new Promise(resolve => setTimeout(resolve, 500))
        setCostData(mockCostData)
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }
    
    loadCostData()
  }, [])
  
  const handleRetry = () => {
    setError(null)
    setLoading(true)
    setTimeout(() => {
      setCostData(mockCostData)
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
        <Skeleton className="h-24" />
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-64" />
        <Skeleton className="h-48" />
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
  
  if (!costData) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <EmptyState
          icon={DollarSign}
          title="尚無成本數據"
          description="系統還沒有任何成本分析數據。當系統開始運行後，您將在這裡看到詳細的成本分析報告。"
        />
      </div>
    )
  }

  const budgetUsagePercentage = (costData.currentMonth / costData.budget) * 100

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">成本分析</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">追蹤與分析 AI 服務成本</p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 w-full sm:w-auto">
          <Select defaultValue="current">
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="current">本月</SelectItem>
              <SelectItem value="last">上月</SelectItem>
              <SelectItem value="quarter">本季</SelectItem>
              <SelectItem value="year">本年</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="w-full sm:w-auto">
            <Download className="w-4 h-4 mr-2" />
            導出報表
          </Button>
        </div>
      </div>

      {costData.alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              {costData.alerts.map((alert, index) => (
                <div key={index} className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <p className="text-sm text-yellow-800">{alert.message}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">本月支出</p>
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${costData.currentMonth.toFixed(2)}
            </p>
            <div className="flex items-center gap-2 mt-2">
              {getTrendIcon(costData.trend)}
              <span className={`text-sm ${costData.trend === 'up' ? 'text-red-600' : 'text-green-600'}`}>
                {((costData.currentMonth / costData.lastMonth - 1) * 100).toFixed(1)}% 較上月
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">月度預算</p>
              <div className="p-2 bg-green-100 rounded-lg">
                <Calendar className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${costData.budget.toFixed(2)}
            </p>
            <div className="mt-2">
              <Progress value={budgetUsagePercentage} className="h-2" />
              <p className="text-sm text-gray-600 mt-1">
                已使用 {budgetUsagePercentage.toFixed(1)}%
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">預估月底</p>
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${(costData.currentMonth * 1.15).toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              基於當前使用趨勢
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>成本分類</CardTitle>
          <CardDescription>按服務類別查看成本分布</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {costData.breakdown.map((item, index) => (
              <div key={index}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-gray-900">{item.category}</span>
                    {getTrendIcon(item.trend)}
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">{item.percentage.toFixed(1)}%</Badge>
                    <span className="font-semibold text-gray-900">
                      ${item.cost.toFixed(2)}
                    </span>
                  </div>
                </div>
                <Progress value={item.percentage} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>成本優化建議</CardTitle>
          <CardDescription>AI 自動分析的節省機會</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <TrendingDown className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">優化 AI 服務使用時段</p>
                <p className="text-sm text-green-700 mt-1">
                  在離峰時段執行批次任務，預計每月可節省 $120
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <TrendingDown className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">調整儲存策略</p>
                <p className="text-sm text-green-700 mt-1">
                  將冷數據遷移至低成本儲存，預計每月可節省 $45
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CostAnalysis
