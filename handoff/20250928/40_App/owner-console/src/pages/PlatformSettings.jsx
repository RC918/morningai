import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Switch } from '@morningai/shared-ui'
import { Settings, Save, ChevronRight } from 'lucide-react'
import { AppleInput } from '@/components/apple/apple-input'
import { AppleButton } from '@/components/apple/apple-button'
import { AppleSelect, SelectItem } from '@/components/apple/apple-select'

const PlatformSettings = () => {
  const { t } = useTranslation()
  return (
    <div className="space-y-8" data-testid="platform-settings">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-[var(--text-primary)]">
          {t('settings.title')}
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">{t('settings.subtitle')}</p>
      </div>

      <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base font-semibold text-[var(--text-primary)]">{t('settings.general.title')}</CardTitle>
          <CardDescription className="text-sm text-[var(--text-secondary)]">{t('settings.general.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 p-5 pt-0">
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

      <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base font-semibold text-[var(--text-primary)]">{t('settings.security.title')}</CardTitle>
          <CardDescription className="text-sm text-[var(--text-secondary)]">{t('settings.security.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 p-5 pt-0">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">{t('settings.security.requireMFA')}</p>
              <p className="text-xs text-[var(--text-secondary)]">{t('settings.security.requireMFADesc')}</p>
            </div>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">{t('settings.security.sessionTimeout')}</p>
              <p className="text-xs text-[var(--text-secondary)]">{t('settings.security.sessionTimeoutDesc')}</p>
            </div>
            <AppleSelect defaultValue="30min" triggerClassName="w-[180px]">
              <SelectItem value="30min">{t('settings.security.30minutes')}</SelectItem>
              <SelectItem value="1hour">{t('settings.security.1hour')}</SelectItem>
              <SelectItem value="4hours">{t('settings.security.4hours')}</SelectItem>
            </AppleSelect>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-base font-semibold text-[var(--text-primary)]">
            {t('settings.2fa.card.title')}
          </CardTitle>
          <CardDescription className="text-sm text-[var(--text-secondary)]">
            {t('settings.2fa.card.description')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5 pt-0">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-[var(--text-primary)]">{t('settings.2fa.card.manage')}</p>
              <p className="text-xs text-[var(--text-secondary)]">
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
