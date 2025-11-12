import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Badge, Button, Tabs, TabsContent, TabsList, TabsTrigger, Alert, AlertDescription, AlertTitle } from '@morningai/shared-ui'
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
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getPermissionLevelColor = (level) => {
    switch (level) {
      case 'prod_full_access':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'prod_low_risk':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'staging_access':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'sandbox_only':
        return 'bg-gray-100 text-gray-800 border-gray-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
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
    switch (eventType) {
      case 'task_success':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'task_failure':
        return <XCircle className="w-4 h-4 text-red-600" />
      case 'budget_exceeded':
        return <AlertTriangle className="w-4 h-4 text-orange-600" />
      case 'permission_denied':
        return <Shield className="w-4 h-4 text-red-600" />
      default:
        return <Activity className="w-4 h-4 text-gray-600" />
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            {t('governance.title')}
          </h1>
          <p className="text-gray-600 mt-1">{t('governance.subtitle')}</p>
        </div>
        <Button onClick={loadGovernanceData} variant="outline" disabled={loading}>
          <Activity className="w-4 h-4 mr-2" />
          {t('governance.refresh')}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadGovernanceData} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              {t('common.refresh')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.stats.totalAgents')}</p>
                <Shield className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {statistics.reputation?.total_agents || 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.stats.avgReputation')}</p>
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {statistics.reputation?.average_score?.toFixed(0) || 100}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.stats.dailyCost')}</p>
                <DollarSign className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                ${statistics.costs?.daily?.usage?.usd?.toFixed(2) || '0.00'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.stats.violations')}</p>
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {violations.length}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="agents" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="agents">{t('governance.tabs.agents')}</TabsTrigger>
          <TabsTrigger value="events">{t('governance.tabs.events')}</TabsTrigger>
          <TabsTrigger value="violations">{t('governance.tabs.violations')}</TabsTrigger>
          <TabsTrigger value="executionLogs">{t('governance.tabs.executionLogs')}</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('governance.agents.title')}</CardTitle>
              <CardDescription>{t('governance.agents.subtitle')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {agents.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">{t('governance.agents.noAgents')}</p>
                ) : (
                  agents.map((agent, index) => (
                    <button
                      key={agent.id} 
                      className="w-full text-left flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => setSelectedAgent(agent)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-2xl font-bold text-gray-400">#{index + 1}</div>
                        <div>
                          <p className="font-semibold text-gray-900">{agent.name}</p>
                          <p className="text-sm text-gray-600">{t('common.idShort', { id: agent.id?.substring(0, 8) + '...' })}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-2xl font-bold text-gray-900">{agent.reputation_score || 0}</p>
                          <p className="text-sm text-gray-600">{t('governance.agents.reputation')}</p>
                        </div>
                        <Badge className={getStatusColor(agent.status)}>
                          {agent.status?.toUpperCase()}
                        </Badge>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('governance.events.title')}</CardTitle>
              <CardDescription>{t('governance.events.subtitle')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {events.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">{t('governance.events.noEvents')}</p>
                ) : (
                  events.map((event) => (
                    <div key={event.event_id} className="flex items-start gap-3 p-3 border rounded-lg">
                      {getEventTypeIcon(event.event_type)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-gray-900">{event.event_type}</p>
                          <span className="text-xs text-gray-500">{formatTimestamp(event.created_at)}</span>
                        </div>
                        {event.reason && (
                          <p className="text-sm text-gray-600 mt-1">{event.reason}</p>
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
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="violations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t('governance.violations.title')}</CardTitle>
              <CardDescription>{t('governance.violations.subtitle')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {violations.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                    <p className="text-gray-500">{t('governance.violations.noViolations')}</p>
                  </div>
                ) : (
                  violations.map((violation) => (
                    <div key={violation.violation_id} className="flex items-start gap-3 p-3 border border-red-200 bg-red-50 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-red-900">{violation.violation_type}</p>
                          <span className="text-xs text-red-600">{formatTimestamp(violation.detected_at)}</span>
                        </div>
                        <p className="text-sm text-red-700 mt-1">{violation.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="destructive" className="text-xs">
                            {t('governance.violations.severity')}: {violation.severity}
                          </Badge>
                          {violation.resolved && (
                            <Badge variant="outline" className="text-xs bg-green-100 text-green-800">
                              {t('governance.violations.resolved')}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="executionLogs" className="space-y-4">
          <AgentExecutionLogs />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default AgentGovernance
