import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Server, Database, Zap } from 'lucide-react'

const SystemMonitoring = () => {
  const { t } = useTranslation()
  
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Activity className="w-8 h-8 text-green-600" />
          {t('monitoring.title')}
        </h1>
        <p className="text-gray-600 mt-1">{t('monitoring.subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5" />
              {t('monitoring.apiServices')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.uptime')}</span>
                <span className="text-sm font-semibold text-green-600">99.9%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.avgResponse')}</span>
                <span className="text-sm font-semibold">45ms</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              {t('monitoring.database')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.connections')}</span>
                <span className="text-sm font-semibold">45/100</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.queryTime')}</span>
                <span className="text-sm font-semibold">12ms</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              {t('monitoring.workers')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.active')}</span>
                <span className="text-sm font-semibold text-green-600">8/10</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">{t('monitoring.queueSize')}</span>
                <span className="text-sm font-semibold">23</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default SystemMonitoring
