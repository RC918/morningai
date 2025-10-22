import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ThemeProvider } from 'next-themes'
import { TolgeeProvider } from '@tolgee/react'
import { Toaster } from '@/components/ui/toaster'
import ErrorBoundary from '@/components/ErrorBoundary'
import Sidebar from '@/components/Sidebar'
import LoginPage from '@/components/LoginPage'
import LandingPage from '@/components/LandingPage'
import WIPPage from '@/components/WIPPage'
import { TenantProvider } from '@/contexts/TenantContext'
import { NotificationProvider, useNotification } from '@/contexts/NotificationContext'
import { Phase3WelcomeModal } from '@/components/Phase3WelcomeModal'
import { PageLoader } from '@/components/feedback/PageLoader'
import { OfflineIndicator } from '@/components/feedback/OfflineIndicator'
import { applyDesignTokens } from '@/lib/design-tokens'
import { isFeatureEnabled, AVAILABLE_FEATURES } from '@/lib/feature-flags'
import useAppStore from '@/stores/appStore'
import apiClient from '@/lib/api'
import '@/i18n/config'
import { tolgee } from '@/i18n/config'
import './App.css'
import './styles/mobile-optimizations.css'
import './styles/motion-governance.css'
import './styles/theme-apple.css'

const Dashboard = lazy(() => import('@/components/Dashboard'))
const StrategyManagement = lazy(() => import('@/components/StrategyManagement'))
const DecisionApproval = lazy(() => import('@/components/DecisionApproval'))
const HistoryAnalysis = lazy(() => import('@/components/HistoryAnalysis'))
const CostAnalysis = lazy(() => import('@/components/CostAnalysis'))
const SystemSettings = lazy(() => import('@/components/SystemSettings'))
const TenantSettings = lazy(() => import('@/components/TenantSettings'))
const CheckoutPage = lazy(() => import('@/components/CheckoutPage'))
const CheckoutSuccess = lazy(() => import('@/components/CheckoutSuccess'))
const CheckoutCancel = lazy(() => import('@/components/CheckoutCancel'))

function AppContent() {
  const { t } = useTranslation()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const { user, setUser, addToast } = useAppStore()
  const { showPhase3Welcome, dismissWelcome } = useNotification()

  useEffect(() => {
    const sentryDsn = import.meta.env.VITE_SENTRY_DSN
    if (sentryDsn && !window.Sentry) {
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
      })
    }

    const handleApiError = (event) => {
      const { endpoint, error, status, requestId } = event.detail
      addToast({
        title: t('common.apiError'),
        description: `${endpoint}: ${error} (ID: ${requestId})`,
        variant: "destructive"
      })
    }

    window.addEventListener('api-error', handleApiError)

    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          const userData = await apiClient.verifyAuth()
          setUser(userData)
          setIsAuthenticated(true)
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        localStorage.removeItem('auth_token')
        setUser({
          id: 'dev_user',
          name: 'Ryan Chen',
          email: 'ryan@morningai.com',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
          role: 'Owner',
          tenant_id: 'tenant_001'
        })
        setIsAuthenticated(true)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
    applyDesignTokens()

    return () => {
      window.removeEventListener('api-error', handleApiError)
    }
  }, [addToast, setUser])

  const handleLogin = (userData, token) => {
    setUser(userData)
    setIsAuthenticated(true)
    localStorage.setItem('auth_token', token)
    addToast({
      title: t('auth.login.loginSuccess'),
      description: t('auth.login.welcomeBack', { name: userData.name }),
      variant: "default"
    })
  }

  const handleLogout = () => {
    setUser({
      id: null,
      name: 'Ryan Chen',
      email: 'ryan@morningai.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
      role: 'Owner',
      tenant_id: 'tenant_001'
    })
    setIsAuthenticated(false)
    localStorage.removeItem('auth_token')
    addToast({
      title: t('auth.logout.logoutSuccess'),
      description: t('auth.logout.logoutMessage'),
      variant: "default"
    })
  }

  if (loading) {
    return <PageLoader message={t('common.loadingApp')} />
  }

  const handleNavigateToLogin = () => {
    window.location.href = '/login'
  }

  const handleSSOLogin = (provider) => {
    console.log(`SSO Login with ${provider}`)
  }

  return (
    <ErrorBoundary>
      <TenantProvider>
        <Router>
          <div className="theme-apple">
            <OfflineIndicator />
            <Phase3WelcomeModal 
              isOpen={showPhase3Welcome}
              onClose={dismissWelcome}
            />
            
            {!isAuthenticated ? (
              <Routes>
                <Route path="/" element={<LandingPage onNavigateToLogin={handleNavigateToLogin} onSSOLogin={handleSSOLogin} />} />
                <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            ) : (
              <div className="flex h-screen bg-gray-100">
              <Sidebar user={user} onLogout={handleLogout} />
              
              <main className="flex-1 overflow-y-auto" role="main" aria-label={t('common.mainContentArea')}>
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
              {isFeatureEnabled(AVAILABLE_FEATURES.SETTINGS) ? (
                <Route path="/settings" element={<SystemSettings />} />
              ) : (
                <Route path="/settings" element={<WIPPage title={t('wip.systemSettings')} />} />
              )}
              <Route path="/tenant-settings" element={<TenantSettings />} />
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
                  </Routes>
                </Suspense>
              </main>
              
                <Toaster />
              </div>
            )}
          </div>
        </Router>
      </TenantProvider>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <TolgeeProvider tolgee={tolgee} fallback={<PageLoader message="Loading translations..." />}>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </TolgeeProvider>
    </ThemeProvider>
  )
}

export default App

