import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import { AuthProvider, useAuth } from '@/components/AuthProvider'
import Sidebar from '@/components/Sidebar'
import LoginPage from '@/components/LoginPage'
import { applyDesignTokens } from '@morningai/shared-ui'
import './App.css'

const OwnerDashboard = lazy(() => import('@/pages/OwnerDashboard'))
const AgentGovernance = lazy(() => import('@/pages/AgentGovernance'))
const TenantManagement = lazy(() => import('@/pages/TenantManagement'))
const SystemMonitoring = lazy(() => import('@/pages/SystemMonitoring'))
const AgentEvaluationDashboard = lazy(() => import('@/pages/AgentEvaluationDashboard'))
const FailureExperimentDashboard = lazy(() => import('@/pages/FailureExperimentDashboard'))
const PlatformSettings = lazy(() => import('@/pages/PlatformSettings'))
const Settings2FA = lazy(() => import('@/pages/Settings2FA'))
const UXMetrics = lazy(() => import('@/pages/UXMetrics'))

function AppContent() {
  const { isAuthenticated, isLoading, user, login, logout, refreshUser } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    const intendedPath = typeof window !== 'undefined' ? window.location.pathname : '/'
    return <LoginPage onLogin={login} onRefreshUser={refreshUser} redirectPath={intendedPath} />
  }

  return (
    <Router>
      <div className="flex h-screen bg-neutral-50">
        <Sidebar user={user} onLogout={logout} />
        
        <main id="main-content" className="flex-1 overflow-y-auto" role="main">
          <Suspense fallback={<div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div></div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<OwnerDashboard />} />
              <Route path="/governance" element={<AgentGovernance />} />
              <Route path="/tenants" element={<TenantManagement />} />
              <Route path="/monitoring" element={<SystemMonitoring />} />
              <Route path="/agent-evaluation" element={<AgentEvaluationDashboard />} />
              <Route path="/failure-experiments" element={<FailureExperimentDashboard />} />
              <Route path="/ux-metrics" element={<UXMetrics />} />
              <Route path="/settings" element={<PlatformSettings />} />
              <Route path="/settings/2fa" element={<Settings2FA />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

function App() {
  useEffect(() => {
    if (typeof document !== 'undefined') {
      applyDesignTokens()
    }
  }, [])

  return (
    <ThemeProvider attribute="class" defaultTheme="light" forcedTheme="light" enableSystem={false}>
      <div className="theme-morning-ai theme-apple">
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </div>
    </ThemeProvider>
  )
}

export default App
