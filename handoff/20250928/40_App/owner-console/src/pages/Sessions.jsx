import { useState, useEffect, useCallback, useMemo, lazy, Suspense } from 'react'
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
  SectionCard,
  Switch,
  AppleButton
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
  Trash2,
  Plus,
  Edit3,
  Lightbulb
} from 'lucide-react'
import { AppleErrorBanner } from '@/components/AppleErrorBanner'
import { apiClientWithMeta, handleApiError } from '@/lib/api-client'
import { 
  CodeReviewPanel,
  TestResultsPanel,
  ConfidenceApproval,
  FileDiffViewer,
  SessionInsights,
  SessionCommandInput,
  CONFIDENCE_THRESHOLD,
  MEDIUM_CONFIDENCE_THRESHOLD,
  validateConfidence
} from '@/components/sessions'

// Lazy load task plan components to improve FCP (First Contentful Paint)
// These components are only needed when a session is selected
const TaskPlanTimeline = lazy(() => import('@/components/sessions/TaskPlanTimeline'))
const TaskEditor = lazy(() => import('@/components/sessions/TaskEditor'))
const ApprovalWorkflow = lazy(() => import('@/components/sessions/ApprovalWorkflow'))

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
      ],
      codeReview: {
        prUrl: 'https://github.com/example/repo/pull/456',
        prStatus: 'pending',
        checksStatus: { passed: 8, failed: 0, pending: 2, total: 10 },
        fileChanges: [
          { path: 'src/auth/google-oauth.ts', additions: 45, deletions: 0, status: 'added' },
          { path: 'src/auth/github-oauth.ts', additions: 52, deletions: 0, status: 'added' },
          { path: 'src/auth/index.ts', additions: 12, deletions: 3, status: 'modified' }
        ],
        fileDiffs: [
          {
            path: 'src/auth/google-oauth.ts',
            language: 'typescript',
            additions: 45,
            deletions: 0,
            diffLines: [
              { type: 'addition', content: "import { OAuth2Client } from 'google-auth-library';", oldLineNumber: null, newLineNumber: 1 },
              { type: 'addition', content: "import { config } from '../config';", oldLineNumber: null, newLineNumber: 2 },
              { type: 'addition', content: '', oldLineNumber: null, newLineNumber: 3 },
              { type: 'addition', content: 'export class GoogleOAuthHandler {', oldLineNumber: null, newLineNumber: 4 },
              { type: 'addition', content: '  private client: OAuth2Client;', oldLineNumber: null, newLineNumber: 5 },
              { type: 'addition', content: '', oldLineNumber: null, newLineNumber: 6 },
              { type: 'addition', content: '  constructor() {', oldLineNumber: null, newLineNumber: 7 },
              { type: 'addition', content: '    this.client = new OAuth2Client(config.google.clientId);', oldLineNumber: null, newLineNumber: 8 },
              { type: 'addition', content: '  }', oldLineNumber: null, newLineNumber: 9 },
              { type: 'addition', content: '}', oldLineNumber: null, newLineNumber: 10 }
            ]
          },
          {
            path: 'src/auth/index.ts',
            language: 'typescript',
            additions: 12,
            deletions: 3,
            diffLines: [
              { type: 'context', content: "import { AuthProvider } from './types';", oldLineNumber: 1, newLineNumber: 1 },
              { type: 'deletion', content: "import { BasicAuth } from './basic-auth';", oldLineNumber: 2, newLineNumber: null },
              { type: 'addition', content: "import { GoogleOAuthHandler } from './google-oauth';", oldLineNumber: null, newLineNumber: 2 },
              { type: 'addition', content: "import { GitHubOAuthHandler } from './github-oauth';", oldLineNumber: null, newLineNumber: 3 },
              { type: 'context', content: '', oldLineNumber: 3, newLineNumber: 4 },
              { type: 'deletion', content: 'export const authProvider = new BasicAuth();', oldLineNumber: 4, newLineNumber: null },
              { type: 'addition', content: 'export const googleAuth = new GoogleOAuthHandler();', oldLineNumber: null, newLineNumber: 5 },
              { type: 'addition', content: 'export const githubAuth = new GitHubOAuthHandler();', oldLineNumber: null, newLineNumber: 6 }
            ]
          }
        ],
        reviewComments: [],
        reviewers: [
          { name: 'Alice Chen', status: 'pending', avatarUrl: null }
        ]
      },
      testResults: {
        totalTests: 12,
        passedTests: 12,
        failedTests: 0,
        skippedTests: 0,
        duration: 4.5,
        testSuites: [
          {
            name: 'GoogleOAuthHandler',
            status: 'passed',
            duration: 2.1,
            tests: [
              { name: 'should redirect to Google OAuth', status: 'passed', duration: 0.3 },
              { name: 'should handle callback', status: 'passed', duration: 0.5 },
              { name: 'should create user session', status: 'passed', duration: 0.4 }
            ]
          },
          {
            name: 'GitHubOAuthHandler',
            status: 'passed',
            duration: 2.4,
            tests: [
              { name: 'should redirect to GitHub OAuth', status: 'passed', duration: 0.3 },
              { name: 'should handle callback', status: 'passed', duration: 0.6 },
              { name: 'should create user session', status: 'passed', duration: 0.5 }
            ]
          }
        ]
      },
      confidenceFactors: [
        { name: 'Code complexity', trend: 'positive', impact: 15, description: 'Low cyclomatic complexity' },
        { name: 'Test coverage', trend: 'positive', impact: 20, description: '95% coverage achieved' },
        { name: 'Similar patterns', trend: 'positive', impact: 10, description: 'Matches existing auth patterns' }
      ],
      riskAssessment: {
        level: 'low',
        summary: 'Low risk implementation with well-tested OAuth patterns',
        factors: [
          { category: 'Security', level: 'low', description: 'Using established OAuth2 libraries' },
          { category: 'Performance', level: 'low', description: 'Minimal impact on response times' },
          { category: 'Compatibility', level: 'medium', description: 'Requires user migration for existing accounts' }
        ]
      }
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
      ],
      codeReview: {
        prUrl: 'https://github.com/example/repo/pull/123',
        prStatus: 'approved',
        checksStatus: { passed: 15, failed: 0, pending: 0, total: 15 },
        fileChanges: [
          { path: 'src/payments/stripe-handler.ts', additions: 120, deletions: 45, status: 'modified' },
          { path: 'src/payments/webhooks.ts', additions: 85, deletions: 0, status: 'added' },
          { path: 'src/payments/types.ts', additions: 25, deletions: 10, status: 'modified' }
        ],
        fileDiffs: [
          {
            path: 'src/payments/stripe-handler.ts',
            language: 'typescript',
            additions: 120,
            deletions: 45,
            diffLines: [
              { type: 'context', content: "import Stripe from 'stripe';", oldLineNumber: 1, newLineNumber: 1 },
              { type: 'deletion', content: "import { legacyPaymentProcessor } from './legacy';", oldLineNumber: 2, newLineNumber: null },
              { type: 'addition', content: "import { PaymentProcessor } from './processor';", oldLineNumber: null, newLineNumber: 2 },
              { type: 'addition', content: "import { WebhookHandler } from './webhooks';", oldLineNumber: null, newLineNumber: 3 },
              { type: 'context', content: '', oldLineNumber: 3, newLineNumber: 4 },
              { type: 'deletion', content: 'export class StripeHandler {', oldLineNumber: 4, newLineNumber: null },
              { type: 'addition', content: 'export class StripeHandler extends PaymentProcessor {', oldLineNumber: null, newLineNumber: 5 },
              { type: 'context', content: '  private stripe: Stripe;', oldLineNumber: 5, newLineNumber: 6 },
              { type: 'addition', content: '  private webhookHandler: WebhookHandler;', oldLineNumber: null, newLineNumber: 7 }
            ]
          },
          {
            path: 'src/payments/webhooks.ts',
            language: 'typescript',
            additions: 85,
            deletions: 0,
            diffLines: [
              { type: 'addition', content: "import Stripe from 'stripe';", oldLineNumber: null, newLineNumber: 1 },
              { type: 'addition', content: "import { logger } from '../utils/logger';", oldLineNumber: null, newLineNumber: 2 },
              { type: 'addition', content: '', oldLineNumber: null, newLineNumber: 3 },
              { type: 'addition', content: 'export class WebhookHandler {', oldLineNumber: null, newLineNumber: 4 },
              { type: 'addition', content: '  async handleEvent(event: Stripe.Event) {', oldLineNumber: null, newLineNumber: 5 },
              { type: 'addition', content: "    logger.info('Processing webhook event', { type: event.type });", oldLineNumber: null, newLineNumber: 6 },
              { type: 'addition', content: '  }', oldLineNumber: null, newLineNumber: 7 },
              { type: 'addition', content: '}', oldLineNumber: null, newLineNumber: 8 }
            ]
          }
        ],
        reviewComments: [
          { id: 1, author: 'Bob Smith', body: 'Great refactoring! Much cleaner now.', path: 'src/payments/stripe-handler.ts', line: 45, resolved: true }
        ],
        reviewers: [
          { name: 'Bob Smith', status: 'approved', avatarUrl: null },
          { name: 'Carol Wang', status: 'approved', avatarUrl: null }
        ]
      },
      testResults: {
        totalTests: 24,
        passedTests: 24,
        failedTests: 0,
        skippedTests: 0,
        duration: 8.2,
        testSuites: [
          {
            name: 'StripeHandler',
            status: 'passed',
            duration: 3.5,
            tests: [
              { name: 'should process payment', status: 'passed', duration: 0.8 },
              { name: 'should handle refund', status: 'passed', duration: 0.6 },
              { name: 'should validate card', status: 'passed', duration: 0.4 }
            ]
          },
          {
            name: 'WebhookHandler',
            status: 'passed',
            duration: 4.7,
            tests: [
              { name: 'should verify signature', status: 'passed', duration: 0.5 },
              { name: 'should handle payment_intent.succeeded', status: 'passed', duration: 0.7 },
              { name: 'should handle payment_intent.failed', status: 'passed', duration: 0.6 }
            ]
          }
        ]
      },
      confidenceFactors: [
        { name: 'Code quality', trend: 'positive', impact: 25, description: 'Clean architecture patterns' },
        { name: 'Test coverage', trend: 'positive', impact: 30, description: '100% coverage achieved' },
        { name: 'Review feedback', trend: 'positive', impact: 20, description: 'All reviewers approved' }
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
      ],
      testResults: {
        totalTests: 5,
        passedTests: 2,
        failedTests: 3,
        skippedTests: 0,
        duration: 2.1,
        testSuites: [
          {
            name: 'GrafanaConnection',
            status: 'failed',
            duration: 2.1,
            tests: [
              { name: 'should connect to API', status: 'failed', duration: 1.0, errorMessage: 'Authentication failed: Invalid API key' },
              { name: 'should fetch dashboards', status: 'failed', duration: 0.5, errorMessage: 'Connection refused' },
              { name: 'should validate config', status: 'passed', duration: 0.3 },
              { name: 'should parse response', status: 'passed', duration: 0.2 },
              { name: 'should handle timeout', status: 'failed', duration: 0.1, errorMessage: 'Test skipped due to connection failure' }
            ]
          }
        ]
      },
      confidenceFactors: [
        { name: 'API connectivity', trend: 'negative', impact: -30, description: 'Cannot connect to Grafana API' },
        { name: 'Configuration', trend: 'negative', impact: -15, description: 'Missing or invalid credentials' },
        { name: 'Code quality', trend: 'neutral', impact: 0, description: 'Code structure is acceptable' }
      ]
    }
  ]
)

/**
 * Helper function to calculate session counts from a sessions array.
 * Used when falling back to MOCK_SESSIONS to keep counts consistent with displayed sessions.
 */
const calculateSessionCounts = (sessionsArray) => {
  return {
    all: sessionsArray.length,
    running: sessionsArray.filter(s => s.status === 'running').length,
    paused: sessionsArray.filter(s => s.status === 'paused').length,
    completed: sessionsArray.filter(s => s.status === 'completed').length,
    failed: sessionsArray.filter(s => s.status === 'failed').length
  }
}

// Pre-calculated counts for MOCK_SESSIONS to avoid recalculating on each fallback
const MOCK_SESSIONS_COUNTS = calculateSessionCounts(MOCK_SESSIONS)

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
// CONFIDENCE_THRESHOLD and MEDIUM_CONFIDENCE_THRESHOLD are now imported from @/components/sessions

const Sessions = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [filter, setFilter] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  // Task Plan Visualization state (#1823)
  const [isTaskEditorOpen, setIsTaskEditorOpen] = useState(false)
  const [editingTask, setEditingTask] = useState(null)
  const [isNewTask, setIsNewTask] = useState(false)
  const [isApprovalOpen, setIsApprovalOpen] = useState(false)
  const [approvalTask, setApprovalTask] = useState(null)
  const [isEditMode, setIsEditMode] = useState(false)
  // Confidence Approval state (#1823)
  const [isConfidenceApprovalOpen, setIsConfidenceApprovalOpen] = useState(false)
  // Issue #1981: Use counts from API response instead of calculating locally
  const [sessionCounts, setSessionCounts] = useState({ all: 0, running: 0, paused: 0, completed: 0, failed: 0 })

  // Monitor FCP (First Contentful Paint) performance metric
  useEffect(() => {
    if (typeof window === 'undefined' || !window.PerformanceObserver) {
      return
    }

    try {
      const observer = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntriesByName('first-contentful-paint')
        if (entries.length > 0) {
          const fcp = entries[0]
          // Log FCP metric for monitoring (can be sent to analytics service)
          console.debug('[Sessions] FCP:', Math.round(fcp.startTime), 'ms')
        }
      })
      
      observer.observe({ type: 'paint', buffered: true })
      
      return () => observer.disconnect()
    } catch (e) {
      // PerformanceObserver not supported or paint type not available
      console.debug('[Sessions] FCP monitoring not available')
    }
  }, [])

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const statusParam = filter !== 'all' ? `?status=${filter}` : ''
      const response = await apiClientWithMeta(`/api/sessions${statusParam}`, { method: 'GET' })
      let sessionsData = response.data?.sessions || []
      // Issue #1981: Use counts from API response (calculated from all sessions, not filtered)
      const countsData = response.data?.counts || { all: 0, running: 0, paused: 0, completed: 0, failed: 0 }
      
      // Use MOCK_SESSIONS as fallback when API returns empty (for demo/preview)
      // This allows users to see the TaskPlanTimeline, TaskEditor, and ApprovalWorkflow components
      // Also sync counts with MOCK_SESSIONS to avoid UI inconsistency (counts showing 0 while list shows sessions)
      if (sessionsData.length === 0) {
        sessionsData = [...MOCK_SESSIONS]
        setSessions(sessionsData)
        setSessionCounts(MOCK_SESSIONS_COUNTS)
      } else {
        setSessions(sessionsData)
        setSessionCounts(countsData)
      }
      
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
      // Use MOCK_SESSIONS as fallback on error (for demo/preview)
      // Also sync counts with MOCK_SESSIONS to avoid UI inconsistency
      setSessions([...MOCK_SESSIONS])
      setSessionCounts(MOCK_SESSIONS_COUNTS)
      setSelectedSession(MOCK_SESSIONS[0])
    } finally {
      setLoading(false)
    }
  }, [t, filter])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Issue #1996: Use AbortController to handle race conditions when filter changes
  const refreshSessionsSilently = useCallback(async (signal) => {
    const currentFilter = filter
    try {
      setIsRefreshing(true)
      const statusParam = currentFilter !== 'all' ? `?status=${currentFilter}` : ''
      const response = await apiClientWithMeta(`/api/sessions${statusParam}`, { 
        method: 'GET',
        signal 
      })
      
      // Verify filter hasn't changed during request
      if (signal?.aborted) return
      
      let sessionsData = response.data?.sessions || []
      // Issue #1981: Use counts from API response (calculated from all sessions, not filtered)
      const countsData = response.data?.counts || { all: 0, running: 0, paused: 0, completed: 0, failed: 0 }
      
      // Use MOCK_SESSIONS as fallback when API returns empty (for demo/preview)
      // Also sync counts with MOCK_SESSIONS to avoid UI inconsistency (counts showing 0 while list shows sessions)
      if (sessionsData.length === 0) {
        sessionsData = [...MOCK_SESSIONS]
        setSessions(sessionsData)
        setSessionCounts(MOCK_SESSIONS_COUNTS)
      } else {
        setSessions(sessionsData)
        setSessionCounts(countsData)
      }
      
      // Issue #1997: Return null instead of prev when session not found
      setSelectedSession(prev => {
        if (prev) {
          const updatedSession = sessionsData.find(s => s.id === prev.id)
          return updatedSession || null
        }
        return prev
      })
    } catch (err) {
      if (err.name === 'AbortError') return
      console.error('Silent refresh failed:', err)
    } finally {
      if (!signal?.aborted) {
        setIsRefreshing(false)
      }
    }
  }, [filter])

  const hasActiveSessions = useMemo(() => {
    return sessions.some(s => s.status === 'running' || s.status === 'paused')
  }, [sessions])

  // Issue #1998: Simplified polling useEffect following React conventions
  useEffect(() => {
    if (!autoRefresh || !hasActiveSessions || loading) {
      return
    }

    const controller = new AbortController()
    const intervalId = setInterval(() => {
      refreshSessionsSilently(controller.signal)
    }, POLLING_INTERVAL_MS)

    return () => {
      controller.abort()
      clearInterval(intervalId)
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

  // Guard clause: validate confidence to handle null/undefined/NaN/out-of-range values
  const getConfidenceColor = useCallback((confidence) => {
    const validConfidence = validateConfidence(confidence)
    if (validConfidence >= CONFIDENCE_THRESHOLD) return 'text-growth'
    if (validConfidence >= MEDIUM_CONFIDENCE_THRESHOLD) return 'text-wisdom'
    return 'text-energy'
  }, [])

  // Memoized derived values to prevent recalculation on every render
  const filteredSessions = useMemo(() => {
    return sessions.filter(session => {
      if (filter === 'all') return true
      return session.status === filter
    })
  }, [sessions, filter])

  // Issue #2066: Memoize currentTask lookup to avoid recalculation on every render
  const currentTaskName = useMemo(() => {
    return selectedSession?.plan?.tasks?.find(t => t.status === 'in_progress')?.name || ''
  }, [selectedSession])

  // Issue #1981: sessionCounts is now a state variable populated from API response
  // This ensures counts reflect ALL sessions, not just the filtered/paginated ones

  // Issue #1991: DRY handler for session actions (pause/resume/cancel)
  const handleSessionAction = useCallback(async (sessionId, action, newStatus) => {
    try {
      await apiClientWithMeta(`/api/sessions/${sessionId}/${action}`, { method: 'POST' })
      setSessions(prev => prev.map(s => 
        s.id === sessionId ? { ...s, status: newStatus } : s
      ))
      setSelectedSession(prev => 
        prev?.id === sessionId ? { ...prev, status: newStatus } : prev
      )
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t(`sessions.error.${action}Failed`, `Failed to ${action} session`),
        logContext: `Sessions.handleSessionAction.${action}`
      })
      setError(errorMessage)
    }
  }, [t])

  // Convenience wrappers for backward compatibility
  const handlePauseSession = useCallback((sessionId) => 
    handleSessionAction(sessionId, 'pause', 'paused'), [handleSessionAction])
  const handleResumeSession = useCallback((sessionId) => 
    handleSessionAction(sessionId, 'resume', 'running'), [handleSessionAction])
  const handleCancelSession = useCallback((sessionId) => 
    handleSessionAction(sessionId, 'cancel', 'failed'), [handleSessionAction])

  // Task Plan Visualization handlers (#1823)
  const handleToggleEditMode = useCallback(() => {
    setIsEditMode(prev => !prev)
  }, [])

  const handleOpenTaskEditor = useCallback((task = null) => {
    setEditingTask(task)
    setIsNewTask(!task)
    setIsTaskEditorOpen(true)
  }, [])

  const handleCloseTaskEditor = useCallback(() => {
    setIsTaskEditorOpen(false)
    setEditingTask(null)
    setIsNewTask(false)
  }, [])

  const handleSaveTask = useCallback(async (taskData) => {
    if (!selectedSession) return

    try {
      if (isNewTask) {
        await apiClientWithMeta(`/api/sessions/${selectedSession.id}/tasks`, {
          method: 'POST',
          body: JSON.stringify(taskData)
        })
      } else {
        await apiClientWithMeta(`/api/sessions/${selectedSession.id}/tasks/${taskData.id}`, {
          method: 'PUT',
          body: JSON.stringify(taskData)
        })
      }
      
      refreshSessionsSilently()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.saveTaskFailed', 'Failed to save task'),
        logContext: 'Sessions.handleSaveTask'
      })
      setError(errorMessage)
    }
  }, [selectedSession, isNewTask, refreshSessionsSilently, t])

  const handleDeleteTask = useCallback(async (taskId) => {
    if (!selectedSession) return

    try {
      await apiClientWithMeta(`/api/sessions/${selectedSession.id}/tasks/${taskId}`, {
        method: 'DELETE'
      })
      
      refreshSessionsSilently()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.deleteTaskFailed', 'Failed to delete task'),
        logContext: 'Sessions.handleDeleteTask'
      })
      setError(errorMessage)
    }
  }, [selectedSession, refreshSessionsSilently, t])

  const handleTaskReorder = useCallback(async (fromIndex, toIndex) => {
    if (!selectedSession) return

    const newTasks = [...selectedSession.plan.tasks]
    const [movedTask] = newTasks.splice(fromIndex, 1)
    newTasks.splice(toIndex, 0, movedTask)

    setSelectedSession(prev => ({
      ...prev,
      plan: { ...prev.plan, tasks: newTasks }
    }))

    try {
      await apiClientWithMeta(`/api/sessions/${selectedSession.id}/tasks/reorder`, {
        method: 'POST',
        body: JSON.stringify({ taskIds: newTasks.map(t => t.id) })
      })
    } catch (err) {
      refreshSessionsSilently()
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.reorderFailed', 'Failed to reorder tasks'),
        logContext: 'Sessions.handleTaskReorder'
      })
      setError(errorMessage)
    }
  }, [selectedSession, refreshSessionsSilently, t])

  const handleOpenApproval = useCallback((task) => {
    setApprovalTask(task)
    setIsApprovalOpen(true)
  }, [])

  const handleCloseApproval = useCallback(() => {
    setIsApprovalOpen(false)
    setApprovalTask(null)
  }, [])

  const handleTaskApproved = useCallback((taskId) => {
    refreshSessionsSilently()
    handleCloseApproval()
  }, [refreshSessionsSilently, handleCloseApproval])

  const handleTaskRejected = useCallback((taskId) => {
    refreshSessionsSilently()
    handleCloseApproval()
  }, [refreshSessionsSilently, handleCloseApproval])

  // Confidence Approval handlers (#1823)
  const handleOpenConfidenceApproval = useCallback(() => {
    setIsConfidenceApprovalOpen(true)
  }, [])

  const handleCloseConfidenceApproval = useCallback(() => {
    setIsConfidenceApprovalOpen(false)
  }, [])

  const handleConfidenceApprove = useCallback(async ({ comment }) => {
    if (!selectedSession?.id) {
      return
    }
    try {
      await apiClientWithMeta(`/api/sessions/${selectedSession.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ comment, action: 'approve' })
      })
      refreshSessionsSilently()
      handleCloseConfidenceApproval()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.approveFailed', 'Failed to approve session'),
        logContext: 'Sessions.handleConfidenceApprove'
      })
      setError(errorMessage)
    }
  }, [selectedSession, refreshSessionsSilently, handleCloseConfidenceApproval, t])

  const handleConfidenceRequestChanges = useCallback(async ({ comment }) => {
    if (!selectedSession?.id) {
      return
    }
    try {
      await apiClientWithMeta(`/api/sessions/${selectedSession.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ comment, action: 'request_changes' })
      })
      refreshSessionsSilently()
      handleCloseConfidenceApproval()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.error.requestChangesFailed', 'Failed to request changes'),
        logContext: 'Sessions.handleConfidenceRequestChanges'
      })
      setError(errorMessage)
    }
  }, [selectedSession, refreshSessionsSilently, handleCloseConfidenceApproval, t])

  const handleSendCommand = useCallback(async ({ sessionId, command, type, timestamp }) => {
    if (!sessionId || !command) {
      return
    }
    try {
      await apiClientWithMeta(`/api/sessions/${sessionId}/command`, {
        method: 'POST',
        body: JSON.stringify({ command, type: type || 'user_command', timestamp })
      })
      refreshSessionsSilently()
    } catch (err) {
      const errorMessage = handleApiError(err, {
        defaultMessage: t('sessions.command.error.sendFailed', 'Failed to send command'),
        logContext: 'Sessions.handleSendCommand'
      })
      setError(errorMessage)
      throw err
    }
  }, [refreshSessionsSilently, t])

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
    <div className="space-y-8" data-testid="sessions-page">
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
          <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
            {t('sessions.autoRefresh.label', 'Auto')}
            <Switch
              checked={autoRefresh}
              onCheckedChange={handleToggleAutoRefresh}
              aria-label={autoRefresh 
                ? t('sessions.autoRefresh.enabled', 'Auto-refresh enabled (10s)')
                : t('sessions.autoRefresh.disabled', 'Auto-refresh disabled')
              }
            />
            {isRefreshing && (
              <RotateCcw className="w-3 h-3 animate-spin text-[var(--text-secondary)]" />
            )}
          </label>
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

      {/* Stats Cards - Using StatCard components */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { key: 'all', label: t('sessions.filter.all', 'All'), icon: Activity, variant: 'default' },
          { key: 'running', label: t('sessions.filter.running', 'Running'), icon: Play, variant: 'blue' },
          { key: 'paused', label: t('sessions.filter.paused', 'Paused'), icon: Pause, variant: 'yellow' },
          { key: 'completed', label: t('sessions.filter.completed', 'Completed'), icon: CheckCircle, variant: 'green' },
          { key: 'failed', label: t('sessions.filter.failed', 'Failed'), icon: XCircle, variant: 'red' }
        ].map(({ key, label, icon: Icon, variant }) => (
          <button
            key={key}
            type="button"
            aria-pressed={filter === key}
            onClick={() => handleFilterChange(key)}
            className={`text-left transition-all rounded-xl ${
              filter === key
                ? 'ring-2 ring-primary-500 ring-offset-2'
                : 'hover:ring-1 hover:ring-primary-300'
            }`}
          >
            <StatCard
              label={label}
              value={String(sessionCounts[key])}
              icon={<Icon className="w-5 h-5" />}
              variant={variant}
            />
          </button>
        ))}
      </div>

      {/* Main Content: Session List + Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Session List */}
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-[var(--text-secondary)] px-1">
            {t('sessions.list.title', 'Sessions')} ({filteredSessions.length})
          </h2>
          
          {filteredSessions.length === 0 ? (
            <SectionCard
              title={t('sessions.list.empty', 'No Sessions')}
              subtitle={t('sessions.list.emptySubtitle', 'No sessions match the current filter')}
            >
              <div className="py-4 text-center">
                <Activity className="w-12 h-12 text-neutral-300 mx-auto" />
              </div>
            </SectionCard>
          ): (
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

        {/* Session Details */}
        <div className="lg:col-span-2">
          {selectedSession ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
              {/* Session Header */}
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                      {selectedSession.title}
                    </h2>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      {selectedSession.goal}
                    </p>
                  </div>
                  <Badge variant={getStatusBadgeVariant(selectedSession.status)} className="text-xs">
                    {getStatusIcon(selectedSession.status)}
                    <span>{t(`sessions.status.${selectedSession.status}`, selectedSession.status)}</span>
                  </Badge>
                </div>
                
                {/* Session Actions */}
                <div className="flex items-center gap-2 mt-4">
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
                  {/* Confidence Review Button (#1823) */}
                  {selectedSession.confidence !== undefined && (
                    <AppleButton 
                      variant="outline" 
                      size="sm" 
                      haptic="light" 
                      onClick={handleOpenConfidenceApproval}
                    >
                      <AlertTriangle className="w-4 h-4 mr-1" />
                      {t('sessions.actions.reviewConfidence', 'Review Confidence')}
                      <span className={`ml-2 px-1 py-0 rounded text-xs font-medium ${getConfidenceColor(selectedSession.confidence)}`}>
                        {Math.round(selectedSession.confidence * 100)}%
                      </span>
                    </AppleButton>
                  )}
                </div>
              </div>

              {/* Session Content Tabs */}
              <Tabs defaultValue="plan" className="w-full">
                <TabsList className="w-full justify-start border-b border-[var(--border)] rounded-none bg-transparent px-5">
                  <TabsTrigger value="plan" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <ListTodo className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.plan', 'Task Plan')}
                  </TabsTrigger>
                  <TabsTrigger value="codeReview" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <FileCode className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.codeReview', 'Code Review')}
                  </TabsTrigger>
                  <TabsTrigger value="tests" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <TestTube className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.tests', 'Tests')}
                  </TabsTrigger>
                  <TabsTrigger value="logs" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <Activity className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.logs', 'Activity Log')}
                  </TabsTrigger>
                  <TabsTrigger value="insights" className="data-[state=active]:border-b-2 data-[state=active]:border-primary-500">
                    <Lightbulb className="w-4 h-4 mr-2" />
                    {t('sessions.tabs.insights', 'Insights')}
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="plan" className="p-5">
                  {/* Edit Mode Toggle & Add Task Button */}
                  <div className="flex items-center justify-end gap-2 mb-4">
                    {selectedSession.status === 'paused' && (
                      <>
                        <AppleButton
                          variant={isEditMode ? 'default' : 'outline'}
                          size="sm"
                          haptic="light"
                          onClick={handleToggleEditMode}
                        >
                          <Edit3 className="w-4 h-4 mr-1" />
                          {isEditMode 
                            ? t('sessions.plan.editModeOn', 'Editing') 
                            : t('sessions.plan.editMode', 'Edit Plan')
                          }
                        </AppleButton>
                        {isEditMode && (
                          <AppleButton
                            variant="outline"
                            size="sm"
                            haptic="light"
                            onClick={() => handleOpenTaskEditor()}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            {t('sessions.plan.addTask', 'Add Task')}
                          </AppleButton>
                        )}
                      </>
                    )}
                  </div>

                  {/* Approval Banner */}
                  {selectedSession.requiresApproval && (
                    <div className="mb-4 p-4 rounded-lg bg-wisdom-10 border border-wisdom">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-wisdom flex-shrink-0 mt-1" />
                        <div className="flex-1">
                          <p className="font-medium text-wisdom-dark">
                            {t('sessions.approval.title', 'Approval Required')}
                          </p>
                          <p className="text-sm text-wisdom-dark mt-1">
                            {selectedSession.approvalReason}
                          </p>
                        </div>
                        <AppleButton
                          variant="default"
                          size="sm"
                          haptic="medium"
                          onClick={() => {
                            const waitingTask = selectedSession.plan.tasks.find(t => t.status === 'waiting_approval')
                            if (waitingTask) {
                              handleOpenApproval(waitingTask)
                            }
                          }}
                        >
                          <CheckCircle className="w-4 h-4 mr-1" />
                          {t('sessions.approval.review', 'Review')}
                        </AppleButton>
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

                  {/* Task Plan Timeline (#1823) */}
                  <Suspense fallback={
                    <div className="space-y-3 animate-pulse">
                      <div className="h-16 bg-neutral-100 dark:bg-neutral-800 rounded-xl" />
                      <div className="h-24 bg-neutral-100 dark:bg-neutral-800 rounded-xl" />
                      <div className="h-24 bg-neutral-100 dark:bg-neutral-800 rounded-xl" />
                    </div>
                  }>
                    <TaskPlanTimeline
                      tasks={selectedSession.plan.tasks}
                      completedTasks={selectedSession.plan.completedTasks}
                      totalTasks={selectedSession.plan.totalTasks}
                      confidence={selectedSession.confidence}
                      editable={isEditMode && selectedSession.status === 'paused'}
                      onTaskReorder={handleTaskReorder}
                      onTaskEdit={handleOpenTaskEditor}
                      onTaskApprove={(taskId) => {
                        const task = selectedSession.plan.tasks.find(t => t.id === taskId)
                        if (task) handleOpenApproval(task)
                      }}
                    />
                  </Suspense>
                </TabsContent>

                <TabsContent value="codeReview" className="p-5">
                  {selectedSession.codeReview ? (
                    <div className="space-y-6">
                      <CodeReviewPanel
                        prUrl={selectedSession.codeReview.prUrl}
                        prStatus={selectedSession.codeReview.prStatus}
                        reviewComments={selectedSession.codeReview.reviewComments}
                        fileChanges={selectedSession.codeReview.fileChanges}
                        reviewers={selectedSession.codeReview.reviewers}
                        checksStatus={selectedSession.codeReview.checksStatus}
                      />
                      
                      {/* File Diffs (#1823) */}
                      {selectedSession.codeReview.fileDiffs && selectedSession.codeReview.fileDiffs.length > 0 && (
                        <div className="space-y-4">
                          <h3 className="text-sm font-medium text-[var(--text-primary)]">
                            {t('sessions.codeReview.fileDiffs', 'File Changes')}
                          </h3>
                          {selectedSession.codeReview.fileDiffs.map((diff) => (
                            <FileDiffViewer
                              key={diff.path}
                              filePath={diff.path}
                              language={diff.language}
                              diffLines={diff.diffLines}
                              additions={diff.additions}
                              deletions={diff.deletions}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <FileCode className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
                      <p className="text-sm text-[var(--text-secondary)]">
                        {t('sessions.codeReview.noPR', 'No pull request created yet')}
                      </p>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="tests" className="p-5">
                  {selectedSession.testResults ? (
                    <TestResultsPanel
                      testSuites={selectedSession.testResults.testSuites}
                      totalTests={selectedSession.testResults.totalTests}
                      passedTests={selectedSession.testResults.passedTests}
                      failedTests={selectedSession.testResults.failedTests}
                      skippedTests={selectedSession.testResults.skippedTests}
                      duration={selectedSession.testResults.duration}
                    />
                  ) : (
                    <div className="text-center py-8">
                      <TestTube className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
                      <p className="text-sm text-[var(--text-secondary)]">
                        {t('sessions.tests.noResults', 'No test results available')}
                      </p>
                    </div>
                  )}
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

                <TabsContent value="insights" className="p-5">
                  <SessionInsights
                    sessionId={selectedSession.id}
                    isOpen={true}
                  />
                </TabsContent>
              </Tabs>

              {/* Session Command Input (#1823) - Quick command/response feature */}
              {/* #2178: Removed redundant disabled prop - handled internally via sessionStatus */}
              <SessionCommandInput
                sessionId={selectedSession.id}
                sessionStatus={selectedSession.status}
                onSendCommand={handleSendCommand}
              />

              {/* Session Footer */}
              <div className="px-5 py-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)]">
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
            </div>
          ) : (
            <SectionCard
              title={t('sessions.details.title', 'Session Details')}
              subtitle={t('sessions.details.subtitle', 'Select a session from the list')}
            >
              <div className="py-8 text-center">
                <ListTodo className="w-16 h-16 text-neutral-300 mx-auto" />
              </div>
            </SectionCard>
          )}
        </div>
      </div>

      {/* Task Editor Modal (#1823) */}
      <Suspense fallback={null}>
        <TaskEditor
          task={editingTask}
          isOpen={isTaskEditorOpen}
          onClose={handleCloseTaskEditor}
          onSave={handleSaveTask}
          onDelete={handleDeleteTask}
          isNewTask={isNewTask}
        />
      </Suspense>

      {/* Approval Workflow Modal (#1823) */}
      {selectedSession && approvalTask && (
        <Suspense fallback={null}>
          <ApprovalWorkflow
            sessionId={selectedSession.id}
            taskId={approvalTask.id}
            isOpen={isApprovalOpen}
            onClose={handleCloseApproval}
            onApproved={handleTaskApproved}
            onRejected={handleTaskRejected}
            approvalData={{
              reason: approvalTask.approvalReason || selectedSession.approvalReason,
              riskLevel: approvalTask.riskLevel || 'medium',
              affectedResources: approvalTask.affectedResources || [],
              taskName: approvalTask.name,
              description: approvalTask.description
            }}
          />
        </Suspense>
      )}

      {/* Confidence Approval Modal (#1823) */}
      {selectedSession && (
        <ConfidenceApproval
          isOpen={isConfidenceApprovalOpen}
          onClose={handleCloseConfidenceApproval}
          onApprove={handleConfidenceApprove}
          onRequestChanges={handleConfidenceRequestChanges}
          confidence={selectedSession.confidence}
          confidenceThreshold={CONFIDENCE_THRESHOLD}
          factors={selectedSession.confidenceFactors || []}
          sessionTitle={selectedSession.title}
          currentTask={currentTaskName}
          riskAssessment={selectedSession.riskAssessment || null}
        />
      )}
    </div>
  )
}

export default Sessions
