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
import { useTranslation } from 'react-i18next'

const HistoryAnalysis = () => {
  const { t } = useTranslation()
  const mockHistory = [
    {
      id: 1,
      date: '2024-01-15',
      type: 'optimization',
      title: t('history.examples.cpuOptimization'),
      impact: 'positive',
      metrics: { cpu: -25, responseTime: -30 },
      status: 'completed'
    },
    {
      id: 2,
      date: '2024-01-14',
      type: 'scaling',
      title: t('history.examples.autoScaling'),
      impact: 'positive',
      metrics: { instances: +2, cost: +18.5 },
      status: 'completed'
    },
    {
      id: 3,
      date: '2024-01-13',
      type: 'alert',
      title: t('history.examples.memoryWarning'),
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('history.title')}</h1>
          <p className="text-gray-600 mt-1">{t('history.description')}</p>
        </div>
        <div className="flex items-center gap-3">
          <Select defaultValue="7d">
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">{t('history.periods.24h')}</SelectItem>
              <SelectItem value="7d">{t('history.periods.7d')}</SelectItem>
              <SelectItem value="30d">{t('history.periods.30d')}</SelectItem>
              <SelectItem value="90d">{t('history.periods.90d')}</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Calendar className="w-4 h-4 mr-2" />
            {t('history.customRange')}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('history.totalEvents')}</p>
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
                <p className="text-sm text-gray-600">{t('history.optimizationExecutions')}</p>
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
                <p className="text-sm text-gray-600">{t('history.warningEvents')}</p>
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
                <p className="text-sm text-gray-600">{t('history.avgResponseTime')}</p>
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
          <CardTitle>{t('history.eventTimeline')}</CardTitle>
          <CardDescription>{t('history.eventTimelineDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockHistory.map((event) => (
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
                      {t(`history.impact.${event.impact}`)}
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
                  {t('history.viewDetails')}
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
