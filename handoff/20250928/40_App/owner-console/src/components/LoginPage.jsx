import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react'
import { AppleButton } from '@/components/apple/apple-button'
import { AppleInput } from '@/components/apple/apple-input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Alert, AlertDescription } from '@morningai/shared-ui'
import { LanguageSwitcher } from './LanguageSwitcher'
import { TwoFactorVerify } from './2fa/TwoFactorVerify'
import { TwoFactorEnroll } from './2fa/TwoFactorEnroll'
import { sanitizeRedirect } from '@/lib/redirect-security'

const LoginPage = ({ onLogin, onRefreshUser, redirectPath = '/' }) => {
  const { t } = useTranslation()
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  const [show2FADialog, setShow2FADialog] = useState(false)
  const [show2FAEnrollDialog, setShow2FAEnrollDialog] = useState(false)
  const [tmpLoginToken, setTmpLoginToken] = useState('')

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)
    
    const handleChange = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handleChange)
    
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const result = await onLogin(credentials)
      
      if (result && result.next_step) {
        const preAuthToken = result.token || result.tmp_login_token
        if (preAuthToken) {
          setTmpLoginToken(preAuthToken)
        }
        
        if (result.next_step === 'enroll_2fa') {
          setShow2FAEnrollDialog(true)
          setLoading(false)
          return
        } else if (result.next_step === 'challenge_2fa') {
          setShow2FADialog(true)
          setLoading(false)
          return
        }
      }
      
      if (result && result.requires_2fa) {
        setShow2FADialog(true)
        setLoading(false)
        return
      }
    } catch (error) {
      console.error('Login error:', error)
      setError(error.message || t('auth.login.loginError'))
    } finally {
      setLoading(false)
    }
  }

  const handle2FAVerify = async (params) => {
    if (tmpLoginToken) {
      const { challengeTwoFA } = await import('@/lib/2fa-api')
      const { storeAccessToken, storeTokenExpiry } = await import('@/lib/auth')
      
      const response = await challengeTwoFA({
        code: params.isBackup ? undefined : params.code,
        backup_code: params.isBackup ? params.code : undefined,
        remember_device: params.rememberDevice,
      }, tmpLoginToken)

      // Store tokens from 2FA response
      if (response?.tokens) {
        if (response.tokens.accessToken) {
          storeAccessToken(response.tokens.accessToken)
        }
        if (response.tokens.expiresAt) {
          storeTokenExpiry(response.tokens.expiresAt)
        }
      }

      setShow2FADialog(false)
      setTmpLoginToken('')
      
      try {
        if (onRefreshUser) {
          await onRefreshUser()
        }
        if (redirectPath && redirectPath !== '/' && typeof window !== 'undefined') {
          const safeRedirect = sanitizeRedirect(redirectPath)
          window.location.href = safeRedirect
        }
      } catch (error) {
        setError(error.message || t('auth.login.loginError'))
      }
    } else {
      const { verifyTwoFALogin } = await import('@/lib/2fa-api')
      const { storeAccessToken, storeTokenExpiry } = await import('@/lib/auth')
      
      const response = await verifyTwoFALogin({
        email: credentials.email,
        password: credentials.password,
        totp_code: params.isBackup ? undefined : params.code,
        backup_code: params.isBackup ? params.code : undefined,
        remember_device: params.rememberDevice,
      })

      // Store tokens from 2FA response
      if (response?.tokens) {
        if (response.tokens.accessToken) {
          storeAccessToken(response.tokens.accessToken)
        }
        if (response.tokens.expiresAt) {
          storeTokenExpiry(response.tokens.expiresAt)
        }
      }

      setShow2FADialog(false)
      
      try {
        if (onRefreshUser) {
          await onRefreshUser()
        }
        if (redirectPath && redirectPath !== '/' && typeof window !== 'undefined') {
          const safeRedirect = sanitizeRedirect(redirectPath)
          window.location.href = safeRedirect
        }
      } catch (error) {
        setError(error.message || t('auth.login.loginError'))
      }
    }
  }

  const handle2FACancel = () => {
    setShow2FADialog(false)
    setShow2FAEnrollDialog(false)
    setTmpLoginToken('')
    setError('')
  }

  const handle2FAEnroll = async (params) => {
    setShow2FAEnrollDialog(false)
    setTmpLoginToken('')
    
    try {
      if (onRefreshUser) {
        await onRefreshUser()
      }
      if (redirectPath && redirectPath !== '/' && typeof window !== 'undefined') {
        const safeRedirect = sanitizeRedirect(redirectPath)
        window.location.href = safeRedirect
      }
    } catch (error) {
      setError(error.message || t('auth.login.loginError'))
    }
  }

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    })
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.22, 1, 0.36, 1]
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 dark:bg-neutral-900">
      <motion.div
        style={{ position: 'fixed', top: '1rem', right: '1rem', zIndex: 50 }}
        initial={prefersReducedMotion ? {} : { opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <LanguageSwitcher variant="compact" />
      </motion.div>
      
      <motion.div
        className="w-full max-w-md px-4"
        data-testid="login-card"
        variants={prefersReducedMotion ? {} : containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div
          className="text-center mb-8"
          variants={prefersReducedMotion ? {} : itemVariants}
        >
          <motion.div
            className="mx-auto w-16 h-16 mb-4"
            whileHover={prefersReducedMotion ? {} : { scale: 1.1, rotate: 5 }}
            transition={{ duration: 0.3 }}
          >
            <img 
              src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
              alt="Morning AI" 
              className="w-full h-full rounded-2xl"
              style={{ width: '64px', height: '64px', maxWidth: '64px', maxHeight: '64px' }}
            />
          </motion.div>
          <h1 className="text-3xl font-bold text-neutral-900 dark:text-white">{t('app.name')}</h1>
          <p className="text-neutral-600 dark:text-neutral-400 mt-2">{t('app.tagline')}</p>
        </motion.div>

        <motion.div variants={prefersReducedMotion ? {} : itemVariants}>
          <Card className="!py-6 border-neutral-200 dark:border-neutral-800">
            <CardHeader className="pt-1 pb-3">
              <CardTitle className="leading-tight">{t('auth.login.title')}</CardTitle>
              <CardDescription className="mt-1.5">
                {t('auth.login.description')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <motion.div
                    initial={prefersReducedMotion ? {} : { opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  </motion.div>
                )}

                <AppleInput
                  id="email"
                  name="email"
                  type="email"
                  label={t('auth.login.email', 'Email')}
                  placeholder={t('auth.login.emailPlaceholder', 'owner@morningai.com')}
                  value={credentials.email}
                  onChange={handleChange}
                  leftIcon={<User className="h-4 w-4" />}
                  required
                  haptic="light"
                />

                <AppleInput
                  id="password"
                  name="password"
                  type="password"
                  label={t('auth.login.password')}
                  placeholder={t('auth.login.passwordPlaceholder')}
                  value={credentials.password}
                  onChange={handleChange}
                  leftIcon={<Lock className="h-4 w-4" />}
                  showPasswordToggle
                  required
                  haptic="light"
                />

                <AppleButton 
                  type="submit" 
                  className="w-full" 
                  disabled={loading}
                  variant="primary"
                  size="default"
                  haptic="medium"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {t('auth.login.loggingIn')}
                    </>
                  ) : (
                    t('auth.login.loginButton')
                  )}
                </AppleButton>
              </form>

              <div className="mt-6 p-4 bg-neutral-100 dark:bg-neutral-800 rounded-lg">
                <h4 className="text-sm font-medium text-neutral-900 dark:text-white mb-2">{t('auth.login.devAccount', 'Development Account')}</h4>
                <div className="text-sm text-neutral-700 dark:text-neutral-300 space-y-1">
                  <p>{t('auth.login.email', 'Email')}: <code className="bg-neutral-200 dark:bg-neutral-700 px-1 rounded">{t('auth.login.emailPlaceholder', 'owner@morningai.com')}</code></p>
                  <p>{t('auth.login.password', 'Password')}: <code className="bg-neutral-200 dark:bg-neutral-700 px-1 rounded">{t('auth.login.passwordPlaceholder', 'owner123')}</code></p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          className="text-center mt-8 text-sm text-neutral-600 dark:text-neutral-400"
          variants={prefersReducedMotion ? {} : itemVariants}
        >
          <p>{t('app.copyright')}</p>
          <p className="mt-1">{t('app.motto')}</p>
        </motion.div>
      </motion.div>

      <TwoFactorVerify
        open={show2FADialog}
        onClose={handle2FACancel}
        onVerify={handle2FAVerify}
      />

      <TwoFactorEnroll
        open={show2FAEnrollDialog}
        onClose={handle2FACancel}
        onComplete={handle2FAEnroll}
        tmpLoginToken={tmpLoginToken}
      />
    </div>
  )
}

export default LoginPage

