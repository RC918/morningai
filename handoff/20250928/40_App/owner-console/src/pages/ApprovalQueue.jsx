import { useState, useEffect, useCallback, useRef } from 'react'
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
  Server,
  Loader2,
  RefreshCw
} from 'lucide-react'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'

const RISK_LEVEL_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }
const AUTO_REFRESH_INTERVAL = 30000 // 30 seconds

const ApprovalQueue = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pendingRequests, setPendingRequests] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [selectedRequest, setSelectedRequest] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionType, setActionType] = useState(null) // 'approve' or 'reject'
  const [rejectionReason, setRejectionReason] = useState('')
  const [activeTab, setActiveTab] = useState('pending')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [shouldFocusDetails, setShouldFocusDetails] = useState(false)
  const listRef = useRef(null)
  const detailsRef = useRef(null)
  const isRefreshingRef = useRef(false) // In-flight guard to prevent race conditions

  const sortRequests = useCallback((requests) => {
    return [...requests].sort((a, b) => {
      // Primary sort: risk level (critical > high > medium > low)
      const riskA = RISK_LEVEL_ORDER[a.risk_level] ?? 4
      const riskB = RISK_LEVEL_ORDER[b.risk_level] ?? 4
      if (riskA !== riskB) return riskA - riskB
      
      // Secondary sort: timeout (sooner first)
      const timeoutA = a.timeout_at ? new Date(a.timeout_at).getTime() : Infinity
      const timeoutB = b.timeout_at ? new Date(b.timeout_at).getTime() : Infinity
      return timeoutA - timeoutB
    })
  }, [])

  const loadApprovalData = useCallback(async (isAutoRefresh = false) => {
    // In-flight guard to prevent race conditions during auto-refresh
    if (isAutoRefresh && isRefreshingRef.current) {
      return
    }
    
    try {
      if (isAutoRefresh) {
        isRefreshingRef.current = true
      } else {
        setLoading(true)
      }
      setError(null)
      
      const [requestsResult, statsResult] = await Promise.all([
        apiClientWithMeta('/api/action-requests', { method: 'GET' }),
        apiClientWithMeta('/api/action-requests/statistics', { method: 'GET' }).catch(err => {
          console.error('Failed to load approval stats:', err)
          return null
        })
      ])

      const requestsData = (requestsResult && requestsResult.data) || {}
      const sortedRequests = sortRequests(requestsData.requests || [])
      setPendingRequests(sortedRequests)
      setLastUpdated(new Date())

      if (statsResult) {
        setStatistics(statsResult.data || null)
      }
    } catch (err) {
      const message = handleApiError(err, {
        defaultMessage: 'Failed to load approval data',
        statusMessages: { 503: 'HITL system not available' },
        logContext: 'loadApprovalData'
      })
      setError(message)
    } finally {
      if (isAutoRefresh) {
        isRefreshingRef.current = false
      } else {
        setLoading(false)
      }
    }
  }, [sortRequests])

  // Initial load
  useEffect(() => {
    loadApprovalData()
  }, [loadApprovalData])

  // Auto-refresh using recursive setTimeout to avoid race conditions
  // setTimeout ensures the next refresh only starts after the previous one completes
  useEffect(() => {
    if (!autoRefresh) return
    
    let timeoutId = null
    let isMounted = true
    
    const scheduleNextRefresh = async () => {
      if (!isMounted) return
      
      await loadApprovalData(true)
      
      if (isMounted) {
        timeoutId = setTimeout(scheduleNextRefresh, AUTO_REFRESH_INTERVAL)
      }
    }
    
    // Start the first refresh after the interval
    timeoutId = setTimeout(scheduleNextRefresh, AUTO_REFRESH_INTERVAL)
    
    return () => {
      isMounted = false
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [autoRefresh, loadApprovalData])

  // Focus management for details panel (replaces setTimeout with requestAnimationFrame)
  useEffect(() => {
    if (!shouldFocusDetails || activeTab !== 'details' || !selectedRequest) return

    const frameId = window.requestAnimationFrame(() => {
      detailsRef.current?.focus()
      setShouldFocusDetails(false)
    })

    return () => window.cancelAnimationFrame(frameId)
  }, [shouldFocusDetails, activeTab, selectedRequest])

  const handleApprove = async (requestId) => {
    try {
      setActionLoading(true)
      setActionType('approve')
      
      await apiClientWithMeta(`/api/action-requests/${requestId}/approve`, {
        method: 'POST'
      })

      await loadApprovalData()
      setSelectedRequest(null)
      setActiveTab('pending')
    } catch (err) {
      const message = handleApiError(err, {
        defaultMessage: 'Failed to approve request',
        logContext: 'handleApprove'
      })
      setError(message)
    } finally {
      setActionLoading(false)
      setActionType(null)
    }
  }

  const handleReject = async (requestId) => {
    try {
      setActionLoading(true)
      setActionType('reject')
      
      await apiClientWithMeta(`/api/action-requests/${requestId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason: rejectionReason })
      })

      await loadApprovalData()
      setSelectedRequest(null)
      setRejectionReason('')
      setActiveTab('pending')
    } catch (err) {
      const message = handleApiError(err, {
        defaultMessage: 'Failed to reject request',
        logContext: 'handleReject'
      })
      setError(message)
    } finally {
      setActionLoading(false)
      setActionType(null)
    }
  }

  // Handle request selection with auto-tab switch
  const handleSelectRequest = useCallback((request) => {
    setSelectedRequest(request)
    setActiveTab('details')
    setShouldFocusDetails(true)
  }, [])

  // Keyboard navigation for the list
  const handleListKeyDown = useCallback((e) => {
    if (!pendingRequests.length) return
    
    const currentIndex = selectedRequest 
      ? pendingRequests.findIndex(r => r.request_id === selectedRequest.request_id)
      : -1
    
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const nextIndex = currentIndex < pendingRequests.length - 1 ? currentIndex + 1 : 0
      handleSelectRequest(pendingRequests[nextIndex])
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : pendingRequests.length - 1
      handleSelectRequest(pendingRequests[prevIndex])
    } else if (e.key === 'Enter' && selectedRequest) {
      e.preventDefault()
      setActiveTab('details')
    }
  }, [pendingRequests, selectedRequest, handleSelectRequest])

  // Format last updated time
  const formatLastUpdated = useCallback((date) => {
    if (!date) return ''
    return date.toLocaleTimeString()
  }, [])

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
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-xs text-[var(--text-secondary)]">
              {t('approvalQueue.lastUpdated', 'Last updated')}: {formatLastUpdated(lastUpdated)}
            </span>
          )}
          <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-[var(--border)]"
              aria-label={t('approvalQueue.autoRefresh', 'Auto-refresh')}
            />
            {t('approvalQueue.autoRefresh', 'Auto-refresh')}
          </label>
          <AppleButton onClick={() => loadApprovalData()} variant="outline" haptic="light" disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
            {t('common.refresh', 'Refresh')}
          </AppleButton>
        </div>
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

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
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
              <div 
                ref={listRef}
                role="listbox"
                aria-label={t('approvalQueue.pending.title', 'Pending Action Requests')}
                onKeyDown={handleListKeyDown}
                tabIndex={pendingRequests.length > 0 ? 0 : -1}
                className="space-y-3 outline-none"
              >
                {pendingRequests.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 space-y-3">
                    <CheckCircle className="w-12 h-12 text-growth" aria-hidden="true" />
                    <p className="text-neutral-500 dark:text-neutral-400">
                      {t('approvalQueue.pending.noRequests', 'No pending approval requests')}
                    </p>
                  </div>
                ) : (
                  pendingRequests.map((request) => (
                    <button
                      key={request.request_id}
                      role="option"
                      aria-selected={selectedRequest?.request_id === request.request_id}
                      className={`w-full text-left p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedRequest?.request_id === request.request_id
                          ? 'border-calm bg-calm-10 ring-2 ring-calm'
                          : 'border-[var(--border)] bg-[var(--surface)] hover:opacity-80'
                      }`}
                      onClick={() => handleSelectRequest(request)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4">
                          <span aria-hidden="true">{getRiskLevelIcon(request.risk_level)}</span>
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
                                <Clock className="w-3 h-3" aria-hidden="true" />
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
                              handleSelectRequest(request)
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
            <div 
              ref={detailsRef}
              tabIndex={-1}
              aria-busy={actionLoading}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card outline-none" 
              data-testid="request-details"
            >
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
                      <span aria-hidden="true">{getActionTypeIcon(selectedRequest.action_type)}</span>
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
                      <AlertTriangle className="w-5 h-5 text-joy" aria-hidden="true" />
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
                  <label className="block">
                    <span className="text-sm text-[var(--text-secondary)] mb-2 block">
                      {t('approvalQueue.details.rejectionReasonLabel', 'Rejection Reason (for audit trail)')}
                    </span>
                    <textarea
                      className="w-full p-3 border rounded-lg bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white"
                      rows={3}
                      placeholder={t('approvalQueue.details.rejectionReasonPlaceholder', 'Enter reason for rejection...')}
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      aria-describedby="rejection-reason-hint"
                    />
                    <span id="rejection-reason-hint" className="text-xs text-[var(--text-secondary)] mt-1 block">
                      {t('approvalQueue.details.rejectionReasonHint', 'Provide a reason to help with audit trail and future reference')}
                    </span>
                  </label>
                </div>

                <div className="flex justify-end gap-3">
                  <AppleButton
                    variant="outline"
                    haptic="light"
                    onClick={() => {
                      setSelectedRequest(null)
                      setRejectionReason('')
                      setActiveTab('pending')
                    }}
                    disabled={actionLoading}
                  >
                    {t('common.cancel', 'Cancel')}
                  </AppleButton>
                  <AppleButton
                    variant="outline"
                    haptic="medium"
                    onClick={() => handleReject(selectedRequest.request_id)}
                    disabled={actionLoading}
                    className="border-energy text-energy hover:bg-energy-10"
                    aria-busy={actionType === 'reject'}
                  >
                    {actionType === 'reject' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                    ) : (
                      <XCircle className="w-4 h-4 mr-2" aria-hidden="true" />
                    )}
                    {actionType === 'reject' 
                      ? t('approvalQueue.actions.rejecting', 'Rejecting...') 
                      : t('common.reject', 'Reject')}
                  </AppleButton>
                  <AppleButton
                    haptic="medium"
                    onClick={() => handleApprove(selectedRequest.request_id)}
                    disabled={actionLoading}
                    className="bg-growth text-white hover:bg-growth-dark"
                    aria-busy={actionType === 'approve'}
                  >
                    {actionType === 'approve' ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
                    ) : (
                      <CheckCircle className="w-4 h-4 mr-2" aria-hidden="true" />
                    )}
                    {actionType === 'approve' 
                      ? t('approvalQueue.actions.approving', 'Approving...') 
                      : t('common.approve', 'Approve')}
                  </AppleButton>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card" data-testid="empty-state">
              <div className="py-8">
                <div className="flex flex-col items-center justify-center space-y-3">
                  <Shield className="w-12 h-12 text-[var(--text-secondary)]" aria-hidden="true" />
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
