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
import { useTranslation } from 'react-i18next'

const StrategyManagement = () => {
  const { t } = useTranslation()
  const mockStrategies = [
    {
      id: 1,
      name: t('strategy.examples.cpuOptimization.name'),
      description: t('strategy.examples.cpuOptimization.description'),
      status: 'active',
      triggers: 3,
      lastExecuted: `2 ${t('strategy.timeAgo.hoursAgo')}`
    },
    {
      id: 2,
      name: t('strategy.examples.dbConnectionPool.name'),
      description: t('strategy.examples.dbConnectionPool.description'),
      status: 'active',
      triggers: 8,
      lastExecuted: `30 ${t('strategy.timeAgo.minutesAgo')}`
    },
    {
      id: 3,
      name: t('strategy.examples.cacheWarmup.name'),
      description: t('strategy.examples.cacheWarmup.description'),
      status: 'paused',
      triggers: 0,
      lastExecuted: `3 ${t('strategy.timeAgo.daysAgo')}`
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{t('strategy.title')}</h1>
          <p className="text-gray-600 mt-1">{t('strategy.description')}</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          {t('strategy.addStrategy')}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('strategy.activeStrategies')}</p>
                <p className="text-2xl font-bold text-gray-900">2</p>
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
                <p className="text-sm text-gray-600">{t('strategy.totalTriggers')}</p>
                <p className="text-2xl font-bold text-gray-900">11</p>
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
                <p className="text-sm text-gray-600">{t('strategy.pausedStrategies')}</p>
                <p className="text-2xl font-bold text-gray-900">1</p>
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
          <CardTitle>{t('strategy.strategyList')}</CardTitle>
          <CardDescription>{t('strategy.strategyListDescription')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockStrategies.map((strategy) => (
              <div
                key={strategy.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  {getStatusIcon(strategy.status)}
                  <div>
                    <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
                    <p className="text-sm text-gray-600">{strategy.description}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <Badge variant="outline" className="text-xs">
                        {t('strategy.triggeredTimes')} {strategy.triggers} {t('strategy.times')}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {t('strategy.lastExecuted')}: {strategy.lastExecuted}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge className={getStatusColor(strategy.status)}>
                    {t(`strategy.status.${strategy.status}`)}
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
