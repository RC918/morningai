import { useEffect } from 'react'
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
        <h1 className="text-3xl font-bold text-gray-900">系統設定</h1>
        <p className="text-gray-600 mt-1">管理您的帳號與系統偏好設定</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            <span className="hidden sm:inline">個人資料</span>
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <Palette className="w-4 h-4" />
            <span className="hidden sm:inline">偏好設定</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">通知</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            <span className="hidden sm:inline">安全性</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>個人資料</CardTitle>
              <CardDescription>管理您的個人資訊</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={profile.avatar} alt={`${profile.name} 的頭像`} />
                  <AvatarFallback>RC</AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm" aria-label="更換頭像">更換頭像</Button>
                  <p className="text-sm text-gray-600 mt-1">JPG、PNG 或 GIF，最大 2MB</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">姓名</Label>
                  <Input
                    id="name"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    aria-describedby="name-description"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">電子郵件</Label>
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
                <span className="text-sm text-gray-600">帳號角色</span>
              </div>

              {error && (
                <div className="text-red-600 text-sm" role="alert" aria-live="polite">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={saveToAPI} disabled={loading} aria-label="儲存個人資料變更">
                  {loading ? '儲存中...' : '儲存變更'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>介面偏好</CardTitle>
              <CardDescription>自訂您的使用體驗</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="language" className="flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  語言
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
                  主題
                </Label>
                <Select value={preferences.theme} onValueChange={setTheme}>
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">淺色</SelectItem>
                    <SelectItem value="dark">深色</SelectItem>
                    <SelectItem value="auto">自動</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {error && (
                <div className="text-red-600 text-sm" role="alert" aria-live="polite">
                  {error}
                </div>
              )}

              <div className="flex justify-end">
                <Button onClick={saveToAPI} disabled={loading} aria-label="儲存變更">
                  {loading ? '儲存中...' : '儲存變更'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>通知設定</CardTitle>
              <CardDescription>管理您希望接收的通知</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>電子郵件通知</Label>
                  <p className="text-sm text-gray-600">接收重要更新的電子郵件</p>
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
                  <Label>桌面通知</Label>
                  <p className="text-sm text-gray-600">在瀏覽器中顯示即時通知</p>
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
                  <Label>AI 建議通知</Label>
                  <p className="text-sm text-gray-600">接收 AI 的優化建議</p>
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
                <Button onClick={saveToAPI} disabled={loading} aria-label="儲存變更">
                  {loading ? '儲存中...' : '儲存變更'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>安全性設定</CardTitle>
              <CardDescription>保護您的帳號安全</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="current-password">當前密碼</Label>
                  <Input id="current-password" type="password" className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="new-password">新密碼</Label>
                  <Input id="new-password" type="password" className="mt-2" />
                </div>
                <div>
                  <Label htmlFor="confirm-password">確認新密碼</Label>
                  <Input id="confirm-password" type="password" className="mt-2" />
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <div className="space-y-0.5">
                  <Label className="flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    雙因素驗證 (2FA)
                  </Label>
                  <p className="text-sm text-gray-600">為您的帳號增加額外安全層</p>
                </div>
                <Badge className="bg-green-100 text-green-800">已啟用</Badge>
              </div>

              <div className="flex justify-end gap-3">
                <Button variant="outline">取消</Button>
                <Button onClick={saveToAPI} disabled={loading}>
                  {loading ? '更新中...' : '更新密碼'}
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
