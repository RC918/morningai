import React, { useState, useEffect } from 'react'
import { User, Users, Settings as SettingsIcon, Bell, Globe, Palette, Shield, Mail, Calendar } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import mockData from '@/mocks/settings.json'

const Settings = () => {
  const [data, setData] = useState({
    profile: {},
    tenants: [],
    preferences: {}
  })
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    setData(mockData)
  }, [])

  const handleSave = async (section) => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsSaving(false)
  }

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-700'
      case 'admin':
        return 'bg-blue-100 text-blue-700'
      case 'member':
        return 'bg-gray-100 text-gray-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700'
      case 'pending':
        return 'bg-yellow-100 text-yellow-700'
      case 'inactive':
        return 'bg-gray-100 text-gray-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">設定</h1>
        <p className="text-gray-600">管理您的個人資料、租戶和系統偏好</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            個人資料
          </TabsTrigger>
          <TabsTrigger value="tenants" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            租戶管理
          </TabsTrigger>
          <TabsTrigger value="preferences" className="flex items-center gap-2">
            <SettingsIcon className="w-4 h-4" />
            系統偏好
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>個人資訊</CardTitle>
              <CardDescription>更新您的個人資料和聯絡資訊</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={data.profile.avatar} alt={data.profile.name} />
                  <AvatarFallback>{data.profile.name?.charAt(0)}</AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm">更換頭像</Button>
                  <p className="text-sm text-gray-500 mt-2">JPG, GIF 或 PNG. 最大 2MB</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">姓名</Label>
                  <Input id="name" defaultValue={data.profile.name} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">電子郵件</Label>
                  <Input id="email" type="email" defaultValue={data.profile.email} />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">角色</Label>
                <Input id="role" defaultValue={data.profile.role} disabled className="bg-gray-50" />
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">加入日期</p>
                    <p className="text-sm text-gray-600">{data.profile.joinedDate}</p>
                  </div>
                </div>
              </div>

              <Button 
                onClick={() => handleSave('profile')}
                disabled={isSaving}
                className="bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]"
              >
                {isSaving ? '儲存中...' : '儲存變更'}
              </Button>
            </CardContent>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>安全設定</CardTitle>
              <CardDescription>管理您的密碼和安全選項</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">目前密碼</Label>
                <Input id="current-password" type="password" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">新密碼</Label>
                <Input id="new-password" type="password" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">確認新密碼</Label>
                <Input id="confirm-password" type="password" />
              </div>

              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-[var(--color-primary-500)]" />
                  <div>
                    <p className="font-medium text-gray-900">雙因素認證</p>
                    <p className="text-sm text-gray-600">為您的帳號增加額外保護</p>
                  </div>
                </div>
                <Switch checked={data.profile.twoFactorEnabled} />
              </div>

              <Button variant="outline">更新密碼</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tenants" className="space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>租戶列表</CardTitle>
                  <CardDescription>管理您所屬的租戶和團隊</CardDescription>
                </div>
                <Button className="bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]">
                  <Users className="w-4 h-4 mr-2" />
                  邀請成員
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.tenants.map((tenant) => (
                  <div
                    key={tenant.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-[var(--color-primary-500)] hover:shadow-md transition-all duration-[var(--duration-fast)]"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 mb-2">{tenant.name}</h4>
                        <div className="flex items-center gap-2 mb-3">
                          <Badge className={getRoleBadgeColor(tenant.role)}>
                            {tenant.role === 'owner' && '擁有者'}
                            {tenant.role === 'admin' && '管理員'}
                            {tenant.role === 'member' && '成員'}
                          </Badge>
                          <Badge className={getStatusBadgeColor(tenant.status)}>
                            {tenant.status === 'active' && '啟用中'}
                            {tenant.status === 'pending' && '等待中'}
                            {tenant.status === 'inactive' && '未啟用'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Users className="w-4 h-4" />
                            {tenant.members} 位成員
                          </span>
                          <span>建立於 {tenant.createdAt}</span>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">管理</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>權限與角色</CardTitle>
              <CardDescription>了解不同角色的權限</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                  <p className="font-medium text-gray-900 mb-1">擁有者</p>
                  <p className="text-sm text-gray-600">完整的管理權限，包括刪除租戶</p>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="font-medium text-gray-900 mb-1">管理員</p>
                  <p className="text-sm text-gray-600">管理成員、設定和大多數功能</p>
                </div>
                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <p className="font-medium text-gray-900 mb-1">成員</p>
                  <p className="text-sm text-gray-600">使用功能和查看資訊</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="space-y-6">
          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>語言與地區</CardTitle>
              <CardDescription>設定您的語言和時區偏好</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">語言</p>
                    <p className="text-sm text-gray-600">選擇介面顯示語言</p>
                  </div>
                </div>
                <Select defaultValue={data.preferences.language}>
                  <SelectTrigger className="w-32">
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
            </CardContent>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>外觀設定</CardTitle>
              <CardDescription>自訂您的介面外觀</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Palette className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">主題模式</p>
                    <p className="text-sm text-gray-600">選擇亮色或暗色主題</p>
                  </div>
                </div>
                <Select defaultValue={data.preferences.theme}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">亮色</SelectItem>
                    <SelectItem value="dark">暗色</SelectItem>
                    <SelectItem value="auto">自動</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-lg">
            <CardHeader>
              <CardTitle>通知設定</CardTitle>
              <CardDescription>控制您接收通知的方式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">電子郵件通知</p>
                    <p className="text-sm text-gray-600">接收重要更新和提醒</p>
                  </div>
                </div>
                <Switch checked={data.preferences.notifications?.email} />
              </div>

              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">桌面通知</p>
                    <p className="text-sm text-gray-600">即時瀏覽器推播通知</p>
                  </div>
                </div>
                <Switch checked={data.preferences.notifications?.desktop} />
              </div>

              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 text-[var(--color-accent-purple-500)]">✨</div>
                  <div>
                    <p className="font-medium text-gray-900">AI 建議通知</p>
                    <p className="text-sm text-gray-600">接收 AI 的智能建議</p>
                  </div>
                </div>
                <Switch checked={data.preferences.notifications?.aiSuggestions} />
              </div>

              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-gray-600" />
                  <div>
                    <p className="font-medium text-gray-900">每週報告</p>
                    <p className="text-sm text-gray-600">每週活動摘要</p>
                  </div>
                </div>
                <Switch checked={data.preferences.notifications?.weeklyReport} />
              </div>
            </CardContent>
          </Card>

          <Button
            onClick={() => handleSave('preferences')}
            disabled={isSaving}
            className="bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]"
          >
            {isSaving ? '儲存中...' : '儲存偏好設定'}
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default Settings
