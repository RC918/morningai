import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Badge, 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger, 
  Skeleton,
  Progress,
  StatCard,
  SectionCard
} from '@morningai/shared-ui'
import { 
  Play,
  Pause,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  ListTodo,
  FileCode,
  FileText,
  TestTube,
  AlertTriangle,
  ChevronRight,
  RotateCcw,
  StopCircle,
  Settings,
  Rocket,
  BadgeCheck,
  Trash2
} from 'lucide-react'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { AppleButton } from '@/components/apple/apple-button'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'

/**
 * Mock data for UI skeleton - moved outside component to prevent recreation on each render.
 * Treat as immutable - do not mutate in place.
 * Will be replaced with real API calls in Phase 2.
 */
const MOCK_SESSIONS = Object.freeze([
    {
      id: 'session_001',
      title: 'Implement user authentication flow',
      goal: 'Add OAuth2 login with Google and GitHub providers',
      status: 'running',
      confidence: 0.87,
      startedAt: '2024-01-15T10:30:00Z',
      updatedAt: '2024-01-15T11:45:00Z',
      progress: 65,
      currentTask: 'Writing integration tests',
      plan: {
        totalTasks: 8,
        completedTasks: 5,
        tasks: [
          { id: 1, name: 'Analyze existing auth code', status: 'completed', type: 'ANALYZE_CODE' },
          { id: 2, name: 'Set up OAuth2 configuration', status: 'completed', type: 'SETUP_ENVIRONMENT' },
          { id: 3, name: 'Implement Google OAuth handler', status: 'completed', type: 'WRITE_CODE' },
          { id: 4, name: 'Implement GitHub OAuth handler', status: 'completed', type: 'WRITE_CODE' },
          { id: 5, name: 'Write unit tests', status: 'completed', type: 'WRITE_TEST' },
          { id: 6, name: 'Write integration tests', status: 'running', type: 'WRITE_TEST' },
          { id: 7, name: 'Run all tests', status: 'pending', type: 'RUN_TEST' },
          { id: 8, name: 'Create pull request', status: 'pending', type: 'CODE_REVIEW' }
        ]
      },
      logs: [
        { timestamp: '2024-01-15T11:45:00Z', message: 'Starting integration test implementation', level: 'info' },
        { timestamp: '2024-01-15T11:30:00Z', message: 'Unit tests passed: 12/12', level: 'success' },
        { timestamp: '2024-01-15T11:15:00Z', message: 'Completed GitHub OAuth handler', level: 'info' }
      ]
    },
    {
      id: 'session_002',
      title: 'Fix database connection pooling',
      goal: 'Resolve connection exhaustion under high load',
      status: 'paused',
      confidence: 0.72,
      startedAt: '2024-01-15T09:00:00Z',
      updatedAt: '2024-01-15T10:15:00Z',
      progress: 40,
      currentTask: 'Waiting for approval',
      requiresApproval: true,
      approvalReason: 'Production database configuration change',
      plan: {
        totalTasks: 6,
        completedTasks: 2,
        tasks: [
          { id: 1, name: 'Analyze connection patterns', status: 'completed', type: 'ANALYZE_CODE' },
          { id: 2, name: 'Design pooling strategy', status: 'completed', type: 'ANALYZE_CODE' },
          { id: 3, name: 'Update pool configuration', status: 'waiting_approval', type: 'WRITE_CODE' },
          { id: 4, name: 'Test in staging', status: 'pending', type: 'RUN_TEST' },
          { id: 5, name: 'Deploy to production', status: 'pending', type: 'DEPLOYMENT' },
          { id: 6, name: 'Monitor metrics', status: 'pending', type: 'VERIFICATION' }
        ]
      },
      logs: [
        { timestamp: '2024-01-15T10:15:00Z', message: 'Awaiting approval for production config change', level: 'warning' },
        { timestamp: '2024-01-15T10:00:00Z', message: 'Pooling strategy designed: min=5, max=20, idle=60s', level: 'info' }
      ]
    },
    {
      id: 'session_003',
      title: 'Refactor payment processing module',
      goal: 'Improve code maintainability and add Stripe webhook support',
      status: 'completed',
      confidence: 0.95,
      startedAt: '2024-01-14T14:00:00Z',
      updatedAt: '2024-01-14T18:30:00Z',
      completedAt: '2024-01-14T18:30:00Z',
      progress: 100,
      currentTask: null,
      prUrl: 'https://github.com/example/repo/pull/123',
      plan: {
        totalTasks: 5,
        completedTasks: 5,
        tasks: [
          { id: 1, name: 'Analyze payment code', status: 'completed', type: 'ANALYZE_CODE' },
          { id: 2, name: 'Refactor payment handlers', status: 'completed', type: 'WRITE_CODE' },
          { id: 3, name: 'Add Stripe webhooks', status: 'completed', type: 'WRITE_CODE' },
          { id: 4, name: 'Write tests', status: 'completed', type: 'WRITE_TEST' },
          { id: 5, name: 'Create PR', status: 'completed', type: 'CODE_REVIEW' }
        ]
      },
      logs: [
        { timestamp: '2024-01-14T18:30:00Z', message: 'PR created and ready for review', level: 'success' },
        { timestamp: '2024-01-14T18:00:00Z', message: 'All tests passed: 24/24', level: 'success' }
      ]
    },
    {
      id: 'session_004',
      title: 'Deploy monitoring dashboard',
      goal: 'Set up Grafana dashboards for system metrics',
      status: 'failed',
      confidence: 0.45,
      startedAt: '2024-01-14T10:00:00Z',
      updatedAt: '2024-01-14T11:30:00Z',
      progress: 30,
      currentTask: null,
      errorMessage: 'Failed to connect to Grafana API: Authentication error',
      plan: {
        totalTasks: 4,
        completedTasks: 1,
        tasks: [
          { id: 1, name: 'Analyze metrics requirements', status: 'completed', type: 'ANALYZE_CODE' },
          { id: 2, name: 'Configure Grafana connection', status: 'failed', type: 'SETUP_ENVIRONMENT' },
          { id: 3, name: 'Create dashboards', status: 'pending', type: 'WRITE_CODE' },
          { id: 4, name: 'Verify deployment', status: 'pending', type: 'VERIFICATION' }
        ]
      },
      logs: [
        { timestamp: '2024-01-14T11:30:00Z', message: 'Failed to connect to Grafana API: Authentication error', level: 'error' },
        { timestamp: '2024-01-14T11:00:00Z', message: 'Attempting Grafana API connection...', level: 'info' }
      ]
    }
  ]
)

/**
 * Sessions page for Meta Agent task execution monitoring.
 * 
 * Design: Follows Devin Sessions sidebar structure with MorningAI design system.
 * - Left panel: Session list with status indicators
 * - Right panel: Session details (plan, tasks, logs)
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 * 
 * Performance optimizations (#1973):
 * - MOCK_SESSIONS moved to module scope to prevent recreation
 * - useCallback for event handlers to prevent unnecessary re-renders
 * - useMemo for derived values (filteredSessions, sessionCounts)
 */
const POLLING_INTERVAL_MS = 10000

/**
 * Temporary fallback to MOCK_SESSIONS when API returns empty data.
 * This allows the UI to demonstrate all data states (Issue #16, PR 1: Sessions UI 骨架).
 * Will be removed once backend has real session data (PR 2: 後端 API 整合).
 */
const USE_MOCK_SESSIONS_FALLBACK = true

const Sessions = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [filter, setFilter] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const pollingIntervalRef = useRef(null)

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const statusParam = filter !== 'all' ? `?status=${filter}` : ''
      const response = await apiClientWithMeta(`/api/sessions${statusParam}`, { method: 'GET' })
      let sessionsData = response.data?.sessions || []
      
      // Fallback to MOCK_SESSIONS when API returns empty data (Issue #16, PR 1: Sessions UI 骨架)
      if (sessionsData.length === 0 && USE_MOCK_SESSIONS_FALLBACK) {
        sessionsData = [...MOCK_SESSIONS]
      }
      
      setSessions(sessionsData)
      
      setSelectedSession(prev => {
        if (!prev && sessionsData.length > 0) {
          return sessionsData[0]
        }
        return prev
      })
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.loadFailed', 'Failed to load sessions'),
        logContext: 'Sessions.loadSessions'
      })
      setError(errorMessage)
      
      // Also fallback to MOCK_SESSIONS on error if enabled
      if (USE_MOCK_SESSIONS_FALLBACK) {
        setSessions([...MOCK_SESSIONS])
        setSelectedSession(MOCK_SESSIONS[0])
      }
    } finally {
      setLoading(false)
    }
  }, [t, filter])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const refreshSessionsSilently = useCallback(async () => {
    try {
      setIsRefreshing(true)
      const statusParam = filter !== 'all' ? `?status=${filter}` : ''
      const response = await apiClientWithMeta(`/api/sessions${statusParam}`, { method: 'GET' })
      let sessionsData = response.data?.sessions || []
      
      // Fallback to MOCK_SESSIONS when API returns empty data (Issue #16, PR 1: Sessions UI 骨架)
      if (sessionsData.length === 0 && USE_MOCK_SESSIONS_FALLBACK) {
        sessionsData = [...MOCK_SESSIONS]
      }
      
      setSessions(sessionsData)
      
      setSelectedSession(prev => {
        if (prev) {
          const updatedSession = sessionsData.find(s => s.id === prev.id)
          return updatedSession || prev
        }
        return prev
      })
    } catch (err) {
      console.error('Silent refresh failed:', err)
    } finally {
      setIsRefreshing(false)
    }
  }, [filter])

  const hasActiveSessions = useMemo(() => {
    return sessions.some(s => s.status === 'running' || s.status === 'paused')
  }, [sessions])

  useEffect(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }

    if (autoRefresh && hasActiveSessions && !loading) {
      pollingIntervalRef.current = setInterval(() => {
        refreshSessionsSilently()
      }, POLLING_INTERVAL_MS)
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
    }
  }, [autoRefresh, hasActiveSessions, loading, refreshSessionsSilently])

  const handleToggleAutoRefresh = useCallback(() => {
    setAutoRefresh(prev => !prev)
  }, [])
  // Memoized filter handler
  const handleFilterChange = useCallback((newFilter) => {
    setFilter(newFilter)
  }, [])

  // Memoized session selection handler using functional update
  const handleSessionSelect = useCallback((session) => {
    setSelectedSession(session)
  }, [])

  const getStatusColor = useCallback((status) => {
    switch (status) {
      case 'running':
        return 'bg-calm-10 text-calm border-calm'
      case 'paused':
        return 'bg-wisdom-10 text-wisdom border-wisdom'
      case 'completed':
        return 'bg-growth-10 text-growth border-growth'
      case 'failed':
        return 'bg-energy-10 text-energy border-energy'
      default:
        return 'bg-neutral-100 text-neutral-600'
    }
  }, [])

  const getStatusIcon = useCallback((status) => {
    switch (status) {
      case 'running':
        return <Play />
      case 'paused':
        return <Pause />
      case 'completed':
        return <CheckCircle />
      case 'failed':
        return <XCircle />
      default:
        return <Clock />
    }
  }, [])

  const getStatusBadgeVariant = useCallback((status) => {
    switch (status) {
      case 'running':
        return 'default'
      case 'completed':
        return 'success'
      case 'failed':
        return 'destructive'
      case 'paused':
        return 'secondary'
      default:
        return 'secondary'
    }
  }, [])

  const getTaskStatusIcon = useCallback((status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-growth" />
      case 'running':
        return <Activity className="w-4 h-4 text-calm animate-pulse" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-energy" />
      case 'waiting_approval':
        return <AlertTriangle className="w-4 h-4 text-wisdom" />
      default:
        return <Clock className="w-4 h-4 text-neutral-400" />
    }
  }, [])

  const getTaskTypeIcon = useCallback((type) => {
    switch (type) {
      case 'ANALYZE_CODE':
        return <FileCode className="w-4 h-4" />
      case 'WRITE_CODE':
        return <FileCode className="w-4 h-4" />
      case 'WRITE_TEST':
      case 'RUN_TEST':
        return <TestTube className="w-4 h-4" />
      case 'CODE_REVIEW':
        return <ListTodo className="w-4 h-4" />
      case 'SETUP_ENVIRONMENT':
        return <Settings className="w-4 h-4" />
      case 'DEPLOYMENT':
        return <Rocket className="w-4 h-4" />
      case 'VERIFICATION':
        return <BadgeCheck className="w-4 h-4" />
      case 'DOCUMENTATION':
        return <FileText className="w-4 h-4" />
      case 'CLEANUP':
        return <Trash2 className="w-4 h-4" />
      default:
        return <Activity className="w-4 h-4" />
    }
  }, [])

  const formatTimestamp = useCallback((timestamp) => {
    if (!timestamp) return t('common.na', 'N/A')
    return new Date(timestamp).toLocaleString()
  }, [t])

  const formatRelativeTime = useCallback((timestamp) => {
    if (!timestamp) return ''
    const now = new Date()
    const date = new Date(timestamp)
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    
    if (minutes < 1) return t('sessions.time.justNow', 'just now')
    if (minutes < 60) return t('sessions.time.minutesAgo', '{{count}}m ago', { count: minutes })
    if (hours < 24) return t('sessions.time.hoursAgo', '{{count}}h ago', { count: hours })
    return new Date(timestamp).toLocaleString()
  }, [t])

  const getConfidenceColor = useCallback((confidence) => {
    if (confidence >= 0.8) return 'text-growth'
    if (confidence >= 0.6) return 'text-wisdom'
    return 'text-energy'
  }, [])

  // Memoized derived values to prevent recalculation on every render
  const filteredSessions = useMemo(() => {
    return sessions.filter(session => {
      if (filter === 'all') return true
      return session.status === filter
    })
  }, [sessions, filter])

  const sessionCounts = useMemo(() => ({
    all: sessions.length,
    running: sessions.filter(s => s.status === 'running').length,
    paused: sessions.filter(s => s.status === 'paused').length,
    completed: sessions.filter(s => s.status === 'completed').length,
    failed: sessions.filter(s => s.status === 'failed').length
  }), [sessions])

  const handlePauseSession = useCallback(async (sessionId) => {
    try {
      await apiClientWithMeta(`/api/sessions/${sessionId}/pause`, { method: 'POST' })
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, status: 'paused' } : s
      ))
      setSelectedSession(prev => 
        prev?.id === sessionId ? { ...prev, status: 'paused' } : prev
      )
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.pauseFailed', 'Failed to pause session'),
        logContext: 'Sessions.handlePauseSession'
      })
      setError(errorMessage)
    }
  }, [t])

  const handleResumeSession = useCallback(async (sessionId) => {
    try {
      await apiClientWithMeta(`/api/sessions/${sessionId}/resume`, { method: 'POST' })
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, status: 'running' } : s
      ))
      setSelectedSession(prev => 
        prev?.id === sessionId ? { ...prev, status: 'running' } : prev
      )
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.resumeFailed', 'Failed to resume session'),
        logContext: 'Sessions.handleResumeSession'
      })
      setError(errorMessage)
    }
  }, [t])

  const handleCancelSession = useCallback(async (sessionId) => {
    try {
      await apiClientWithMeta(`/api/sessions/${sessionId}/cancel`, { method: 'POST' })
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, status: 'failed' } : s
      ))
      setSelectedSession(prev => 
        prev?.id === sessionId ? { ...prev, status: 'failed' } : prev
      )
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.cancelFailed', 'Failed to cancel session'),
        logContext: 'Sessions.handleCancelSession'
      })
      setError(errorMessage)
    }
  }, [t])

  if (loading) {
    return (
      <div className="space-y-6" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-7 w-48 mb-2" aria-hidden="true" />
            <Skeleton className="h-5 w-96" aria-hidden="true" />
          </div>
          <Skeleton className="h-10 w-28" aria-hidden="true" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full" aria-hidden="true" />
            ))}
          </div>
          <div className="lg:col-span-2">
            <Skeleton className="h-96 w-full" aria-hidden="true" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="sessions-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            {t('sessions.title', 'Agent Sessions')}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {t('sessions.subtitle', 'Monitor and manage Meta Agent task execution sessions')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleAutoRefresh}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
              autoRefresh
                ? 'bg-growth-10 text-growth border border-growth-20'
                : 'bg-neutral-100 text-neutral-500 border border-neutral-200 dark:bg-neutral-800 dark:border-neutral-700'
            }`}
            title={autoRefresh 
              ? t('sessions.autoRefresh.enabled', 'Auto-refresh enabled (10s)')
              : t('sessions.autoRefresh.disabled', 'Auto-refresh disabled')
            }
          >
            <div className={`w-2 h-2 rounded-full ${
              autoRefresh && hasActiveSessions
                ? 'bg-growth animate-pulse'
                : autoRefresh
                  ? 'bg-growth'
                  : 'bg-neutral-400'
            }`} />
            <span>{t('sessions.autoRefresh.label', 'Auto')}</span>
            {isRefreshing && (
              <RotateCcw className="w-3 h-3 animate-spin" />
            )}
          </button>
          <AppleButton onClick={loadSessions} variant="outline" haptic="light" disabled={loading}>
            <RotateCcw className="w-4 h-4 mr-2" />
            {t('common.refresh', 'Refresh')}
          </AppleButton>
        </div>
      </div>

      {error && (
        <AppleErrorBanner
          title={t('common.error', 'Error')}
          message={error}
          onRetry={loadSessions}
        />
      )}

      {/* Stats Cards - KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <button 
          type="button"
          onClick={() => handleFilterChange('all')}
          className={`cursor-pointer transition-all rounded-xl text-left ${filter === 'all' ? 'ring-2 ring-primary-500' : ''}`}
        >
          <StatCard
            label={t('sessions.filter.all', 'All')}
            value={String(sessionCounts.all)}
            icon={<Activity className="w-5 h-5" />}
            variant="blue"
          />
        </button>
        <button 
          type="button"
          onClick={() => handleFilterChange('running')}
          className={`cursor-pointer transition-all rounded-xl text-left ${filter === 'running' ? 'ring-2 ring-primary-500' : ''}`}
        >
          <StatCard
            label={t('sessions.filter.running', 'Running')}
            value={String(sessionCounts.running)}
            icon={<Play className="w-5 h-5" />}
            variant="green"
          />
        </button>
        <button 
          type="button"
          onClick={() => handleFilterChange('paused')}
          className={`cursor-pointer transition-all rounded-xl text-left ${filter === 'paused' ? 'ring-2 ring-primary-500' : ''}`}
        >
          <StatCard
            label={t('sessions.filter.paused', 'Paused')}
            value={String(sessionCounts.paused)}
            icon={<Pause className="w-5 h-5" />}
            variant="yellow"
          />
        </button>
        <button 
          type="button"
          onClick={() => handleFilterChange('completed')}
          className={`cursor-pointer transition-all rounded-xl text-left ${filter === 'completed' ? 'ring-2 ring-primary-500' : ''}`}
        >
          <StatCard
            label={t('sessions.filter.completed', 'Completed')}
            value={String(sessionCounts.completed)}
            icon={<CheckCircle className="w-5 h-5" />}
            variant="green"
          />
        </button>
        <button 
          type="button"
          onClick={() => handleFilterChange('failed')}
          className={`cursor-pointer transition-all rounded-xl text-left ${filter === 'failed' ? 'ring-2 ring-primary-500' : ''}`}
        >
          <StatCard
            label={t('sessions.filter.failed', 'Failed')}
            value={String(sessionCounts.failed)}
            icon={<XCircle className="w-5 h-5" />}
            variant="red"
          />
        </button>
      </div>

      {/* Main Content: Session List + Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session List */}
        <SectionCard
          title={t('sessions.list.title', 'Sessions')}
          subtitle={`${filteredSessions.length} ${t('sessions.list.count', 'sessions')}`}
        >
          <div className="space-y-3">
            {filteredSessions.length === 0 ? (
              <div className="p-8 text-center">
                <Activity className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
                <p className="text-neutral-500">
                  {t('sessions.list.noSessions', 'No sessions found')}
                </p>
              </div>
            ) : (
              filteredSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleSessionSelect(session)}
                  className={`w-full text-left rounded-xl border p-4 transition-all ${
                    selectedSession?.id === session.id
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-[var(--border)] bg-[var(--surface)] hover:border-primary-300'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0 overflow-hidden">
                        <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                          {session.title}
                        </p>
                        <p className="text-xs text-[var(--text-secondary)] mt-1 truncate">
                          {session.goal}
                        </p>
                      </div>
                      <ChevronRight className={`w-4 h-4 ml-2 flex-shrink-0 ${
                        selectedSession?.id === session.id ? 'text-primary-500' : 'text-neutral-400'
                      }`} />
                    </div>
                    
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant={getStatusBadgeVariant(session.status)} className="text-xs">
                        {getStatusIcon(session.status)}
                        <span>{t(`sessions.status.${session.status}`, session.status)}</span>
                      </Badge>
                      
                      {session.requiresApproval && (
                        <Badge variant="warning" className="text-xs">
                          <AlertTriangle />
                          <span>{t('sessions.needsApproval', 'Needs Approval')}</span>
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                      <span>{formatRelativeTime(session.updatedAt)}</span>
                      <span className={getConfidenceColor(session.confidence)}>
                        {t('sessions.confidence', 'Confidence')}: {Math.round(session.confidence * 100)}%
                      </span>
                    </div>
                    
                    <Progress value={session.progress} className="h-1" />
                  </div>
                </button>
              ))
            )}
          </div>
        </SectionCard>

        {/* Session Details */}
        <div className="lg:col-span-2">
          {selectedSession ? (
            <SectionCard
              title={selectedSession.title}
              subtitle={selectedSession.goal}
              action={
                <Badge variant={getStatusBadgeVariant(selectedSession.status)} className="text-xs">
                  {getStatusIcon(selectedSession.status)}
                  <span>{t(`sessions.status.${selectedSession.status}`, selectedSession.status)}</span>
                </Badge>
              }
            >
              {/* Session Actions */}
              <div className="flex items-center gap-2 mb-4">
                {selectedSession.status === 'running' && (
                  <AppleButton variant="outline" size="sm" haptic="light" onClick={() => handlePauseSession(selectedSession.id)}>
                    <Pause className="w-4 h-4 mr-1" />
                    {t('sessions.actions.pause', 'Pause')}
                  </AppleButton>
                )}
                {selectedSession.status === 'paused' && (
                  <AppleButton variant="outline" size="sm" haptic="light" onClick={() => handleResumeSession(selectedSession.id)}>
                    <Play className="w-4 h-4 mr-1" />
                    {t('sessions.actions.resume', 'Resume')}
                  </AppleButton>
                )}
                {(selectedSession.status === 'running' || selectedSession.status === 'paused') && (
                  <AppleButton variant="outline" size="sm" haptic="light" onClick={() => handleCancelSession(selectedSession.id)}>
                    <StopCircle className="w-4 h-4 mr-1" />
                    {t('sessions.actions.cancel', 'Cancel')}
                  </AppleButton>
                )}
                {selectedSession.requiresApproval && (
                  <AppleButton variant="default" size="sm" haptic="medium" disabled>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    {t('sessions.actions.approve', 'Approve')}
                  </AppleButton>
                )}
              </div>

              {/* Session Content Tabs */}
              <Tabs defaultValue="plan" className="w-full">
                <TabsList className="w-full justify-start border-b border-[var(--border)] rounded-none bg-transparent px-5">
                  <TabsTrigger value="plan" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <ListTodo className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.plan', 'Task Plan')}
                  </TabsTrigger>
                  <TabsTrigger value="logs" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <Activity className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.logs', 'Activity Log')}
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="plan" className="p-5">
                  {/* Progress Summary */}
                  <div className="flex items-center justify-between mb-4 p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800">
                    <div>
                      <p className="text-sm text-[var(--text-secondary)]">
                        {t('sessions.plan.progress', 'Progress')}
                      </p>
                      <p className="text-lg font-semibold text-[var(--text-primary)]">
                        {selectedSession.plan.completedTasks} / {selectedSession.plan.totalTasks} {t('sessions.plan.tasks', 'tasks')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-[var(--text-secondary)]">
                        {t('sessions.confidence', 'Confidence')}
                      </p>
                      <p className={`text-lg font-semibold ${getConfidenceColor(selectedSession.confidence)}`}>
                        {Math.round(selectedSession.confidence * 100)}%
                      </p>
                    </div>
                  </div>

                  {/* Approval Banner */}
                  {selectedSession.requiresApproval && (
                    <div className="mb-4 p-4 rounded-lg bg-wisdom-10 border border-wisdom">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-wisdom flex-shrink-0 mt-1" />
                        <div>
                          <p className="font-medium text-wisdom-dark">
                            {t('sessions.approval.title', 'Approval Required')}
                          </p>
                          <p className="text-sm text-wisdom-dark mt-1">
                            {selectedSession.approvalReason}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error Banner */}
                  {selectedSession.errorMessage && (
                    <div className="mb-4 p-4 rounded-lg bg-energy-10 border border-energy">
                      <div className="flex items-start gap-3">
                        <XCircle className="w-5 h-5 text-energy flex-shrink-0 mt-1" />
                        <div>
                          <p className="font-medium text-energy-dark">
                            {t('sessions.error.title', 'Execution Failed')}
                          </p>
                          <p className="text-sm text-energy-dark mt-1">
                            {selectedSession.errorMessage}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Task List */}
                  <div className="space-y-2">
                    {selectedSession.plan.tasks.map((task, index) => (
                      <div
                        key={task.id}
                        className={`flex items-center gap-3 p-3 rounded-lg border ${
                          task.status === 'running'
                            ? 'border-calm bg-calm-10'
                            : task.status === 'completed'
                            ? 'border-growth-20 bg-growth-10'
                            : task.status === 'failed'
                            ? 'border-energy bg-energy-10'
                            : task.status === 'waiting_approval'
                            ? 'border-wisdom bg-wisdom-10'
                            : 'border-[var(--border)] bg-[var(--surface)]'
                        }`}
                      >
                        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-neutral-100 dark:bg-neutral-700 text-xs font-medium">
                          {index + 1}
                        </div>
                        {getTaskStatusIcon(task.status)}
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium ${
                            task.status === 'pending' ? 'text-neutral-500' : 'text-[var(--text-primary)]'
                          }`}>
                            {task.name}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {getTaskTypeIcon(task.type)}
                          <span className="text-xs text-[var(--text-secondary)]">
                            {t(`sessions.taskType.${task.type}`, task.type)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="logs" className="p-5">
                  <div className="space-y-3">
                    {selectedSession.logs.map((log, index) => (
                      <div
                        key={index}
                        className={`flex items-start gap-3 p-3 rounded-lg ${
                          log.level === 'error'
                            ? 'bg-energy-10'
                            : log.level === 'warning'
                            ? 'bg-wisdom-10'
                            : log.level === 'success'
                            ? 'bg-growth-10'
                            : 'bg-neutral-50 dark:bg-neutral-800'
                        }`}
                      >
                        <div className={`w-2 h-2 rounded-full mt-2 ${
                          log.level === 'error'
                            ? 'bg-energy'
                            : log.level === 'warning'
                            ? 'bg-wisdom'
                            : log.level === 'success'
                            ? 'bg-growth'
                            : 'bg-neutral-400'
                        }`} />
                        <div className="flex-1">
                          <p className="text-sm text-[var(--text-primary)]">
                            {log.message}
                          </p>
                          <p className="text-xs text-[var(--text-secondary)] mt-1">
                            {formatTimestamp(log.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>

              {/* Session Footer */}
              <div className="mt-4 pt-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)]">
                <div className="flex items-center justify-between">
                  <span>
                    {t('sessions.startedAt', 'Started')}: {formatTimestamp(selectedSession.startedAt)}
                  </span>
                  {selectedSession.prUrl && (
                    <a
                      href={selectedSession.prUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-500 hover:underline"
                    >
                      {t('sessions.viewPR', 'View Pull Request')}
                    </a>
                  )}
                </div>
              </div>
            </SectionCard>
          ) : filteredSessions.length === 0 ? (
            <SectionCard title={t('sessions.details.title', 'Session Details')}>
              <div className="p-8 text-center">
                <Activity className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
                <p className="text-neutral-500">
                  {t('sessions.details.noSessions', 'No sessions available')}
                </p>
                <p className="text-sm text-neutral-400 mt-2">
                  {t('sessions.details.noSessionsHint', 'Sessions will appear here when agents start executing tasks')}
                </p>
              </div>
            </SectionCard>
          ) : (
            <SectionCard title={t('sessions.details.title', 'Session Details')}>
              <div className="p-8 text-center">
                <ListTodo className="w-16 h-16 text-neutral-300 mx-auto mb-4" />
                <p className="text-neutral-500">
                  {t('sessions.selectSession', 'Select a session to view details')}
                </p>
              </div>
            </SectionCard>
          )}
        </div>
      </div>
    </div>
  )
}

export default Sessions
