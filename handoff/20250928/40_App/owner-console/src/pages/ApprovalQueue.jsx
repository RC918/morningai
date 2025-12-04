import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge, Tabs, TabsContent, TabsList, TabsTrigger, Skeleton } from '@morningai/shared-ui'
import { 
  Shield, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Database,
  FileWarning,
  Server
} from 'lucide-react'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const ApprovalQueue = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pendingRequests, setPendingRequests] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [selectedRequest, setSelectedRequest] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [rejectionReason, setRejectionReason] = useState('')

  useEffect(() => {
    loadApprovalData()
  }, [])

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    }
  }

  const loadApprovalData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [requestsResponse, statsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/action-requests`, { headers: getAuthHeaders() }),
        fetch(`${API_BASE}/api/action-requests/statistics`, { headers: getAuthHeaders() })
      ])

      if (requestsResponse.ok) {
        const data = await requestsResponse.json()
        setPendingRequests(data.requests || [])
      } else if (requestsResponse.status === 503) {
        setError('HITL system not available')
      }

      if (statsResponse.ok) {
        const data = await statsResponse.json()
        setStatistics(data)
      }
    } catch (error) {
      console.error('Failed to load approval data:', error)
      setError(error.message || 'Failed to load approval data')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (requestId) => {
    try {
      setActionLoading(true)
      const response = await fetch(`${API_BASE}/api/action-requests/${requestId}/approve`, {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        await loadApprovalData()
        setSelectedRequest(null)
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to approve request')
      }
    } catch (error) {
      setError(error.message || 'Failed to approve request')
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async (requestId) => {
    try {
      setActionLoading(true)
      const response = await fetch(`${API_BASE}/api/action-requests/${requestId}/reject`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ reason: rejectionReason })
      })

      if (response.ok) {
        await loadApprovalData()
        setSelectedRequest(null)
        setRejectionReason('')
      } else {
        const data = await response.json()
        setError(data.message || 'Failed to reject request')
      }
    } catch (error) {
      setError(error.message || 'Failed to reject request')
    } finally {
      setActionLoading(false)
    }
  }

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'critical':
        return 'bg-energy-10 text-energy border-energy'
      case 'high':
        return 'bg-joy-10 text-joy border-joy'
      case 'medium':
        return 'bg-wisdom-10 text-wisdom border-wisdom'
      case 'low':
        return 'bg-calm-10 text-calm border-calm'
      default:
        return 'bg-neutral-100 text-neutral-600'
    }
  }

  const getRiskLevelIcon = (level) => {
    switch (level) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-energy" />
      case 'high':
        return <FileWarning className="w-5 h-5 text-joy" />
      case 'medium':
        return <Database className="w-5 h-5 text-wisdom" />
      default:
        return <Server className="w-5 h-5 text-calm" />
    }
  }

  const getActionTypeIcon = (actionType) => {
    const type = actionType?.toLowerCase() || ''
    if (type.includes('drop') || type.includes('delete') || type.includes('truncate')) {
      return <Database className="w-5 h-5 text-energy" />
    }
    if (type.includes('deploy') || type.includes('production')) {
      return <Server className="w-5 h-5 text-joy" />
    }
    if (type.includes('secret') || type.includes('env') || type.includes('credential')) {
      return <FileWarning className="w-5 h-5 text-wisdom" />
    }
    return <Activity className="w-5 h-5 text-calm" />
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }

  const getTimeRemaining = (timeoutAt) => {
    if (!timeoutAt) return 'N/A'
    const now = new Date()
    const timeout = new Date(timeoutAt)
    const diff = timeout - now
    
    if (diff <= 0) return 'Expired'
    
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    
    if (hours > 0) {
      return `${hours}h ${minutes}m remaining`
    }
    return `${minutes}m remaining`
  }

  if (loading) {
    return (
      <div className="space-y-8" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-7 w-48 mb-2" aria-hidden="true" />
            <Skeleton className="h-5 w-96" aria-hidden="true" />
          </div>
          <Skeleton className="h-10 w-28" aria-hidden="true" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
              <Skeleton className="h-4 w-20 mb-2" aria-hidden="true" />
              <Skeleton className="h-8 w-16" aria-hidden="true" />
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
          <div className="px-5 py-4 border-b border-[var(--border)]">
            <Skeleton className="h-6 w-48 mb-2" aria-hidden="true" />
            <Skeleton className="h-4 w-64" aria-hidden="true" />
          </div>
          <div className="p-5 space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-full" aria-hidden="true" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8" aria-busy={loading} data-testid="approval-queue">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            {t('approvalQueue.title', 'Approval Queue')}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {t('approvalQueue.subtitle', 'Review and approve high-risk actions requiring human authorization')}
          </p>
        </div>
        <AppleButton onClick={loadApprovalData} variant="outline" haptic="light" disabled={loading}>
          <Activity className="w-4 h-4 mr-2" />
          {t('common.refresh', 'Refresh')}
        </AppleButton>
      </div>

      {error && (
        <AppleErrorBanner
          title={t('common.error', 'Error')}
          message={error}
          onRetry={loadApprovalData}
        />
      )}

      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-secondary)]">
                {t('approvalQueue.stats.pending', 'Pending')}
              </p>
              <Clock className="w-5 h-5 text-joy" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">
              {statistics.pending_count || 0}
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-secondary)]">
                {t('approvalQueue.stats.critical', 'Critical')}
              </p>
              <AlertTriangle className="w-5 h-5 text-energy" />
            </div>
            <p className="text-2xl font-bold text-energy">
              {statistics.by_risk_level?.critical || 0}
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-secondary)]">
                {t('approvalQueue.stats.high', 'High Risk')}
              </p>
              <FileWarning className="w-5 h-5 text-joy" />
            </div>
            <p className="text-2xl font-bold text-joy">
              {statistics.by_risk_level?.high || 0}
            </p>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-[var(--text-secondary)]">
                {t('approvalQueue.stats.medium', 'Medium/Low')}
              </p>
              <Shield className="w-5 h-5 text-calm" />
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">
              {(statistics.by_risk_level?.medium || 0) + (statistics.by_risk_level?.low || 0)}
            </p>
          </div>
        </div>
      )}

      <Tabs defaultValue="pending" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pending">
            {t('approvalQueue.tabs.pending', 'Pending Approvals')}
            {pendingRequests.length > 0 && (
              <Badge className="ml-2 bg-energy-10 text-energy">{pendingRequests.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="details">
            {t('approvalQueue.tabs.details', 'Request Details')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card" data-testid="pending-requests">
            <div className="px-5 py-4 border-b border-[var(--border)]">
              <h2 className="text-base font-semibold text-[var(--text-primary)]">
                {t('approvalQueue.pending.title', 'Pending Action Requests')}
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                {t('approvalQueue.pending.subtitle', 'Actions awaiting your approval before execution')}
              </p>
            </div>
            <div className="p-5">
              <div className="space-y-3">
                {pendingRequests.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 space-y-3">
                    <CheckCircle className="w-12 h-12 text-growth" />
                    <p className="text-neutral-500 dark:text-neutral-400">
                      {t('approvalQueue.pending.noRequests', 'No pending approval requests')}
                    </p>
                  </div>
                ) : (
                  pendingRequests.map((request) => (
                    <button
                      key={request.request_id}
                      className="w-full text-left p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] cursor-pointer transition-opacity hover:opacity-80"
                      onClick={() => setSelectedRequest(request)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          {getRiskLevelIcon(request.risk_level)}
                          <div>
                            <p className="font-semibold text-[var(--text-primary)]">
                              {request.action_type}
                            </p>
                            <p className="text-sm text-[var(--text-secondary)] mt-1">
                              {request.action_description}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge className={getRiskLevelColor(request.risk_level)}>
                                {request.risk_level?.toUpperCase()}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {t('approvalQueue.details.agent', 'Agent')}: {request.agent_id}
                              </Badge>
                              <Badge variant="outline" className="text-xs flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {getTimeRemaining(request.timeout_at)}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <AppleButton
                            variant="outline"
                            size="sm"
                            haptic="light"
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedRequest(request)
                            }}
                            disabled={actionLoading}
                          >
                            {t('approvalQueue.viewDetails', 'View Details')}
                          </AppleButton>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          {selectedRequest ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card" data-testid="request-details">
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
                      {getActionTypeIcon(selectedRequest.action_type)}
                      {selectedRequest.action_type}
                    </h2>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{selectedRequest.request_id}</p>
                  </div>
                  <Badge className={getRiskLevelColor(selectedRequest.risk_level)}>
                    {selectedRequest.risk_level?.toUpperCase()} RISK
                  </Badge>
                </div>
              </div>
              <div className="p-5 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-[var(--text-secondary)]">{t('approvalQueue.details.agent', 'Agent')}</p>
                    <p className="font-medium text-[var(--text-primary)]">{selectedRequest.agent_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-[var(--text-secondary)]">{t('approvalQueue.details.created', 'Created')}</p>
                    <p className="font-medium text-[var(--text-primary)]">
                      {formatTimestamp(selectedRequest.created_at)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-[var(--text-secondary)]">{t('approvalQueue.details.timeout', 'Timeout')}</p>
                    <p className="font-medium text-[var(--text-primary)]">
                      {getTimeRemaining(selectedRequest.timeout_at)}
                    </p>
                  </div>
                  {selectedRequest.trace_id && (
                    <div>
                      <p className="text-sm text-[var(--text-secondary)]">{t('approvalQueue.details.traceId', 'Trace ID')}</p>
                      <p className="font-medium text-[var(--text-primary)] font-mono text-sm">
                        {selectedRequest.trace_id}
                      </p>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-sm text-[var(--text-secondary)] mb-2">{t('approvalQueue.details.description', 'Description')}</p>
                  <p className="text-[var(--text-primary)] bg-neutral-50 dark:bg-neutral-800 p-4 rounded-lg">
                    {selectedRequest.action_description}
                  </p>
                </div>

                {selectedRequest.risk_reason && (
                  <div>
                    <p className="text-sm text-[var(--text-secondary)] mb-2">{t('approvalQueue.details.riskReason', 'Risk Reason')}</p>
                    <div className="flex items-start gap-2 bg-joy-10 p-4 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-joy mt-0.5" />
                      <p className="text-joy-dark">{selectedRequest.risk_reason}</p>
                    </div>
                  </div>
                )}

                {selectedRequest.affected_resources && selectedRequest.affected_resources.length > 0 && (
                  <div>
                    <p className="text-sm text-[var(--text-secondary)] mb-2">{t('approvalQueue.details.affectedResources', 'Affected Resources')}</p>
                    <div className="space-y-1">
                      {selectedRequest.affected_resources.map((resource, idx) => (
                        <Badge key={idx} variant="outline" className="mr-2">
                          {resource}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedRequest.action_payload && (
                  <div>
                    <p className="text-sm text-[var(--text-secondary)] mb-2">{t('approvalQueue.details.actionPayload', 'Action Payload')}</p>
                    <pre className="bg-neutral-50 dark:bg-neutral-800 p-4 rounded-lg overflow-x-auto text-sm">
                      {JSON.stringify(selectedRequest.action_payload, null, 2)}
                    </pre>
                  </div>
                )}

                <div className="border-t pt-4">
                  <p className="text-sm text-[var(--text-secondary)] mb-2">
                    {t('approvalQueue.details.rejectionReason', 'Rejection Reason (optional)')}
                  </p>
                  <textarea
                    className="w-full p-3 border rounded-lg bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
                    rows={3}
                    placeholder="Enter reason for rejection..."
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                  />
                </div>

                <div className="flex justify-end gap-3">
                  <AppleButton
                    variant="outline"
                    haptic="light"
                    onClick={() => {
                      setSelectedRequest(null)
                      setRejectionReason('')
                    }}
                  >
                    {t('common.cancel', 'Cancel')}
                  </AppleButton>
                  <AppleButton
                    variant="outline"
                    haptic="medium"
                    onClick={() => handleReject(selectedRequest.request_id)}
                    disabled={actionLoading}
                    className="border-energy text-energy hover:bg-energy-10"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    {t('common.reject', 'Reject')}
                  </AppleButton>
                  <AppleButton
                    haptic="medium"
                    onClick={() => handleApprove(selectedRequest.request_id)}
                    disabled={actionLoading}
                    className="bg-growth text-white hover:bg-growth-dark"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    {t('common.approve', 'Approve')}
                  </AppleButton>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card" data-testid="empty-state">
              <div className="py-12">
                <div className="flex flex-col items-center justify-center space-y-3">
                  <Shield className="w-12 h-12 text-[var(--text-secondary)]" />
                  <p className="text-sm text-[var(--text-secondary)]">
                    {t('approvalQueue.details.selectRequest', 'Select a request from the pending list to view details')}
                  </p>
                </div>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default ApprovalQueue
