import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Alert, AlertDescription, Progress } from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  Users, 
  Shield,
  Activity,
  DollarSign,
  TrendingUp,
  Server,
  X
} from 'lucide-react'
import { getStoredUser } from '@/lib/auth'
import { getTwoFAStatus } from '@/lib/2fa-api'

const OwnerDashboard = () => {
  const { t } = useTranslation()
  const [stats, setStats] = useState({
    totalTenants: 12,
    activeAgents: 45,
    totalCost: 1234.56,
    systemHealth: 98.5
  })
  const [show2FAPrompt, setShow2FAPrompt] = useState(false)
  const [checking2FA, setChecking2FA] = useState(true)

  useEffect(() => {
    const check2FAStatus = async () => {
      try {
        const user = getStoredUser()
        if (user && user.role === 'owner') {
          const status = await getTwoFAStatus()
          if (!status.enabled && !status.feature_disabled) {
            setShow2FAPrompt(true)
          }
        }
      } catch (error) {
        console.error('Failed to check 2FA status:', error)
      } finally {
        setChecking2FA(false)
      }
    }

    check2FAStatus()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-800">{t('dashboard.title')}</h1>
        <p className="text-sm text-neutral-500 mt-1">{t('dashboard.subtitle')}</p>
      </div>

      {!checking2FA && show2FAPrompt && (
        <Alert className="bg-warning-50 border-warning-200">
          <Shield className="h-4 w-4 text-warning-600" />
          <AlertDescription className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-medium text-warning-900">{t('dashboard.2fa.prompt.title')}</p>
              <p className="text-sm text-warning-800 mt-1">
                {t('dashboard.2fa.prompt.description')}
              </p>
            </div>
            <div className="flex items-center gap-2 ml-4">
              <Link to="/settings/2fa">
                <AppleButton size="sm" variant="primary">
                  {t('dashboard.2fa.prompt.setupButton')}
                </AppleButton>
              </Link>
              <AppleButton
                size="sm"
                variant="ghost"
                onClick={() => setShow2FAPrompt(false)}
                className="text-warning-900 hover:text-warning-950"
              >
                <X className="h-4 w-4" />
              </AppleButton>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* iotask style: Primary blue for main metrics */}
        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200 hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">{t('dashboard.stats.totalTenants')}</CardTitle>
            <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
              <Users className="h-5 w-5 text-primary-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-neutral-800">{stats.totalTenants}</div>
            <p className="text-xs text-success-500 mt-1 flex items-center">
              <TrendingUp className="inline h-3 w-3 mr-1" /> +2 {t('dashboard.stats.thisMonth')}
            </p>
          </CardContent>
        </Card>

        {/* iotask style: Pink accent for agents */}
        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200 hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">{t('dashboard.stats.activeAgents')}</CardTitle>
            <div className="w-10 h-10 rounded-lg bg-pink-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-pink-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-neutral-800">{stats.activeAgents}</div>
            <p className="text-xs text-neutral-500 mt-1">
              {t('dashboard.stats.acrossAllTenants')}
            </p>
          </CardContent>
        </Card>

        {/* iotask style: Orange for cost/warnings */}
        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200 hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">{t('dashboard.stats.monthlyCost')}</CardTitle>
            <div className="w-10 h-10 rounded-lg bg-warning-100 flex items-center justify-center">
              <DollarSign className="h-5 w-5 text-warning-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-neutral-800">${stats.totalCost.toFixed(2)}</div>
            <p className="text-xs text-neutral-500 mt-1">
              {t('dashboard.stats.platformWideUsage')}
            </p>
          </CardContent>
        </Card>

        {/* iotask style: Green for success/health */}
        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200 hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-neutral-500">{t('dashboard.stats.systemHealth')}</CardTitle>
            <div className="w-10 h-10 rounded-lg bg-success-100 flex items-center justify-center">
              <Activity className="h-5 w-5 text-success-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-neutral-800">{stats.systemHealth}%</div>
            <p className="text-xs text-success-500 mt-1">
              {t('dashboard.stats.allSystemsOperational')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* iotask style: Project Progress Section */}
      <Card className="bg-white rounded-lg shadow-sm border border-neutral-200">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-neutral-800">{t('dashboard.projectProgress.title')}</CardTitle>
          <CardDescription className="text-sm text-neutral-500">{t('dashboard.projectProgress.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-5">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-neutral-700">{t('dashboard.projectProgress.agentDeployment')}</span>
                <span className="text-neutral-500">85%</span>
              </div>
              <Progress value={85} variant="default" aria-label="Agent Deployment: 85%" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-neutral-700">{t('dashboard.projectProgress.dataIntegration')}</span>
                <span className="text-neutral-500">60%</span>
              </div>
              <Progress value={60} variant="success" aria-label="Data Integration: 60%" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-neutral-700">{t('dashboard.projectProgress.securityAudit')}</span>
                <span className="text-neutral-500">45%</span>
              </div>
              <Progress value={45} variant="warning" aria-label="Security Audit: 45%" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="font-medium text-neutral-700">{t('dashboard.projectProgress.performanceOptimization')}</span>
                <span className="text-neutral-500">30%</span>
              </div>
              <Progress value={30} variant="pink" aria-label="Performance Optimization: 30%" />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-neutral-800">{t('dashboard.recentActivity.title')}</CardTitle>
            <CardDescription className="text-sm text-neutral-500">{t('dashboard.recentActivity.subtitle')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* iotask style: Green for success */}
              <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-neutral-700">{t('dashboard.recentActivity.newTenant')}</p>
                  <p className="text-xs text-neutral-500">{t('dashboard.recentActivity.placeholder.acme')}</p>
                </div>
              </div>
              {/* iotask style: Primary blue for normal */}
              <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-neutral-700">{t('dashboard.recentActivity.agentDeployed')}</p>
                  <p className="text-xs text-neutral-500">{t('dashboard.recentActivity.placeholder.opsAgent')}</p>
                </div>
              </div>
              {/* iotask style: Orange for warnings */}
              <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-neutral-700">{t('dashboard.recentActivity.maintenanceScheduled')}</p>
                  <p className="text-xs text-neutral-500">{t('dashboard.recentActivity.placeholder.maintenance')}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white rounded-lg shadow-sm border border-neutral-200">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-neutral-800">{t('dashboard.systemStatus.title')}</CardTitle>
            <CardDescription className="text-sm text-neutral-500">{t('dashboard.systemStatus.subtitle')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* iotask style: Green badges for healthy status */}
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="flex items-center gap-3">
                  <Server className="h-4 w-4 text-neutral-400" />
                  <span className="text-sm text-neutral-700">{t('dashboard.systemStatus.apiBackend')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-success-100 px-2.5 py-0.5 text-xs text-success-600 font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="flex items-center gap-3">
                  <Server className="h-4 w-4 text-neutral-400" />
                  <span className="text-sm text-neutral-700">{t('dashboard.systemStatus.database')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-success-100 px-2.5 py-0.5 text-xs text-success-600 font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="flex items-center gap-3">
                  <Server className="h-4 w-4 text-neutral-400" />
                  <span className="text-sm text-neutral-700">{t('dashboard.systemStatus.redisCache')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-success-100 px-2.5 py-0.5 text-xs text-success-600 font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-neutral-50 transition-colors">
                <div className="flex items-center gap-3">
                  <Server className="h-4 w-4 text-neutral-400" />
                  <span className="text-sm text-neutral-700">{t('dashboard.systemStatus.workerNodes')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-success-100 px-2.5 py-0.5 text-xs text-success-600 font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default OwnerDashboard
