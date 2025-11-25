import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Button, Alert, AlertDescription } from '@morningai/shared-ui'
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
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-large-title font-bold text-neutral-900 dark:text-white">{t('dashboard.title')}</h1>
        <p className="text-body text-neutral-600 dark:text-neutral-400 mt-1">{t('dashboard.subtitle')}</p>
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
                <Button size="sm" variant="default">
                  {t('dashboard.2fa.prompt.setupButton')}
                </Button>
              </Link>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShow2FAPrompt(false)}
                className="text-warning-900 hover:text-warning-950"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Emotional Color: calm (藍) - 正常/穩定 */}
        <Card className="material-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-callout font-medium">{t('dashboard.stats.totalTenants')}</CardTitle>
            <div className="w-8 h-8 rounded-full bg-calm-10 flex items-center justify-center">
              <Users className="h-4 w-4 text-calm" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-title-2 md:text-title-1 font-bold text-calm">{stats.totalTenants}</div>
            <p className="text-footnote text-muted-foreground">
              <TrendingUp className="inline h-3 w-3 text-growth" /> +2 {t('dashboard.stats.thisMonth')}
            </p>
          </CardContent>
        </Card>

        {/* Emotional Color: wisdom (紫) - 洞察/智慧 */}
        <Card className="material-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-callout font-medium">{t('dashboard.stats.activeAgents')}</CardTitle>
            <div className="w-8 h-8 rounded-full bg-wisdom-10 flex items-center justify-center">
              <Shield className="h-4 w-4 text-wisdom" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-title-2 md:text-title-1 font-bold text-wisdom">{stats.activeAgents}</div>
            <p className="text-footnote text-muted-foreground">
              {t('dashboard.stats.acrossAllTenants')}
            </p>
          </CardContent>
        </Card>

        {/* Emotional Color: joy (橙) - 警告/注意 (成本需要關注) */}
        <Card className="material-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-callout font-medium">{t('dashboard.stats.monthlyCost')}</CardTitle>
            <div className="w-8 h-8 rounded-full bg-joy-10 flex items-center justify-center">
              <DollarSign className="h-4 w-4 text-joy" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-title-2 md:text-title-1 font-bold text-joy">${stats.totalCost.toFixed(2)}</div>
            <p className="text-footnote text-muted-foreground">
              {t('dashboard.stats.platformWideUsage')}
            </p>
          </CardContent>
        </Card>

        {/* Emotional Color: growth (綠) - 成功/成長 */}
        <Card className="material-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-callout font-medium">{t('dashboard.stats.systemHealth')}</CardTitle>
            <div className="w-8 h-8 rounded-full bg-growth-10 flex items-center justify-center">
              <Activity className="h-4 w-4 text-growth" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-title-2 md:text-title-1 font-bold text-growth">{stats.systemHealth}%</div>
            <p className="text-footnote text-growth">
              {t('dashboard.stats.allSystemsOperational')}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="material-card">
          <CardHeader>
            <CardTitle>{t('dashboard.recentActivity.title')}</CardTitle>
            <CardDescription>{t('dashboard.recentActivity.subtitle')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Emotional Color: growth (綠) - 成功/成長 */}
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 bg-growth rounded-full"></div>
                <div className="flex-1">
                  <p className="text-callout font-medium">{t('dashboard.recentActivity.newTenant')}</p>
                  <p className="text-caption-2 text-neutral-500 dark:text-neutral-400">{t('dashboard.recentActivity.placeholder.acme')}</p>
                </div>
              </div>
              {/* Emotional Color: calm (藍) - 正常/穩定 */}
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 bg-calm rounded-full"></div>
                <div className="flex-1">
                  <p className="text-callout font-medium">{t('dashboard.recentActivity.agentDeployed')}</p>
                  <p className="text-caption-2 text-neutral-500 dark:text-neutral-400">{t('dashboard.recentActivity.placeholder.opsAgent')}</p>
                </div>
              </div>
              {/* Emotional Color: joy (橙) - 警告/注意 */}
              <div className="flex items-center gap-4">
                <div className="w-2 h-2 bg-joy rounded-full"></div>
                <div className="flex-1">
                  <p className="text-callout font-medium">{t('dashboard.recentActivity.maintenanceScheduled')}</p>
                  <p className="text-caption-2 text-neutral-500 dark:text-neutral-400">{t('dashboard.recentActivity.placeholder.maintenance')}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="material-card">
          <CardHeader>
            <CardTitle>{t('dashboard.systemStatus.title')}</CardTitle>
            <CardDescription>{t('dashboard.systemStatus.subtitle')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Emotional Color: growth (綠) - 成功/健康 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-growth" />
                  <span className="text-callout">{t('dashboard.systemStatus.apiBackend')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-growth-10 px-2 py-1 text-caption-2 text-growth font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-growth" />
                  <span className="text-callout">{t('dashboard.systemStatus.database')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-growth-10 px-2 py-1 text-caption-2 text-growth font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-growth" />
                  <span className="text-callout">{t('dashboard.systemStatus.redisCache')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-growth-10 px-2 py-1 text-caption-2 text-growth font-medium">
                  {t('dashboard.systemStatus.healthy')}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="h-4 w-4 text-growth" />
                  <span className="text-callout">{t('dashboard.systemStatus.workerNodes')}</span>
                </div>
                <span className="inline-flex items-center rounded-full bg-growth-10 px-2 py-1 text-caption-2 text-growth font-medium">
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
