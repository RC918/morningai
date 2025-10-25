import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Lock, User, AlertCircle, Loader2, Mail, CheckCircle } from 'lucide-react'
import { AppleButton } from '@/components/ui/apple-button'
import { AppleInput } from '@/components/ui/apple-input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { LanguageSwitcher } from './LanguageSwitcher'
import { supabase } from '@/lib/supabaseClient'
import { signInWithOAuth } from '@/lib/supabaseClient'

const SignupPage = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

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
    setSuccess(false)

    if (formData.password !== formData.confirmPassword) {
      setError(t('auth.signup.passwordMismatch', 'Passwords do not match'))
      setLoading(false)
      return
    }

    if (formData.password.length < 6) {
      setError(t('auth.signup.passwordTooShort', 'Password must be at least 6 characters'))
      setLoading(false)
      return
    }

    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          data: {
            full_name: formData.fullName
          }
        }
      })

      if (signUpError) {
        setError(signUpError.message)
        setLoading(false)
        return
      }

      if (data.user) {
        setSuccess(true)
        setTimeout(() => {
          navigate('/login')
        }, 3000)
      }
    } catch (error) {
      console.error('Signup error:', error)
      setError(t('auth.signup.signupError', 'An error occurred during signup'))
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSSOSignup = async (provider) => {
    try {
      setLoading(true)
      setError('')
      
      const { error } = await signInWithOAuth(provider, {
        redirectTo: `${window.location.origin}/auth/callback`
      })
      
      if (error) {
        setError(t('auth.sso.initializationFailed'))
        setLoading(false)
      }
    } catch (error) {
      console.error('SSO signup error:', error)
      setError(t('auth.sso.initializationFailed'))
      setLoading(false)
    }
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
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
        variants={prefersReducedMotion ? {} : containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div
          className="text-center mb-8"
          variants={prefersReducedMotion ? {} : itemVariants}
        >
          <Link to="/" className="inline-block">
            <motion.div
              className="mx-auto w-16 h-16 mb-4"
              whileHover={prefersReducedMotion ? {} : { scale: 1.1, rotate: 5 }}
              transition={{ duration: 0.3 }}
            >
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-full h-full rounded-2xl cursor-pointer"
                style={{ width: '64px', height: '64px', maxWidth: '64px', maxHeight: '64px' }}
              />
            </motion.div>
          </Link>
          <Link to="/" className="inline-block hover:opacity-80 transition-opacity">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{t('app.name')}</h1>
          </Link>
          <p className="text-gray-600 dark:text-gray-600 mt-2">{t('app.tagline')}</p>
        </motion.div>

        <motion.div variants={prefersReducedMotion ? {} : itemVariants}>
          <Card>
            <CardHeader>
              <CardTitle>{t('auth.signup.title', '創建帳號')}</CardTitle>
              <CardDescription>
                {t('auth.signup.description', '填寫以下資訊以創建您的帳號')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {success ? (
                <motion.div
                  initial={prefersReducedMotion ? {} : { opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-8"
                >
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    {t('auth.signup.successTitle', '註冊成功！')}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-600 mb-4">
                    {t('auth.signup.successMessage', '請檢查您的電子郵件以驗證帳號。')}
                  </p>
                  <p className="text-sm text-gray-500">
                    {t('auth.signup.redirecting', '正在跳轉到登入頁面...')}
                  </p>
                </motion.div>
              ) : (
                <>
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
                      id="fullName"
                      name="fullName"
                      type="text"
                      label={t('auth.signup.fullName', '姓名')}
                      placeholder={t('auth.signup.fullNamePlaceholder', '請輸入您的姓名')}
                      value={formData.fullName}
                      onChange={handleChange}
                      leftIcon={<User className="w-4 h-4" />}
                      required
                      haptic="light"
                    />

                    <AppleInput
                      id="email"
                      name="email"
                      type="email"
                      label={t('auth.signup.email', '電子郵件')}
                      placeholder={t('auth.signup.emailPlaceholder', '請輸入電子郵件')}
                      value={formData.email}
                      onChange={handleChange}
                      leftIcon={<Mail className="w-4 h-4" />}
                      required
                      haptic="light"
                    />

                    <AppleInput
                      id="password"
                      name="password"
                      type="password"
                      label={t('auth.signup.password', '密碼')}
                      placeholder={t('auth.signup.passwordPlaceholder', '至少 6 個字元')}
                      value={formData.password}
                      onChange={handleChange}
                      leftIcon={<Lock className="w-4 h-4" />}
                      showPasswordToggle
                      required
                      minLength={6}
                      haptic="light"
                      helperText={t('auth.signup.passwordHelp', '密碼至少需要 6 個字元')}
                    />

                    <AppleInput
                      id="confirmPassword"
                      name="confirmPassword"
                      type="password"
                      label={t('auth.signup.confirmPassword', '確認密碼')}
                      placeholder={t('auth.signup.confirmPasswordPlaceholder', '再次輸入密碼')}
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      leftIcon={<Lock className="w-4 h-4" />}
                      showPasswordToggle
                      required
                      haptic="light"
                    />

                    <motion.div
                      whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
                      whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
                    >
                      <AppleButton 
                        type="submit" 
                        className="w-full" 
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {t('auth.signup.signingUp', '註冊中...')}
                          </>
                        ) : (
                          t('auth.signup.signupButton', '註冊')
                        )}
                      </AppleButton>
                    </motion.div>
                  </form>

                  <div className="mt-6">
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <Separator className="w-full" />
                      </div>
                      <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-white dark:bg-gray-800 px-2 text-gray-500">
                          {t('auth.signup.orSignupWith', '或使用以下方式註冊')}
                        </span>
                      </div>
                    </div>

                    <div className="mt-6 grid grid-cols-3 gap-3">
                      <AppleButton
                        type="button"
                        variant="outline"
                        onClick={() => handleSSOSignup('google')}
                        disabled={loading}
                        className="w-full"
                        aria-label={t('auth.sso.signupWithGoogle', '使用 Google 註冊')}
                      >
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                          <path
                            fill="currentColor"
                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                          />
                          <path
                            fill="currentColor"
                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                          />
                          <path
                            fill="currentColor"
                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                          />
                          <path
                            fill="currentColor"
                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                          />
                        </svg>
                      </AppleButton>

                      <AppleButton
                        type="button"
                        variant="outline"
                        onClick={() => handleSSOSignup('apple')}
                        disabled={loading}
                        className="w-full"
                        aria-label={t('auth.sso.signupWithApple', '使用 Apple 註冊')}
                      >
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
                        </svg>
                      </AppleButton>

                      <AppleButton
                        type="button"
                        variant="outline"
                        onClick={() => handleSSOSignup('github')}
                        disabled={loading}
                        className="w-full"
                        aria-label={t('auth.sso.signupWithGitHub', '使用 GitHub 註冊')}
                      >
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
                        </svg>
                      </AppleButton>
                    </div>
                  </div>

                  <div className="mt-6 text-center text-sm text-gray-600 dark:text-gray-600">
                    {t('auth.signup.alreadyHaveAccount', '已經有帳號了？')}{' '}
                    <Link to="/login" className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium">
                      {t('auth.signup.loginLink', '登入')}
                    </Link>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          className="text-center mt-8 text-sm text-gray-600 dark:text-gray-600"
          variants={prefersReducedMotion ? {} : itemVariants}
        >
          <p>{t('app.copyright')}</p>
          <p className="mt-1">{t('app.motto')}</p>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default SignupPage
