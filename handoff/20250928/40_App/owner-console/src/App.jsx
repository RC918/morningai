import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import Sidebar from '@/components/Sidebar'
import './App.css'

const OwnerDashboard = lazy(() => import('@/pages/OwnerDashboard'))
const AgentGovernance = lazy(() => import('@/pages/AgentGovernance'))
const TenantManagement = lazy(() => import('@/pages/TenantManagement'))
const SystemMonitoring = lazy(() => import('@/pages/SystemMonitoring'))
const PlatformSettings = lazy(() => import('@/pages/PlatformSettings'))

function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState(true)
  const [user, setUser] = useState({
    id: 'owner_dev',
    name: 'Ryan Chen',
    email: 'ryan@morningai.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
    role: 'Owner'
  })

  const handleLogout = () => {
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('owner_auth_token')
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
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AppContent />
    </ThemeProvider>
  )
}

export default App
