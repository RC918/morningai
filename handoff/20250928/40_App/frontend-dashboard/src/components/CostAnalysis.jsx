import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AppleButton } from '@/components/ui/apple-button'
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
import { useTranslation } from 'react-i18next'
import { customFetch } from '@/lib/api-client'

const CostAnalysis = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [costData, setCostData] = useState(null)
  const [period, setPeriod] = useState('daily')

  useEffect(() => {
    loadCostData()
  }, [period])

  const loadCostData = async () => {
    try {
      setLoading(true)
      const data = await customFetch({ 
        url: `/api/governance/costs?period=${period}&trace_id=system` 
      })
      setCostData(data)
    } catch (error) {
      console.error('Failed to load cost data:', error)
      setCostData(mockCostData)
    } finally {
      setLoading(false)
    }
  }

  const mockCostData = {
    currentMonth: 1245.50,
    lastMonth: 980.30,
    budget: 2000,
    trend: 'up',
    breakdown: [
      { category: t('cost.categories.aiService'), cost: 680.20, percentage: 54.6, trend: 'up' },
      { category: t('cost.categories.compute'), cost: 345.80, percentage: 27.8, trend: 'stable' },
      { category: t('cost.categories.storage'), cost: 142.50, percentage: 11.4, trend: 'down' },
      { category: t('cost.categories.network'), cost: 77.00, percentage: 6.2, trend: 'up' }
    ],
    alerts: [
      { type: 'warning', message: t('cost.alerts.aiServiceIncrease') },
      { type: 'info', message: t('cost.alerts.budgetExceeded') }
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

  const displayData = costData || mockCostData
  const currentUsage = costData?.usage?.usd || mockCostData.currentMonth
  const budgetLimit = costData?.limits?.usd || mockCostData.budget
  const budgetUsagePercentage = (currentUsage / budgetLimit) * 100

  if (loading && !costData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('cost.title')}</h1>
          <p className="text-gray-600 mt-1">{t('cost.description')}</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="hourly">Hourly</SelectItem>
              <SelectItem value="task">Per Task</SelectItem>
            </SelectContent>
          </Select>
          <AppleButton variant="outline" onClick={loadCostData}>
            <Download className="w-4 h-4 mr-2" />
            {t('cost.exportReport')}
          </AppleButton>
        </div>
      </div>

      {mockCostData.alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              {mockCostData.alerts.map((alert, index) => (
                <div key={index} className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <p className="text-sm text-yellow-800">{alert.message}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">{t('cost.currentMonth')}</p>
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${currentUsage.toFixed(2)}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={costData?.within_budget ? "outline" : "destructive"}>
                {costData?.within_budget ? 'Within Budget' : 'Over Budget'}
              </Badge>
              {costData?.alert_level && (
                <Badge variant={costData.alert_level === 'critical' ? 'destructive' : costData.alert_level === 'warning' ? 'warning' : 'outline'}>
                  {costData.alert_level}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">{t('cost.monthlyBudget')}</p>
              <div className="p-2 bg-green-100 rounded-lg">
                <Calendar className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${budgetLimit.toFixed(2)}
            </p>
            <div className="mt-2">
              <Progress value={budgetUsagePercentage} className="h-2" />
              <p className="text-sm text-gray-600 mt-1">
                {t('cost.usedPercentage')} {budgetUsagePercentage.toFixed(1)}%
              </p>
              {costData && (
                <p className="text-xs text-gray-500 mt-1">
                  Tokens: {costData.usage?.tokens?.toLocaleString() || 0} / {costData.limits?.tokens?.toLocaleString() || 0}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">{t('cost.estimatedEndOfMonth')}</p>
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${(mockCostData.currentMonth * 1.15).toFixed(2)}
            </p>
            <p className="text-sm text-gray-600 mt-2">
              {t('cost.basedOnCurrentTrend')}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('cost.costBreakdown')}</CardTitle>
          <CardDescription>{t('cost.costBreakdownDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockCostData.breakdown.map((item, index) => (
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
          <CardTitle>{t('cost.optimizationSuggestions')}</CardTitle>
          <CardDescription>{t('cost.optimizationSuggestionsDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <TrendingDown className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">{t('cost.suggestions.optimizeAiUsage')}</p>
                <p className="text-sm text-green-700 mt-1">
                  {t('cost.suggestions.optimizeAiUsageDescription')}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <TrendingDown className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">{t('cost.suggestions.adjustStorageStrategy')}</p>
                <p className="text-sm text-green-700 mt-1">
                  {t('cost.suggestions.adjustStorageStrategyDescription')}
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
