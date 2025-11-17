import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@morningai/shared-ui'
import { Badge } from '@morningai/shared-ui'
import { AppleButton } from '@/components/ui/apple-button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@morningai/shared-ui'
import { Progress } from '@morningai/shared-ui'
import { 
  Shield, 
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Activity
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { customFetch } from '@/lib/api-client'

type PermissionLevel = 'prod_full_access' | 'prod_low_risk' | 'staging_access' | 'sandbox_only'
type EventType = 'task_success' | 'task_failure' | 'budget_exceeded' | 'permission_denied'

interface Agent {
  agent_id: string
  agent_type: string
  reputation_score: number
  permission_level: PermissionLevel
}

interface GovernanceEvent {
  event_id: string
  event_type: EventType
  created_at: string
  reason?: string
  delta: number
  trace_id?: string
}

interface Violation {
  violation_id: string
  violation_type: string
  detected_at: string
  description: string
  severity: string
  resolved?: boolean
}

interface CostData {
  usd?: number
}

interface DailyCost {
  usage?: CostData
}

interface CostsData {
  daily?: DailyCost
}

interface Statistics {
  total_agents?: number
  average_score?: number
  agents_by_level?: Record<string, number>
  high_reputation_agents?: number
  low_reputation_agents?: number
  costs?: CostsData
}

const AgentGovernance = (): React.ReactElement => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState<boolean>(true)
  const [agents, setAgents] = useState<Agent[]>([])
  const [events, setEvents] = useState<GovernanceEvent[]>([])
  const [violations, setViolations] = useState<Violation[]>([])
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)

  useEffect(() => {
    loadGovernanceData()
  }, [])

  const loadGovernanceData = async (): Promise<void> => {
    try {
      setLoading(true)
      
      const [agentsData, eventsData, violationsData, statsData]: [
        { agents?: Agent[] },
        { events?: GovernanceEvent[] },
        { violations?: Violation[] },
        Statistics
      ] = await Promise.all([
        customFetch({ url: '/api/governance/agents' }),
        customFetch({ url: '/api/governance/events?limit=50' }),
        customFetch({ url: '/api/governance/violations?limit=50' }),
        customFetch({ url: '/api/governance/statistics' })
      ])

      setAgents(agentsData.agents || [])
      setEvents(eventsData.events || [])
      setViolations(violationsData.violations || [])
      setStatistics(statsData)
    } catch (error) {
      console.error('Failed to load governance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPermissionLevelColor = (level: PermissionLevel): string => {
    switch (level) {
      case 'prod_full_access':
        return 'bg-success-100 text-success-800 border-success-300'
      case 'prod_low_risk':
        return 'bg-primary-100 text-primary-800 border-primary-300'
      case 'staging_access':
        return 'bg-warning-100 text-warning-800 border-warning-300'
      case 'sandbox_only':
        return 'bg-neutral-100 text-neutral-800 border-neutral-300'
      default:
        return 'bg-neutral-100 text-neutral-800 border-neutral-300'
    }
  }

  const getPermissionLevelLabel = (level: PermissionLevel): string => {
    const labels: Record<PermissionLevel, string> = {
      'prod_full_access': 'Production Full',
      'prod_low_risk': 'Production Low Risk',
      'staging_access': 'Staging',
      'sandbox_only': 'Sandbox Only'
    }
    return labels[level] || level
  }

  const getEventTypeIcon = (eventType: EventType): React.ReactElement => {
    switch (eventType) {
      case 'task_success':
        return <CheckCircle className="w-4 h-4 text-success-600" />
      case 'task_failure':
        return <XCircle className="w-4 h-4 text-error-600" />
      case 'budget_exceeded':
        return <AlertTriangle className="w-4 h-4 text-warning-600" />
      case 'permission_denied':
        return <Shield className="w-4 h-4 text-error-600" />
      default:
        return <Activity className="w-4 h-4 text-gray-600" />
    }
  }

  const formatTimestamp = (timestamp: string | undefined): string => {
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary-600" />
            Agent Governance
          </h1>
          <p className="text-gray-600 mt-1">Monitor agent reputation, permissions, and compliance</p>
        </div>
        <AppleButton onClick={loadGovernanceData} variant="outline">
          <Activity className="w-4 h-4 mr-2" />
          Refresh
        </AppleButton>
      </div>

      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Total Agents</p>
                <Shield className="w-5 h-5 text-primary-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {statistics.total_agents || 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Avg Reputation</p>
                <TrendingUp className="w-5 h-5 text-success-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {statistics.average_score?.toFixed(0) || 100}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Daily Cost</p>
                <DollarSign className="w-5 h-5 text-accent-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                ${statistics.costs?.daily?.usage?.usd?.toFixed(2) || '0.00'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Violations</p>
                <AlertTriangle className="w-5 h-5 text-error-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {violations.length}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="agents" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Reputation Leaderboard</CardTitle>
              <CardDescription>Agents ranked by reputation score and permission level</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {agents.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No agents found</p>
                ) : (
                  agents.map((agent, index) => (
                    <div 
                      key={agent.agent_id} 
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => setSelectedAgent(agent)}
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-2xl font-bold text-gray-400">#{index + 1}</div>
                        <div>
                          <p className="font-semibold text-gray-900">{agent.agent_type}</p>
                          <p className="text-sm text-gray-600">ID: {agent.agent_id?.substring(0, 8)}...</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-2xl font-bold text-gray-900">{agent.reputation_score}</p>
                          <p className="text-sm text-gray-600">Reputation</p>
                        </div>
                        <Badge className={getPermissionLevelColor(agent.permission_level)}>
                          {getPermissionLevelLabel(agent.permission_level)}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Events</CardTitle>
              <CardDescription>Reputation events and agent activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {events.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No events found</p>
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
                            Delta: {event.delta > 0 ? '+' : ''}{event.delta}
                          </Badge>
                          {event.trace_id && (
                            <Badge variant="outline" className="text-xs">
                              Trace: {event.trace_id.substring(0, 8)}
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
              <CardTitle>Policy Violations</CardTitle>
              <CardDescription>Security and compliance violations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {violations.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-success-600 mx-auto mb-2" />
                    <p className="text-gray-500">No violations detected</p>
                  </div>
                ) : (
                  violations.map((violation) => (
                    <div key={violation.violation_id} className="flex items-start gap-3 p-3 border border-error-200 bg-error-50 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-error-600 mt-0.5" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-error-900">{violation.violation_type}</p>
                          <span className="text-xs text-error-600">{formatTimestamp(violation.detected_at)}</span>
                        </div>
                        <p className="text-sm text-error-700 mt-1">{violation.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="destructive" className="text-xs">
                            Severity: {violation.severity}
                          </Badge>
                          {violation.resolved && (
                            <Badge variant="outline" className="text-xs bg-success-100 text-success-800">
                              Resolved
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
      </Tabs>
    </div>
  )
}

export default AgentGovernance
