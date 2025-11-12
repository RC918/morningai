import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { TolgeeProvider } from '@tolgee/react'
import { Toaster } from '@morningai/shared-ui'
import { toast } from '@/lib/toast-with-announcement'
import { AppleLiveActivity } from '@/components/ui/apple-live-activity'
import { AppleActionSheet } from '@/components/ui/apple-action-sheet'
import { AppleSpotlight } from '@/components/ui/apple-spotlight'
import { AppleControlCenter } from '@/components/ui/apple-control-center'
import { AccessibilityProvider } from '@/components/ui/apple-accessibility-settings'
import ErrorBoundary from '@/components/ErrorBoundary'
import Sidebar from '@/components/Sidebar'
import GlobalSearch from '@/components/GlobalSearch'
import LoginPage from '@/components/LoginPage'
import SignupPage from '@/components/SignupPage'
import LandingPage from '@/components/LandingPage'
import WIPPage from '@/components/WIPPage'
import { TenantProvider } from '@/contexts/TenantContext'
import { NotificationProvider, useNotification } from '@/contexts/NotificationContext'
import { PageLoader } from '@/components/feedback/PageLoader'
import { OfflineIndicator } from '@/components/feedback/OfflineIndicator'
import { SkipToContent } from '@/components/SkipToContent'
import { applyDesignTokens } from '@morningai/shared-ui'
import { isFeatureEnabled, AVAILABLE_FEATURES } from '@/lib/feature-flags'
import { reportWebVitals } from '@/lib/performance'
import useAppStore from '@/stores/appStore'
import apiClient from '@/lib/api'
import { bootstrapCsrf } from '@/lib/api-client'
import { supabase, getSession, signInWithOAuth } from '@/lib/supabaseClient'
import '@/i18n/config'
import { tolgee } from '@/i18n/config'
import './App.css'
import './styles/mobile-optimizations.css'
import './styles/motion-governance.css'
import './styles/micro-interactions.css'
import './styles/theme-apple.css'
import './styles/final-override.css'

const Dashboard = lazy(() => import('@/components/Dashboard'))
const StrategyManagement = lazy(() => import('@/components/StrategyManagement'))
const DecisionApproval = lazy(() => import('@/components/DecisionApproval'))
const HistoryAnalysis = lazy(() => import('@/components/HistoryAnalysis'))
const CostAnalysis = lazy(() => import('@/components/CostAnalysis'))
const AgentGovernance = lazy(() => import('@/components/AgentGovernance'))
const SystemSettings = lazy(() => import('@/components/SystemSettings'))
const TenantSettings = lazy(() => import('@/components/TenantSettings'))
const CheckoutPage = lazy(() => import('@/components/CheckoutPage'))
const CheckoutSuccess = lazy(() => import('@/components/CheckoutSuccess'))
const CheckoutCancel = lazy(() => import('@/components/CheckoutCancel'))
const AuthCallback = lazy(() => import('@/components/AuthCallback'))
const Settings2FA = lazy(() => import('@/pages/Settings2FA'))

function AppContent() {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [redirectToLogin, setRedirectToLogin] = useState<string | null>(null)
  const { user, setUser, addToast } = useAppStore()

  useEffect(() => {
    if (!isAuthenticated && redirectToLogin !== null) {
      const returnUrl = encodeURIComponent(redirectToLogin)
      navigate(`/login?returnUrl=${returnUrl}`, { replace: true })
      setRedirectToLogin(null)
    }
  }, [isAuthenticated, redirectToLogin, navigate])

  useEffect(() => {
    const PUBLIC_ROUTES = new Set(['/', '/login', '/signup', '/pricing', '/auth/callback'])
    if (isAuthenticated && PUBLIC_ROUTES.has(location.pathname)) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, location.pathname, navigate])

  useEffect(() => {
    const handleApiError = (event: Event) => {
      const customEvent = event as CustomEvent
      const { endpoint, error, status, requestId } = customEvent.detail
      addToast({
        title: t('common.apiError'),
        description: `${endpoint}: ${error} (ID: ${requestId})`,
        variant: "destructive"
      })
    }

    const handleAuthError = async (event: Event) => {
      const customEvent = event as CustomEvent
      const { endpoint, message } = customEvent.detail
      console.warn('Auth error detected, logging out:', { endpoint, message })
      
      try {
        await supabase.auth.signOut()
      } catch (error) {
        console.error('Supabase signOut error during auth-error:', error)
      }
      
      document.cookie = 'csrf_token=; Max-Age=0; path=/; SameSite=None; Secure'
      
      setIsAuthenticated(false)
      setUser({
        id: null,
        name: '',
        email: '',
        avatar: '',
        role: '',
        tenant_id: ''
      })
      
      const isAuthRoute = ['/login', '/signup', '/auth'].some(p => window.location.pathname.startsWith(p))
      if (isAuthRoute) {
        setRedirectToLogin('/')
      } else {
        const returnUrl = window.location.pathname + window.location.search
        setRedirectToLogin(returnUrl)
      }
      
      addToast({
        title: t('auth.sessionExpired'),
        description: t('auth.pleaseSignInAgain'),
        variant: "destructive"
      })
    }

    window.addEventListener('api-error', handleApiError as EventListener)
    window.addEventListener('auth-error', handleAuthError as EventListener)

    const PUBLIC_ROUTES = new Set(['/', '/login', '/signup', '/pricing', '/auth/callback'])
    if (PUBLIC_ROUTES.has(location.pathname)) {
      setLoading(false)
      return () => {
        window.removeEventListener('api-error', handleApiError as EventListener)
        window.removeEventListener('auth-error', handleAuthError as EventListener)
      }
    }

    if (isAuthenticated) {
      setLoading(false)
      return () => {
        window.removeEventListener('api-error', handleApiError as EventListener)
        window.removeEventListener('auth-error', handleAuthError as EventListener)
      }
    }

    const checkAuth = async () => {
      try {
        const { session, error: sessionError } = await getSession()
        
        if (session && !sessionError) {
          const csrfBootstrapped = await bootstrapCsrf()
          if (!csrfBootstrapped) {
            console.error('CSRF bootstrap failed, clearing state and redirecting to login')
            try {
              await supabase.auth.signOut()
            } catch (error) {
              console.error('Supabase signOut error during CSRF failure:', error)
            }
            document.cookie = 'csrf_token=; Max-Age=0; path=/; SameSite=None; Secure'
            setUser({
              id: null,
              name: '',
              email: '',
              avatar: '',
              role: '',
              tenant_id: ''
            })
            setIsAuthenticated(false)
            setRedirectToLogin(location.pathname + location.search)
            setLoading(false)
            return
          }
          
          const supabaseUser = session.user
          setUser({
            id: supabaseUser.id,
            name: supabaseUser.user_metadata?.full_name || supabaseUser.email?.split('@')[0] || 'User',
            email: supabaseUser.email,
            avatar: supabaseUser.user_metadata?.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${supabaseUser.email}`,
            role: 'Owner',
            tenant_id: 'tenant_001'
          })
          setIsAuthenticated(true)
          setLoading(false)
          return
        }
        
        try {
          const csrfBootstrapped = await bootstrapCsrf()
          if (!csrfBootstrapped) {
            console.error('CSRF bootstrap failed, clearing state and redirecting to login')
            document.cookie = 'csrf_token=; Max-Age=0; path=/; SameSite=None; Secure'
            setUser({
              id: null,
              name: '',
              email: '',
              avatar: '',
              role: '',
              tenant_id: ''
            })
            setIsAuthenticated(false)
            setRedirectToLogin(location.pathname + location.search)
            setLoading(false)
            return
          }
          
          const userData = await apiClient.getCurrentUser()
          setUser(userData)
          setIsAuthenticated(true)
        } catch (authError) {
          if (import.meta.env.DEV) {
            setUser({
              id: 'dev_user',
              name: 'Ryan Chen',
              email: 'ryan@morningai.com',
              avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
              role: 'Owner',
              tenant_id: 'tenant_001'
            })
            setIsAuthenticated(true)
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        if (import.meta.env.DEV) {
          setUser({
            id: 'dev_user',
            name: 'Ryan Chen',
            email: 'ryan@morningai.com',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
            role: 'Owner',
            tenant_id: 'tenant_001'
          })
          setIsAuthenticated(true)
        }
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
    applyDesignTokens('.theme-morning-ai')

    return () => {
      window.removeEventListener('api-error', handleApiError as EventListener)
      window.removeEventListener('auth-error', handleAuthError as EventListener)
    }
  }, [addToast, setUser, t, isAuthenticated, location.pathname, location.search])

  const handleLogin = (userData: any) => {
    setUser(userData)
    setIsAuthenticated(true)
    addToast({
      title: t('auth.login.loginSuccess'),
      description: t('auth.login.welcomeBack', { name: userData.name }),
      variant: "default"
    })
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
    } catch (error) {
      console.error('Supabase signOut error:', error)
    }
    
    document.cookie = 'csrf_token=; Max-Age=0; path=/; SameSite=None; Secure'
    
    setUser({
      id: null,
      name: '',
      email: '',
      avatar: '',
      role: '',
      tenant_id: ''
    })
    setIsAuthenticated(false)
    addToast({
      title: t('auth.logout.logoutSuccess'),
      description: t('auth.logout.logoutMessage'),
      variant: "default"
    })
    
    navigate('/', { replace: true })
  }

  if (loading) {
    return <PageLoader message={t('common.loadingApp')} />
  }

  const handleNavigateToLogin = () => {
    window.location.href = '/login'
  }

  const handleSSOLogin = async (provider: string) => {
    try {
      const { error } = await signInWithOAuth(provider, {
        redirectTo: `${window.location.origin}/auth/callback`
      })
      
      if (error) {
        console.error('SSO login error:', error)
        addToast({
          title: t('auth.login.loginError'),
          description: error.message,
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('SSO login error:', error)
      addToast({
        title: t('auth.login.loginError'),
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: "destructive"
      })
    }
  }

  return (
    <ErrorBoundary>
      <div className="theme-morning-ai theme-apple">
        <OfflineIndicator />
        
        {!isAuthenticated ? (
          <Routes>
            <Route path="/" element={<LandingPage onNavigateToLogin={handleNavigateToLogin} onSSOLogin={handleSSOLogin} />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        ) : (
          <TenantProvider>
          <div className="flex h-screen bg-gray-100">
          <SkipToContent />
          <Sidebar user={user} onLogout={handleLogout} />
          
          <main id="main-content" className="flex-1 overflow-y-auto" role="main" aria-label={t('common.mainContentArea')}>
            <Suspense fallback={<PageLoader message={t('common.loadingPage')} />}>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Feature-gated routes */}
          {isFeatureEnabled(AVAILABLE_FEATURES.DASHBOARD) && (
            <Route path="/dashboard" element={<Dashboard />} />
          )}
          {isFeatureEnabled(AVAILABLE_FEATURES.STRATEGIES) ? (
            <Route path="/strategies" element={<StrategyManagement />} />
          ) : (
            <Route path="/strategies" element={<WIPPage title={t('wip.strategyManagement')} />} />
          )}
          {isFeatureEnabled(AVAILABLE_FEATURES.APPROVALS) ? (
            <Route path="/approvals" element={<DecisionApproval />} />
          ) : (
            <Route path="/approvals" element={<WIPPage title={t('wip.decisionApproval')} />} />
          )}
          {isFeatureEnabled(AVAILABLE_FEATURES.HISTORY) ? (
            <Route path="/history" element={<HistoryAnalysis />} />
          ) : (
            <Route path="/history" element={<WIPPage title={t('wip.historyAnalysis')} />} />
          )}
          {isFeatureEnabled(AVAILABLE_FEATURES.COSTS) ? (
            <Route path="/costs" element={<CostAnalysis />} />
          ) : (
            <Route path="/costs" element={<WIPPage title={t('wip.costAnalysis')} />} />
          )}
          <Route path="/governance" element={<AgentGovernance />} />
          {isFeatureEnabled(AVAILABLE_FEATURES.SETTINGS) ? (
            <Route path="/settings" element={<SystemSettings />} />
          ) : (
            <Route path="/settings" element={<WIPPage title={t('wip.systemSettings')} />} />
          )}
          <Route path="/tenant-settings" element={<TenantSettings />} />
          <Route path="/settings/2fa" element={<Settings2FA />} />
          {isFeatureEnabled(AVAILABLE_FEATURES.CHECKOUT) ? (
            <Route path="/checkout" element={<CheckoutPage />} />
          ) : (
            <Route path="/checkout" element={<WIPPage title={t('wip.checkoutPage')} />} />
          )}
          <Route path="/checkout/success" element={<CheckoutSuccess />} />
          <Route path="/checkout/cancel" element={<CheckoutCancel />} />

          {/* WIP pages for disabled features */}
          <Route path="/wip" element={<WIPPage />} />
          
          {/* Fallback to dashboard if no dashboard feature enabled */}
          {!isFeatureEnabled(AVAILABLE_FEATURES.DASHBOARD) && (
            <Route path="/dashboard" element={<WIPPage title={t('wip.dashboard')} />} />
          )}
          
          {/* Catch-all route for authenticated users */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
          </main>
          
            <Toaster />
            <GlobalSearch />
          </div>
          </TenantProvider>
        )}
      </div>
    </ErrorBoundary>
  )
}

function App() {
  useEffect(() => {
    const sentryDsn = import.meta.env.VITE_SENTRY_DSN
    if (sentryDsn && !window.__SENTRY_INITIALIZED__) {
      import('@sentry/react').then((Sentry) => {
        Sentry.init({
          dsn: sentryDsn,
          environment: import.meta.env.MODE,
          integrations: [
            Sentry.browserTracingIntegration(),
            Sentry.replayIntegration()
          ],
          tracesSampleRate: 1.0,
          replaysSessionSampleRate: 0.1,
          replaysOnErrorSampleRate: 1.0,
        })
        window.Sentry = Sentry
        window.__SENTRY_INITIALIZED__ = true
      })
    }

    reportWebVitals((metric) => {
      if (import.meta.env.DEV) {
        console.log(`[Web Vitals] ${metric.name}:`, metric.value, metric)
      }
      
      if (import.meta.env.PROD && window.gtag) {
        window.gtag('event', metric.name, {
          value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
          event_category: 'Web Vitals',
          event_label: metric.id,
          non_interaction: true,
        })
      }
    })
  }, [])

  return (
    <ThemeProvider defaultTheme="system" storageKey="morningai-theme">
      <TolgeeProvider tolgee={tolgee} fallback={<PageLoader message="Loading translations..." />}>
        <NotificationProvider>
          <AccessibilityProvider>
            <AppleActionSheet.Provider>
              <AppleSpotlight.Provider>
                <AppleControlCenter.Provider>
                  <AppleLiveActivity.Provider position="top">
                    <Router>
                      <AppContent />
                    </Router>
                  </AppleLiveActivity.Provider>
                </AppleControlCenter.Provider>
              </AppleSpotlight.Provider>
            </AppleActionSheet.Provider>
          </AccessibilityProvider>
        </NotificationProvider>
      </TolgeeProvider>
    </ThemeProvider>
  )
}

export default App

