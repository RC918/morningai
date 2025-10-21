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
          <Skeleton className="h-8 w-48 mb-2" aria-busy="true" aria-label="載入頁面標題" />
          <Skeleton className="h-4 w-96" aria-busy="true" aria-label="載入頁面描述" />
        </div>
        <div className="space-y-6">
          <Skeleton className="h-96" aria-busy="true" aria-label="載入主要設定區域" />
          <Skeleton className="h-64" aria-busy="true" aria-label="載入次要設定區域" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">系統設定</h1>
          <p className="text-gray-600">管理您的帳戶偏好設定和系統配置</p>
        </div>
        {hasChanges && (
          <Button onClick={saveSettings} disabled={saving}>
            {saving ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saving ? '儲存中...' : '儲存變更'}
          </Button>
        )}
      </div>

      <Tabs defaultValue="preferences" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="preferences" className="flex items-center">
            <User className="w-4 h-4 mr-2" />
            偏好設定
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center">
            <Bell className="w-4 h-4 mr-2" />
            通知設定
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center">
            <Shield className="w-4 h-4 mr-2" />
            安全設定
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center">
            <Settings className="w-4 h-4 mr-2" />
            系統配置
          </TabsTrigger>
          <TabsTrigger value="billing" className="flex items-center">
            <CreditCard className="w-4 h-4 mr-2" />
            帳單資訊
          </TabsTrigger>
        </TabsList>

        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Palette className="w-5 h-5 mr-2" />
                外觀設定
              </CardTitle>
              <CardDescription>自訂您的介面外觀和體驗</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">主題</Label>
                  <Select 
                    value={settings?.user_preferences?.theme} 
                    onValueChange={(value) => updateSetting('user_preferences', 'theme', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">淺色主題</SelectItem>
                      <SelectItem value="dark">深色主題</SelectItem>
                      <SelectItem value="auto">自動</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="language">語言</Label>
                  <Select 
                    value={settings?.user_preferences?.language}
                    onValueChange={(value) => updateSetting('user_preferences', 'language', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="zh-TW">繁體中文</SelectItem>
                      <SelectItem value="en-US">English</SelectItem>
                      <SelectItem value="ja-JP">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="timezone">時區</Label>
                <Select 
                  value={settings?.user_preferences?.timezone}
                  onValueChange={(value) => updateSetting('user_preferences', 'timezone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Asia/Taipei">台北 (UTC+8)</SelectItem>
                    <SelectItem value="Asia/Tokyo">東京 (UTC+9)</SelectItem>
                    <SelectItem value="UTC">UTC (UTC+0)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="auto_refresh">自動重新整理間隔 (秒)</Label>
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
                通知偏好設定
              </CardTitle>
              <CardDescription>選擇您希望接收通知的方式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {settings?.user_preferences?.notifications && Object.entries(settings.user_preferences.notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <Label htmlFor={key} className="text-sm font-medium">
                      {key === 'email' && '電子郵件通知'}
                      {key === 'push' && '推播通知'}
                      {key === 'sms' && '簡訊通知'}
                      {key === 'slack' && 'Slack 通知'}
                    </Label>
                    <p className="text-sm text-gray-500">
                      {key === 'email' && '接收重要系統更新和警報'}
                      {key === 'push' && '瀏覽器推播通知'}
                      {key === 'sms' && '緊急事件簡訊通知'}
                      {key === 'slack' && '團隊協作通知'}
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
                安全設定
              </CardTitle>
              <CardDescription>管理您的帳戶安全和存取控制</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">雙重驗證</Label>
                  <p className="text-sm text-gray-500">為您的帳戶增加額外的安全層</p>
                </div>
                <div className="flex items-center space-x-2">
                  {settings?.security_settings?.two_factor_enabled && (
                    <Badge variant="secondary" className="text-green-600">
                      <Check className="w-3 h-3 mr-1" />
                      已啟用
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
                <Label htmlFor="session_timeout">工作階段逾時 (秒)</Label>
                <Input
                  id="session_timeout"
                  type="number"
                  value={settings?.security_settings?.session_timeout}
                  onChange={(e) => updateSetting('security_settings', 'session_timeout', parseInt(e.target.value))}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">稽核日誌</Label>
                  <p className="text-sm text-gray-500">記錄所有系統存取和操作</p>
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
                系統配置
              </CardTitle>
              <CardDescription>調整系統行為和效能設定</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">自動審批</Label>
                  <p className="text-sm text-gray-500">低風險決策自動審批</p>
                </div>
                <Switch
                  checked={settings?.system_config?.auto_approval}
                  onCheckedChange={(checked) => updateSetting('system_config', 'auto_approval', checked)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="risk_threshold">風險閾值</Label>
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
                <Label htmlFor="monitoring_interval">監控間隔 (秒)</Label>
                <Input
                  id="monitoring_interval"
                  type="number"
                  value={settings?.system_config?.monitoring_interval}
                  onChange={(e) => updateSetting('system_config', 'monitoring_interval', parseInt(e.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="api_rate_limit">API 速率限制 (每小時)</Label>
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
                帳單資訊
              </CardTitle>
              <CardDescription>管理您的訂閱和付款方式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">目前方案</Label>
                  <div className="flex items-center mt-1">
                    <Badge variant="secondary" className="text-blue-600">
                      {settings?.billing_info?.current_plan?.toUpperCase()}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label className="text-sm font-medium">計費週期</Label>
                  <p className="text-sm text-gray-600 mt-1">
                    {settings?.billing_info?.billing_cycle === 'monthly' ? '每月' : '每年'}
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm font-medium">下次計費日期</Label>
                <p className="text-sm text-gray-600 mt-1">
                  {settings?.billing_info?.next_billing_date}
                </p>
              </div>

              <div>
                <Label className="text-sm font-medium">付款方式</Label>
                <p className="text-sm text-gray-600 mt-1">
                  {settings?.billing_info?.payment_method}
                </p>
              </div>

              <div className="flex space-x-2">
                <Button variant="outline">
                  更新付款方式
                </Button>
                <Button variant="outline">
                  查看帳單歷史
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
