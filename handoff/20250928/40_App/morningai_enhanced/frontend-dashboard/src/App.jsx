import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Sidebar from '@/components/Sidebar'
import Dashboard from '@/components/Dashboard'
import StrategyManagement from '@/components/StrategyManagement'
import DecisionApproval from '@/components/DecisionApproval'
import HistoryAnalysis from '@/components/HistoryAnalysis'
import CostAnalysis from '@/components/CostAnalysis'
import SystemSettings from '@/components/SystemSettings'
import Checkout from '@/components/Checkout'
import LoginPage from '@/components/LoginPage'
import './App.css'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 檢查用戶認證狀態
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          // 驗證token有效性
          const response = await fetch('/api/auth/verify', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
            setIsAuthenticated(true)
          } else {
            localStorage.removeItem('auth_token')
          }
        }
      } catch (error) {
        console.error('認證檢查失敗:', error)
        localStorage.removeItem('auth_token')
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const handleLogin = (userData, token) => {
    setUser(userData)
    setIsAuthenticated(true)
    localStorage.setItem('auth_token', token)
  }

  const handleLogout = () => {
    setUser(null)
    setIsAuthenticated(false)
    localStorage.removeItem('auth_token')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
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
        
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/strategies" element={<StrategyManagement />} />
            <Route path="/approvals" element={<DecisionApproval />} />
            <Route path="/history" element={<HistoryAnalysis />} />
            <Route path="/costs" element={<CostAnalysis />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/settings" element={<SystemSettings />} />
          </Routes>
        </main>
        
        <Toaster />
      </div>
    </Router>
  )
}

export default App

