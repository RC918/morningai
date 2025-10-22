import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  User, 
  Bell, 
  Shield, 
  Palette, 
  Globe, 
  CreditCard,
  Settings,
  Save,
  RefreshCw,
  AlertTriangle,
  Check
} from 'lucide-react'
import { colors, spacing, typography } from '@/lib/design-tokens'
import apiClient from '@/lib/api'

const SettingsPageSkeleton = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [settings, setSettings] = useState(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await apiClient.getSettings()
      setSettings(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load settings:', error)
      setLoading(false)
    }
  }

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }))
    setHasChanges(true)
  }

  const updateNestedSetting = (category, parentKey, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [parentKey]: {
          ...prev[category][parentKey],
          [key]: value
        }
      }
    }))
    setHasChanges(true)
  }

  const saveSettings = async () => {
    setSaving(true)
    try {
      const result = await apiClient.saveSettings(settings)
      
      if (result.success) {
        setHasChanges(false)
      }
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-6">
          <Skeleton className="h-8 w-48 mb-2" aria-busy="true" aria-label={t('settings.loadingTitle')} />
          <Skeleton className="h-4 w-96" aria-busy="true" aria-label={t('settings.loadingDescription')} />
        </div>
        <div className="space-y-6">
          <Skeleton className="h-96" aria-busy="true" aria-label={t('settings.loadingMainSettings')} />
          <Skeleton className="h-64" aria-busy="true" aria-label={t('settings.loadingSecondarySettings')} />
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('settings.title')}</h1>
          <p className="text-gray-600">{t('settings.description')}</p>
        </div>
        {hasChanges && (
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saving ? t('settings.saving') : t('settings.saveChanges')}
          </Button>
        )}
      </div>

      <Tabs defaultValue="preferences" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="preferences" className="flex items-center">
            <User className="w-4 h-4 mr-2" />
            {t('settings.tabs.preferences')}
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center">
            <Bell className="w-4 h-4 mr-2" />
            {t('settings.tabs.notifications')}
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center">
            <Shield className="w-4 h-4 mr-2" />
            {t('settings.tabs.security')}
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center">
            <Settings className="w-4 h-4 mr-2" />
            {t('settings.tabs.system')}
          </TabsTrigger>
          <TabsTrigger value="billing" className="flex items-center">
            <CreditCard className="w-4 h-4 mr-2" />
            {t('settings.tabs.billing')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Palette className="w-5 h-5 mr-2" />
                {t('settings.preferences.title')}
              </CardTitle>
              <CardDescription>{t('settings.preferences.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">{t('settings.preferences.theme')}</Label>
                  <Select 
                    value={settings?.user_preferences?.theme} 
                    onValueChange={(value) => updateSetting('user_preferences', 'theme', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">{t('settings.preferences.themeLight')}</SelectItem>
                      <SelectItem value="dark">{t('settings.preferences.themeDark')}</SelectItem>
                      <SelectItem value="auto">{t('settings.preferences.themeAuto')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">{t('settings.preferences.language')}</Label>
                  <Select 
                    value={settings?.user_preferences?.language}
                    onValueChange={(value) => updateSetting('user_preferences', 'language', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="zh-TW">{t('settings.languages.zhTW')}</SelectItem>
                      <SelectItem value="en-US">{t('settings.languages.enUS')}</SelectItem>
                      <SelectItem value="ja-JP">{t('settings.languages.jaJP')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="timezone">{t('settings.preferences.timezone')}</Label>
                <Select 
                  value={settings?.user_preferences?.timezone}
                  onValueChange={(value) => updateSetting('user_preferences', 'timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Asia/Taipei">{t('settings.timezones.taipei')}</SelectItem>
                    <SelectItem value="Asia/Tokyo">{t('settings.timezones.tokyo')}</SelectItem>
                    <SelectItem value="UTC">{t('settings.timezones.utc')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="auto_refresh">{t('settings.preferences.autoRefresh')}</Label>
                <Input
                  id="auto_refresh"
                  type="number"
                  value={settings?.user_preferences?.auto_refresh}
                  onChange={(e) => updateSetting('user_preferences', 'auto_refresh', parseInt(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="w-5 h-5 mr-2" />
                {t('settings.notifications.title')}
              </CardTitle>
              <CardDescription>{t('settings.notifications.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {settings?.user_preferences?.notifications && Object.entries(settings.user_preferences.notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <Label htmlFor={key} className="text-sm font-medium">
                      {t(`settings.notifications.${key}`)}
                    </Label>
                    <p className="text-sm text-gray-600">
                      {t(`settings.notifications.${key}Description`)}
                    </p>
                  </div>
                  <Switch
                    id={key}
                    checked={value}
                    onCheckedChange={(checked) => updateNestedSetting('user_preferences', 'notifications', key, checked)}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                {t('settings.security.title')}
              </CardTitle>
              <CardDescription>{t('settings.security.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">{t('settings.security.twoFactor')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.security.twoFactorDescription')}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {settings?.security_settings?.two_factor_enabled && (
                    <Badge variant="secondary" className="text-green-600">
                      <Check className="w-3 h-3 mr-1" />
                      {t('settings.security.twoFactorEnabled')}
                    </Badge>
                  )}
                  <Switch
                    checked={settings?.security_settings?.two_factor_enabled}
                    onCheckedChange={(checked) => updateSetting('security_settings', 'two_factor_enabled', checked)}
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="session_timeout">{t('settings.security.sessionTimeout')}</Label>
                <Input
                  id="session_timeout"
                  type="number"
                  value={settings?.security_settings?.session_timeout}
                  onChange={(e) => updateSetting('security_settings', 'session_timeout', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">{t('settings.security.auditLogging')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.security.auditLoggingDescription')}</p>
                </div>
                <Switch
                  checked={settings?.security_settings?.audit_logging}
                  onCheckedChange={(checked) => updateSetting('security_settings', 'audit_logging', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                {t('settings.system.title')}
              </CardTitle>
              <CardDescription>{t('settings.system.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">{t('settings.system.autoApproval')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.system.autoApprovalDescription')}</p>
                </div>
                <Switch
                  checked={settings?.system_config?.auto_approval}
                  onCheckedChange={(checked) => updateSetting('system_config', 'auto_approval', checked)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="risk_threshold">{t('settings.system.riskThreshold')}</Label>
                <Input
                  id="risk_threshold"
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={settings?.system_config?.risk_threshold}
                  onChange={(e) => updateSetting('system_config', 'risk_threshold', parseFloat(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="monitoring_interval">{t('settings.system.monitoringInterval')}</Label>
                <Input
                  id="monitoring_interval"
                  type="number"
                  value={settings?.system_config?.monitoring_interval}
                  onChange={(e) => updateSetting('system_config', 'monitoring_interval', parseInt(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="api_rate_limit">{t('settings.system.apiRateLimit')}</Label>
                <Input
                  id="api_rate_limit"
                  type="number"
                  value={settings?.system_config?.api_rate_limit}
                  onChange={(e) => updateSetting('system_config', 'api_rate_limit', parseInt(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="billing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCard className="w-5 h-5 mr-2" />
                {t('settings.billing.title')}
              </CardTitle>
              <CardDescription>{t('settings.billing.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">{t('settings.billing.currentPlan')}</Label>
                  <div className="flex items-center mt-1">
                    <Badge variant="secondary" className="text-blue-600">
                      {settings?.billing_info?.current_plan?.toUpperCase()}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">{t('settings.billing.billingCycle')}</Label>
                  <p className="text-sm text-gray-600 mt-1">
                    {settings?.billing_info?.billing_cycle === 'monthly' ? t('settings.billing.billingCycleMonthly') : t('settings.billing.billingCycleYearly')}
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm font-medium">{t('settings.billing.nextBillingDate')}</Label>
                <p className="text-sm text-gray-600 mt-1">
                  {settings?.billing_info?.next_billing_date}
                </p>
              </div>

              <div>
                <Label className="text-sm font-medium">{t('settings.billing.paymentMethod')}</Label>
                <p className="text-sm text-gray-600 mt-1">
                  {settings?.billing_info?.payment_method}
                </p>
              </div>

              <div className="flex space-x-2">
                <Button variant="outline">
                  {t('settings.billing.updatePaymentMethod')}
                </Button>
                <Button variant="outline">
                  {t('settings.billing.viewBillingHistory')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SettingsPageSkeleton
