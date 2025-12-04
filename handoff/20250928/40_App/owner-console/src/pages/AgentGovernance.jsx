import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button, Tabs, TabsContent, TabsList, TabsTrigger, StatCard, SectionCard } from '@morningai/shared-ui'
import { 
  Shield, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  DollarSign,
  Activity
} from 'lucide-react'
import { getAdminAgents } from '@/lib/generated/admin/admin'
import { getGovernanceEvents, getGovernanceViolations, getGovernanceStatistics } from '@/lib/generated/governance/governance'
import AgentExecutionLogs from '@/components/AgentExecutionLogs'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'

const AgentGovernance = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [agents, setAgents] = useState([])
  const [events, setEvents] = useState([])
  const [violations, setViolations] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)

  useEffect(() => {
    loadGovernanceData()
  }, [])

  const loadGovernanceData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [agentsResponse, eventsResponse, violationsResponse, statsResponse] = await Promise.all([
        getAdminAgents({ status: 'all', limit: 100 }),
        getGovernanceEvents({ limit: 50 }),
        getGovernanceViolations({ limit: 50 }),
        getGovernanceStatistics()
      ])

      if (agentsResponse.status === 200) {
        setAgents(agentsResponse.data.agents || [])
      }

      if (eventsResponse.status === 200) {
        setEvents(eventsResponse.data.events || [])
      }

      if (violationsResponse.status === 200) {
        setViolations(violationsResponse.data.violations || [])
      }

      if (statsResponse.status === 200) {
        setStatistics(statsResponse.data)
      }
    } catch (error) {
      console.error('Failed to load governance data:', error)
      setError(error.message || 'Failed to load governance data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    // Emotional Color Mapping:
    // - active → growth (綠) - 成功/運行中
    // - paused → joy (橙) - 警告/暫停
    // - error → energy (紅) - 錯誤/危險
    // - default → calm (藍) - 正常/穩定
    switch (status) {
      case 'active':
        return 'bg-growth-10 text-growth'
      case 'paused':
        return 'bg-joy-10 text-joy'
      case 'error':
        return 'bg-energy-10 text-energy'
      default:
        return 'bg-calm-10 text-calm'
    }
  }

  const getPermissionLevelColor = (level) => {
    // Emotional Color Mapping:
    // - prod_full_access → growth (綠) - 成功/完全權限
    // - prod_low_risk → wisdom (紫) - 洞察/低風險
    // - staging_access → joy (橙) - 警告/測試環境
    // - sandbox_only → calm (藍) - 正常/沙盒
    switch (level) {
      case 'prod_full_access':
        return 'bg-growth-10 text-growth'
      case 'prod_low_risk':
        return 'bg-wisdom-10 text-wisdom'
      case 'staging_access':
        return 'bg-joy-10 text-joy'
      case 'sandbox_only':
        return 'bg-calm-10 text-calm'
      default:
        return 'bg-calm-10 text-calm'
    }
  }

  const getPermissionLevelLabel = (level) => {
    const labels = {
      'prod_full_access': t('governance.permissions.prodFull'),
      'prod_low_risk': t('governance.permissions.prodLowRisk'),
      'staging_access': t('governance.permissions.staging'),
      'sandbox_only': t('governance.permissions.sandbox')
    }
    return labels[level] || level
  }

  const getEventTypeIcon = (eventType) => {
    // Emotional Color Mapping for event icons
    switch (eventType) {
      case 'task_success':
        return <CheckCircle className="w-4 h-4 text-growth" />
      case 'task_failure':
        return <XCircle className="w-4 h-4 text-energy" />
      case 'budget_exceeded':
        return <AlertTriangle className="w-4 h-4 text-joy" />
      case 'permission_denied':
        return <Shield className="w-4 h-4 text-energy" />
      default:
        return <Activity className="w-4 h-4 text-calm" />
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <PageScaffold
      title={t('governance.title')}
      subtitle={t('governance.subtitle')}
      titleIcon={<Shield className="w-6 h-6" />}
      actions={
        <AppleButton onClick={loadGovernanceData} variant="outline" haptic="light" disabled={loading}>
          <Activity className="w-4 h-4 mr-2" />
          {t('governance.refresh')}
        </AppleButton>
      }
      banner={error && (
        <AppleErrorBanner
          title={t('common.error')}
          message={error}
          onRetry={loadGovernanceData}
        />
      )}
      kpis={statistics && (
        <>
          <StatCard
            label={t('governance.stats.totalAgents')}
            value={String(statistics.reputation?.total_agents || 0)}
            icon={<Shield className="w-5 h-5" />}
            variant="default"
          />
          <StatCard
            label={t('governance.stats.avgReputation')}
            value={String(statistics.reputation?.average_score?.toFixed(0) || 100)}
            icon={<TrendingUp className="w-5 h-5" />}
            variant="green"
          />
          <StatCard
            label={t('governance.stats.dailyCost')}
            value={`$${statistics.costs?.daily?.usage?.usd?.toFixed(2) || '0.00'}`}
            icon={<DollarSign className="w-5 h-5" />}
            variant="yellow"
          />
          <StatCard
            label={t('governance.stats.violations')}
            value={String(violations.length)}
            icon={<AlertTriangle className="w-5 h-5" />}
            variant={violations.length > 0 ? 'red' : 'green'}
          />
        </>
      )}
    >
      <Tabs defaultValue="agents" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="agents">{t('governance.tabs.agents')}</TabsTrigger>
          <TabsTrigger value="events">{t('governance.tabs.events')}</TabsTrigger>
          <TabsTrigger value="violations">{t('governance.tabs.violations')}</TabsTrigger>
          <TabsTrigger value="executionLogs">{t('governance.tabs.executionLogs')}</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <SectionCard
            title={t('governance.agents.title')}
            subtitle={t('governance.agents.subtitle')}
          >
            <div className="space-y-3">
              {agents.length === 0 ? (
                <p className="text-center text-[var(--text-secondary)] py-8">{t('governance.agents.noAgents')}</p>
              ) : (
                agents.map((agent, index) => (
                  <button
                    key={agent.id} 
                    className="w-full text-left flex items-center justify-between p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] cursor-pointer transition-opacity hover:opacity-80"
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-lg font-bold text-[var(--text-secondary)]">#{index + 1}</div>
                      <div>
                        <p className="font-semibold text-[var(--text-primary)]">{agent.name}</p>
                        <p className="text-sm text-[var(--text-secondary)]">{t('common.idShort', { id: agent.id?.substring(0, 8) + '...' })}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-[var(--text-primary)]">{agent.reputation_score || 0}</p>
                        <p className="text-sm text-[var(--text-secondary)]">{t('governance.agents.reputation')}</p>
                      </div>
                      <Badge className={getStatusColor(agent.status)}>
                        {agent.status?.toUpperCase()}
                      </Badge>
                    </div>
                  </button>
                ))
              )}
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="events" className="space-y-4">
          <SectionCard
            title={t('governance.events.title')}
            subtitle={t('governance.events.subtitle')}
          >
            <div className="space-y-2">
              {events.length === 0 ? (
                <p className="text-center text-[var(--text-secondary)] py-8">{t('governance.events.noEvents')}</p>
              ) : (
                events.map((event) => (
                  <div key={event.event_id} className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
                    {getEventTypeIcon(event.event_type)}
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-[var(--text-primary)]">{event.event_type}</p>
                        <span className="text-xs text-[var(--text-secondary)]">{formatTimestamp(event.created_at)}</span>
                      </div>
                      {event.reason && (
                        <p className="text-sm text-[var(--text-secondary)] mt-1">{event.reason}</p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">
                          {t('governance.events.delta')}: {event.delta > 0 ? '+' : ''}{event.delta}
                        </Badge>
                        {event.trace_id && (
                          <Badge variant="outline" className="text-xs">
                            {t('governance.events.trace')}: {event.trace_id.substring(0, 8)}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="violations" className="space-y-4">
          <SectionCard
            title={t('governance.violations.title')}
            subtitle={t('governance.violations.subtitle')}
          >
            <div className="space-y-2">
              {violations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 space-y-3">
                  <CheckCircle className="w-12 h-12 text-success-600" />
                  <p className="text-[var(--text-secondary)]">{t('governance.violations.noViolations')}</p>
                </div>
              ) : (
                violations.map((violation) => (
                  <div key={violation.violation_id} className="flex items-start gap-3 p-3 rounded-lg border border-error-200 bg-error-50/80 dark:bg-error-900/20">
                    <AlertTriangle className="w-5 h-5 text-error-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-error-900">{violation.violation_type}</p>
                        <span className="text-xs text-error-600">{formatTimestamp(violation.detected_at)}</span>
                      </div>
                      <p className="text-sm text-error-700 mt-1">{violation.description}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="destructive" className="text-xs">
                          {t('governance.violations.severity')}: {violation.severity}
                        </Badge>
                        {violation.resolved && (
                          <Badge variant="outline" className="text-xs bg-success-100 text-success-800">
                            {t('governance.violations.resolved')}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </SectionCard>
        </TabsContent>

        <TabsContent value="executionLogs" className="space-y-4">
          <AgentExecutionLogs />
        </TabsContent>
      </Tabs>
    </PageScaffold>
  )
}

export default AgentGovernance
