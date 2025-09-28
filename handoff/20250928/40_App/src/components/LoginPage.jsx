import { useState } from 'react'
import { Brain, Lock, User, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

const LoginPage = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // 模擬API調用
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      })

      if (response.ok) {
        const data = await response.json()
        onLogin(data.user, data.token)
      } else {
        const errorData = await response.json()
        setError(errorData.message || '登錄失敗，請檢查用戶名和密碼')
      }
    } catch (error) {
      // 開發環境下的模擬登錄
      if (credentials.username === 'admin' && credentials.password === 'admin123') {
        const mockUser = {
          id: 1,
          name: '系統管理員',
          username: 'admin',
          role: '超級管理員',
          avatar: null
        }
        const mockToken = 'mock-jwt-token-' + Date.now()
        onLogin(mockUser, mockToken)
      } else {
        setError('登錄失敗：用戶名或密碼錯誤')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md">
        {/* Logo和標題 */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Morning AI</h1>
          <p className="text-gray-600 mt-2">智能決策系統管理平台</p>
        </div>

        {/* 登錄表單 */}
        <Card>
          <CardHeader>
            <CardTitle>登錄到系統</CardTitle>
            <CardDescription>
              請輸入您的憑證以訪問管理儀表板
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="username">用戶名</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="username"
                    name="username"
                    type="text"
                    placeholder="請輸入用戶名"
                    value={credentials.username}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">密碼</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder="請輸入密碼"
                    value={credentials.password}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    登錄中...
                  </div>
                ) : (
                  '登錄'
                )}
              </Button>
            </form>

            {/* 開發環境提示 */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2">開發環境測試帳號</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>用戶名: <code className="bg-blue-100 px-1 rounded">admin</code></p>
                <p>密碼: <code className="bg-blue-100 px-1 rounded">admin123</code></p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 底部信息 */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>© 2024 Morning AI. 版權所有</p>
          <p className="mt-1">智能決策，自主學習，持續優化</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage

