import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Switch } from '@morningai/shared-ui'
import { Settings, Save, Shield, ChevronRight } from 'lucide-react'
import { AppleInput } from '@/components/apple/apple-input'
import { AppleButton } from '@/components/apple/apple-button'
import { AppleSelect, SelectItem } from '@/components/apple/apple-select'

const PlatformSettings = () => {
  const { t } = useTranslation()
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-large-title font-bold text-neutral-900 dark:text-white flex items-center gap-3">
          <Settings className="w-8 h-8 text-neutral-600 dark:text-neutral-400" />
          {t('settings.title')}
        </h1>
        <p className="text-body text-neutral-600 dark:text-neutral-400 mt-1">{t('settings.subtitle')}</p>
      </div>

      <Card className="material-card">
        <CardHeader className="px-6 pt-6">
          <CardTitle>{t('settings.general.title')}</CardTitle>
          <CardDescription>{t('settings.general.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-6 pb-6">
          <AppleInput
            id="platform-name"
            type="text"
            label={t('settings.general.platformName')}
            defaultValue="MorningAI Platform"
            variant="filled"
            haptic="light"
          />
          <AppleInput
            id="support-email"
            type="email"
            label={t('settings.general.supportEmail')}
            defaultValue="support@morningai.com"
            variant="filled"
            haptic="light"
          />
          <AppleButton variant="primary" haptic="medium">
            <Save className="w-4 h-4 mr-2" />
            {t('settings.general.saveChanges')}
          </AppleButton>
        </CardContent>
      </Card>

      <Card className="material-card">
        <CardHeader className="px-6 pt-6">
          <CardTitle>{t('settings.security.title')}</CardTitle>
          <CardDescription>{t('settings.security.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 px-6 pb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-callout font-medium">{t('settings.security.requireMFA')}</p>
              <p className="text-footnote text-neutral-600">{t('settings.security.requireMFADesc')}</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-callout font-medium">{t('settings.security.sessionTimeout')}</p>
              <p className="text-footnote text-neutral-600">{t('settings.security.sessionTimeoutDesc')}</p>
            </div>
            <AppleSelect defaultValue="30min" triggerClassName="w-[180px]">
              <SelectItem value="30min">{t('settings.security.30minutes')}</SelectItem>
              <SelectItem value="1hour">{t('settings.security.1hour')}</SelectItem>
              <SelectItem value="4hours">{t('settings.security.4hours')}</SelectItem>
            </AppleSelect>
          </div>
        </CardContent>
      </Card>

      <Card className="material-card">
        <CardHeader className="px-6 pt-6">
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            {t('settings.2fa.card.title')}
          </CardTitle>
          <CardDescription>
            {t('settings.2fa.card.description')}
          </CardDescription>
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-callout font-medium">{t('settings.2fa.card.manage')}</p>
              <p className="text-footnote text-neutral-600">
                {t('settings.2fa.card.manageDescription')}
              </p>
            </div>
            <Link to="/settings/2fa">
              <AppleButton variant="outline" className="flex items-center gap-2">
                {t('settings.2fa.card.manageButton')}
                <ChevronRight className="w-4 h-4" />
              </AppleButton>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PlatformSettings
