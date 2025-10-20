import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import ErrorBoundary from '@/components/ErrorBoundary'
import * as Sentry from '@sentry/react'
import Sidebar from '@/components/Sidebar'
import Dashboard from '@/components/Dashboard'
import StrategyManagement from '@/components/StrategyManagement'
import DecisionApproval from '@/components/DecisionApproval'
import HistoryAnalysis from '@/components/HistoryAnalysis'
import CostAnalysis from '@/components/CostAnalysis'
import SystemSettings from '@/components/SystemSettings'
import TenantSettings from '@/components/TenantSettings'
import CheckoutPage from '@/components/CheckoutPage'
import CheckoutSuccess from '@/components/CheckoutSuccess'
import CheckoutCancel from '@/components/CheckoutCancel'
import LandingPage from '@/components/LandingPage'
import LoginPage from '@/components/LoginPage'
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
import './App.css'

function ProtectedRoute({ children }) {
  const { user } = useAppStore()
  const location = useLocation()
  
  if (!user || !user.id) {
    return <Navigate to="/" state={{ from: location }} replace />
  }
  
  return children
}

function PublicRoute({ children }) {
  const { user } = useAppStore()
  
  if (user && user.id) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

function AppRoutes() {
  const navigate = useNavigate()
  const { user, setUser, addToast } = useAppStore()
  const { showPhase3Welcome, dismissWelcome } = useNotification()

  const handleLogin = (userData, token) => {
    setUser(userData)
    localStorage.setItem('auth_token', token)
    addToast({
      title: "登入成功",
      description: `歡迎回來，${userData.name}！`,
      variant: "default"
    })
    navigate('/dashboard')
  }

  const handleSSOLogin = (provider) => {
    console.log(`SSO Login with ${provider}`)
    addToast({
      title: "SSO 登入",
      description: `正在使用 ${provider} 登入...`,
      variant: "default"
    })
  }

  const handleLogout = () => {
    setUser({
      id: null,
      name: null,
      email: null,
      avatar: null,
      role: null,
      tenant_id: null
    })
    localStorage.removeItem('auth_token')
    addToast({
      title: "已登出",
      description: "您已成功登出系統",
      variant: "default"
    })
    navigate('/')
  }

  const handleNavigateToLogin = () => {
    navigate('/login')
  }

  return (
    <>
      <OfflineIndicator />
      <Routes>
        <Route 
          path="/" 
          element={
            <PublicRoute>
              <LandingPage 
                onNavigateToLogin={handleNavigateToLogin}
                onSSOLogin={handleSSOLogin}
              />
            </PublicRoute>
          } 
        />
        
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginPage onLogin={handleLogin} />
            </PublicRoute>
          } 
        />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Phase3WelcomeModal 
                isOpen={showPhase3Welcome}
                onClose={dismissWelcome}
              />
              <div className="flex h-screen bg-gray-100">
                <Sidebar user={user} onLogout={handleLogout} />
                
                <main className="flex-1 overflow-y-auto" role="main" aria-label="主要內容區域">
                  <Routes>
                    <Route path="/dashboard" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.DASHBOARD) ? (
                        <Dashboard />
                      ) : (
                        <WIPPage title="儀表板開發中" />
                      )
                    } />
                    
                    <Route path="/strategies" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.STRATEGIES) ? (
                        <StrategyManagement />
                      ) : (
                        <WIPPage title="策略管理開發中" />
                      )
                    } />
                    
                    <Route path="/approvals" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.APPROVALS) ? (
                        <DecisionApproval />
                      ) : (
                        <WIPPage title="決策審批開發中" />
                      )
                    } />
                    
                    <Route path="/history" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.HISTORY) ? (
                        <HistoryAnalysis />
                      ) : (
                        <WIPPage title="歷史分析開發中" />
                      )
                    } />
                    
                    <Route path="/costs" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.COSTS) ? (
                        <CostAnalysis />
                      ) : (
                        <WIPPage title="成本分析開發中" />
                      )
                    } />
                    
                    <Route path="/settings" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.SETTINGS) ? (
                        <SystemSettings />
                      ) : (
                        <WIPPage title="系統設定開發中" />
                      )
                    } />
                    
                    <Route path="/tenant-settings" element={<TenantSettings />} />
                    
                    <Route path="/checkout" element={
                      isFeatureEnabled(AVAILABLE_FEATURES.CHECKOUT) ? (
                        <CheckoutPage />
                      ) : (
                        <WIPPage title="結帳頁面開發中" />
                      )
                    } />
                    
                    <Route path="/checkout/success" element={<CheckoutSuccess />} />
                    <Route path="/checkout/cancel" element={<CheckoutCancel />} />
                    <Route path="/wip" element={<WIPPage />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </main>
                
                <Toaster />
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}

function AppContent() {
  const [loading, setLoading] = useState(true)
  const { setUser, addToast } = useAppStore()

  useEffect(() => {
    const sentryDsn = import.meta.env.VITE_SENTRY_DSN
    if (sentryDsn && !window.Sentry) {
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
    }

    const handleApiError = (event) => {
      const { endpoint, error, status, requestId } = event.detail
      addToast({
        title: "API 錯誤",
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
        }
      } catch (error) {
        console.error('認證檢查失敗:', error)
        localStorage.removeItem('auth_token')
        setUser({
          id: 'dev_user',
          name: 'Ryan Chen',
          email: 'ryan@morningai.com',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
          role: 'Owner',
          tenant_id: 'tenant_001'
        })
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

  if (loading) {
    return <PageLoader message="正在載入應用程式..." />
  }

  return (
    <ErrorBoundary>
      <TenantProvider>
        <Router>
          <AppRoutes />
        </Router>
      </TenantProvider>
    </ErrorBoundary>
  )
}

function App() {
  return (
    <NotificationProvider>
      <AppContent />
    </NotificationProvider>
  )
}

export default App
