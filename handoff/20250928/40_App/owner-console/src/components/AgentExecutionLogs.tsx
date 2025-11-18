import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle, 
  Badge, 
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Alert,
  AlertDescription,
  AlertTitle,
  StatusBadge,
  StatusBadgeProps,
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Skeleton,
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger
} from '@morningai/shared-ui'
import { 
  Filter,
  RefreshCw,
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle,
  Copy,
  ExternalLink,
  Eye
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'
import { buildTraceUrl } from '@/lib/trace'

const TRACE_VIEWER_URL = import.meta.env.VITE_TRACE_VIEWER_URL || ''

interface ExecutionLogAgent {
  agent_type?: string
  reputation_score?: number
}

interface ExecutionLogTimestamps {
  created_at?: string
  started_at?: string
  completed_at?: string
  updated_at?: string
}

interface ExecutionLog {
  task_id: string
  status: string
  task_type?: string
  agent?: ExecutionLogAgent
  tenant_id?: string
  duration_ms?: number
  timestamps?: ExecutionLogTimestamps
  error_message?: string
  trace_id?: string
  pr_url?: string
}

interface ExecutionSummary {
  total_executions: number
  success_rate?: number
  avg_duration_ms?: number
  status_counts?: Record<string, number>
}

interface PaginationState {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

interface FiltersState {
  status: string
  agent_id: string
  agent_type: string
  tenant_id: string
  task_type: string
  start_date: string
  end_date: string
  time_range: string
  sort_by: string
  sort_order: string
}

interface ExecutionLogsResponse {
  execution_logs: ExecutionLog[]
  summary: ExecutionSummary
  pagination: {
    total_items: number
    total_pages: number
  }
}

const warnedStatuses = new Set<string>()

/**
 * Normalize backend execution log status to StatusBadge variants
 * Handles common synonyms and case variations
 */
export const normalizeExecutionLogStatus = (
  status: string | undefined
): { normalized: StatusBadgeProps['status']; isKnown: boolean } => {
  if (!status) {
    return { normalized: 'queued', isKnown: false }
  }

  const normalized = status.toLowerCase().trim()

  const statusMap: Record<string, StatusBadgeProps['status']> = {
    'completed': 'completed',
    'success': 'completed',
    'succeeded': 'completed',
    'done': 'completed',
    'finished': 'completed',
    
    'running': 'running',
    'in_progress': 'running',
    'in-progress': 'running',
    'processing': 'running',
    'active': 'running',
    'executing': 'running',
    
    'failed': 'failed',
    'error': 'failed',
    'errored': 'failed',
    'exception': 'failed',
    'crashed': 'failed',
    
    'queued': 'queued',
    'pending': 'queued',
    'waiting': 'queued',
    
    'assigned': 'assigned',
    'scheduled': 'assigned',
    
    'cancelled': 'cancelled',
    'canceled': 'cancelled',
    'aborted': 'cancelled',
    'terminated': 'cancelled',
  }

  const mappedStatus = statusMap[normalized]
  
  if (!mappedStatus) {
    if (!warnedStatuses.has(normalized)) {
      console.warn(`[AgentExecutionLogs] Unknown execution log status: "${status}". Defaulting to "queued". Please add mapping if this is a valid status.`)
      warnedStatuses.add(normalized)
    }
    return { normalized: 'queued', isKnown: false }
  }

  return { normalized: mappedStatus, isKnown: true }
}

const AgentExecutionLogs = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [summary, setSummary] = useState<ExecutionSummary | null>(null)
  const [selectedLog, setSelectedLog] = useState<ExecutionLog | null>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [pagination, setPagination] = useState<PaginationState>({ 
    page: 1, 
    page_size: 50, 
    total_items: 0, 
    total_pages: 0 
  })
  
  const [filters, setFilters] = useState<FiltersState>({
    status: '',
    agent_id: '',
    agent_type: '',
    tenant_id: '',
    task_type: '',
    start_date: '',
    end_date: '',
    time_range: '',
    sort_by: 'created_at',
    sort_order: 'desc'
  })

  useEffect(() => {
    if (filters.time_range) {
      const now = new Date()
      let startDate = ''
      
      switch (filters.time_range) {
        case '24h':
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          break
        case '7d':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          break
        case '30d':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
          break
        case 'custom':
          return
        default:
          return
      }
      
      setFilters(prev => ({
        ...prev,
        start_date: startDate,
        end_date: now.toISOString().split('T')[0]
      }))
    }
  }, [filters.time_range])

  useEffect(() => {
    loadExecutionLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pagination.page, filters.sort_by, filters.sort_order])

  const loadExecutionLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
        sort_by: filters.sort_by,
        sort_order: filters.sort_order
      })
      
      if (filters.status) params.append('status', filters.status)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)
      if (filters.agent_type) params.append('agent_type', filters.agent_type)
      if (filters.tenant_id) params.append('tenant_id', filters.tenant_id)
      if (filters.task_type) params.append('task_type', filters.task_type)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await apiClient(`/admin/agent-execution-logs?${params.toString()}`) as ExecutionLogsResponse
      
      if (response.execution_logs) {
        setLogs(response.execution_logs)
        setSummary(response.summary)
        setPagination(prev => ({
          ...prev,
          total_items: response.pagination.total_items,
          total_pages: response.pagination.total_pages
        }))
      }
    } catch (err) {
      console.error('Failed to load execution logs:', err)
      setError((err as Error).message || 'Failed to load execution logs')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyFilters = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    loadExecutionLogs()
  }

  const handleClearFilters = () => {
    setFilters({
      status: '',
      agent_id: '',
      agent_type: '',
      tenant_id: '',
      task_type: '',
      start_date: '',
      end_date: '',
      time_range: '',
      sort_by: 'created_at',
      sort_order: 'desc'
    })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const formatDuration = (durationMs: number | undefined): string => {
    if (!durationMs) return t('common.na')
    const seconds = Math.floor(durationMs / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  const formatTimestamp = (timestamp: string | undefined): string => {
    if (!timestamp) return t('common.na')
    return new Date(timestamp).toLocaleString()
  }

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }))
  }

  const handleCopy = async (value: string, type: 'traceId' | 'taskId' | 'tenantId') => {
    try {
      await navigator.clipboard.writeText(value)
      const successKey = `governance.executionLogs.${type}Copied`
      toast.success(t(successKey))
    } catch (err) {
      console.error(`Failed to copy ${type}:`, err)
      const failureKey = `governance.executionLogs.${type}CopyFailed`
      toast.error(t(failureKey))
    }
  }

  const handleViewDetails = (log: ExecutionLog) => {
    setSelectedLog(log)
    setIsDrawerOpen(true)
  }

  const isEmptyValue = (value: any): boolean => {
    if (value == null) return true
    if (Array.isArray(value)) return value.length === 0
    if (typeof value === 'object') return Object.keys(value).length === 0
    return false
  }

  const showSkeleton = loading && logs.length === 0

  if (showSkeleton) {
    return (
      <div className="space-y-6" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        {/* Summary Statistics Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <Skeleton className="h-4 w-24" aria-hidden="true" />
                  <Skeleton className="h-5 w-5 rounded-full" aria-hidden="true" />
                </div>
                <Skeleton className="h-9 w-20" aria-hidden="true" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i}>
                  <Skeleton className="h-4 w-20 mb-2" aria-hidden="true" />
                  <Skeleton className="h-10 w-full" aria-hidden="true" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Table Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" aria-hidden="true" />
            <Skeleton className="h-4 w-64 mt-2" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-6 w-20" aria-hidden="true" />
                  <Skeleton className="h-4 w-32" aria-hidden="true" />
                  <Skeleton className="h-4 w-24" aria-hidden="true" />
                  <Skeleton className="h-4 w-28" aria-hidden="true" />
                  <Skeleton className="h-4 w-32" aria-hidden="true" />
                  <Skeleton className="h-4 w-16" aria-hidden="true" />
                  <Skeleton className="h-4 w-36" aria-hidden="true" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6" aria-busy={loading} data-testid="agent-execution-logs">
      {error && (
        <Alert variant="destructive" data-testid="error-alert">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadExecutionLogs} 
              variant="outline" 
              size="sm" 
              className="ml-4"
              aria-label={t('governance.executionLogs.retryLoad')}
              data-testid="retry-button"
            >
              {t('common.retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card data-testid="summary-total">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.totalExecutions')}</p>
                <Activity className="w-5 h-5 text-primary-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {summary.total_executions || 0}
              </p>
            </CardContent>
          </Card>

          <Card data-testid="summary-success-rate">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.successRate')}</p>
                <CheckCircle className="w-5 h-5 text-success-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {summary.success_rate ? `${(summary.success_rate * 100).toFixed(1)}%` : t('common.na')}
              </p>
            </CardContent>
          </Card>

          <Card data-testid="summary-avg-duration">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.avgDuration')}</p>
                <Clock className="w-5 h-5 text-accent-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {formatDuration(summary.avg_duration_ms)}
              </p>
            </CardContent>
          </Card>

          <Card data-testid="summary-status-breakdown">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.statusBreakdown')}</p>
                <Filter className="w-5 h-5 text-neutral-600" />
              </div>
              <div className="space-y-1">
                {summary.status_counts && Object.entries(summary.status_counts).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between text-sm">
                    <span className="text-neutral-600 dark:text-neutral-400">{t(`governance.executionLogs.statuses.${status}`)}</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            {t('common.filter')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.status')}
              </label>
              <Select 
                value={filters.status} 
                onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              >
                <SelectTrigger data-testid="filter-status">
                  <SelectValue placeholder={t('governance.executionLogs.filters.allStatuses')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t('governance.executionLogs.filters.allStatuses')}</SelectItem>
                  <SelectItem value="queued">{t('governance.executionLogs.statuses.queued')}</SelectItem>
                  <SelectItem value="assigned">{t('governance.executionLogs.statuses.assigned')}</SelectItem>
                  <SelectItem value="running">{t('governance.executionLogs.statuses.running')}</SelectItem>
                  <SelectItem value="completed">{t('governance.executionLogs.statuses.completed')}</SelectItem>
                  <SelectItem value="failed">{t('governance.executionLogs.statuses.failed')}</SelectItem>
                  <SelectItem value="cancelled">{t('governance.executionLogs.statuses.cancelled')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.agentType')}
              </label>
              <Select 
                value={filters.agent_type} 
                onValueChange={(value) => setFilters(prev => ({ ...prev, agent_type: value }))}
              >
                <SelectTrigger data-testid="filter-agent-type">
                  <SelectValue placeholder={t('governance.executionLogs.filters.allAgentTypes')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t('governance.executionLogs.filters.allAgentTypes')}</SelectItem>
                  <SelectItem value="dev_agent">{t('governance.executionLogs.agentTypes.devAgent')}</SelectItem>
                  <SelectItem value="ops_agent">{t('governance.executionLogs.agentTypes.opsAgent')}</SelectItem>
                  <SelectItem value="pm_agent">{t('governance.executionLogs.agentTypes.pmAgent')}</SelectItem>
                  <SelectItem value="growth_strategist">{t('governance.executionLogs.agentTypes.growthStrategist')}</SelectItem>
                  <SelectItem value="meta_agent">{t('governance.executionLogs.agentTypes.metaAgent')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.agentId')}
              </label>
              <Input
                value={filters.agent_id}
                onChange={(e) => setFilters(prev => ({ ...prev, agent_id: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.agentIdPlaceholder')}
                data-testid="filter-agent-id"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.taskType')}
              </label>
              <Input
                value={filters.task_type}
                onChange={(e) => setFilters(prev => ({ ...prev, task_type: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.taskTypePlaceholder')}
                data-testid="filter-task-type"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.timeRange')}
              </label>
              <Select 
                value={filters.time_range} 
                onValueChange={(value) => setFilters(prev => ({ ...prev, time_range: value }))}
              >
                <SelectTrigger data-testid="filter-time-range">
                  <SelectValue placeholder={t('governance.executionLogs.filters.selectTimeRange')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t('governance.executionLogs.filters.allTime')}</SelectItem>
                  <SelectItem value="24h">{t('governance.executionLogs.filters.last24Hours')}</SelectItem>
                  <SelectItem value="7d">{t('governance.executionLogs.filters.last7Days')}</SelectItem>
                  <SelectItem value="30d">{t('governance.executionLogs.filters.last30Days')}</SelectItem>
                  <SelectItem value="custom">{t('governance.executionLogs.filters.customRange')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.startDate')}
              </label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value, time_range: 'custom' }))}
                disabled={filters.time_range !== 'custom' && filters.time_range !== ''}
                data-testid="filter-start-date"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.endDate')}
              </label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value, time_range: 'custom' }))}
                disabled={filters.time_range !== 'custom' && filters.time_range !== ''}
                data-testid="filter-end-date"
              />
            </div>

            <div className="flex items-end gap-2">
              <Button onClick={handleApplyFilters} className="flex-1" data-testid="apply-filters">
                {t('governance.executionLogs.filters.applyFilters')}
              </Button>
              <Button onClick={handleClearFilters} variant="outline" data-testid="clear-filters">
                {t('governance.executionLogs.filters.clearFilters')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Execution Logs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{t('governance.executionLogs.title')}</CardTitle>
              <CardDescription>{t('governance.executionLogs.subtitle')}</CardDescription>
            </div>
            <Button onClick={loadExecutionLogs} variant="outline" size="sm" disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {t('governance.refresh')}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {logs.length === 0 && !loading ? (
            <div className="text-center py-8" role="region" aria-labelledby="empty-logs-title">
              <p id="empty-logs-title" className="text-neutral-500">{t('governance.executionLogs.noLogs')}</p>
            </div>
          ) : (
            <>
              {/* Desktop Table View (md and up) */}
              <div className="hidden md:block">
                <Table data-testid="execution-table">
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('governance.executionLogs.columns.status')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.taskId')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.taskType')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.agent')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.tenant')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.duration')}</TableHead>
                      <TableHead>{t('governance.executionLogs.details.createdAt')}</TableHead>
                      <TableHead className="text-right">{t('common.actions')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => {
                      const { normalized: normalizedStatus, isKnown } = normalizeExecutionLogStatus(log.status)
                      return (
                        <TableRow 
                          key={log.task_id}
                          data-testid="execution-row"
                          data-task-id={log.task_id}
                          data-status={normalizedStatus}
                          data-trace-id={log.trace_id || ''}
                          data-tenant-id={log.tenant_id || ''}
                        >
                          <TableCell>
                            <StatusBadge status={normalizedStatus} showIcon data-status={normalizedStatus}>
                              {isKnown 
                                ? t(`governance.executionLogs.statuses.${normalizedStatus}`)
                                : t('governance.executionLogs.statuses.unknown')
                              }
                            </StatusBadge>
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            <div className="flex items-center gap-2">
                              <span>{log.task_id?.substring(0, 12)}...</span>
                              {log.trace_id && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0"
                                    onClick={() => handleCopy(log.trace_id!, 'traceId')}
                                    aria-label={t('governance.executionLogs.copyTraceId')}
                                    title={t('governance.executionLogs.copyTraceId')}
                                    data-testid="copy-trace-id"
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                  {TRACE_VIEWER_URL && (
                                    <a
                                      href={buildTraceUrl(TRACE_VIEWER_URL, log.trace_id)}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center justify-center h-6 w-6 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                                      aria-label={t('governance.executionLogs.viewTraceDetails')}
                                      title={t('governance.executionLogs.viewTraceDetails')}
                                      data-testid="trace-link"
                                    >
                                      <ExternalLink className="h-3 w-3 text-primary-600 dark:text-primary-400" />
                                    </a>
                                  )}
                                </>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            {log.task_type ? (
                              <Badge variant="outline" className="text-xs">
                                {log.task_type}
                              </Badge>
                            ) : (
                              <span className="text-neutral-400">{t('common.na')}</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {log.agent ? (
                              <div>
                                <p className="font-medium text-sm">{log.agent.agent_type || t('common.na')}</p>
                                {log.agent.reputation_score !== undefined && (
                                  <p className="text-xs text-neutral-500">
                                    {t('governance.agents.reputation')}: {log.agent.reputation_score}
                                  </p>
                                )}
                              </div>
                            ) : (
                              <span className="text-neutral-400">{t('common.na')}</span>
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {log.tenant_id ? `${log.tenant_id.substring(0, 12)}...` : t('common.na')}
                          </TableCell>
                          <TableCell className="font-medium">
                            {formatDuration(log.duration_ms)}
                          </TableCell>
                          <TableCell className="text-xs">
                            {formatTimestamp(log.timestamps?.created_at)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetails(log)}
                              aria-label={t('governance.executionLogs.viewDetails')}
                              data-testid="view-details"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>

              {/* Mobile Card View (below md) */}
              <div className="md:hidden space-y-3">
                {logs.map((log) => {
                  const { normalized: normalizedStatus, isKnown } = normalizeExecutionLogStatus(log.status)
                  return (
                    <div key={log.task_id} className="border rounded-lg p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <StatusBadge status={normalizedStatus} showIcon>
                              {isKnown 
                                ? t(`governance.executionLogs.statuses.${normalizedStatus}`)
                                : t('governance.executionLogs.statuses.unknown')
                              }
                            </StatusBadge>
                            <span className="text-sm font-mono text-neutral-600 dark:text-neutral-400">
                              {log.task_id?.substring(0, 12)}...
                            </span>
                            {log.trace_id && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  onClick={() => handleCopy(log.trace_id!, 'traceId')}
                                  aria-label={t('governance.executionLogs.copyTraceId')}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                                {TRACE_VIEWER_URL && (
                                  <a
                                    href={buildTraceUrl(TRACE_VIEWER_URL, log.trace_id)}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center justify-center h-6 w-6 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                                    aria-label={t('governance.executionLogs.viewTraceDetails')}
                                    title={t('governance.executionLogs.viewTraceDetails')}
                                  >
                                    <ExternalLink className="h-3 w-3 text-primary-600 dark:text-primary-400" />
                                  </a>
                                )}
                              </>
                            )}
                            {log.task_type && (
                              <Badge variant="outline" className="text-xs">
                                {log.task_type}
                              </Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            {log.agent && (
                              <div>
                                <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.agent')}</p>
                                <p className="font-medium">{log.agent.agent_type || t('common.na')}</p>
                                {log.agent.reputation_score !== undefined && (
                                  <p className="text-xs text-neutral-500">
                                    {t('governance.agents.reputation')}: {log.agent.reputation_score}
                                  </p>
                                )}
                              </div>
                            )}
                            
                            {log.tenant_id && (
                              <div>
                                <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.tenant')}</p>
                                <p className="font-medium font-mono text-xs">{log.tenant_id.substring(0, 12)}...</p>
                              </div>
                            )}
                            
                            <div>
                              <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.duration')}</p>
                              <p className="font-medium">{formatDuration(log.duration_ms)}</p>
                            </div>
                            
                            <div>
                              <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.details.createdAt')}</p>
                              <p className="font-medium text-xs">{formatTimestamp(log.timestamps?.created_at)}</p>
                            </div>
                          </div>

                          {log.error_message && (
                            <div className="mt-3 p-2 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-sm text-error-800 dark:text-error-400">
                              <p className="font-semibold">{t('governance.executionLogs.details.errorMessage')}:</p>
                              <p className="text-xs mt-1">{log.error_message}</p>
                            </div>
                          )}

                          <div className="mt-3 flex justify-end">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleViewDetails(log)}
                              aria-label={t('governance.executionLogs.viewDetails')}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              {t('governance.executionLogs.viewDetails')}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                {t('governance.executionLogs.pagination.showing', {
                  start: (pagination.page - 1) * pagination.page_size + 1,
                  end: Math.min(pagination.page * pagination.page_size, pagination.total_items),
                  total: pagination.total_items
                })}
              </p>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious 
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.page > 1) {
                          handlePageChange(pagination.page - 1)
                        }
                      }}
                      onKeyDown={(e) => {
                        if (pagination.page === 1 && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault()
                        }
                      }}
                      aria-disabled={pagination.page === 1}
                      tabIndex={pagination.page === 1 ? -1 : 0}
                      className={pagination.page === 1 ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <span className="text-sm text-neutral-600 dark:text-neutral-400 px-4">
                      {t('governance.executionLogs.pagination.page', {
                        current: pagination.page,
                        total: pagination.total_pages
                      })}
                    </span>
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext 
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.page < pagination.total_pages) {
                          handlePageChange(pagination.page + 1)
                        }
                      }}
                      onKeyDown={(e) => {
                        if (pagination.page === pagination.total_pages && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault()
                        }
                      }}
                      aria-disabled={pagination.page === pagination.total_pages}
                      tabIndex={pagination.page === pagination.total_pages ? -1 : 0}
                      className={pagination.page === pagination.total_pages ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution Log Details Sheet */}
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetContent className="w-full sm:max-w-2xl overflow-y-auto" data-testid="details-drawer">
          <SheetHeader>
            <SheetTitle>{t('governance.executionLogs.details.title')}</SheetTitle>
            <SheetDescription>
              {t('governance.executionLogs.details.subtitle')}
            </SheetDescription>
          </SheetHeader>

          {selectedLog && (
            <div className="mt-6 space-y-6" data-testid="details-content">
              {/* Status and Basic Info */}
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    {t('governance.executionLogs.columns.status')}
                  </label>
                  <div className="mt-1">
                    <StatusBadge status={normalizeExecutionLogStatus(selectedLog.status).normalized} showIcon>
                      {t(`governance.executionLogs.statuses.${normalizeExecutionLogStatus(selectedLog.status).normalized}`)}
                    </StatusBadge>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    {t('governance.executionLogs.columns.taskId')}
                  </label>
                  <div className="mt-1 flex items-center gap-2">
                    <code className="text-sm font-mono bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded">
                      {selectedLog.task_id}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleCopy(selectedLog.task_id, 'taskId')}
                      aria-label={t('governance.executionLogs.copyTaskId')}
                      data-testid="copy-task-id"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {selectedLog.trace_id && (
                  <div>
                    <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      {t('governance.executionLogs.details.traceId')}
                    </label>
                    <div className="mt-1 flex items-center gap-2">
                      <code className="text-sm font-mono bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded">
                        {selectedLog.trace_id}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => handleCopy(selectedLog.trace_id!, 'traceId')}
                        aria-label={t('governance.executionLogs.copyTraceId')}
                        data-testid="copy-trace-id-drawer"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      {TRACE_VIEWER_URL && (
                        <a
                          href={buildTraceUrl(TRACE_VIEWER_URL, selectedLog.trace_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center h-7 w-7 rounded hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                          aria-label={t('governance.executionLogs.viewTraceDetails')}
                          title={t('governance.executionLogs.viewTraceDetails')}
                          data-testid="trace-link-drawer"
                        >
                          <ExternalLink className="h-3 w-3 text-primary-600 dark:text-primary-400" />
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {selectedLog.task_type && (
                  <div>
                    <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      {t('governance.executionLogs.columns.taskType')}
                    </label>
                    <div className="mt-1">
                      <Badge variant="outline">{selectedLog.task_type}</Badge>
                    </div>
                  </div>
                )}

                {selectedLog.pr_url && (
                  <div>
                    <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      {t('governance.executionLogs.details.prUrl')}
                    </label>
                    <div className="mt-1 max-w-[420px]">
                      <a
                        href={selectedLog.pr_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={selectedLog.pr_url}
                        className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 inline-flex items-center gap-1 truncate"
                      >
                        <span className="truncate">{selectedLog.pr_url}</span>
                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Agent Info */}
              {selectedLog.agent && (
                <div className="border-t pt-4" data-testid="details-agent">
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3">
                    {t('governance.executionLogs.columns.agent')}
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('governance.agents.type')}
                      </span>
                      <span className="text-sm font-medium">{selectedLog.agent.agent_type || t('common.na')}</span>
                    </div>
                    {selectedLog.agent.reputation_score !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-sm text-neutral-600 dark:text-neutral-400">
                          {t('governance.agents.reputation')}
                        </span>
                        <span className="text-sm font-medium">{selectedLog.agent.reputation_score}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Timing Info */}
              <div className="border-t pt-4" data-testid="details-timestamps">
                <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3">
                  {t('governance.executionLogs.details.timing')}
                </h3>
                <div className="space-y-2">
                  {selectedLog.timestamps?.created_at && (
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('governance.executionLogs.details.createdAt')}
                      </span>
                      <span className="text-sm font-medium">{formatTimestamp(selectedLog.timestamps.created_at)}</span>
                    </div>
                  )}
                  {selectedLog.timestamps?.started_at && (
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('governance.executionLogs.details.startedAt')}
                      </span>
                      <span className="text-sm font-medium">{formatTimestamp(selectedLog.timestamps.started_at)}</span>
                    </div>
                  )}
                  {selectedLog.timestamps?.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('governance.executionLogs.details.completedAt')}
                      </span>
                      <span className="text-sm font-medium">{formatTimestamp(selectedLog.timestamps.completed_at)}</span>
                    </div>
                  )}
                  {selectedLog.duration_ms !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600 dark:text-neutral-400">
                        {t('governance.executionLogs.columns.duration')}
                      </span>
                      <span className="text-sm font-medium">{formatDuration(selectedLog.duration_ms)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Error Message */}
              {selectedLog.error_message && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-semibold text-error-600 dark:text-error-400 mb-3">
                    {t('governance.executionLogs.details.errorMessage')}
                  </h3>
                  <div className="p-3 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded">
                    <p className="text-sm text-error-800 dark:text-error-400 font-mono whitespace-pre-wrap">
                      {selectedLog.error_message}
                    </p>
                  </div>
                </div>
              )}

              {/* Tenant Info */}
              {selectedLog.tenant_id && (
                <div className="border-t pt-4">
                  <h3 className="text-sm font-semibold text-neutral-900 dark:text-white mb-3">
                    {t('governance.executionLogs.columns.tenant')}
                  </h3>
                  <div className="flex items-center gap-2">
                    <code className="text-sm font-mono bg-neutral-100 dark:bg-neutral-800 px-2 py-1 rounded">
                      {selectedLog.tenant_id}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0"
                      onClick={() => handleCopy(selectedLog.tenant_id!, 'tenantId')}
                      aria-label={t('governance.executionLogs.copyTenantId')}
                      data-testid="copy-tenant-id"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  )
}

export default AgentExecutionLogs
