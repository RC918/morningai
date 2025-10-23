import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Shield, 
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Activity,
  Award
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import apiClient from '@/lib/api'

const AgentGovernance = () => {
  const { t } = useTranslation()
  const [agents, setAgents] = useState([])
  const [events, setEvents] = useState([])
  const [violations, setViolations] = useState([])
  const [statistics, setStatistics] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState(null)

  useEffect(() => {
    loadGovernanceData()
  }, [])

  const loadGovernanceData = async () => {
    try {
      setLoading(true)
      
      const [agentsRes, eventsRes, violationsRes, statsRes] = await Promise.all([
        apiClient.get('/api/governance/agents?limit=20'),
        apiClient.get('/api/governance/events?limit=50'),
        apiClient.get('/api/governance/violations?limit=20'),
        apiClient.get('/api/governance/statistics')
      ])

      setAgents(agentsRes.agents || [])
      setEvents(eventsRes.events || [])
      setViolations(violationsRes.violations || [])
      setStatistics(statsRes.statistics || {})
    } catch (error) {
      console.error('Failed to load governance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPermissionLevelBadge = (level) => {
    const levels = {
      'sandbox_only': { color: 'bg-gray-100 text-gray-800', label: 'Sandbox' },
      'staging_access': { color: 'bg-blue-100 text-blue-800', label: 'Staging' },
      'prod_low_risk': { color: 'bg-yellow-100 text-yellow-800', label: 'Prod (Low Risk)' },
      'prod_full_access': { color: 'bg-green-100 text-green-800', label: 'Prod (Full)' }
    }
    const config = levels[level] || levels['sandbox_only']
    return <Badge className={config.color}>{config.label}</Badge>
  }

  const getReputationColor = (score) => {
    if (score >= 160) return 'text-green-600'
    if (score >= 130) return 'text-blue-600'
    if (score >= 90) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getEventTypeIcon = (eventType) => {
    const icons = {
      'pr_merged': <CheckCircle className="w-4 h-4 text-green-600" />,
      'pr_reverted': <XCircle className="w-4 h-4 text-red-600" />,
      'test_passed': <CheckCircle className="w-4 h-4 text-green-600" />,
      'test_failed': <XCircle className="w-4 h-4 text-red-600" />,
      'human_escalation': <AlertCircle className="w-4 h-4 text-yellow-600" />,
      'violation_detected': <AlertCircle className="w-4 h-4 text-red-600" />,
      'cost_overrun': <DollarSign className="w-4 h-4 text-red-600" />,
      'permission_upgraded': <TrendingUp className="w-4 h-4 text-green-600" />,
      'permission_downgraded': <TrendingDown className="w-4 h-4 text-red-600" />
    }
    return icons[eventType] || <Activity className="w-4 h-4 text-gray-600" />
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    const date = new Date(timestamp)
    return date.toLocaleString()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading governance data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            Agent Governance
          </h1>
          <p className="text-gray-600 mt-1">Monitor agent reputation, permissions, and compliance</p>
        </div>
        <Button onClick={loadGovernanceData}>
          <Activity className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Statistics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Total Agents</p>
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {statistics.total_agents || agents.length}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Average Score</p>
              <Award className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {statistics.average_score?.toFixed(0) || 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">High Reputation</p>
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {statistics.high_reputation_agents || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Violations (24h)</p>
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {violations.length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="agents" className="w-full">
        <TabsList>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
        </TabsList>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Reputation Leaderboard</CardTitle>
              <CardDescription>All agents ranked by reputation score</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {agents.map((agent, index) => (
                  <div 
                    key={agent.agent_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedAgent(agent)}
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-gray-900">{agent.agent_type || 'Unknown'}</p>
                          {getPermissionLevelBadge(agent.permission_level)}
                        </div>
                        <p className="text-sm text-gray-600">ID: {agent.agent_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Reputation</p>
                        <p className={`text-2xl font-bold ${getReputationColor(agent.reputation_score)}`}>
                          {agent.reputation_score}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">PRs Merged</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {agent.summary?.statistics?.pr_merged_count || 0}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Test Pass Rate</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {agent.summary?.statistics?.test_pass_rate?.toFixed(0) || 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {agents.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No agents found
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Events</CardTitle>
              <CardDescription>Latest reputation-affecting events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {events.map((event) => (
                  <div 
                    key={event.event_id}
                    className="flex items-start gap-3 p-3 border rounded-lg hover:bg-gray-50"
                  >
                    {getEventTypeIcon(event.event_type)}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-gray-900">{event.event_type}</p>
                        <Badge variant="outline">{event.score_delta > 0 ? '+' : ''}{event.score_delta}</Badge>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{event.reason || 'No reason provided'}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Agent: {event.agent_id}</span>
                        <span>Trace: {event.trace_id}</span>
                        <span>{formatTimestamp(event.created_at)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {events.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No events found
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Violations Tab */}
        <TabsContent value="violations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Violation History</CardTitle>
              <CardDescription>Policy violations and security events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {violations.map((violation) => (
                  <div 
                    key={violation.event_id}
                    className="flex items-start gap-3 p-3 border border-red-200 bg-red-50 rounded-lg"
                  >
                    <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-red-900">Violation Detected</p>
                        <Badge className="bg-red-100 text-red-800">-{Math.abs(violation.score_delta)}</Badge>
                      </div>
                      <p className="text-sm text-red-700 mt-1">{violation.reason || 'Policy violation'}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-red-600">
                        <span>Agent: {violation.agent_id}</span>
                        <span>Trace: {violation.trace_id}</span>
                        <span>{formatTimestamp(violation.created_at)}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {violations.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                    <p>No violations detected</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Selected Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{selectedAgent.agent_type}</CardTitle>
                  <CardDescription>Agent ID: {selectedAgent.agent_id}</CardDescription>
                </div>
                <Button variant="ghost" onClick={() => setSelectedAgent(null)}>
                  <XCircle className="w-5 h-5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Reputation Score</p>
                  <p className={`text-3xl font-bold ${getReputationColor(selectedAgent.reputation_score)}`}>
                    {selectedAgent.reputation_score}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Permission Level</p>
                  <div className="mt-2">
                    {getPermissionLevelBadge(selectedAgent.permission_level)}
                  </div>
                </div>
              </div>

              {selectedAgent.summary?.statistics && (
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-3">Statistics</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-sm text-gray-600">PRs Merged</p>
                      <p className="text-xl font-bold">{selectedAgent.summary.statistics.pr_merged_count || 0}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-sm text-gray-600">PRs Reverted</p>
                      <p className="text-xl font-bold">{selectedAgent.summary.statistics.pr_reverted_count || 0}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-sm text-gray-600">Test Pass Rate</p>
                      <p className="text-xl font-bold">{selectedAgent.summary.statistics.test_pass_rate?.toFixed(0) || 0}%</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-sm text-gray-600">Violations</p>
                      <p className="text-xl font-bold">{selectedAgent.summary.statistics.violation_count || 0}</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="border-t pt-4">
                <h3 className="font-semibold mb-3">Timestamps</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created:</span>
                    <span>{formatTimestamp(selectedAgent.created_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Updated:</span>
                    <span>{formatTimestamp(selectedAgent.last_updated)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Last Activity:</span>
                    <span>{formatTimestamp(selectedAgent.last_activity)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default AgentGovernance
