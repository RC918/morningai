import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { motion } from 'framer-motion'
import { LanguageSwitcher } from './LanguageSwitcher'
import apiClient from '@/lib/api'

const LoginPage = ({ onLogin }) => {
  const { t } = useTranslation()
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
      const result = await apiClient.login(credentials)
      
      if (result.user && result.token) {
        onLogin(result.user, result.token)
      } else {
        setError(result.message || t('auth.login.loginFailed'))
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
        setError(t('auth.login.loginError'))
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
      <div style={{ position: 'fixed', top: '1rem', right: '1rem', zIndex: 50 }}>
        <LanguageSwitcher variant="compact" />
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Logo和標題 */}
        <div className="text-center mb-8">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
            className="mx-auto w-16 h-16 mb-4"
          >
            <img 
              src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
              alt="Morning AI" 
              className="w-full h-full rounded-2xl"
              style={{ width: '64px', height: '64px', maxWidth: '64px', maxHeight: '64px' }}
            />
          </motion.div>
          <h1 className="text-3xl font-bold text-gray-900">{t('app.name')}</h1>
          <p className="text-gray-600 mt-2">{t('app.tagline')}</p>
        </div>

        {/* 登錄表單 */}
        <Card>
          <CardHeader>
            <CardTitle>{t('auth.login.title')}</CardTitle>
            <CardDescription>
              {t('auth.login.description')}
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
                <Label htmlFor="username">{t('auth.login.username')}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="username"
                    name="username"
                    type="text"
                    placeholder={t('auth.login.usernamePlaceholder')}
                    value={credentials.username}
                    onChange={handleChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t('auth.login.password')}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    placeholder={t('auth.login.passwordPlaceholder')}
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
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('auth.login.loggingIn')}
                  </>
                ) : (
                  t('auth.login.loginButton')
                )}
              </Button>
            </form>

            {/* 開發環境提示 */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2">{t('auth.login.devAccount')}</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>{t('auth.login.username')}: <code className="bg-blue-100 px-1 rounded">admin</code></p>
                <p>{t('auth.login.password')}: <code className="bg-blue-100 px-1 rounded">admin123</code></p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 底部信息 */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>{t('app.copyright')}</p>
          <p className="mt-1">{t('app.motto')}</p>
        </div>
      </motion.div>
    </div>
  )
}

export default LoginPage

