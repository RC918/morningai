import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import { TolgeeProvider } from '@tolgee/react'
import { tolgee } from './i18n'
import Sidebar from '@/components/Sidebar'
import LoginPage from '@/components/LoginPage'
import './App.css'

const OwnerDashboard = lazy(() => import('@/pages/OwnerDashboard'))
const AgentGovernance = lazy(() => import('@/pages/AgentGovernance'))
const TenantManagement = lazy(() => import('@/pages/TenantManagement'))
const SystemMonitoring = lazy(() => import('@/pages/SystemMonitoring'))
const PlatformSettings = lazy(() => import('@/pages/PlatformSettings'))

function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('owner_auth_token')
    const savedUser = localStorage.getItem('owner_user')
    
    if (token && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser)
        setUser(parsedUser)
        setIsAuthenticated(true)
      } catch (error) {
        console.error('Failed to parse saved user:', error)
        localStorage.removeItem('owner_auth_token')
        localStorage.removeItem('owner_user')
      }
    }
    
    setLoading(false)
  }, [])

  const handleLogin = (userData, token) => {
    setUser(userData)
    setIsAuthenticated(true)
    localStorage.setItem('owner_auth_token', token)
    localStorage.setItem('owner_user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('owner_auth_token')
    localStorage.removeItem('owner_user')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <Sidebar user={user} onLogout={handleLogout} />
        
        <main id="main-content" className="flex-1 overflow-y-auto" role="main">
          <Suspense fallback={<div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div></div>}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<OwnerDashboard />} />
              <Route path="/governance" element={<AgentGovernance />} />
              <Route path="/tenants" element={<TenantManagement />} />
              <Route path="/monitoring" element={<SystemMonitoring />} />
              <Route path="/settings" element={<PlatformSettings />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  )
}

function App() {
  return (
    <TolgeeProvider tolgee={tolgee} fallback="Loading translations...">
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <AppContent />
      </ThemeProvider>
    </TolgeeProvider>
  )
}

export default App
