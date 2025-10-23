import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Save } from 'lucide-react'

const PlatformSettings = () => {
  const { t } = useTranslation()
  
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Settings className="w-8 h-8 text-gray-600" />
          {t('settings.title')}
        </h1>
        <p className="text-gray-600 mt-1">{t('settings.subtitle')}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.general.title')}</CardTitle>
          <CardDescription>{t('settings.general.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">{t('settings.general.platformName')}</label>
            <input 
              type="text" 
              defaultValue="MorningAI Platform" 
              className="w-full mt-1 px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="text-sm font-medium">{t('settings.general.supportEmail')}</label>
            <input 
              type="email" 
              defaultValue="support@morningai.com" 
              className="w-full mt-1 px-3 py-2 border rounded-lg"
            />
          </div>
          <Button>
            <Save className="w-4 h-4 mr-2" />
            {t('settings.general.saveChanges')}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('settings.security.title')}</CardTitle>
          <CardDescription>{t('settings.security.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('settings.security.requireMFA')}</p>
              <p className="text-sm text-gray-600">{t('settings.security.requireMFADesc')}</p>
            </div>
            <input type="checkbox" defaultChecked className="w-5 h-5" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{t('settings.security.sessionTimeout')}</p>
              <p className="text-sm text-gray-600">{t('settings.security.sessionTimeoutDesc')}</p>
            </div>
            <select className="px-3 py-2 border rounded-lg">
              <option>{t('settings.security.30minutes')}</option>
              <option>{t('settings.security.1hour')}</option>
              <option>{t('settings.security.4hours')}</option>
            </select>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PlatformSettings
