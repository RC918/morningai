import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { 
  Alert, 
  AlertDescription,
  StatCard,
  SectionCard,
  TimelineList,
  SystemStatusList,
  ProgressTrack
} from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { Shield, X } from 'lucide-react'
import { getStoredUser } from '@/lib/auth'
import { getTwoFAStatus } from '@/lib/2fa-api'

const OwnerDashboard = () => {
  const { t } = useTranslation()
  const [stats] = useState({
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

  const progressItems = [
    { 
      label: t('dashboard.projectProgress.agentDeployment'), 
      value: 85, 
      hint: t('dashboard.projectProgress.hints.agentDeployment')
    },
    { 
      label: t('dashboard.projectProgress.dataIntegration'), 
      value: 60, 
      hint: t('dashboard.projectProgress.hints.dataIntegration')
    },
    { 
      label: t('dashboard.projectProgress.securityAudit'), 
      value: 45, 
      hint: t('dashboard.projectProgress.hints.securityAudit')
    },
    { 
      label: t('dashboard.projectProgress.performanceOptimization'), 
      value: 30, 
      hint: t('dashboard.projectProgress.hints.performanceOptimization')
    },
  ]

  const activityItems = [
    { 
      id: '1', 
      title: t('dashboard.recentActivity.newTenant'), 
      desc: t('dashboard.recentActivity.placeholder.acme'), 
      time: t('dashboard.recentActivity.time.5min')
    },
    { 
      id: '2', 
      title: t('dashboard.recentActivity.agentDeployed'), 
      desc: t('dashboard.recentActivity.placeholder.opsAgent'), 
      time: t('dashboard.recentActivity.time.30min')
    },
    { 
      id: '3', 
      title: t('dashboard.recentActivity.maintenanceScheduled'), 
      desc: t('dashboard.recentActivity.placeholder.maintenance'), 
      time: t('dashboard.recentActivity.time.1hour')
    },
  ]

  const statusItems = [
    { service: t('dashboard.systemStatus.apiBackend'), status: 'Healthy', latency: '220ms' },
    { service: t('dashboard.systemStatus.database'), status: 'Healthy', latency: '18ms' },
    { service: t('dashboard.systemStatus.redisCache'), status: 'Healthy', latency: '4ms' },
    { service: t('dashboard.systemStatus.workerNodes'), status: 'Healthy', latency: '12ms' },
  ]

  return (
    <div className="space-y-8">
      <div className="flex flex-col">
        <h1 className="text-xl font-semibold text-neutral-800 dark:text-neutral-100">{t('dashboard.title')}</h1>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">{t('dashboard.subtitle')}</p>
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

      {/* KPI Row - Using StatCard components */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard 
          label={t('dashboard.stats.totalTenants')} 
          value={String(stats.totalTenants)} 
          trend={`+2 ${t('dashboard.stats.thisMonth')}`}
        />
        <StatCard 
          label={t('dashboard.stats.activeAgents')} 
          value={String(stats.activeAgents)} 
          badge={t('dashboard.stats.crossTenant')}
        />
        <StatCard 
          label={t('dashboard.stats.monthlyCost')} 
          value={`$${stats.totalCost.toFixed(2)}`}
        />
        <StatCard 
          label={t('dashboard.stats.systemHealth')} 
          value={`${stats.systemHealth}%`}
        />
      </div>

      {/* Main Content - Using SectionCard with nested components */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <SectionCard
          title={t('dashboard.projectProgress.title')}
          subtitle={t('dashboard.projectProgress.subtitle')}
        >
          <ProgressTrack items={progressItems} />
        </SectionCard>

        <SectionCard
          title={t('dashboard.recentActivity.title')}
          subtitle={t('dashboard.recentActivity.subtitle')}
        >
          <TimelineList items={activityItems} />
        </SectionCard>

        <SectionCard
          title={t('dashboard.systemStatus.title')}
          subtitle={t('dashboard.systemStatus.subtitle')}
        >
          <SystemStatusList items={statusItems} />
        </SectionCard>
      </div>
    </div>
  )
}

export default OwnerDashboard
