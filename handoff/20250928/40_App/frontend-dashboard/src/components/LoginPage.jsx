import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
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
      if (credentials.username === 'admin' && credentials.password === 'admin123') {
        const mockUser = {
          id: 1,
          name: t('sidebar.user.defaultName'),
          username: 'admin',
          role: t('sidebar.user.defaultRole'),
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div style={{ position: 'fixed', top: '1rem', right: '1rem', zIndex: 50 }}>
        <LanguageSwitcher variant="compact" />
      </div>
      
      <div className="w-full max-w-md px-4">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 mb-4">
            <img 
              src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
              alt="Morning AI" 
              className="w-full h-full rounded-2xl"
              style={{ width: '64px', height: '64px', maxWidth: '64px', maxHeight: '64px' }}
            />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('app.name')}</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">{t('app.tagline')}</p>
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
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
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
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
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

            <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">{t('auth.login.devAccount')}</h4>
              <div className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                <p>{t('auth.login.username')}: <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">admin</code></p>
                <p>{t('auth.login.password')}: <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">admin123</code></p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="text-center mt-8 text-sm text-gray-500 dark:text-gray-400">
          <p>{t('app.copyright')}</p>
          <p className="mt-1">{t('app.motto')}</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage

