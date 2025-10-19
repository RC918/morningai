import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { 
  User, 
  Bell, 
  Shield, 
  Palette,
  Globe,
  Key
} from 'lucide-react'
import useSettingsStore from '@/stores/settingsStore'

const SystemSettings = () => {
  const { t } = useTranslation()
  
  const {
    profile,
    preferences,
    loading,
    error,
    setProfile,
    setPreferences,
    setLanguage,
    setTheme,
    setNotifications,
    loadFromAPI,
    saveToAPI
  } = useSettingsStore()

  useEffect(() => {
    loadFromAPI().catch(console.warn)
  }, [loadFromAPI])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', preferences.theme)
    if (preferences.theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [preferences.theme])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-gray-600 mt-1">{t('settings.description')}</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            <span className="hidden sm:inline">{t('settings.tabs.profile')}</span>
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Palette className="w-4 h-4" />
            <span className="hidden sm:inline">{t('settings.tabs.preferences')}</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">{t('settings.tabs.notifications')}</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            <span className="hidden sm:inline">{t('settings.tabs.security')}</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.profile.title')}</CardTitle>
              <CardDescription>{t('settings.profile.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={profile.avatar} alt={`${profile.name} avatar`} />
                  <AvatarFallback>RC</AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm" aria-label={t('settings.profile.avatar')}>
                    {t('settings.profile.avatar')}
                  </Button>
                  <p className="text-sm text-gray-600 mt-1">{t('settings.profile.avatarHint')}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">{t('settings.profile.name')}</Label>
                  <Input
                    id="name"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    aria-describedby="name-description"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">{t('settings.profile.email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    aria-describedby="email-description"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Badge>{profile.role}</Badge>
                <span className="text-sm text-gray-600">{t('settings.profile.role')}</span>
              </div>

              {error && (
                <div className="text-red-600 text-sm" role="alert" aria-live="polite">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={saveToAPI} disabled={loading} aria-label={t('settings.profile.saveChanges')}>
                  {loading ? t('settings.profile.saving') : t('settings.profile.saveChanges')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.preferences.title')}</CardTitle>
              <CardDescription>{t('settings.preferences.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="language" className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  {t('settings.preferences.language')}
                </Label>
                <Select value={preferences.language} onValueChange={setLanguage}>
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="zh-TW">繁體中文</SelectItem>
                    <SelectItem value="zh-CN">简体中文</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="ja">日本語</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="theme" className="flex items-center gap-2">
                  <Palette className="w-4 h-4" />
                  {t('settings.preferences.theme')}
                </Label>
                <Select value={preferences.theme} onValueChange={setTheme}>
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">{t('settings.preferences.themeLight')}</SelectItem>
                    <SelectItem value="dark">{t('settings.preferences.themeDark')}</SelectItem>
                    <SelectItem value="auto">{t('settings.preferences.themeAuto')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {error && (
                <div className="text-red-600 text-sm" role="alert" aria-live="polite">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={saveToAPI} disabled={loading} aria-label={t('settings.profile.saveChanges')}>
                  {loading ? t('settings.profile.saving') : t('settings.profile.saveChanges')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.notifications.title')}</CardTitle>
              <CardDescription>{t('settings.notifications.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{t('settings.notifications.email')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.notifications.emailDescription')}</p>
                </div>
                <Switch
                  checked={preferences.notifications.email}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...preferences.notifications, email: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{t('settings.notifications.desktop')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.notifications.desktopDescription')}</p>
                </div>
                <Switch
                  checked={preferences.notifications.desktop}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...preferences.notifications, desktop: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{t('settings.notifications.aiSuggestions')}</Label>
                  <p className="text-sm text-gray-600">{t('settings.notifications.aiSuggestionsDescription')}</p>
                </div>
                <Switch
                  checked={preferences.notifications.aiSuggestions}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...preferences.notifications, aiSuggestions: checked })
                  }
                />
              </div>

              {error && (
                <div className="text-red-600 text-sm" role="alert" aria-live="polite">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={saveToAPI} disabled={loading} aria-label={t('settings.profile.saveChanges')}>
                  {loading ? t('settings.profile.saving') : t('settings.profile.saveChanges')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.security.title')}</CardTitle>
              <CardDescription>{t('settings.security.description')}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="current-password">{t('settings.security.currentPassword')}</Label>
                  <Input id="current-password" type="password" className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="new-password">{t('settings.security.newPassword')}</Label>
                  <Input id="new-password" type="password" className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="confirm-password">{t('settings.security.confirmPassword')}</Label>
                  <Input id="confirm-password" type="password" className="mt-2" />
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    {t('settings.security.twoFactor')}
                  </Label>
                  <p className="text-sm text-gray-600">{t('settings.security.twoFactorDescription')}</p>
                </div>
                <Badge className="bg-green-100 text-green-800">{t('settings.security.twoFactorEnabled')}</Badge>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline">{t('actions.cancel')}</Button>
                <Button onClick={saveToAPI} disabled={loading}>
                  {loading ? t('settings.security.updating') : t('settings.security.updatePassword')}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SystemSettings
