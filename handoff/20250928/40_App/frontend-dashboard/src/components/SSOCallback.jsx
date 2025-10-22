import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ssoAuthService } from '@/lib/auth/sso'
import useAppStore from '@/stores/appStore'

const SSOCallback = ({ provider }) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('processing')
  const [error, setError] = useState(null)
  const { setUser, addToast } = useAppStore()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        setStatus('processing')
        
        const result = await ssoAuthService.handleCallback(provider, searchParams)
        
        if (result.user && result.token) {
          setUser(result.user)
          setStatus('success')
          
          addToast({
            title: t('auth.sso.loginSuccess'),
            description: t('auth.login.welcomeBack', { name: result.user.name }),
            variant: "default"
          })
          
          setTimeout(() => {
            navigate('/dashboard')
          }, 1000)
        } else {
          throw new Error('Invalid response from SSO provider')
        }
      } catch (err) {
        console.error('SSO callback error:', err)
        setError(err.message)
        setStatus('error')
        
        addToast({
          title: t('auth.sso.loginFailed'),
          description: err.message,
          variant: "destructive"
        })
        
        setTimeout(() => {
          navigate('/login')
        }, 3000)
      }
    }

    handleCallback()
  }, [provider, searchParams, navigate, setUser, addToast, t])

  const getProviderName = () => {
    const names = {
      google: 'Google',
      apple: 'Apple',
      github: 'GitHub'
    }
    return names[provider] || provider
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md px-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="text-center">
            {status === 'processing' && (
              <>
                <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {t('auth.sso.processing')}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {t('auth.sso.processingMessage', { provider: getProviderName() })}
                </p>
              </>
            )}

            {status === 'success' && (
              <>
                <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {t('auth.sso.success')}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {t('auth.sso.successMessage')}
                </p>
              </>
            )}

            {status === 'error' && (
              <>
                <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {t('auth.sso.error')}
                </h2>
                <Alert variant="destructive" className="mt-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
                <p className="text-gray-600 dark:text-gray-400 mt-4">
                  {t('auth.sso.redirectingToLogin')}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SSOCallback
